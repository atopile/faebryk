# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import P

logger = logging.getLogger(__name__)


class INA228_ReferenceDesign(Module):
    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    shunt: F.Resistor
    ina288: F.INA228

    pwr_load: F.ElectricPower
    pwr_source: F.ElectricPower

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    @L.rt_field
    def can_bridge(self):
        (F.can_bridge_defined(self.pwr_load, self.pwr_source))

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self, gnd_only=True)
        )

    def __init__(self, filtered: bool = False):
        super().__init__()
        self._filtered = filtered

    def __preinit__(self):
        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        self.shunt.resistance.merge(15 * P.mohm)
        self.shunt.rated_power.merge(2 * P.W)
        # TODO: calculate according to datasheet p36

        if self._filtered:
            filter_cap = F.Capacitor()
            filter_resistors = L.list_field(2, F.Resistor)

            filter_cap.capacitance.merge(0.1 * P.uF)
            filter_cap.rated_voltage.merge(170 * P.V)
            for res in filter_resistors:
                res.resistance.merge(10 * P.kohm)
        # TODO: auto calculate, see: https://www.ti.com/lit/ug/tidu473/tidu473.pdf

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        self.pwr_load.hv.connect_via(self.shunt, self.pwr_source.hv)
        self.ina288.bus_voltage_sense.connect(self.pwr_load.hv)
        if self._filtered:
            self.pwr_load.hv.connect_via(filter_cap, self.pwr_source.hv)
            self.ina288.differential_input.n.connect_via(
                filter_resistors[1], self.pwr_load.hv
            )
            self.ina288.differential_input.p.connect_via(
                filter_resistors[0], self.pwr_source.hv
            )
        else:
            self.ina288.differential_input.n.connect(self.pwr_load.hv)
            self.ina288.differential_input.p.connect(self.pwr_source.hv)

        # decouple power rail
        self.ina288.power.get_trait(F.can_be_decoupled).decouple().capacitance.merge(
            0.1 * P.uF
        )
