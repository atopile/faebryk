# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module






from faebryk.libs.units import P, Quantity

logger = logging.getLogger(__name__)


class Mounting_Hole(Module):



            diameter : F.TBD[Quantity]

        self.add_trait(can_attach_to_footprint_symmetrically())
    designator_prefix = L.f_field(F.has_designator_prefix_defined)("H")

        # Only 3.2mm supported for now
        self.diameter.merge(F.Constant(3.2 * P.mm))

        self.add_trait(
            has_defined_footprint(
                KicadF.Footprint("MountingHole:MountingHole_3.2mm_M3_Pad", pin_names=[])
            )
        )
