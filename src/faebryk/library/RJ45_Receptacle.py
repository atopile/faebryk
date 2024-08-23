# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from enum import Enum, auto

from faebryk.core.module import Module





class RJ45_Receptacle(Module):
    class Mounting(Enum):
        TH = auto()
        SMD = auto()



        # interfaces

            pin = L.if_list(8, F.Electrical)
            shield: F.Electrical

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("J")


            mounting : F.TBD[self.Mounting]
