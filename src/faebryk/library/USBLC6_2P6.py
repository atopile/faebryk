# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module



class USBLC6_2P6(Module):
    """
    Low capacitance TVS diode array (for USB2.0)
    """



        # interfaces

            usb : USB2_0

        x = self
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.usb.usb_if.d.p,
                    "2": x.usb.usb_if.buspower.lv,
                    "3": x.usb.usb_if.d.n,
                    "4": x.usb.usb_if.d.n,
                    "5": x.usb.usb_if.buspower.hv,
                    "6": x.usb.usb_if.d.p,
                }
            )
        )

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
    datasheet = L.f_field(F.has_datasheet_defined)("https://datasheet.lcsc.com/lcsc/2108132230_TECH-PUBLIC-USBLC6-2P6_C2827693.pdf")
