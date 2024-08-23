# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module, ModuleInterface





class Sercom(ModuleInterface):



            unnamed = L.if_list(4, F.ElectricLogic)

        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(has_single_electric_reference_defined(ref))
