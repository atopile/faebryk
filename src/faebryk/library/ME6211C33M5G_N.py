# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module
from faebryk.core.util import connect_to_all_interfaces





from faebryk.libs.units import P


class ME6211C33M5G_N(Module):
    """
    3.3V 600mA LDO
    """

    def __init__(self, default_enabled: bool = True) -> None:
        super().__init__()

        # interfaces

            power_in: F.ElectricPower
            power_out: F.ElectricPower
            enable: F.Electrical

        # components




        # set constraints
        self.power_out.voltage.merge(F.Range(3.3 * 0.98 * P.V, 3.3 * 1.02 * P.V))

        # connect decouple capacitor
        self.power_in.get_trait(can_be_decoupled).decouple()
        self.power_out.get_trait(can_be_decoupled).decouple()

        # LDO in & out share gnd reference
        self.power_in.lv.connect(self.power_out.lv)

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": self.power_in.hv,
                    "2": self.power_in.lv,
                    "3": self.enable,
                    "5": self.power_out.hv,
                }
            )
        )

        self.add_trait(
            has_datasheet_defined(
                "https://datasheet.lcsc.com/lcsc/1811131510_MICRONE-Nanjing-Micro-One-Elec-ME6211C33M5G-N_C82942.pdf"
            )
        )

        if default_enabled:
            self.enable.connect(self.power_in.hv)

        connect_to_all_interfaces(self.power_in.lv, [self.power_out.lv])
