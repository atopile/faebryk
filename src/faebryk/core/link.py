# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import inspect
import logging
from typing import TYPE_CHECKING, Callable

from faebryk.core.core import LINK_TB, FaebrykLibObject

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from faebryk.core.graphinterface import (
        GraphInterface,
        GraphInterfaceHierarchical,
        GraphInterfaceSelf,
    )


class Link(FaebrykLibObject):
    def __init__(self) -> None:
        super().__init__()

        if LINK_TB:
            self.tb = inspect.stack()

    def get_connections(self) -> list["GraphInterface"]:
        raise NotImplementedError

    def __eq__(self, __value: "Link") -> bool:
        return set(self.get_connections()) == set(__value.get_connections())

    def __hash__(self) -> int:
        return super().__hash__()

    def __str__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"([{', '.join(str(i) for i in self.get_connections())}])"
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class LinkPointer(Link):
    """A Link that points towards a self-gif"""

    def __init__(
        self,
        interfaces: list["GraphInterfaceSelf | GraphInterface"],
    ) -> None:
        from faebryk.core.graphinterface import GraphInterfaceSelf

        super().__init__()
        assert len(interfaces) == 2
        if isinstance(interfaces[0], GraphInterfaceSelf) and not isinstance(
            interfaces[1], GraphInterfaceSelf
        ):
            self.self_gif = interfaces[0]
            self.other_gif = interfaces[1]
        elif isinstance(interfaces[1], GraphInterfaceSelf) and not isinstance(
            interfaces[0], GraphInterfaceSelf
        ):
            self.self_gif = interfaces[1]
            self.other_gif = interfaces[0]
        else:
            raise TypeError("Interfaces must be one self-gif and one other-gif")

    def get_connections(self) -> list["GraphInterface"]:
        return [self.self_gif, self.other_gif]


class LinkSibling(LinkPointer):
    """A link represents a connection between a self-gif and a gif in the same node"""


class LinkParent(Link):
    def __init__(self, interfaces: list["GraphInterface"]) -> None:
        super().__init__()
        from faebryk.core.graphinterface import GraphInterfaceHierarchical

        assert all([isinstance(i, GraphInterfaceHierarchical) for i in interfaces])
        # TODO rethink invariant
        assert len(interfaces) == 2
        assert len([i for i in interfaces if i.is_parent]) == 1  # type: ignore

        self.interfaces: list["GraphInterfaceHierarchical"] = interfaces  # type: ignore

    def get_connections(self):
        return self.interfaces

    def get_parent(self):
        return [i for i in self.interfaces if i.is_parent][0]

    def get_child(self):
        return [i for i in self.interfaces if not i.is_parent][0]


class LinkNamedParent(LinkParent):
    def __init__(self, name: str, interfaces: list["GraphInterface"]) -> None:
        super().__init__(interfaces)
        self.name = name

    @classmethod
    def curry(cls, name: str):
        def curried(interfaces: list["GraphInterface"]):
            return cls(name, interfaces)

        return curried


class LinkDirect(Link):
    """Represents a symmetrical link between two interfaces of the same type"""

    def __init__(self, interfaces: list["GraphInterface"]) -> None:
        super().__init__()
        assert (
            len(set(map(type, interfaces))) == 1
        ), "Interfaces must be of the same type"
        self.interfaces = interfaces

    def get_connections(self) -> list["GraphInterface"]:
        return self.interfaces


class LinkFilteredException(Exception): ...


class _TLinkDirectShallow(LinkDirect):
    def __new__(cls, *args, **kwargs):
        if cls is _TLinkDirectShallow:
            raise TypeError(
                "Can't instantiate abstract class _TLinkDirectShallow directly"
            )
        return super().__new__(cls)


def LinkDirectShallow(if_filter: Callable[[LinkDirect, "GraphInterface"], bool]):
    class _LinkDirectShallow(_TLinkDirectShallow):
        i_filter = if_filter

        def __init__(self, interfaces: list["GraphInterface"]) -> None:
            if not all(map(self.i_filter, interfaces)):
                raise LinkFilteredException()
            super().__init__(interfaces)

    return _LinkDirectShallow
