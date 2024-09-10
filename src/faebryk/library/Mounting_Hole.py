# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum, StrEnum

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L

logger = logging.getLogger(__name__)


class Mounting_Hole(Module):
    class MetricDiameter(Enum):
        M2 = ("2.2mm", "_M2")
        M3 = ("3.2mm", "_M3")
        M4 = ("4.3mm", "_M4")
        M5 = ("5.3mm", "_M5")
        M6 = ("6.4mm", "_M6")
        M8 = ("8.4mm", "_M8")

    class PadType(StrEnum):
        NoPad = ""
        Pad = "_Pad"
        TopBottom = "_TopBottom"
        TopOnly = "_TopOnly"
        Via = "_Via"

    diameter: MetricDiameter
    pad_type: PadType

    attach_to_footprint: F.can_attach_to_footprint_symmetrically
    designator_prefix = L.f_field(F.has_designator_prefix_defined)("H")

    def __preinit__(self):
        # footprint = L.f_field(F.has_footprint_defined)(
        #    F.KicadFootprint("MountingHole:MountingHole_3.2mm_M3_Pad", pin_names=[])
        # )

        # TODO: make back to f_field, rt_field because of imports
        @L.rt_field
        def footprint(self):
            assert self.diameter is not None
            assert self.pad_type is not None
            return F.has_footprint_defined(
                F.KicadFootprint(
                    f"MountingHole:MountingHole_{self.diameter.value[0]}{self.diameter.value[1] if self.pad_type.value != self.PadType.NoPad else ''}{self.pad_type.value}",  # noqa E501
                    pin_names=[],
                )
            )
