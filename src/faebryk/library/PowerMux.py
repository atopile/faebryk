# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class PowerMux(Module):
    power_in = L.list_field(2, F.ElectricPower)
    power_out: F.ElectricPower
    select: F.ElectricLogic
