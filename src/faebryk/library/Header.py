# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from enum import Enum, auto

from faebryk.core.module import Module


from faebryk.libs.units import Quantity



class Header(Module):
    class PinType(Enum):
        MALE = auto()
        FEMALE = auto()

    class PadType(Enum):
        THROUGH_HOLE = auto()
        SMD = auto()

    class Angle(Enum):
        STRAIGHT = auto()
        VERTICAL90 = auto()
        HORIZONTAL90 = auto()

    def __init__(
        self,
        horizonal_pin_count: int,
        vertical_pin_count: int,
    ) -> None:
        super().__init__()




            unnamed = L.if_list(horizonal_pin_count * vertical_pin_count, F.Electrical)


            pin_pitch : F.TBD[Quantity]
            pin_type : F.TBD[self.PinType]
            pad_type : F.TBD[self.PadType]
            angle : F.TBD[self.Angle]
            pin_count_horizonal = F.Constant(horizonal_pin_count)
            pin_count_vertical = F.Constant(vertical_pin_count)

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("J")
