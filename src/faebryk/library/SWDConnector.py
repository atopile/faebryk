# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L


class SWDConnector(Module):
    swd: F.SWD
    gnd_detect: F.ElectricLogic
    reference: F.ElectricPower

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("J")

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        self.get_trait(F.has_single_electric_reference).get_reference().connect(
            self.reference
        )

        # ------------------------------------
        #          parametrization
        # ------------------------------------
