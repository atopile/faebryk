# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class RS232TranceiverBase(Module):
    """
    Common base module for RS232 tranceivers
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    c1: F.ElectricPower
    c2: F.ElectricPower
    vp: F.ElectricPower
    vn: F.ElectricPower
    power: F.ElectricPower

    enable: F.ElectricLogic

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        for pwr in self.get_children(direct_only=True, types=F.ElectricPower):
            cap = pwr.decoupled.decouple()
            # TODO: min values according to self.power.voltage
            # 3.0V to 3.6V > C_all = 0.1μF
            # 4.5V to 5.5V > C1 = 0.047µF, C2,Cvp, Cvn = 0.33µF
            # 3.0V to 5.5V > C_all = 0.22μF
            #
            cap.capacitance.merge(0.22 * P.uF)
            cap.rated_voltage.merge(F.Range.lower_bound(16 * P.V))

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        self.power.voltage.merge(F.Range(3.0 * P.V, 5.5 * P.V))
