# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging

from faebryk.core.node import Node, NodeException
from faebryk.libs.util import cast_assert

logger = logging.getLogger(__name__)


class TraitNotFound(NodeException):
    def __init__(self, node: Node, trait: type["Trait"], *args: object) -> None:
        super().__init__(
            node, *args, f"Trait {trait} not found in {type(node)}[{node}]"
        )
        self.trait = trait


class TraitAlreadyExists(NodeException):
    def __init__(self, node: Node, trait: "TraitImpl", *args: object) -> None:
        trait_type = trait._trait
        super().__init__(
            node,
            *args,
            f"Trait {trait_type} already exists in {node}: {node.get_trait(trait_type)}"
            f", trying to add {trait}",
        )
        self.trait = trait


class Trait(Node):
    @classmethod
    def impl[T: "Trait"](cls: type[T]):
        class _Impl(TraitImpl, cls): ...

        return _Impl


class TraitImpl(Node):
    _trait: type[Trait]

    def __preinit__(self) -> None:
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

        assert isinstance(self._trait, type)
        assert issubclass(self._trait, Trait)
        assert self._trait is not TraitImpl

    @property
    def obj(self) -> Node:
        p = self.get_parent()
        if not p:
            raise Exception("trait is not linked to node")
        return p[0]

    def get_obj[T: Node](self, type: type[T]) -> T:
        return cast_assert(type, self.obj)

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

    # Overwriteable --------------------------------------------------------------------

    def _handle_added_to_parent(self):
        self.on_obj_set()

    def on_obj_set(self): ...

    def handle_duplicate(self, other: "TraitImpl", node: Node):
        assert other is not self
        raise TraitAlreadyExists(node, self)

    # override this to implement a dynamic trait
    def is_implemented(self):
        return True
