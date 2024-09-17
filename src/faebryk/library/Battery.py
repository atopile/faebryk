# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


import faebryk.library._F as F
import faebryk.libs.library.L as L
from faebryk.core.module import Module
from faebryk.libs.units import Quantity


class Battery(Module):
    voltage: F.TBD[Quantity]
    capacity: F.TBD[Quantity]

    power: F.ElectricPower

    def __preinit__(self) -> None:
        self.power.voltage.merge(self.voltage)

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(self.power)
