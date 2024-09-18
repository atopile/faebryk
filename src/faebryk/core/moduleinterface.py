# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging
from collections import defaultdict
from itertools import pairwise
from tracemalloc import start
from typing import (
    Iterable,
    Iterator,
    Sequence,
    cast,
)

from deprecated import deprecated
from typing_extensions import Self

from faebryk.core.core import Namespace
from faebryk.core.graphinterface import (
    GraphInterface,
    GraphInterfaceHierarchical,
    GraphInterfaceSelf,
)
from faebryk.core.link import (
    Link,
    LinkDirect,
    LinkDirectConditional,
    LinkDirectShallow,
)
from faebryk.core.node import GraphInterfaceHierarchicalNode, Node, f_field
from faebryk.core.trait import Trait
from faebryk.libs.util import groupby, once, unique

logger = logging.getLogger(__name__)


# The resolve functions are really weird
# You have to look into where they are called to make sense of what they are doing
# Chain resolve is for deciding what to do in a case like this
# if1 -> link1 -> if2 -> link2 -> if3
# This will then decide with which link if1 and if3 are connected
def _resolve_link_transitive(links: Iterable[type[Link]]) -> type[Link]:
    from faebryk.libs.util import is_type_set_subclasses

    uniq = set(links)
    assert uniq

    if len(uniq) == 1:
        return next(iter(uniq))

    if is_type_set_subclasses(uniq, {LinkDirectConditional}):
        # TODO this only works if the filter is identical
        raise NotImplementedError()

    if is_type_set_subclasses(uniq, {LinkDirect, LinkDirectConditional}):
        return [u for u in uniq if issubclass(u, LinkDirectConditional)][0]

    raise NotImplementedError()


# This one resolves the case if1 -> link1 -> if2; if1 -> link2 -> if2
def _resolve_link_duplicate(links: Iterable[type[Link]]) -> type[Link]:
    from faebryk.libs.util import is_type_set_subclasses

    uniq = set(links)
    assert uniq

    if len(uniq) == 1:
        return next(iter(uniq))

    if is_type_set_subclasses(uniq, {LinkDirect, LinkDirectConditional}):
        return [u for u in uniq if not issubclass(u, LinkDirectConditional)][0]

    raise NotImplementedError()


class GraphInterfaceHierarchicalModuleSpecial(GraphInterfaceHierarchical): ...


class GraphInterfaceModuleConnection(GraphInterface): ...


class _PathFinder:
    # node_type, src_gif, name, up
    type PathStackElement = tuple[type[Node], GraphInterfaceHierarchical, str, bool]
    type PathStack = list[PathStackElement]
    type Path = list[GraphInterface]

    @staticmethod
    def _get_path_hierarchy_stack(path: Path) -> PathStack:
        out: _PathFinder.PathStack = []

        for edge in pairwise(path):
            up = GraphInterfaceHierarchical.is_uplink(edge)
            if not up and not GraphInterfaceHierarchical.is_downlink(edge):
                continue
            edge = cast(
                tuple[GraphInterfaceHierarchical, GraphInterfaceHierarchical], edge
            )
            parent_gif = edge[0 if up else 1]

            p = parent_gif.get_parent()
            assert p
            out.append((type(p[0]), edge[0], p[1], up))

        return out

    @staticmethod
    def _fold_stack(stack: PathStack):
        # extra bool = split/promise
        unresolved_stack: list[tuple[tuple[type[Node], str, bool], bool]] = []
        promise_stack: list[_PathFinder.PathStackElement] = []
        for pt, gif, name, up in stack:
            if unresolved_stack and unresolved_stack[-1][0] == (pt, name, not up):
                promise = unresolved_stack[-1][1]
                unresolved_stack.pop()
                if promise:
                    promise_stack.append((pt, gif, name, up))
                continue

            # if down -> promise
            promise = not up
            unresolved_stack.append(((pt, name, up), promise))
            if promise:
                promise_stack.append((pt, gif, name, up))

        return unresolved_stack, promise_stack

    # Path filters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def _filter_path_gif_type(path: Path):
        return isinstance(
            path[-1],
            (
                GraphInterfaceSelf,
                GraphInterfaceHierarchicalNode,
                GraphInterfaceHierarchicalModuleSpecial,
                GraphInterfaceModuleConnection,
            ),
        )

    @staticmethod
    def _filter_path_by_dead_end_split(path: Path):
        tri_edge = path[-3:]
        if not len(tri_edge) == 3:
            return True

        if not all(isinstance(gif, GraphInterfaceHierarchicalNode) for gif in tri_edge):
            return True

        tri_edge = cast(
            tuple[
                GraphInterfaceHierarchicalNode,
                GraphInterfaceHierarchicalNode,
                GraphInterfaceHierarchicalNode,
            ],
            tri_edge,
        )

        # check if child->parent->child
        if (
            not tri_edge[0].is_parent
            and tri_edge[1].is_parent
            and not tri_edge[2].is_parent
        ):
            return False

        return True

    @staticmethod
    def _filter_path_by_end_in_self_gif(path: Path):
        return isinstance(path[-1], GraphInterfaceSelf)

    @staticmethod
    def _filter_path_same_end_type(path: Path):
        return type(path[-1].node) is type(path[0].node)

    @staticmethod
    def _filter_path_by_stack(path: Path, multi_paths_out: list[Path]):
        stack = _PathFinder._get_path_hierarchy_stack(path)
        unresolved_stack, contains_promise = _PathFinder._fold_stack(stack)
        if unresolved_stack:
            return False

        if contains_promise:
            multi_paths_out.append(path)
            return False

        return True

    @staticmethod
    def _filter_path_by_link_filter(path: Path, inline: bool):
        # optimization: if called inline, only last link has to be checked
        if inline and len(path) >= 2:
            links = [path[-2].is_connected_to(path[-1])]
        else:
            links = [e1.is_connected_to(e2) for e1, e2 in pairwise(path)]

        filtering_links = [
            link for link in links if isinstance(link, LinkDirectConditional)
        ]
        return all(not link.is_filtered(path) for link in filtering_links)

    @staticmethod
    def _filter_paths_by_split_join(
        paths: list[Path],
    ) -> list[Path]:
        # TODO basically the only thing we need to do is
        # - check whether for every promise descend all children have a path
        #   that joins again before the end
        # - join again before end == ends in same node (self_gif)

        # entry -> list[exit]
        path_filtered = {id(p): False for p in paths}
        split: dict[GraphInterfaceHierarchical, list[_PathFinder.Path]] = defaultdict(
            list
        )

        # build split map
        for path in paths:
            stack = _PathFinder._get_path_hierarchy_stack(path)
            unresolved_stack, promise_stack = _PathFinder._fold_stack(stack)

            if unresolved_stack or not promise_stack:
                continue

            for node_type, gif, name, up in promise_stack:
                if up:
                    # join
                    continue
                # split
                split[gif].append(path)

        for start_gif, split_paths in split.items():
            all_children = [
                n.parent
                for n in start_gif.node.get_children(
                    direct_only=True, types=ModuleInterface
                )
            ]
            index = split_paths[0].index(start_gif)

            grouped_by_end = groupby(split_paths, lambda p: p[-1])
            for end_gif, grouped_paths in grouped_by_end.items():
                path_suffixes = {id(p): p[index:] for p in grouped_paths}

                # not full coverage
                if set(all_children) != set(p[1] for p in path_suffixes.values()):
                    for path in grouped_paths:
                        path_filtered[id(path)] = True
                    continue

        out = [p for p in paths if not path_filtered[id(p)]]
        return out

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @staticmethod
    def find_paths(src: "ModuleInterface"):
        multi_paths: list[_PathFinder.Path] = []

        # Stage filters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        filters_inline = [
            _PathFinder._filter_path_gif_type,
            _PathFinder._filter_path_by_dead_end_split,
            lambda path: _PathFinder._filter_path_by_link_filter(path, inline=True),
        ]

        filters_single = [
            _PathFinder._filter_path_by_end_in_self_gif,
            _PathFinder._filter_path_same_end_type,
            lambda path: _PathFinder._filter_path_by_stack(path, multi_paths),
        ]

        filters_multiple = [
            _PathFinder._filter_paths_by_split_join,
        ]
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        paths = src.bfs_paths(lambda path, _: all(f(path) for f in filters_inline))
        # parallel
        for f in filters_single:
            paths = [p for p in paths if f(p)]
        # serial
        # paths = [p for p in paths if all(f(p) for f in filters_single)]
        for f in filters_multiple:
            paths.extend(f(multi_paths))

        paths = unique(paths, id)

        nodes = Node.get_nodes_from_gifs([p[-1] for p in paths])
        return nodes


