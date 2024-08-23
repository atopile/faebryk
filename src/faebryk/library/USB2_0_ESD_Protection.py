# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module


from faebryk.libs.units import P


logger = logging.getLogger(__name__)


class USB2_0_ESD_Protection(Module):





            usb = L.if_list(2, USB2_0)


            vbus_esd_protection : F.TBD[bool]
            data_esd_protection : F.TBD[bool]

        self.usb[0].usb_if.buspower.voltage.merge(F.Range(4.75 * P.V, 5.25 * P.V))

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.usb[0].usb_if.d, self.usb[1].usb_if.d)
        self.usb[0].connect(self.usb[1])

        self.usb[0].usb_if.buspower.connect(self.usb[1].usb_if.buspower)

        self.usb[0].usb_if.buspower.get_trait(can_be_decoupled).decouple()

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
