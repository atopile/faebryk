# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class B0505S(Module):
    """
    Isolated 5V DC to 5V DC converter
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    power_in: F.ElectricPower
    power_out: F.ElectricPower

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2307211806_EVISUN-B0505S-1WR3_C7465178.pdf"
    )

    @L.rt_field
    def can_attach_to_footprint(self):
        return F.can_attach_to_footprint_via_pinmap(
            pinmap={
                "1": self.power_in.lv,
                "2": self.power_in.hv,
                "3": self.power_out.lv,
                "4": self.power_out.hv,
            }
        )

    # self.add_trait(can_bridge_defined(self.power_in, self.power_out))
    def __preinit__(self):
        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        self.power_in.get_trait(F.can_be_decoupled).decouple().capacitance.merge(
            F.Constant(4.7 * P.uF)
        )
        self.power_out.get_trait(F.can_be_decoupled).decouple().capacitance.merge(
            F.Constant(10 * P.uF)
        )

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        self.power_in.voltage.merge(F.Range(4.3 * P.V, 9 * P.V))
        self.power_out.voltage.merge(F.Range.from_center(5 * P.V, 0.5 * P.V))
