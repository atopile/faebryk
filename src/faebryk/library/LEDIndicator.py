# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
from faebryk.core.module import Module


class LEDIndicator(Module):


        # interfaces

            logic_in: F.ElectricLogic
            power_in: F.ElectricPower

        # components

            led = PoweredLED()
            # TODO make generic
            power_switch = PowerSwitchMOSFET(lowside=True, normally_closed=False)

        self.power_in.connect_via(self.power_switch, self.led.power)
        self.power_switch.logic_in.connect(self.logic_in)
