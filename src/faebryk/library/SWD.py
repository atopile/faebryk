# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface




class SWD(ModuleInterface):



            clk: F.ElectricLogic
            dio: F.ElectricLogic
            swo: F.ElectricLogic
            reset: F.ElectricLogic



    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )
