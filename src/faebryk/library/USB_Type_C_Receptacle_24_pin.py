# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module







class USB_Type_C_Receptacle_24_pin(Module):


        # interfaces

            # TODO make arrays?
            cc1: F.Electrical
            cc2: F.Electrical
            sbu1: F.Electrical
            sbu2: F.Electrical
            shield: F.Electrical
            # power
            gnd = L.if_list(4, F.Electrical)
            vbus = L.if_list(4, F.Electrical)
            # diffpairs: p, n
            rx1 = DifferentialPair()
            rx2 = DifferentialPair()
            tx1 = DifferentialPair()
            tx2 = DifferentialPair()
            d1 = DifferentialPair()
            d2 = DifferentialPair()

        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "A1": self.gnd[0],
                    "A2": self.tx1.p,
                    "A3": self.tx1.n,
                    "A4": self.vbus[0],
                    "A5": self.cc1,
                    "A6": self.d1.p,
                    "A7": self.d1.n,
                    "A8": self.sbu1,
                    "A9": self.vbus[1],
                    "A10": self.rx2.n,
                    "A11": self.rx2.p,
                    "A12": self.gnd[1],
                    "B1": self.gnd[2],
                    "B2": self.tx2.p,
                    "B3": self.tx2.n,
                    "B4": self.vbus[2],
                    "B5": self.cc2,
                    "B6": self.d2.p,
                    "B7": self.d2.n,
                    "B8": self.sbu2,
                    "B9": self.vbus[3],
                    "B10": self.rx1.n,
                    "B11": self.rx1.p,
                    "B12": self.gnd[3],
                    "0": self.shield,
                }
            )
        )

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("J")
