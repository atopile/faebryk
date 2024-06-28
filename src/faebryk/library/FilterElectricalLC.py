# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import math

from faebryk.core.util import specialize_interface
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Filter import Filter
from faebryk.library.has_parameter_construction_dependency import (
    has_parameter_construction_dependency,
)
from faebryk.library.Inductor import Inductor
from faebryk.library.SignalElectrical import SignalElectrical


class FilterElectricalLC(Filter):
    @classmethod
    def PARAMS(cls):
        class _PARAMs(super().PARAMS()): ...

        return _PARAMs

    def __init__(self):
        super().__init__()

        self.PARAMs = self.PARAMS()(self)

        self.IFs_filter = self.IFs

        class _IFs(super().IFS()):
            in_ = SignalElectrical()
            out = SignalElectrical()

        self.IFs = _IFs(self)

        specialize_interface(self.IFs_filter.in_, self.IFs.in_)
        specialize_interface(self.IFs_filter.out, self.IFs.out)

        class _NODES(super().NODES()):
            capacitor = Capacitor()
            inductor = Inductor()

        self.NODEs = _NODES(self)

        class _has_parameter_construction_dependency(
            has_parameter_construction_dependency.impl()
        ):
            def construct(_self):
                if not self._construct():
                    return
                _self._fullfill()

        self.add_trait(_has_parameter_construction_dependency())

    def _construct(self):
        # TODO other responses
        self.PARAMs.response.merge(Filter.Response.LOWPASS)

        # TODO other orders
        self.PARAMs.order.merge(2)

        L = self.NODEs.inductor.PARAMs.inductance
        C = self.NODEs.capacitor.PARAMs.capacitance
        fc = self.PARAMs.cutoff_frequency

        # TODO requires parameter constraint solving implemented
        # fc.merge(1 / (2 * math.pi * math.sqrt(C * L)))

        # instead assume fc being the driving param
        C.merge(1 / ((2 * math.pi * fc) ^ 2) * L)

        # TODO consider splitting C / L in a typical way

        # low pass
        self.IFs.in_.IFs.signal.connect_via(
            (self.NODEs.inductor, self.NODEs.capacitor),
            self.IFs.in_.IFs.reference.IFs.lv,
        )

        self.IFs.in_.IFs.signal.connect_via(
            self.NODEs.inductor, self.IFs.out.IFs.signal
        )
