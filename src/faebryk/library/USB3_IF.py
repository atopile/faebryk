# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface


class USB3_IF(ModuleInterface):
    usb_if = USB2_0_IF()
    rx = DifferentialPair()
    tx = DifferentialPair()
    gnd_drain: F.Electrical
