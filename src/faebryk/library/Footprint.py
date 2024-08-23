# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.node import Node
from faebryk.core.trait import Trait


class Footprint(Module):
    class TraitT(Trait): ...

    @staticmethod
    def get_footprint_of_parent(
        intf: ModuleInterface,
    ) -> "tuple[Node, Footprint]":
        from faebryk.core.util import get_parent_with_trait

        parent, trait = get_parent_with_trait(intf, has_footprint)
        return parent, trait.get_footprint()
