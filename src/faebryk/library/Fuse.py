# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum, auto

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import Quantity

logger = logging.getLogger(__name__)


class Fuse(Module):
    class FuseType(Enum):
        NON_RESETTABLE = auto()
        RESETTABLE = auto()

    class ResponseType(Enum):
        SLOW = auto()
        FAST = auto()

    unnamed = L.if_list(2, F.Electrical)
    fuse_type: F.TBD[FuseType]
    response_type: F.TBD[ResponseType]
    trip_current: F.TBD[Quantity]

    attach_to_footprint: F.can_attach_to_footprint_symmetrically

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.unnamed[0], self.unnamed[1])

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("F")
