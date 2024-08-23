# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L

logger = logging.getLogger(__name__)


class Button(Module):
    unnamed = L.if_list(2, F.Electrical)

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("S")

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.unnamed[0], self.unnamed[1])
