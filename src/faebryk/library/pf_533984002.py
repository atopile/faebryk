# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module







class pf_533984002(Module):


        # interfaces

            pin = L.if_list(2, F.Electrical)
            mount = L.if_list(2, F.Electrical)

        x = self
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.pin[0],
                    "2": x.pin[1],
                    "3": x.mount[0],
                    "4": x.mount[1],
                }
            )
        )

        self.add_trait(
            has_datasheet_defined(
                "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1912111437_SHOU-HAN-1-25-2P_C393945.pdf"
            )
        )

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("J")
