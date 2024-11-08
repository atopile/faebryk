# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging
from typing import (
    Sequence,
    cast,
)

from typing_extensions import Self

from faebryk.core.cpp import (
    GraphInterfaceModuleConnection,
)
from faebryk.core.graphinterface import GraphInterface
from faebryk.core.link import (
    LinkDirect,
    LinkDirectConditional,
    LinkDirectConditionalFilterResult,
)
from faebryk.core.node import CNode, Node, NodeException
from faebryk.core.pathfinder import Path, find_paths
from faebryk.core.trait import Trait
from faebryk.library.can_specialize import can_specialize
from faebryk.libs.util import cast_assert, once

logger = logging.getLogger(__name__)


class ModuleInterface(Node):
    class TraitT(Trait): ...

    specializes: GraphInterface
    specialized: GraphInterface
    connected: GraphInterfaceModuleConnection

    class _LinkDirectShallow(LinkDirectConditional):
        """
        Make link that only connects up but not down
        """

        def has_no_parent_with_type(self, node: CNode):
            parents = (p[0] for p in node.get_hierarchy()[:-1])
            return not any(isinstance(p, self.test_type) for p in parents)

        def __init__(self, test_type: type["ModuleInterface"]):
            self.test_type = test_type
            super().__init__(
                lambda src, dst: LinkDirectConditionalFilterResult.FILTER_PASS
                if self.has_no_parent_with_type(src.node)
                else LinkDirectConditionalFilterResult.FILTER_FAIL_UNRECOVERABLE,
                needs_only_first_in_path=True,
            )

    @classmethod
    @once
    def LinkDirectShallow(cls):
        class _LinkDirectShallowMif(ModuleInterface._LinkDirectShallow):
            def __init__(self):
                super().__init__(test_type=cls)

        return _LinkDirectShallowMif

    def __preinit__(self) -> None: ...

    def connect(self: Self, *other: Self, linkcls=None) -> Self:
        if not {type(o) for o in other}.issubset({type(self)}):
            raise NodeException(
                self,
                f"Can only connect modules of same type: {{{type(self)}}},"
                f" got {{{','.join(str(type(o)) for o in other)}}}",
            )

        # TODO: consider returning self always
        # - con: if construcing anonymous stuff in connection no ref
        # - pro: more intuitive
        ret = other[-1] if other else self

        if linkcls is None or linkcls is LinkDirect:
            self.connected.connect([o.connected for o in other])
            return ret

        # TODO: give link a proper copy constructor
        for o in other:
            self.connected.connect(o.connected, link=linkcls())

        return ret

    def connect_via(self, bridge: Node | Sequence[Node], *other: Self, linkcls=None):
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

    def get_connected(self) -> dict[Self, Path]:
        paths = find_paths(self, [])
        return {cast_assert(type(self), p[-1].node): p for p in paths}

    def is_connected_to(self, other: "ModuleInterface") -> list[Path]:
        return [
            path for path in find_paths(self, [other]) if path[-1] is other.self_gif
        ]

    def specialize[T: ModuleInterface](self, special: T) -> T:
        logger.debug(f"Specializing MIF {self} with {special}")

        extra = set()
        # allow non-base specialization if explicitly allowed
        if special.has_trait(can_specialize):
            extra = set(special.get_trait(can_specialize).get_specializable_types())

        assert isinstance(special, type(self)) or any(
            issubclass(t, type(self)) for t in extra
        )

        # This is doing the heavy lifting
        self.connected.connect(special.connected)

        # Establish sibling relationship
        self.specialized.connect(special.specializes)

        return cast(T, special)

    # def get_general(self):
    #    out = self.specializes.get_parent()
    #    if out:
    #        return out[0]
    #    return None

    def __init_subclass__(cls, *, init: bool = True) -> None:
        if hasattr(cls, "_on_connect"):
            raise TypeError("Overriding _on_connect is deprecated")

        return super().__init_subclass__(init=init)
