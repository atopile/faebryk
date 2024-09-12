# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

"""
This file contains a faebryk sample.
"""

import logging

import typer

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.exporters.pcb.layout.extrude import LayoutExtrude
from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy
from faebryk.libs.brightness import TypicalLuminousIntensity
from faebryk.libs.examples.buildutil import apply_design_to_pcb
from faebryk.libs.library import L
from faebryk.libs.logging import setup_basic_logging

logger = logging.getLogger(__name__)


class App(Module):
    led = L.f_field(F.LEDIndicator)(use_mosfet=False)
    mcu: F.RP2040_ReferenceDesign
    usb_power: F.USB_C_5V_PSU

    def __preinit__(self) -> None:
        # Parametrize
        self.led.led.led.color.merge(F.LED.Color.YELLOW)
        self.led.led.led.brightness.merge(
            TypicalLuminousIntensity.APPLICATION_LED_INDICATOR_INSIDE.value.value
        )

        self.usb_power.power_out.connect(self.mcu.usb.usb_if.buspower)
        self.mcu.rp2040.gpio[25].connect(self.led.logic_in)
        self.mcu.rp2040.pinmux.enable(self.mcu.rp2040.gpio[25])

        self._set_layout()

    def _set_layout(self):
        # set center
        self.add(
            F.has_pcb_position_defined(
                F.has_pcb_position.Point(
                    (50, 50, 0, F.has_pcb_position.layer_type.TOP_LAYER)
                )
            )
        )

        # distribute horizontally
        layout = LayoutTypeHierarchy(
            layouts=[
                LayoutTypeHierarchy.Level(
                    mod_type=Module,
                    layout=LayoutExtrude((20, 0)),
                )
            ]
        )
        self.add(F.has_pcb_layout_defined(layout))


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
