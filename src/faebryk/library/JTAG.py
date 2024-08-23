# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface





class JTAG(ModuleInterface):



            dbgrq: F.ElectricLogic
            tdo: F.ElectricLogic
            tdi: F.ElectricLogic
            tms: F.ElectricLogic
            tck: F.ElectricLogic
            n_trst: F.ElectricLogic
            n_reset: F.ElectricLogic
            vtref: F.Electrical

        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(has_single_electric_reference_defined(ref))
