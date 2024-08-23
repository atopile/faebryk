# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module





from faebryk.libs.units import P



class USB_C_5V_PSU(Module):


        # interfaces

            power_out: F.ElectricPower
            usb = USB_C()

        # components

            configuration_resistors = L.if_list(
                2,
                lambda: F.Resistor().builder(
                    lambda r: r.resistance.merge(F.Constant(5.1 * P.kohm))
                ),
            )

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

        # configure as ufp with 5V@max3A
        self.usb.cc1.connect_via(self.configuration_resistors[0], self.power_out.lv)
        self.usb.cc2.connect_via(self.configuration_resistors[1], self.power_out.lv)
