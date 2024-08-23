# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module


from faebryk.libs.units import Quantity



class Potentiometer(Module):



            resistors = L.if_list(2, F.Electrical)
            wiper: F.Electrical


            total_resistance : F.TBD[Quantity]


            resistors = L.if_list(2, F.Resistor)

        for i, resistor in enumerate(self.resistors):
            self.resistors[i].connect_via(resistor, self.wiper)

            # TODO use range(0, total_resistance)
            resistor.resistance.merge(self.total_resistance)

    def connect_as_voltage_divider(
        self, high: F.Electrical, low: F.Electrical, out: F.Electrical
    ):
        self.resistors[0].connect(high)
        self.resistors[1].connect(low)
        self.wiper.connect(out)
