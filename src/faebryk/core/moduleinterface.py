# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging
from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise
from typing import Sequence, cast

from typing_extensions import Self

from faebryk.core.graphinterface import (
    GraphInterface,
    GraphInterfaceHierarchical,
    GraphInterfaceSelf,
)
from faebryk.core.link import (
    Link,
    LinkDirect,
    LinkDirectConditional,
    LinkDirectDerived,
    LinkFilteredException,
    LinkParent,
)
from faebryk.core.node import (
    GraphInterfaceHierarchicalNode,
    Node,
    NodeException,
    f_field,
)
from faebryk.core.trait import Trait
from faebryk.libs.util import groupby, unique

logger = logging.getLogger(__name__)


class GraphInterfaceHierarchicalModuleSpecial(GraphInterfaceHierarchical): ...


class GraphInterfaceModuleConnection(GraphInterface): ...


class _PathFinder:
    @dataclass
    class PathStackElement:
        parent_type: type[Node]
        child_type: type[Node]
        parent_gif: GraphInterfaceHierarchical
        name: str
        up: bool

    @dataclass
    class UnresolvedStackElement:
        elem: "_PathFinder.PathStackElement"
        promise: bool

        def match(self, elem: "_PathFinder.PathStackElement"):
            return (
                self.elem.parent_type == elem.parent_type
                and self.elem.child_type == elem.child_type
                and self.elem.name == elem.name
                and self.elem.up != elem.up
            )

    type PathStack = list[PathStackElement]
    type Path = list[GraphInterface]

    @staticmethod
    def _get_path_hierarchy_stack(path: Path) -> PathStack:
        out: _PathFinder.PathStack = []

        for edge in pairwise(path):
            up = GraphInterfaceHierarchicalNode.is_uplink(edge)
            if not up and not GraphInterfaceHierarchicalNode.is_downlink(edge):
                continue
            edge = cast(
                tuple[GraphInterfaceHierarchical, GraphInterfaceHierarchical], edge
            )
            child_gif = edge[0 if up else 1]
            parent_gif = edge[1 if up else 0]

            p = child_gif.get_parent()
            assert p
            name = p[1]
            out.append(
                _PathFinder.PathStackElement(
                    parent_type=type(parent_gif.node),
                    child_type=type(child_gif.node),
                    parent_gif=parent_gif,
                    name=name,
                    up=up,
                )
            )

        return out

    @staticmethod
    def _fold_stack(stack: PathStack):
        unresolved_stack: list[_PathFinder.UnresolvedStackElement] = []
        promise_stack: list[_PathFinder.PathStackElement] = []
        for elem in stack:
            if unresolved_stack and unresolved_stack[-1].match(elem):
                promise = unresolved_stack.pop().promise
                if promise:
                    promise_stack.append(elem)

            else:
                # if down & multipath -> promise
                promise = (
                    not elem.up
                    and len(
                        elem.parent_gif.node.get_children(
                            direct_only=True, types=ModuleInterface
                        )
                    )
                    > 1
                )

                unresolved_stack.append(
                    _PathFinder.UnresolvedStackElement(elem, promise)
                )

                if promise:
                    promise_stack.append(elem)

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
    def _filter_path_by_node_type(path: Path):
        # TODO for module specialization also modules will be allowed
        return isinstance(path[-1].node, ModuleInterface)

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
    def _filter_path_by_dst(path: Path, dst_self: set[int]):
        return id(path[-1]) in dst_self

    @staticmethod
    def _filter_path_by_end_in_self_gif(path: Path):
        return isinstance(path[-1], GraphInterfaceSelf)

    @staticmethod
    def _filter_path_same_end_type(path: Path):
        return type(path[-1].node) is type(path[0].node)

    @staticmethod
    def _mark_path_with_promises(path: Path):
        stack = _PathFinder._get_path_hierarchy_stack(path)
        _, promise_stack = _PathFinder._fold_stack(stack)
        return True, not promise_stack

    @staticmethod
    def _filter_path_by_stack(path: Path, multi_paths_out: list[Path]):
        # TODO optimize, once path is weak it wont become strong again
        stack = _PathFinder._get_path_hierarchy_stack(path)
        unresolved_stack, contains_promise = _PathFinder._fold_stack(stack)
        if unresolved_stack:
            return False

        if contains_promise:
            multi_paths_out.append(path)
            return False

        return True

    @staticmethod
    def _filter_and_mark_path_by_link_filter(path: Path, inline: bool):
        # TODO: optimization: if called inline, only last link has to be checked
        links = [e1.is_connected_to(e2) for e1, e2 in pairwise(path)]

        filtering_links = [
            link for link in links if isinstance(link, LinkDirectConditional)
        ]
        return all(not link.is_filtered(path) for link in filtering_links)

    @staticmethod
    def _filter_paths_by_split_join(
        paths: list[Path],
    ) -> list[Path]:
        # basically the only thing we need to do is
        # - check whether for every promise descend all children have a path
        #   that joins again before the end
        # - join again before end == ends in same node (self_gif)

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
    def find_paths[T: ModuleInterface](
        src: T, *dst: T
    ) -> dict[T, list["_PathFinder.Path"]]:
        multi_paths: list[_PathFinder.Path] = []

        # Stage filters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        filters_inline = [
            _PathFinder._filter_path_gif_type,
            _PathFinder._filter_path_by_dead_end_split,
            _PathFinder._filter_path_by_node_type,
            lambda path: _PathFinder._filter_and_mark_path_by_link_filter(
                path, inline=True
            ),
            _PathFinder._mark_path_with_promises,
        ]

        # TODO apparently not really faster to have single dst
        if dst:
            dst_self = {id(dst.self_gif) for dst in dst}
            dst_filters = [lambda path: _PathFinder._filter_path_by_dst(path, dst_self)]
        else:
            dst_filters = [
                _PathFinder._filter_path_by_end_in_self_gif,
                _PathFinder._filter_path_same_end_type,
            ]

        filters_single = dst_filters + [
            lambda path: _PathFinder._filter_path_by_stack(path, multi_paths),
        ]

        filters_multiple = [
            _PathFinder._filter_paths_by_split_join,
        ]

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def filter_inline(path: _PathFinder.Path, _) -> tuple[bool, bool]:
            in_path, strong = True, True
            for f in filters_inline:
                # No point in continuing filtering if not strong
                if not strong:
                    return in_path, strong

                f_res = f(path)
                if isinstance(f_res, bool):
                    in_path &= f_res
                    continue
                in_path &= f_res[0]
                strong &= f_res[1]
            return in_path, strong

        paths = src.bfs_paths(filter_inline)
        # parallel
        for f in filters_single:
            paths = [p for p in paths if f(p)]
        # serial
        # paths = [p for p in paths if all(f(p) for f in filters_single)]
        for f in filters_multiple:
            paths.extend(f(multi_paths))

        paths = unique(paths, id)

        node_paths = groupby(paths, lambda p: p[-1].node)

        assert all(isinstance(p, type(src)) for p in node_paths.keys())
        return cast(dict[T, list["_PathFinder.Path"]], node_paths)


