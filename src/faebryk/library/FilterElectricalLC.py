# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import math

import faebryk.library._F as F
from faebryk.libs.library import L


class FilterElectricalLC(F.Filter):
    in_: F.SignalElectrical
    out: F.SignalElectrical
    capacitor: F.Capacitor
    inductor: F.Inductor

    def __preinit__(self) -> None: ...

    @L.rt_field
    def has_parameter_construction_dependency(self):
        class _has_parameter_construction_dependency(
            F.has_parameter_construction_dependency.impl()
        ):
            def construct(_self):
                if not self._construct():
                    return
                _self._fullfill()

        return _has_parameter_construction_dependency()

    def _construct(self):
        # TODO other responses
        self.response.merge(F.Filter.Response.LOWPASS)

        # TODO other orders
        self.order.merge(2)

        L = self.inductor.inductance
        C = self.capacitor.capacitance
        fc = self.cutoff_frequency

        # TODO requires parameter constraint solving implemented
        # fc.merge(1 / (2 * math.pi * math.sqrt(C * L)))

        # instead assume fc being the driving param
        C.merge(1 / ((2 * math.pi * fc) ^ 2) * L)

        # TODO consider splitting C / L in a typical way

        # low pass
        self.in_.signal.connect_via(
            (self.inductor, self.capacitor),
            self.in_.reference.lv,
        )

        self.in_.signal.connect_via(self.inductor, self.out.signal)
