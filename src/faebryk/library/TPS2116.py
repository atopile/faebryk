# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class TPS2116(F.PowerMux):
    """
    2to1 1.6 V to 5.5 V, 2.5-A Low IQ Power Mux with Manual and Priority Switchover
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    power_in = L.list_field(2, F.ElectricPower)
    power_out: F.ElectricPower
    select: F.Electrical
    mode: F.ElectricLogic
    status: F.ElectricLogic

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://www.ti.com/lit/ds/symlink/tps2116.pdf"
    )

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self, gnd_only=True)
        )

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        self.power_in[0].connect_shallow(self.power_out)
        self.power_in[1].connect_shallow(self.power_out)

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        for power in [self.power_in[0], self.power_in[1], self.power_out]:
            power.voltage.merge(F.Range(1.6 * P.V, 5.5 * P.V))
