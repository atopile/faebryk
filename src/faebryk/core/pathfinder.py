# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import io
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise
from typing import Any, Callable, cast

from more_itertools import partition
from rich.console import Console
from rich.table import Table

from faebryk.core.bfs import BFSPath, bfs_visit
from faebryk.core.graphinterface import (
    GraphInterface,
    GraphInterfaceHierarchical,
    GraphInterfaceSelf,
)
from faebryk.core.link import LinkDirectConditional
from faebryk.core.moduleinterface import (
    GraphInterfaceHierarchicalModuleSpecial,
    GraphInterfaceModuleConnection,
    ModuleInterface,
)
from faebryk.core.node import (
    GraphInterfaceHierarchicalNode,
    Node,
)
from faebryk.libs.exceptions import FaebrykException
from faebryk.libs.util import ConfigFlag, consume, groupby

logger = logging.getLogger(__name__)

type Path = BFSPath

CPP = ConfigFlag(
    "CORE_MIFS_CPP", default=True, descr="Use C++ implementation of PathFinder"
)


def perf_counter(*args, **kwargs):
    @dataclass
    class Counter:
        in_cnt: int = 0
        weak_in_cnt: int = 0
        out_weaker: int = 0
        out_stronger: int = 0
        out_cnt: int = 0
        time_spent: float = 0
        multi: bool = False

    class Counters:
        def __init__(self):
            self.counters: dict[Callable[[Path], Any], Counter] = {}

        def reset(self):
            for k, v in self.counters.items():
                self.counters[k] = Counter(multi=v.multi)

        def __repr__(self):
            table = Table(title="Filter Counters")
            table.add_column("func", style="cyan", width=30)
            table.add_column("in", style="green", justify="right")
            table.add_column("weak in", style="green", justify="right")
            table.add_column("out", style="green", justify="right")
            table.add_column("drop", style="cyan", justify="center")
            table.add_column("filt", style="magenta", justify="right")
            table.add_column("weaker", style="green", justify="right")
            table.add_column("stronger", style="green", justify="right")
            table.add_column("time", style="yellow", justify="right")
            table.add_column("time/in", style="yellow", justify="right")

            for section in partition(lambda x: x[1].multi, self.counters.items()):
                for k, v in sorted(
                    section,
                    key=lambda x: (x[1].out_cnt, x[1].in_cnt),
                    reverse=True,
                ):
                    table.add_row(
                        k.__name__,
                        str(v.in_cnt),
                        str(v.weak_in_cnt),
                        str(v.out_cnt),
                        "x" if getattr(k, "discovery_filter", False) else "",
                        f"{(1-v.out_cnt/v.in_cnt)*100:.1f} %" if v.in_cnt else "-",
                        str(v.out_weaker),
                        str(v.out_stronger),
                        f"{v.time_spent*1000:.2f} ms",
                        f"{v.time_spent/v.in_cnt*1000*1000:.2f} us"
                        if v.in_cnt
                        else "-",
                    )
                table.add_section()

            table.add_section()
            table.add_row(
                "Total",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                f"{sum(v.time_spent for v in self.counters.values())*1000:.2f} ms",
                f"{sum(v.time_spent/v.in_cnt for v in self.counters.values() if v.in_cnt)*1000*1000:.2f} us",
            )

            console = Console(record=True, width=120, file=io.StringIO())
            console.print(table)
            return console.export_text(styles=True)

    multi = kwargs.get("multi", False)

    if multi:

        def perf_counter_multi[F: Callable[[list[Path]], Any]](f: F) -> F:
            perf_counter.counters.counters[f] = Counter(multi=True)

            def wrapper(paths: list[Path], *args, **kwargs):
                counter = perf_counter.counters.counters[f]

                counter.in_cnt += len(paths)
                counter.weak_in_cnt += sum(1 for p in paths if not p.strong)
                confidence = [p.confidence for p in paths]

                start = time.perf_counter()
                res = f(paths, *args, **kwargs)
                counter.time_spent += time.perf_counter() - start

                counter.out_cnt += len(res)
                counter.out_stronger += sum(
                    1 for p, c in zip(paths, confidence) if p.confidence > c
                )
                counter.out_weaker += sum(
                    1 for p, c in zip(paths, confidence) if p.confidence < c
                )

                return res

            return wrapper

        w = perf_counter_multi

    else:

        def perf_counter_[F: Callable[[Path], Any]](f: F) -> F:
            perf_counter.counters.counters[f] = Counter()

            def wrapper(path: Path, *args, **kwargs):
                counter = perf_counter.counters.counters[f]

                counter.in_cnt += 1
                if not path.strong:
                    counter.weak_in_cnt += 1

                confidence = path.confidence

                start = time.perf_counter()
                res = f(path, *args, **kwargs)
                counter.time_spent += time.perf_counter() - start

                if res:
                    counter.out_cnt += 1
                if path.confidence > confidence:
                    counter.out_stronger += 1
                elif path.confidence < confidence:
                    counter.out_weaker += 1

                return res

            return wrapper

        w = perf_counter_

    if not hasattr(perf_counter, "counters"):
        perf_counter.counters = Counters()
    if len(args) == 1 and callable(args[0]):
        f = args[0]
        return w(f)
    return w


