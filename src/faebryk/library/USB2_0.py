# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.core import ModuleInterface
from faebryk.library.DifferentialPair import DifferentialPair
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.Range import Range


class USB2_0(ModuleInterface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        class IFS(ModuleInterface.IFS()):
            d = DifferentialPair()
            buspower = ElectricPower()

        self.IFs = IFS(self)

        self.IFs.buspower.PARAMs.voltage.merge(Range(4.75, 5.25))
