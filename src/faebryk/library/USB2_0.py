# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.moduleinterface import ModuleInterface


class USB2_0(ModuleInterface):
    usb_if: F.USB2_0_IF

    def __preinit__(self):
        self.usb_if.buspower.voltage.merge(F.Range.from_center(5, 0.25))
