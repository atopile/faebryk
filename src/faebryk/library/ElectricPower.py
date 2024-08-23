# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


import faebryk.library._F as F
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.libs.library import L
from faebryk.libs.units import P, Quantity


class ElectricPower(F.Power):
    class can_be_decoupled_power(F.can_be_decoupled_defined):
        def __init__(self) -> None: ...

        def on_obj_set(self):
            super().__init__(hv=self.get_obj().hv, lv=self.get_obj().lv)

        def decouple(self):
            return (
                super()
                .decouple()
                .builder(
                    lambda c: c.rated_voltage.merge(
                        F.Range(0 * P.V, self.get_obj().voltage * 2.0)
                    )
                )
            )

    class can_be_surge_protected_power(F.can_be_surge_protected_defined):
        def __init__(self) -> None: ...

        def on_obj_set(self):
            super().__init__(self.get_obj().lv, self.get_obj().hv)

        def protect(self):
            return [
                tvs.builder(
                    lambda t: t.reverse_working_voltage.merge(self.get_obj().voltage)
                )
                for tvs in super().protect()
            ]

    hv: F.Electrical
    lv: F.Electrical

    voltage: F.TBD[Quantity]

    surge_protected: can_be_surge_protected_power
    decoupled: can_be_decoupled_power

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(self)

    def __preinit__(self) -> None:
        ...
        # self.voltage.merge(
        #    self.hv.potential - self.lv.potential
        # )

    def _on_connect(self, other: ModuleInterface) -> None:
        super()._on_connect(other)

        if not isinstance(other, F.ElectricPower):
            return

        self.voltage.merge(other.voltage)
