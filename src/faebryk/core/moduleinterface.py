# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging
from itertools import pairwise
from typing import (
    Iterable,
    Sequence,
)

from deprecated import deprecated
from more_itertools import chunked
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
    LinkDirectShallow,
)
from faebryk.core.node import GraphInterfaceHierarchicalNode, Node, f_field
from faebryk.core.trait import Trait
from faebryk.libs.util import once

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
        multi_paths: list[list[GraphInterface]] = []

        # Path filters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def _filter_path_gif_type(path: list[GraphInterface]):
            return isinstance(
                path[-1],
                (
                    GraphInterfaceSelf,
                    GraphInterfaceHierarchicalNode,
                    GraphInterfaceHierarchicalModuleSpecial,
                    GraphInterfaceModuleConnection,
                ),
            )

        def _filter_path_same_end_type(path: list[GraphInterface]):
            return type(path[-1].node) is type(path[0].node)

        def _get_path_hierarchy_stack(path: list[GraphInterface]):
            out: list[tuple[type[Node], str, bool]] = []

            for edge in pairwise(path):
                up = GraphInterfaceHierarchical.is_uplink(edge)
                if not up and not GraphInterfaceHierarchical.is_downlink(edge):
                    continue
                parent_gif = edge[0 if up else 1]
                assert isinstance(parent_gif, GraphInterfaceHierarchical)

                p = parent_gif.get_parent()
                assert p
                out.append((type(p[0]), p[1], up))

            return out

        def _filter_path_by_stack(path: list[GraphInterface]):
            stack = _get_path_hierarchy_stack(path)
            resolved_stack = []
            for pt, name, up in stack:
                if resolved_stack and resolved_stack[-1] == (pt, name, not up):
                    resolved_stack.pop()
                    continue

                if up:
                    resolved_stack.append((pt, name, up))
                else:
                    multi_paths.append(path)
                    return False

            return not resolved_stack

        def _filter_path_by_link_filter(path: list[GraphInterface]):
            links = [e1.is_connected_to(e2) for e1, e2 in pairwise(path)]
            filtering_links = [
                link for link in links if isinstance(link, LinkDirectConditional)
            ]
            return all(not link.is_filtered(path) for link in filtering_links)

        # Stage filters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        def filter_path_inline(path: list[GraphInterface], link: Link) -> bool:
            return (
                _filter_path_gif_type(path)
                and True  # TODO more?
                and True  # TODO
            )

        def filter_single(path: list[GraphInterface]):
            return (
                _filter_path_same_end_type(path)
                and _filter_path_by_stack(path)
                and _filter_path_by_link_filter(path)
            )

        def filter_multiple(
            paths: list[list[GraphInterface]],
        ) -> list[list[GraphInterface]]:
            # TODO split path filter
            return []

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        _, paths = self.bfs_paths(filter_path_inline)
        paths = [p for p in paths if filter_single(p)]
        paths.extend(filter_multiple(multi_paths))

        nodes = self.get_nodes_from_gifs([p[-1] for p in paths])
        return nodes

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
