# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging
from typing import Sequence, cast

from typing_extensions import Self

from faebryk.core.graphinterface import (
    Graph,
    GraphInterface,
    GraphInterfaceHierarchical,
)
from faebryk.core.link import (
    Link,
    LinkDirect,
    LinkDirectConditional,
    LinkDirectDerived,
    LinkParent,
)
from faebryk.core.node import (
    Node,
    NodeException,
    f_field,
)
from faebryk.core.trait import Trait

logger = logging.getLogger(__name__)


class GraphInterfaceHierarchicalModuleSpecial(GraphInterfaceHierarchical): ...


class GraphInterfaceModuleConnection(GraphInterface): ...


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

            if isinstance(path[0].node, self._children_types):
                return LinkDirectConditional.FilterResult.FAIL_UNRECOVERABLE

            return LinkDirectConditional.FilterResult.PASS

        def __init__(
            self,
            interfaces: list["GraphInterface"],
        ) -> None:
            self._children_types = tuple(
                {
                    type(mif)
                    for mif in interfaces[0].node.get_children(
                        direct_only=False, types=ModuleInterface
                    )
                }
            )

            super().__init__(interfaces)

    def __preinit__(self) -> None: ...

    # Graph ----------------------------------------------------------------------------
    def _connect_via_implied_paths(self, other: Self, paths: list[Graph.Path]):
        if self.connected.is_connected_to(other.connected):
            # TODO link resolution
            return

        # heuristic: choose path with fewest conditionals
        paths_links = [
            (path, [e1.is_connected_to(e2) for e1, e2 in path.edges]) for path in paths
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

        self.connect(other, linkcls=LinkDirectDerived.curry(path.path))

    def get_connected(self):
        from faebryk.core.pathfinder import PathFinder

        for path in PathFinder.find_paths(self):
            node = cast(Self, path.last.node)
            self._connect_via_implied_paths(node, [path])
            yield node

    def is_connected_to(self, other: "ModuleInterface"):
        return next(self.get_paths_to(other), None)

    def get_paths_to(self, *other: "ModuleInterface"):
        from faebryk.core.pathfinder import PathFinder

        return PathFinder.find_paths(self, *other)

    def connect(self: Self, *other: Self, linkcls: type[Link] | None = None) -> Self:
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
