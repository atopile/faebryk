# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface





class USB_C(ModuleInterface):



            usb3 : USB3
            cc1: F.Electrical
            cc2: F.Electrical
            sbu1: F.Electrical
            sbu2: F.Electrical
            rx = DifferentialPair()
            tx = DifferentialPair()

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )
