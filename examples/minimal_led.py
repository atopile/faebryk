# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

"""
This file contains a faebryk sample.
"""

import logging

import typer

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.brightness import TypicalLuminousIntensity
from faebryk.libs.examples.buildutil import apply_design_to_pcb
from faebryk.libs.logging import setup_basic_logging

logger = logging.getLogger(__name__)


class App(Module):
    led: F.PoweredLED
    battery: F.Battery
    mcu: F.RP2040_ReferenceDesign

    def __preinit__(self) -> None:
        # self.led.power.connect(self.battery.power)

        # Parametrize
        self.led.led.color.merge(F.LED.Color.YELLOW)
        self.led.led.brightness.merge(
            TypicalLuminousIntensity.APPLICATION_LED_INDICATOR_INSIDE.value.value
        )

        F.ElectricLogic.connect_all_node_references(
            [self.led, self.battery, self.mcu], gnd_only=True
        )
        # self.mcu.usb.usb_if.buspower.connect(self.battery.power)

        self.mcu.rp2040.i2c[0].sda.signal.connect(self.led.power.hv)
        self.mcu.rp2040.i2c[0].sda.reference.connect_shallow(self.led.power)
        self.mcu.rp2040.pinmux.enable(
            self.mcu.rp2040.i2c[0].sda, pins=list(range(10, 20))
        )


# Boilerplate -----------------------------------------------------------------


def main():
    logger.info("Building app")
    app = App()

    logger.info("Export")
    apply_design_to_pcb(app)


if __name__ == "__main__":
    setup_basic_logging()
    logger.info("Running example")

    typer.run(main)
