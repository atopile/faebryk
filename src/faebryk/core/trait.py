# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging
from abc import ABC
from typing import TypeVar

from deprecated import deprecated

from faebryk.core.core import FaebrykLibObject
from faebryk.core.node import Node

logger = logging.getLogger(__name__)


class Trait[T: Node](Node):
    @classmethod
    def impl(cls: type["Trait"]):
        class _Impl[T_: Node](TraitImpl[T_], cls): ...

        return _Impl[T]


U = TypeVar("U", bound="FaebrykLibObject")


class TraitImpl[U: Node](ABC):
    _trait: type[Trait[U]]

    def __finit__(self) -> None:
        found = False
        bases = type(self).__bases__
        while not found:
            for base in bases:
                if not issubclass(base, TraitImpl) and issubclass(base, Trait):
                    self._trait = base
                    found = True
                    break
            bases = [
                new_base
                for base in bases
                if issubclass(base, TraitImpl)
                for new_base in base.__bases__
            ]
            assert len(bases) > 0

        assert type(self._trait) is type
        assert issubclass(self._trait, Trait)
        assert self._trait is not TraitImpl

    def handle_added_to_parent(self):
        self.on_obj_set()

    def on_obj_set(self): ...

    def remove_obj(self):
        self._obj = None

    @property
    def obj(self) -> U:
        p = self.get_parent()
        if not p:
            raise Exception("trait is not linked to node")
        return p[0]

    @deprecated("Use obj property")
    def get_obj(self) -> U:
        return self.obj

    def cmp(self, other: "TraitImpl") -> tuple[bool, "TraitImpl"]:
        assert type(other), TraitImpl

        # If other same or more specific
        if other.implements(self._trait):
            return True, other

        # If we are more specific
        if self.implements(other._trait):
            return True, self

        return False, self

    def implements(self, trait: type):
        assert issubclass(trait, Trait)

        return issubclass(self._trait, trait)

    # override this to implement a dynamic trait
    def is_implemented(self):
        return True
