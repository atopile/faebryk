# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging


from faebryk.libs.units import Quantity

logger = logging.getLogger(__name__)


class TVS(Diode):
    reverse_breakdown_voltage: F.TBD[Quantity]
