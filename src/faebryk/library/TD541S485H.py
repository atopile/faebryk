# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module



logger = logging.getLogger(__name__)


class TD541S485H(Module):





            power: F.ElectricPower
            power_iso_in: F.ElectricPower
            power_iso_out: F.ElectricPower
            uart = F.UART_Base()
            rs485 = RS485()
            read_enable: F.Electrical
            write_enable: F.Electrical



        self.power.decoupled.decouple()
        self.power_iso_in.decoupled.decouple()
        self.power_iso_out.decoupled.decouple()

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

        self.power_iso_in.lv.connect(self.power_iso_out.lv)

        x = self
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.power.lv,
                    "2": x.power.hv,
                    "3": x.uart.rx.signal,
                    "4": x.read_enable,
                    "5": x.write_enable,
                    "6": x.uart.tx.signal,
                    "7": x.power.hv,
                    "8": x.power.lv,
                    "9": x.power_iso_out.lv,
                    "10": x.power_iso_out.hv,
                    "13": x.rs485.diff_pair.n,
                    "14": x.rs485.diff_pair.p,
                    "15": x.power_iso_in.hv,
                    "16": x.power_iso_in.lv,
                }
            )
        )
