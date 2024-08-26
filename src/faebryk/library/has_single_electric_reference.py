# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


from abc import abstractmethod

import faebryk.library._F as F
from faebryk.core.trait import Trait


class has_single_electric_reference(Trait):
    @abstractmethod
    def get_reference(self) -> F.ElectricPower: ...
