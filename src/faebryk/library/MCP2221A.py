# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module




logger = logging.getLogger(__name__)


class MCP2221A(Module):





            power: F.ElectricPower
            power_vusb: F.ElectricPower
            uart = UART_Base()
            i2c = I2C()
            gpio = L.if_list(4, F.Electrical)
            reset: F.ElectricLogic
            usb = USB2_0()



        self.power.get_trait(can_be_decoupled).decouple()
        self.power_vusb.get_trait(can_be_decoupled).decouple()

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

        self.power.lv.connect(self.power_vusb.lv)
