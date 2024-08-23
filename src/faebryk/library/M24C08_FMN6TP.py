# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module







from faebryk.libs.units import P


logger = logging.getLogger(__name__)


# TODO remove generic stuff into EEPROM/i2c device etc
class M24C08_FMN6TP(Module):



            power: F.ElectricPower
            data = I2C()
            nwc: F.ElectricLogic
            e = L.if_list(3, F.ElectricLogic)

        x = self
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.e[0].signal,
                    "2": x.e[1].signal,
                    "3": x.e[2].signal,
                    "4": x.power.lv,
                    "5": x.data.sda.signal,
                    "6": x.data.scl.signal,
                    "7": x.nwc.signal,
                    "8": x.power.hv,
                }
            )
        ).attach(SOIC(8, size_xy=(3.9 * P.mm, 4.9 * P.mm), pitch=1.27 * P.mm))

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

        self.data.terminate()
        self.power.get_trait(can_be_decoupled).decouple()

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

    def set_address(self, addr: int):
        assert addr < (1 << len(self.e))

        for i, e in enumerate(self.e):
            e.set(addr & (1 << i) != 0)
