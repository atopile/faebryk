# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.Signal import Signal


class SignalElectrical(Signal):
    def __init__(self) -> None:
        super().__init__()

        class _IFs(Signal.IFS()):
            # line is a better name, but for compatibility with Logic we use signal
            # might change in future
            signal = Electrical()
            reference = ElectricPower()

        self.IFs = _IFs(self)
