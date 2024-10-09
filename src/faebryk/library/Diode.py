# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.parameter import ParameterOperatable
from faebryk.libs.library import L
from faebryk.libs.units import P


class Diode(Module):
    forward_voltage = L.p_field(
        units=P.V,
        likely_constrained=True,
        soft_set=L.Range(0.1 * P.V, 1 * P.V),
        tolerance_guess=10 * P.percent,
    )
    current = L.p_field(
        units=P.A,
        likely_constrained=True,
        soft_set=L.Range(0.1 * P.mA, 100 * P.A),
        tolerance_guess=10 * P.percent,
    )
    reverse_working_voltage = L.p_field(
        units=P.V,
        likely_constrained=True,
        soft_set=L.Range(10 * P.V, 100 * P.V),
        tolerance_guess=10 * P.percent,
    )
    reverse_leakage_current = L.p_field(
        units=P.A,
        likely_constrained=True,
        soft_set=L.Range(0.1 * P.nA, 1 * P.µA),
        tolerance_guess=10 * P.percent,
    )
    max_current = L.p_field(
        units=P.A,
        likely_constrained=True,
        soft_set=L.Range(0.1 * P.mA, 100 * P.A),
        tolerance_guess=10 * P.percent,
    )

    anode: F.Electrical
    cathode: F.Electrical

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.anode, self.cathode)

    @L.rt_field
    def simple_value_representation(self):
        return F.has_simple_value_representation_based_on_params(
            (self.forward_voltage,),
            lambda p: p.as_unit("V"),
        )

    designator_prefix = L.f_field(F.has_designator_prefix_defined)(
        F.has_designator_prefix.Prefix.D
    )

    @L.rt_field
    def pin_association_heuristic(self):
        return F.has_pin_association_heuristic_lookup_table(
            mapping={
                self.anode: ["A", "Anode", "+"],
                self.cathode: ["K", "C", "Cathode", "-"],
            },
            accept_prefix=False,
            case_sensitive=False,
        )

    def __preinit__(self):
        self.current.constrain_le(self.max_current)

    def get_needed_series_resistance_for_current_limit(
        self, input_voltage_V: ParameterOperatable
    ):
        return (input_voltage_V - self.forward_voltage) / self.current
