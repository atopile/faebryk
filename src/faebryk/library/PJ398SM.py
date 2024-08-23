# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module




class PJ398SM(Module):



            tip: F.Electrical
            sleeve: F.Electrical
            switch: F.Electrical

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("J")
