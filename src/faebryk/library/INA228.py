# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L
from faebryk.libs.units import P

logger = logging.getLogger(__name__)


class INA228(Module):
    def set_address(self, address: int = 0x00) -> None:
        """Set the I2C address of the INA228"""
        # allias
        gnd = self.power.lv
        vs = self.power.hv
        sda = self.i2c.sda
        scl = self.i2c.scl

        address_map = {
            0b0000: (gnd, gnd),
            0b0001: (gnd, vs),
            0b0010: (gnd, sda),
            0b0011: (gnd, scl),
            0b0100: (vs, gnd),
            0b0101: (vs, vs),
            0b0110: (vs, sda),
            0b0111: (vs, scl),
            0b1000: (sda, gnd),
            0b1001: (sda, vs),
            0b1010: (sda, sda),
            0b1011: (sda, scl),
            0b1100: (scl, gnd),
            0b1101: (scl, vs),
            0b1110: (scl, sda),
            0b1111: (scl, scl),
        }
        address |= 0b1000000
        # address looks like 0b100xxxx

        a1_connect, a0_connect = address_map.get(address, (gnd, gnd))
        self.address_config_pin[0].connect(a0_connect)
        self.address_config_pin[1].connect(a1_connect)

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    i2c: F.I2C
    power: F.ElectricPower
    address_config_pin = L.list_field(2, F.ElectricLogic)
    alert: F.ElectricLogic
    bus_voltage_sense: F.Electrical
    differential_input: F.DifferentialPair

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://www.ti.com/lit/ds/symlink/ina228.pdf"
    )

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        self.power.voltage.merge(F.Range(2.7 * P.V, 5.5 * P.V))
