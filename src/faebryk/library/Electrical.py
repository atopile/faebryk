# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface
from faebryk.library.TBD import TBD
from faebryk.libs.units import Quantity


class Electrical(ModuleInterface):
    potential: TBD[Quantity]
