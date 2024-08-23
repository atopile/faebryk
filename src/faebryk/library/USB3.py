# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface


from faebryk.libs.units import P


class USB3(ModuleInterface):



            usb3_if = USB3_IF()

        self.usb3_if.gnd_drain.connect(self.usb3_if.usb_if.buspower.lv)

        self.usb3_if.usb_if.buspower.voltage.merge(F.Range(4.75 * P.V, 5.5 * P.V))
