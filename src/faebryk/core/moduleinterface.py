# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging
from typing import (
    Iterable,
    Sequence,
)

from typing_extensions import Self

from faebryk.core.core import LINK_TB
from faebryk.core.graphinterface import (
    GraphInterface,
    GraphInterfaceHierarchical,
)
from faebryk.core.link import (
    Link,
    LinkDirect,
    LinkDirectShallow,
    LinkFilteredException,
    _TLinkDirectShallow,
)
from faebryk.core.node import Node
from faebryk.core.trait import Trait
from faebryk.libs.util import print_stack

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

    if is_type_set_subclasses(uniq, {_TLinkDirectShallow}):
        # TODO this only works if the filter is identical
        raise NotImplementedError()

    if is_type_set_subclasses(uniq, {LinkDirect, _TLinkDirectShallow}):
        return [u for u in uniq if issubclass(u, _TLinkDirectShallow)][0]

    raise NotImplementedError()


# This one resolves the case if1 -> link1 -> if2; if1 -> link2 -> if2
def _resolve_link_duplicate(links: Iterable[type[Link]]) -> type[Link]:
    from faebryk.libs.util import is_type_set_subclasses

    uniq = set(links)
    assert uniq

    if len(uniq) == 1:
        return next(iter(uniq))

    if is_type_set_subclasses(uniq, {LinkDirect, _TLinkDirectShallow}):
        return [u for u in uniq if not issubclass(u, _TLinkDirectShallow)][0]

    raise NotImplementedError()


class _LEVEL:
    """connect depth counter to debug connections in ModuleInterface"""

    def __init__(self) -> None:
        self.value = 0

    def inc(self):
        self.value += 1
        return self.value - 1

    def dec(self):
        self.value -= 1


_CONNECT_DEPTH = _LEVEL()


class GraphInterfaceModuleSibling(GraphInterfaceHierarchical): ...


class GraphInterfaceModuleConnection(GraphInterface): ...


