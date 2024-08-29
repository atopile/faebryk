# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import Quantity


class Crystal(Module):
    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------

    frequency: F.TBD[Quantity]
    frequency_tolerance: F.TBD[F.Range]
    frequency_temperature_tolerance: F.TBD[F.Range]
    frequency_ageing: F.TBD[F.Range]
    equivalent_series_resistance: F.TBD[Quantity]
    shunt_capacitance: F.TBD[Quantity]
    load_impedance: F.TBD[Quantity]

    gnd: F.Electrical
    unnamed = L.list_field(2, F.Electrical)

    # ----------------------------------------
    #               parameters
    # ----------------------------------------

    # ----------------------------------------
    #                traits
    # ----------------------------------------
    designator = L.f_field(F.has_designator_prefix_defined)("XTAL")

    # ----------------------------------------
    #                connections
    # ----------------------------------------
