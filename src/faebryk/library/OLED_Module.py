# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum, auto

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import P

logger = logging.getLogger(__name__)


class OLED_Module(Module):
    class Resolution(Enum):
        H64xV32 = auto()
        H128xV32 = auto()
        H128xV64 = auto()
        H256xV64 = auto()

    class DisplayController(Enum):
        SSD1315 = auto()
        SSD1306 = auto()

    power: F.ElectricPower
    i2c: F.I2C

    resolution: F.TBD[Resolution]
    display_controller: F.TBD[DisplayController]

    def __preinit__(self):
        self.power.voltage.merge(F.Range(3.0 * P.V, 5 * P.V))
        self.power.decoupled.decouple()

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("OLED")
