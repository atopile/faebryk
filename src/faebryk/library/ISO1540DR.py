# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class ISO1540(Module):
    """
    ISO1540 Low-Power Bidirectional I2C Isolator
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    power: F.ElectricPower
    i2c: F.I2C
    power_iso: F.ElectricPower
    i2c_iso: F.I2C

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2304140030_Texas-Instruments-ISO1540DR_C179739.pdf"
    )
    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

    @L.rt_field
    def can_attach_to_footprint(self):
        return F.can_attach_to_footprint_via_pinmap(
            pinmap={
                "1": self.power.hv,
                "2": self.i2c.sda,
                "3": self.i2c.scl,
                "4": self.power.lv,
                "5": self.power_iso.lv,
                "6": self.i2c_iso.scl,
                "7": self.i2c_iso.sda,
                "8": self.power_iso.hv,
            }
        )

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        self.power.voltage.merge(F.Range(3.0 * P.V, 5.5 * P.V))
        self.power_iso.voltage.merge(F.Range(3.0 * P.V, 5.5 * P.V))

        self.power.decoupled.decouple().capacitance.merge(10 * P.uF)
        self.power_iso.decoupled.decouple().capacitance.merge(10 * P.uF)
