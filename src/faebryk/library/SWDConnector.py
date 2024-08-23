# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module, ModuleInterface





class SWDConnector(Module):



            swd = SWD()
            gnd_detect: F.ElectricLogic
            vcc: F.ElectricPower



    designator_prefix = L.f_field(F.has_designator_prefix_defined)("J")

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )
