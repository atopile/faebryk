# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module


class PoweredLED(Module):



            power: F.ElectricPower


            current_limiting_resistor : F.Resistor
            led = LED()

        self.power.hv.connect(self.led.anode)
        self.led.connect_via_current_limiting_resistor_to_power(
            self.current_limiting_resistor,
            self.power,
            low_side=True,
        )

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.power.hv, self.power.lv)
        self.current_limiting_resistor.allow_removal_if_zero()
