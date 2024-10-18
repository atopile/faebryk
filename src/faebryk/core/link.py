# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import inspect
import logging
from enum import Enum, auto
from itertools import pairwise
from typing import TYPE_CHECKING

from faebryk.core.core import LINK_TB, FaebrykLibObject

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from faebryk.core.graphinterface import GraphInterface, GraphInterfaceHierarchical


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


class LinkSibling(Link):
    def __init__(self, interfaces: list["GraphInterface"]) -> None:
        super().__init__()
        self.interfaces = interfaces

    def get_connections(self) -> list["GraphInterface"]:
        return self.interfaces


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
        class LinkNamedParentWithName(LinkNamedParent):
            def __init__(self, interfaces: list["GraphInterface"]) -> None:
                super().__init__(name, interfaces)

        return LinkNamedParentWithName


class LinkDirect(Link):
    def __init__(self, interfaces: list["GraphInterface"]) -> None:
        super().__init__()
        assert len(set(map(type, interfaces))) == 1
        self.interfaces = interfaces

    def get_connections(self) -> list["GraphInterface"]:
        return self.interfaces


class LinkFilteredException(Exception): ...


class LinkDirectConditional(LinkDirect):
    class FilterResult(Enum):
        PASS = auto()
        FAIL_RECOVERABLE = auto()
        FAIL_UNRECOVERABLE = auto()

    def __init__(self, interfaces: list["GraphInterface"]) -> None:
        if self.is_filtered(interfaces) != LinkDirectConditional.FilterResult.PASS:
            raise LinkFilteredException()
        self.interfaces = interfaces

    def get_interfaces(self) -> list["GraphInterface"]:
        return self.interfaces

    def is_filtered(self, path: list["GraphInterface"]) -> FilterResult:
        return LinkDirectConditional.FilterResult.PASS


class LinkDirectDerived(LinkDirectConditional):
    def __init__(
        self, interfaces: list["GraphInterface"], path: list["GraphInterface"]
    ) -> None:
        self.path = path

        links = [e1.is_connected_to(e2) for e1, e2 in pairwise(path)]
        self.filters = [
            link for link in links if isinstance(link, LinkDirectConditional)
        ]

        super().__init__(interfaces)

    def is_filtered(
        self, path: list["GraphInterface"]
    ) -> LinkDirectConditional.FilterResult:
        result = LinkDirectConditional.FilterResult.PASS
        for f in self.filters:
            match res := f.is_filtered(path):
                case LinkDirectConditional.FilterResult.FAIL_UNRECOVERABLE:
                    return res
                case LinkDirectConditional.FilterResult.FAIL_RECOVERABLE:
                    result = res

        return result

    @classmethod
    def curry(cls, path: list["GraphInterface"]):
        class LinkDirectDerivedWithPath(LinkDirectDerived):
            def __init__(self, interfaces: list["GraphInterface"]) -> None:
                super().__init__(interfaces, path)

        return LinkDirectDerivedWithPath
