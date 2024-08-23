# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod


class has_equal_pins(F.Footprint.TraitT):
    @abstractmethod
    def get_pin_map(self) -> dict[Pad, str]: ...
