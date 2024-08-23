# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module


from faebryk.libs.units import Quantity


logger = logging.getLogger(__name__)


class Resistor_Voltage_Divider(Module):



            resistor = L.if_list(2, Resistor)


            node = L.if_list(3, F.Electrical)


            ratio : F.TBD[Quantity]
            max_current : F.TBD[Quantity]

        self.node[0].connect_via(self.resistor[0], self.node[1])
        self.node[1].connect_via(self.resistor[1], self.node[2])

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.node[0], self.node[1])
