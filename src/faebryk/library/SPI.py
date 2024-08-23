# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface


class SPI(ModuleInterface):
    sclk: F.Electrical
    miso: F.Electrical
    mosi: F.Electrical
    gnd: F.Electrical
