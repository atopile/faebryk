# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.module import Module


logger = logging.getLogger(__name__)


class ESP32_C3_MINI_1_Reference_Design(Module):
    """ESP32_C3_MINI_1 Module reference design"""




            esp32_c3_mini_1 = ESP32_C3_MINI_1()
            # TODO make switch debounced
            boot_switch = Button()  # TODO: this cannot be picked Switch(F.Electrical)
            reset_switch = Button()  # TODO: this cannot be picked Switch(F.Electrical)
            low_speed_crystal_clock = Crystal_Oscillator()


            vdd3v3: F.ElectricPower
            uart = UART_Base()
            jtag = JTAG()
            usb = USB2_0()

        gnd = self.vdd3v3.lv

        # connect power
        self.vdd3v3.connect(self.esp32_c3_mini_1.vdd3v3)

        # TODO: set default boot mode (GPIO[8] pull up with 10k resistor) + (GPIO[2] pull up with 10k resistor)  # noqa: E501
        # boot and enable switches
        # TODO: Fix bridging of (boot and reset) switches
        # self.esp32_c3_mini_1.chip_enable.connect_via(
        #    self.boot_switch, gnd
        # )
        # TODO: lowpass chip_enable
        # self.gpio[9].connect_via(self.reset_switch, gnd)

        # connect low speed crystal oscillator
        self.low_speed_crystal_clock.n.connect(self.esp32_c3_mini_1.gpio[0].signal)
        self.low_speed_crystal_clock.p.connect(self.esp32_c3_mini_1.gpio[1].signal)
        self.low_speed_crystal_clock.power.lv.connect(gnd)

        # TODO: set the following in the pinmux
        # jtag gpio 4,5,6,7
        # USB gpio 18,19

        # connect USB
        self.usb.connect(self.esp32_c3_mini_1.esp32_c3.usb)

        # connect UART[0]
        self.uart.connect(self.esp32_c3_mini_1.esp32_c3.uart[0])
