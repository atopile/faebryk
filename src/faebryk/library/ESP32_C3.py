# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.core import Module
from faebryk.core.util import connect_to_all_interfaces
from faebryk.library.can_be_decoupled import can_be_decoupled
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_datasheet_defined import has_datasheet_defined
from faebryk.library.has_designator_prefix_defined import has_designator_prefix_defined
from faebryk.library.has_single_electric_reference_defined import (
    has_single_electric_reference_defined,
)
from faebryk.library.I2C import I2C
from faebryk.library.Range import Range
from faebryk.library.UART_Base import UART_Base
from faebryk.library.USB2_0 import USB2_0
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


class ESP32_C3(Module):
    """ESP32-C3"""

    def __init__(self) -> None:
        super().__init__()

        class _NODEs(Module.NODES()): ...

        self.NODEs = _NODEs(self)

        class _IFs(Module.IFS()):
            gnd = times(22, Electrical)
            pwr3v3 = ElectricPower()
            usb = USB2_0()
            i2c = I2C()
            gpio = times(22, ElectricLogic)  # 11-19 not connected
            enable = ElectricLogic()
            serial = times(2, UART_Base)
            boot_mode = ElectricLogic()

        self.IFs = _IFs(self)

        x = self.IFs

        # https://www.espressif.com/sites/default/files/documentation/esp32-c3_technical_reference_manual_en.pdf#uart
        for ser in x.serial:
            ser.PARAMs.baud.merge(Range(0, 5000000))

        # connect all logic references
        # ref = ElectricLogic.connect_all_module_references(self)
        self.add_trait(has_single_electric_reference_defined(self.IFs.pwr3v3))

        # set constraints
        self.IFs.pwr3v3.PARAMs.voltage.merge(Range(3.0, 3.6))

        # connect all grounds to eachother and power
        connect_to_all_interfaces(self.IFs.pwr3v3.IFs.lv, self.IFs.gnd)

        # connect power decoupling caps
        self.IFs.pwr3v3.get_trait(can_be_decoupled).decouple()
        # TODO: should be 100nF + 10uF

        # rc delay circuit on enable pin for startup delay
        # https://www.espressif.com/sites/default/files/russianDocumentation/esp32-c3-mini-1_datasheet_en.pdf page 24  # noqa E501
        # TODO: add lowpass filter
        # self.IFs.enable.IFs.signal.connect_via(
        #    self.NODEs.en_rc_capacitor, self.IFs.pwr3v3.IFs.lv
        # )
        self.IFs.enable.get_trait(ElectricLogic.can_be_pulled).pull(
            up=True
        )  # TODO: en_rc_capacitor

        # set default boot mode to "SPI Boot mode" (gpio = N.C. or HIGH)
        # https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf page 25  # noqa E501
        # TODO: make configurable
        self.IFs.gpio[8].get_trait(ElectricLogic.can_be_pulled).pull(
            up=True
        )  # boot_resistors[0]
        self.IFs.gpio[2].get_trait(ElectricLogic.can_be_pulled).pull(
            up=True
        )  # boot_resistors[1]
        self.IFs.gpio[9].connect(
            self.IFs.boot_mode
        )  # ESP32-c3 defaults to pull-up at boot = SPI-Boot

        self.add_trait(has_designator_prefix_defined("U"))

        self.add_trait(
            has_datasheet_defined(
                "https://www.espressif.com/sites/default/files/russianDocumentation/esp32-c3-mini-1_datasheet_en.pdf"
            )
        )
        # self.add_trait(has_datasheet_defined("https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf"))
