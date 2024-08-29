# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.brightness import TypicalLuminousIntensity
from faebryk.libs.library import L
from faebryk.libs.units import P

logger = logging.getLogger(__name__)


class RP2040_Reference_Design(Module):
    """Minimal required design for the Raspberry Pi RP2040 microcontroller.
    Based on the official Raspberry Pi RP2040 hardware design guidlines"""

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------

    power: F.ElectricPower
    usb: F.USB2_0

    rp2040: F.RP2040
    flash: F.SPIFlash
    led: F.PoweredLED
    usb_current_limit_resistor = L.list_field(2, F.Resistor)
    # TODO: add crystal oscillator
    # TODO: add voltage divider with switch
    # TODO: add boot button
    # TODO: add reset button
    # TODO: add optional LM4040 voltage reference or voltage divider

    def __preinit__(self):
        # ----------------------------------------
        #                aliasess
        # ----------------------------------------
        gnd = self.power.lv
        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        self.power.voltage.merge(F.Constant(3.3 * P.V))

        self.flash.memory_size.merge(F.Constant(16 * P.Mbit))

        self.led.led.color.merge(F.LED.Color.GREEN)
        self.led.led.brightness.merge(
            TypicalLuminousIntensity.APPLICATION_LED_INDICATOR_INSIDE.value.value
        )

        self.usb_current_limit_resistor[0].resistance.merge(F.Constant(27 * P.ohm))
        self.usb_current_limit_resistor[1].resistance.merge(F.Constant(27 * P.ohm))

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        # connect power rails
        main_power_rail = self.power
        for pwrrail in [
            self.rp2040.io_vdd,
            self.rp2040.adc_vdd,
            self.rp2040.vreg_in,
            self.rp2040.usb.usb_if.buspower,
        ]:
            pwrrail.connect(main_power_rail)

        self.rp2040.vreg_out.connect(self.rp2040.core_vdd)

        # connect flash
        self.flash.spi.connect(self.rp2040.qspi)
        self.flash.power.connect(main_power_rail)

        # connect led
        self.rp2040.gpio[25].connect_via(self.led, gnd)

        # connect usb
        self.usb.usb_if.d.p.connect_via(
            self.usb_current_limit_resistor[0],
            self.rp2040.usb.usb_if.d.p,
        )
        self.usb.usb_if.d.n.connect_via(
            self.usb_current_limit_resistor[1],
            self.rp2040.usb.usb_if.d.n,
        )

    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf"
    )
