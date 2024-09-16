# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.node import Node
from faebryk.core.trait import Trait


class Symbol(Module):
    class TraitT(Trait): ...

    @staticmethod
    def get_symbol_of_parent(
        intf: ModuleInterface,
    ) -> "tuple[Node, Symbol]":
        parent, trait = intf.get_parent_with_trait(F.has_symbol)
        return parent, trait.get_symbol()
