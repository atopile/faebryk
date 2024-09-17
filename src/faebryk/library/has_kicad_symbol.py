# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod
from typing import TYPE_CHECKING

import faebryk.library._F as F

if TYPE_CHECKING:
    from faebryk.library.Pad import Pad


class has_kicad_symbol(F.Symbol.TraitT):
    @abstractmethod
    def get_kicad_symbol_name(self) -> str: ...

    @abstractmethod
    def get_pin_names(self) -> dict["Pad", str]: ...

    def get_kicad_symbol_name(self) -> str:
        return self.get_kicad_symbol_name().split(":")[-1]