def discovery[F: Callable[[Path], Any]](f: F) -> F:
    def wrapper(path: Path, *args, **kwargs):
        res = f(path, *args, **kwargs)
        if not res:
            path.filtered = True
        return res

    wrapper.discovery_filter = True
    wrapper.__name__ = f.__name__

    return wrapper


class PathFinder:
    @dataclass
    class PathStackElement:
        parent_type: type[Node]
        child_type: type[Node]
        parent_gif: GraphInterfaceHierarchical
        name: str
        up: bool

    @dataclass
    class UnresolvedStackElement:
        elem: "PathFinder.PathStackElement"
        promise: bool

        def match(self, elem: "PathFinder.PathStackElement"):
            return (
                self.elem.parent_type == elem.parent_type
                and self.elem.child_type == elem.child_type
                and self.elem.name == elem.name
                and self.elem.up != elem.up
            )

    type PathStack = list[PathStackElement]

    @staticmethod
    def _extend_path_hierarchy_stack(edge: tuple[GraphInterface, GraphInterface]):
        up = GraphInterfaceHierarchicalNode.is_uplink(edge)
        if not up and not GraphInterfaceHierarchicalNode.is_downlink(edge):
            return
        edge = cast(tuple[GraphInterfaceHierarchical, GraphInterfaceHierarchical], edge)
        child_gif = edge[0 if up else 1]
        parent_gif = edge[1 if up else 0]

        p = child_gif.get_parent()
        assert p
        name = p[1]
        return PathFinder.PathStackElement(
            parent_type=type(parent_gif.node),
            child_type=type(child_gif.node),
            parent_gif=parent_gif,
            name=name,
            up=up,
        )

    @staticmethod
    def _get_path_hierarchy_stack(
        path_: Path,
        stack_cache: dict[tuple[GraphInterface, ...], "PathStack"] | None = None,
    ) -> PathStack:
        out: PathFinder.PathStack = []

        path = path_.path
        if (
            stack_cache
            and (cached_path := stack_cache.get(tuple(path[:-1]))) is not None
        ):
            out = cached_path
            path = path[-2:]

        for edge in pairwise(path):
            elem = PathFinder._extend_path_hierarchy_stack(edge)
            if elem:
                out.append(elem)

        if stack_cache is not None:
            stack_cache[tuple(path)] = out
        return out

    @staticmethod
    def _extend_fold_stack(
        elem: "PathFinder.PathStackElement",
        unresolved_stack: list["PathFinder.UnresolvedStackElement"],
        promise_stack: list["PathFinder.PathStackElement"],
    ):
        if unresolved_stack and unresolved_stack[-1].match(elem):
            promise = unresolved_stack.pop().promise
            if promise:
                promise_stack.append(elem)

        else:
            # if down & multipath -> promise
            promise = not elem.up and bool(
                consume(
                    elem.parent_gif.node.get_children_gen(
                        direct_only=True,
                        types=ModuleInterface,
                    ),
                    2,
                )
            )

            unresolved_stack.append(PathFinder.UnresolvedStackElement(elem, promise))

            if promise:
                promise_stack.append(elem)

    @staticmethod
    def _fold_stack(stack: PathStack):
        unresolved_stack: list[PathFinder.UnresolvedStackElement] = []
        promise_stack: list[PathFinder.PathStackElement] = []
        for elem in stack:
            PathFinder._extend_fold_stack(elem, unresolved_stack, promise_stack)

        return unresolved_stack, promise_stack

    # Path filters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @perf_counter
    @discovery
    @staticmethod
    def _filter_path_gif_type(path: Path):
        return isinstance(
            path.last,
            (
                GraphInterfaceSelf,
                GraphInterfaceHierarchicalNode,
                GraphInterfaceHierarchicalModuleSpecial,
                GraphInterfaceModuleConnection,
            ),
        )

    @perf_counter
    @discovery
    @staticmethod
    def _filter_path_by_node_type(path: Path):
        # TODO for module specialization also modules will be allowed
        return isinstance(path.last.node, ModuleInterface)

    @staticmethod
    def _check_tri_edge(tri_edge_in: list[GraphInterface]):
        if not len(tri_edge_in) == 3:
            return True

        if not all(
            isinstance(gif, GraphInterfaceHierarchicalNode) for gif in tri_edge_in
        ):
            return True

        tri_edge = cast(
            tuple[
                GraphInterfaceHierarchicalNode,
                GraphInterfaceHierarchicalNode,
                GraphInterfaceHierarchicalNode,
            ],
            tri_edge_in,
        )

        # check if child->parent->child
        if (
            not tri_edge[0].is_parent
            and tri_edge[1].is_parent
            and not tri_edge[2].is_parent
        ):
            return False

        return True

    @perf_counter
    @discovery
    @staticmethod
    def _filter_path_by_dead_end_split(path: Path):
        return PathFinder._check_tri_edge(path.path[-3:])

    @perf_counter
    @discovery
    @staticmethod
    def _filter_path_by_dead_end_split_full(path: Path):
        for i in range(len(path.path) - 2):
            if not PathFinder._check_tri_edge(path.path[i : i + 3]):
                return False
        return True

    @perf_counter
    @staticmethod
    def _filter_path_by_dst(path: Path, dst_self: set[int]):
        return id(path.last) in dst_self

    @perf_counter
    @staticmethod
    def _filter_path_by_end_in_self_gif(path: Path):
        return isinstance(path.last, GraphInterfaceSelf)

    @perf_counter
    @staticmethod
    def _filter_path_same_end_type(path: Path):
        return type(path.last.node) is type(path.first.node)

    @perf_counter
    @staticmethod
    def _mark_path_with_promises_heuristic(path: Path):
        """
        Marks paths that have promises in-case they get filtered down the line
        """
        # inline version
        edge = path.last_edge
        if not edge:
            return True

        if GraphInterfaceHierarchicalNode.is_downlink(edge):
            path.confidence *= 0.9

        return True

    @perf_counter
    @staticmethod
    def _build_path_stack(path: Path):
        """
        Marks paths that have promises in-case they get filtered down the line
        """
        # inline version
        edge = path.last_edge
        if not edge:
            return True

        elem = PathFinder._extend_path_hierarchy_stack(edge)
        if not elem:
            return True

        unresolved_stack, promise_stack = map(
            list, path.path_data.get("promises", ([], []))
        )

        promise_cnt = len(promise_stack)
        PathFinder._extend_fold_stack(elem, unresolved_stack, promise_stack)
        path.path_data = path.path_data | {
            "promises": (unresolved_stack, promise_stack),
            "promise_depth": len(promise_stack),  # convenience
        }
        promise_growth = len(promise_stack) - promise_cnt
        path.confidence *= 0.5**promise_growth

        return True

    @perf_counter
    @staticmethod
    def _build_path_stack_full(path: Path):
        stack = PathFinder._get_path_hierarchy_stack(path)
        unresolved_stack, promise_stack = PathFinder._fold_stack(stack)
        path.path_data = path.path_data | {
            "promises": (unresolved_stack, promise_stack),
            "promise_depth": len(promise_stack),  # convenience
        }
        path.confidence *= 0.5 ** len(promise_stack)
        return True

    @perf_counter
    @staticmethod
    def _filter_path_by_stack(path: Path, multi_paths_out: list[Path]):
        unresolved_stack, promise_stack = path.path_data.get("promises", ([], []))
        if unresolved_stack:
            return False

        if promise_stack:
            multi_paths_out.append(path)
            return False

        return True

    @perf_counter
    @discovery
    @staticmethod
    def _filter_and_mark_path_by_link_filter(path: Path, inline: bool = True):
        for edge in path.edges:
            linkobj = path.get_link(edge)

            if not isinstance(linkobj, LinkDirectConditional):
                continue

            # perf boost
            if inline:
                if isinstance(linkobj, ModuleInterface.LinkDirectShallow):
                    # don't need to recheck shallows
                    if len(path) > 2 and edge[1] is not path.last:
                        continue

            match linkobj.is_filtered(path.path):
                case LinkDirectConditional.FilterResult.FAIL_UNRECOVERABLE:
                    return False
                case LinkDirectConditional.FilterResult.FAIL_RECOVERABLE:
                    path.confidence *= 0.8

        return True

    @perf_counter(multi=True)
    @staticmethod
    def _filter_paths_by_split_join(
        paths: list[Path],
    ) -> list[Path]:
        # basically the only thing we need to do is
        # - check whether for every promise descend all children have a path
        #   that joins again before the end
        # - join again before end == ends in same node (self_gif)

        path_filtered = {id(p): False for p in paths}
        split: dict[GraphInterfaceHierarchical, list[Path]] = defaultdict(list)

        # build split map
        for path in paths:
            unresolved_stack, promise_stack = path.path_data.get("promises", ([], []))

            if unresolved_stack or not promise_stack:
                continue

            for elem in promise_stack:
                if elem.up:
                    # join
                    continue
                # split
                split[elem.parent_gif].append(path)

        for start_gif, split_paths in split.items():
            all_children = [
                n.parent
                for n in start_gif.node.get_children(
                    direct_only=True, types=ModuleInterface
                )
            ]
            index = split_paths[0].path.index(start_gif)

            grouped_by_end = groupby(split_paths, lambda p: p.path[-1])
            for end_gif, grouped_paths in grouped_by_end.items():
                path_suffixes = {id(p): p.path[index:] for p in grouped_paths}

                # not full coverage
                if set(all_children) != set(p[1] for p in path_suffixes.values()):
                    for path in grouped_paths:
                        path_filtered[id(path)] = True
                    continue

        out = [p for p in paths if not path_filtered[id(p)]]
        for p in out:
            p.confidence = 1.0
        return out

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def _count(_: Path):
        if not hasattr(PathFinder._count, "paths"):
            PathFinder._count.paths = 0

        PathFinder._count.paths += 1
        if PathFinder._count.paths % 50000 == 0:
            logger.info(f"{PathFinder._count.paths}")
        return True

    @staticmethod
    def find_paths_py(src: "ModuleInterface", *dst: "ModuleInterface"):
        PathFinder._count.paths = 0
        perf_counter.counters.reset()

        if dst:
            dst = tuple(d for d in dst if type(d) is type(src))
            if not dst:
                return
            dst_self = {id(dst.self_gif) for dst in dst}
            # TODO apparently not really faster to have single dst
            dst_filters = [lambda path: PathFinder._filter_path_by_dst(path, dst_self)]
        else:
            dst_filters = [
                PathFinder._filter_path_by_end_in_self_gif,
                PathFinder._filter_path_same_end_type,
            ]
        if src is dst:
            raise FaebrykException("src and dst are the same")

        multi_paths: list[Path] = []

        # Stage filters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        filters_discovery = [
            PathFinder._count,
            PathFinder._filter_path_by_node_type,
            PathFinder._filter_path_gif_type,
            # TODO pretty slow
            # PathFinder._filter_path_by_dead_end_split,
            PathFinder._mark_path_with_promises_heuristic,
            # PathFinder._build_path_stack,
        ]

        filters_single = [
            *filters_discovery,
            # ---------------------
            *dst_filters,
            PathFinder._filter_path_by_dead_end_split_full,
            PathFinder._build_path_stack_full,
            lambda path: PathFinder._filter_path_by_stack(path, multi_paths),
            lambda path: PathFinder._filter_and_mark_path_by_link_filter(
                path, inline=False
            ),
        ]

        filters_multiple = [
            PathFinder._filter_paths_by_split_join,
        ]

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # yield path & discovery filter
        for p in bfs_visit([src.self_gif]):
            if not all(f(p) for f in filters_single):
                continue
            yield p

        # yield multi path filter
        yielded_multi = set()

        def try_multi_filter():
            for f in filters_multiple:
                for p in f(multi_paths):
                    if id(p) in yielded_multi:
                        continue
                    yield p

        yield from try_multi_filter()

        if logger.isEnabledFor(logging.INFO):
            logger.info(f"Searched {PathFinder._count.paths} paths")
            logger.info(f"\n\t\t{perf_counter.counters}")

    @staticmethod
    def find_paths_cpp(src: "ModuleInterface", *dst: "ModuleInterface"):
        from faebryk.core.cpp.graph import CGraph

        time_start = time.perf_counter()
        Gpp = CGraph(src.get_graph())
        time_construct = time.perf_counter() - time_start

        paths = Gpp.find_paths(src, *dst)
        time_find = time.perf_counter() - time_construct - time_start

        print(
            f"Time construct: {time_construct*1000:.2f}ms"
            f" Time find: {time_find*1000:.2f}ms"
        )

        return iter(paths)

    @staticmethod
    def find_paths(src: "ModuleInterface", *dst: "ModuleInterface"):
        if CPP:
            return PathFinder.find_paths_cpp(src, *dst)
        else:
            return PathFinder.find_paths_py(src, *dst)
