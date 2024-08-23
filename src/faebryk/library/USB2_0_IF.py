# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.moduleinterface import ModuleInterface


class USB2_0_IF(ModuleInterface):
    d: F.DifferentialPair
    buspower: F.ElectricPower
