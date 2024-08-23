# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod

from faebryk.library.Footprint import Footprint
from faebryk.library.Pad import Pad


class has_equal_pins(Footprint.TraitT):
    @abstractmethod
    def get_pin_map(self) -> dict[Pad, str]: ...
