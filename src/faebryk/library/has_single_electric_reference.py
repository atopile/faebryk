# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


from abc import abstractmethod

from faebryk.core.core import Trait


class has_single_electric_reference(Trait):
    @abstractmethod
    def get_reference(self) -> F.ElectricPower: ...
