# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L


class PoweredLED(Module):
    power: F.ElectricPower
    current_limiting_resistor: F.Resistor
    led: F.LED

    def __init__(self, low_side_resistor: bool = True):
        self.low_side_resistor = low_side_resistor

    def __preinit__(self):
        self.power.hv.connect(
            self.led.anode
        ) if self.low_side_resistor else self.power.lv.connect(self.led.cathode)
        self.led.connect_via_current_limiting_resistor_to_power(
            self.current_limiting_resistor,
            self.power,
            low_side=self.low_side_resistor,
        )
        self.current_limiting_resistor.allow_removal_if_zero()

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.power.hv, self.power.lv)