class ModuleInterface(Node):
    class TraitT(Trait): ...

    specializes: GraphInterface
    specialized: GraphInterface
    connected: GraphInterfaceModuleConnection

    # TODO rename
    @classmethod
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

    _LinkDirectShallow: type[_TLinkDirectShallow] | None = None

    def __finit__(self) -> None:
        if not type(self)._LinkDirectShallow:
            type(self)._LinkDirectShallow = type(self).LinkDirectShallow()

    def _connect_siblings_and_connections(
        self, other: "ModuleInterface", linkcls: type[Link]
    ) -> Self:
        from faebryk.core.util import get_connected_mifs_with_link

        if other is self:
            return self

        # Already connected
        if self.is_connected_to(other):
            return self

        # if link is filtered, cancel here
        self._connect_across_hierarchies(other, linkcls)
        if not self.is_connected_to(other):
            return self

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"MIF connection: {self} to {other}")

        def cross_connect(
            s_group: dict[ModuleInterface, type[Link]],
            d_group: dict[ModuleInterface, type[Link]],
            hint=None,
        ):
            if logger.isEnabledFor(logging.DEBUG) and hint is not None:
                logger.debug(f"Connect {hint} {s_group} -> {d_group}")

            for s, slink in s_group.items():
                for d, dlink in d_group.items():
                    # can happen while connection trees are resolving
                    if s is d:
                        continue
                    link = _resolve_link_transitive([slink, dlink, linkcls])

                    s._connect_across_hierarchies(d, linkcls=link)

        def _get_connected_mifs(gif: GraphInterface):
            return {k: type(v) for k, v in get_connected_mifs_with_link(gif).items()}

        # Connect to all connections
        s_con = _get_connected_mifs(self.connected) | {self: linkcls}
        d_con = _get_connected_mifs(other.connected) | {other: linkcls}
        cross_connect(s_con, d_con, "connections")

        # Connect to all siblings
        s_sib = (
            _get_connected_mifs(self.specialized)
            | _get_connected_mifs(self.specializes)
            | {self: linkcls}
        )
        d_sib = (
            _get_connected_mifs(other.specialized)
            | _get_connected_mifs(other.specializes)
            | {other: linkcls}
        )
        cross_connect(s_sib, d_sib, "siblings")

        return self

    def _on_connect(self, other: "ModuleInterface"):
        """override to handle custom connection logic"""
        ...

    def _try_connect_down(self, other: "ModuleInterface", linkcls: type[Link]) -> None:
        from faebryk.core.util import zip_children_by_name

        if not isinstance(other, type(self)):
            return

        for _, (src, dst) in zip_children_by_name(self, other, ModuleInterface).items():
            if src is None or dst is None:
                continue
            src.connect(dst, linkcls=linkcls)

    def _try_connect_up(self, other: "ModuleInterface") -> None:
        p1 = self.get_parent()
        p2 = other.get_parent()
        if not (
            p1
            and p2
            and p1[0] is not p2[0]
            and isinstance(p1[0], type(p2[0]))
            and isinstance(p1[0], ModuleInterface)
        ):
            return

        src_m = p1[0]
        dst_m = p2[0]
        assert isinstance(dst_m, ModuleInterface)

        def _is_connected(a, b):
            assert isinstance(a, ModuleInterface)
            assert isinstance(b, ModuleInterface)
            return a.is_connected_to(b)

        src_m_is = src_m.get_children(direct_only=True, types=ModuleInterface)
        dst_m_is = dst_m.get_children(direct_only=True, types=ModuleInterface)
        connection_map = [
            (src_i, dst_i, _is_connected(src_i, dst_i))
            for src_i, dst_i in zip(src_m_is, dst_m_is)
        ]

        assert connection_map

        if not all(connected for _, _, connected in connection_map):
            return

        # decide which LinkType to use here
        # depends on connections between src_i & dst_i
        # e.g. if any Shallow, we need to choose shallow
        link = _resolve_link_transitive(
            [type(sublink) for _, _, sublink in connection_map if sublink]
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Up connect {src_m} -> {dst_m}")
        src_m.connect(dst_m, linkcls=link)

    def _connect_across_hierarchies(
        self, other: "ModuleInterface", linkcls: type[Link]
    ):
        existing_link = self.is_connected_to(other)
        if existing_link:
            if isinstance(existing_link, linkcls):
                return
            resolved = _resolve_link_duplicate([type(existing_link), linkcls])
            if resolved is type(existing_link):
                return
            if LINK_TB:
                print(print_stack(existing_link.tb))
            raise NotImplementedError(
                "Overriding existing links not implemented, tried to override "
                + f"{existing_link} with {resolved}"
            )

        # level 0 connect
        try:
            self.connected.connect(other.connected, linkcls=linkcls)
        except LinkFilteredException:
            return

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"{' '*2*_CONNECT_DEPTH.inc()}Connect {self} to {other}")
        self._on_connect(other)

        con_depth_one = _CONNECT_DEPTH.value == 1
        recursion_error = None
        try:
            # level +1 (down) connect
            self._try_connect_down(other, linkcls=linkcls)

            # level -1 (up) connect
            self._try_connect_up(other)

        except RecursionError as e:
            recursion_error = e
            if not con_depth_one:
                raise

        if recursion_error:
            raise Exception(f"Recursion error while connecting {self} to {other}")

        _CONNECT_DEPTH.dec()

    def get_direct_connections(self) -> set["ModuleInterface"]:
        return {
            gif.node
            for gif in self.connected.get_direct_connections()
            if isinstance(gif.node, ModuleInterface) and gif.node is not self
        }

    def connect(self, other: Self, linkcls=None) -> Self:
        # TODO consider some type of check at the end within the graph instead
        # assert type(other) is type(self)
        if linkcls is None:
            linkcls = LinkDirect
        return self._connect_siblings_and_connections(other, linkcls=linkcls)

    def connect_via(
        self, bridge: Node | Sequence[Node], other: Self | None = None, linkcls=None
    ):
        from faebryk.library.can_bridge import can_bridge

        bridges = [bridge] if isinstance(bridge, Node) else bridge
        intf = self
        for sub_bridge in bridges:
            t = sub_bridge.get_trait(can_bridge)
            intf.connect(t.get_in(), linkcls=linkcls)
            intf = t.get_out()

        if other:
            intf.connect(other, linkcls=linkcls)

    def connect_shallow(self, other: Self) -> Self:
        return self.connect(other, linkcls=type(self)._LinkDirectShallow)

    def is_connected_to(self, other: "ModuleInterface"):
        return self.connected.is_connected(other.connected)