class ModuleInterface(Node):
    class TraitT(Trait): ...

    specializes = f_field(GraphInterfaceHierarchicalModuleSpecial)(is_parent=False)
    specialized = f_field(GraphInterfaceHierarchicalModuleSpecial)(is_parent=True)
    connected: GraphInterfaceModuleConnection

    # TODO rename
    @classmethod
    @once
    def LinkDirectShallow(cls):
        """
        Make link that only connects up but not down
        """

        def test(node: Node):
            return not any(isinstance(p[0], cls) for p in node.get_hierarchy()[:-1])

        class _LinkDirectShallowMif(
            LinkDirectShallow(lambda link, gif: test(gif.node))
        ): ...

        return _LinkDirectShallowMif

    def __preinit__(self) -> None: ...

    # Graph ----------------------------------------------------------------------------
    def get_connected(self):
        return _PathFinder.find_paths(self)

    def is_connected_to(self, other: "ModuleInterface"):
        if not isinstance(other, type(self)):
            return False
        # TODO more efficient implementation
        return other in self.get_connected()

    @deprecated("Does not work")
    def _on_connect(self, other: "ModuleInterface"):
        """override to handle custom connection logic"""
        ...

    def connect[T: "ModuleInterface"](
        self: Self, *other: T, linkcls: type[Link] | None = None
    ) -> T | Self:
        if linkcls is None:
            linkcls = LinkDirect

        self.connected.connect(*{o.connected for o in other}, linkcls=linkcls)

        return other[-1] if other else self

    # Convenience functions ------------------------------------------------------------
    def connect_via(
        self,
        bridge: Node | Sequence[Node],
        *other: Self,
        linkcls: type[Link] | None = None,
    ):
        from faebryk.library.can_bridge import can_bridge

        bridges = [bridge] if isinstance(bridge, Node) else bridge
        intf = self
        for sub_bridge in bridges:
            t = sub_bridge.get_trait(can_bridge)
            intf.connect(t.get_in(), linkcls=linkcls)
            intf = t.get_out()

        intf.connect(*other, linkcls=linkcls)

    def connect_shallow(self, *other: Self) -> Self:
        return self.connect(*other, linkcls=type(self).LinkDirectShallow())

    def specialize[T: ModuleInterface](self, special: T) -> T:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Specializing MIF {self} with {special}")

        assert isinstance(special, type(self))

        # This is doing the heavy lifting
        self.connect(special)

        # Establish sibling relationship
        self.specialized.connect(special.specializes)

        return special
