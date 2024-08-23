# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module


from faebryk.libs.units import P, Quantity

logger = logging.getLogger(__name__)


class UART_RS485(Module):





            power: F.ElectricPower
            uart = UART_Base()
            rs485 = RS485()
            read_enable: F.Electrical
            write_enable: F.Electrical


            max_data_rate : F.TBD[Quantity]
            gpio_voltage : F.TBD[Quantity]

        self.power.voltage.merge(F.Range(3.3 * P.V, 5.0 * P.V))

        self.power.get_trait(can_be_decoupled).decouple()

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