class ModuleInterface(Node):
    class TraitT(Trait): ...

    specializes = f_field(GraphInterfaceHierarchicalModuleSpecial)(is_parent=False)
    specialized = f_field(GraphInterfaceHierarchicalModuleSpecial)(is_parent=True)
    connected: GraphInterfaceModuleConnection

    class LinkDirectShallow(LinkDirectConditional):
        """
        Make link that only connects up but not down
        """

        def is_filtered(self, path: list[GraphInterface]):
            # only beginning and end matter
            # end is same type as beginning

            return isinstance(path[0].node, self._children_types)

        def __init__(
            self,
            interfaces: list["GraphInterface"],
        ) -> None:
            super().__init__(interfaces)

            self._children_types = tuple(
                {
                    type(mif)
                    for mif in interfaces[0].node.get_children(
                        direct_only=False, types=ModuleInterface
                    )
                }
            )

            if self.is_filtered(interfaces):
                raise LinkFilteredException()

    def __preinit__(self) -> None: ...

    # Graph ----------------------------------------------------------------------------
    def _connect_via_implied_paths(self, other: Self, paths: list[_PathFinder.Path]):
        if self.connected.is_connected_to(other.connected):
            return

        # heuristic: choose path with fewest conditionals
        paths_links = [
            (path, [e1.is_connected_to(e2) for e1, e2 in pairwise(path)])
            for path in paths
        ]
        paths_conditionals = [
            (
                path,
                [link for link in links if isinstance(link, LinkDirectConditional)],
            )
            for path, links in paths_links
        ]
        path = min(paths_conditionals, key=lambda x: len(x[1]))[0]
        #

        self.connect(other, linkcls=LinkDirectDerived.curry(path))

    def get_connected(self):
        paths = _PathFinder.find_paths(self)
        for n, paths_to_node in paths.items():
            self._connect_via_implied_paths(n, paths_to_node)

        return set(paths.keys())

    def is_connected_to(self, other: "ModuleInterface"):
        if type(other) is not type(self):
            return None
        paths = _PathFinder.find_paths(self, other)
        return other in paths

    def get_path_to(self, other: "ModuleInterface"):
        if type(other) is not type(self):
            return None
        paths = _PathFinder.find_paths(self, other)
        return paths.get(cast(Self, other))

    def connect[T: "ModuleInterface"](
        self: Self, *other: T, linkcls: type[Link] | None = None
    ) -> T | Self:
        if linkcls is None:
            linkcls = LinkDirect

        if not {type(o) for o in other}.issubset({type(self)}):
            raise NodeException(
                self,
                f"Can only connect modules of same type: {{{type(self)}}},"
                f" got {{{','.join(str(type(o)) for o in other)}}}",
            )

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
        return self.connect(*other, linkcls=type(self).LinkDirectShallow)

    def specialize[T: ModuleInterface](self, special: T) -> T:
        assert isinstance(special, type(self))
        self.specialized.connect(special.specializes, linkcls=LinkParent)

        return cast(T, special)

    def get_general(self):
        out = self.specializes.get_parent()
        if out:
            return out[0]
        return None
