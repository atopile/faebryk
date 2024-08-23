# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module


logger = logging.getLogger(__name__)


class Powered_Relay(Module):



            relay = Relay()
            indicator = PoweredLED()
            flyback_diode = Diode()
            relay_driver = PowerSwitchMOSFET(lowside=True, normally_closed=False)


            switch_a_nc: F.Electrical
            switch_a_common: F.Electrical
            switch_a_no: F.Electrical
            switch_b_no: F.Electrical
            switch_b_common: F.Electrical
            switch_b_nc: F.Electrical
            enable: F.ElectricLogic
            power: F.ElectricPower



        self.relay.switch_a_common.connect(self.switch_a_common)
        self.relay.switch_a_nc.connect(self.switch_a_nc)
        self.relay.switch_a_no.connect(self.switch_a_no)
        self.relay.switch_b_common.connect(self.switch_b_common)
        self.relay.switch_b_nc.connect(self.switch_b_nc)
        self.relay.switch_b_no.connect(self.switch_b_no)

        self.relay_driver.power_in.connect(self.power)
        self.relay_driver.logic_in.connect(self.enable)
        self.relay_driver.switched_power_out.lv.connect(self.relay.coil_n)
        self.relay_driver.switched_power_out.hv.connect(self.relay.coil_p)

        self.relay.coil_n.connect_via(self.flyback_diode, self.relay.coil_p)

        self.indicator.power.connect(self.relay_driver.switched_power_out)
