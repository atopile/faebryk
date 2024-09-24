# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from itertools import pairwise

import faebryk.library._F as F
from faebryk.libs.app.parameters import resolve_dynamic_parameters
from faebryk.libs.units import P
from faebryk.libs.util import times


def test_fused_power():
    power_in = F.ElectricPower()
    power_out = F.ElectricPower()

    power_in.voltage.merge(10 * P.V)
    power_in.max_current.merge(500 * P.mA)

    power_in_fused = power_in.fused()

    power_in_fused.connect(power_out)

    fuse = next(iter(power_in_fused.get_children(direct_only=False, types=F.Fuse)))

    resolve_dynamic_parameters(fuse.get_graph())

    assert fuse.trip_current.get_most_narrow() == F.Range(0 * P.A, 500 * P.mA)
    assert power_out.voltage.get_most_narrow() == 10 * P.V
    # self.assertEqual(
    #    power_in_fused.max_current.get_most_narrow(), F.Range(0 * P.A, 500 * P.mA)
    # )
    assert power_out.max_current.get_most_narrow() == F.TBD()


def test_voltage_propagation():
    powers = times(4, F.ElectricPower)

    powers[0].voltage.merge(F.Range(10 * P.V, 15 * P.V))

    for p1, p2 in pairwise(powers):
        p1.connect(p2)

    resolve_dynamic_parameters(powers[0].get_graph())

    assert powers[-1].voltage.get_most_narrow() == F.Range(10 * P.V, 15 * P.V)

    powers[3].voltage.merge(10 * P.V)
    assert powers[0].voltage.get_most_narrow() == 10 * P.V
