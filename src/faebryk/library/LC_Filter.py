# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


from faebryk.core.core import Module, Parameter
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricPower import ElectricPower
from faebryk.libs.util import times
from vindriktning_esp32_c3.library.Inductor import Inductor


class LC_Filter(Module):
    """
    Pi type LC filter
    #TODO: make into universal LC filter or filter module
    """

    def __init__(self, inductance: Parameter, capacitance: Parameter):
        super().__init__()

        # Interfaces
        class _IFs(Module.IFS()):
            power = ElectricPower()
            signal_in = Electrical()
            signal_out = Electrical()

        self.IFs = _IFs(self)

        # Components
        class _NODEs(Module.NODES()):
            inductor = Inductor(inductance)
            capacitor = times(2, Capacitor)

        self.NODEs = _NODEs(self)

        for cap in self.NODEs.capacitor:
            cap.PARAMs.capacitance.merge(capacitance)

        # Connections
        self.IFs.signal_in.connect_via(self.NODEs.inductor, self.IFs.signal_out)
        self.IFs.signal_in.connect_via(self.NODEs.capacitor[0], self.IFs.power.IFs.lv)
        self.IFs.signal_out.connect_via(self.NODEs.capacitor[1], self.IFs.power.IFs.lv)

        # traits
        self.add_trait(can_bridge_defined(self.IFs.signal_in, self.IFs.signal_out))
