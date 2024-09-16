# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from typing import TYPE_CHECKING

from faebryk.core.module import Module

if TYPE_CHECKING:
    from faebryk.library.Symbol import Symbol


class has_symbol(Module.TraitT):
    @abstractmethod
    def get_symbol(self) -> "Symbol": ...
