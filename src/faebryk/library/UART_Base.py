# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface



from faebryk.libs.units import Quantity


class UART_Base(ModuleInterface):



            rx: F.ElectricLogic
            tx: F.ElectricLogic


            baud: F.TBD[Quantity]

        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(has_single_electric_reference_defined(ref))

    def _on_connect(self, other: "UART_Base"):
        super()._on_connect(other)

        self.baud.merge(other.baud)
