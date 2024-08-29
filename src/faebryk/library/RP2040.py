# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L

logger = logging.getLogger(__name__)


class RP2040(Module):
    io_vdd: F.ElectricPower
    adc_vdd: F.ElectricPower
    core_vdd: F.ElectricPower
    vreg_in: F.ElectricPower
    vreg_out: F.ElectricPower
    power_vusb: F.ElectricPower
    gpio = L.node_list(30, F.Electrical)
    run: F.ElectricLogic
    usb: F.USB2_0
    qspi = L.f_field(F.MultiSPI)(data_lane_count=4)
    xin: F.Electrical
    xout: F.Electrical
    test: F.Electrical
    swd: F.SWD
    # TODO: these peripherals and more can be mapped to different pins
    i2c: F.I2C
    uart: F.UART_Base

    def __preinit__(self):
        # decouple power rails and connect GNDs toghether
        gnd = self.io_vdd.lv
        for pwrrail in [
            self.io_vdd,
            self.adc_vdd,
            self.core_vdd,
            self.vreg_in,
            self.vreg_out,
            self.usb.usb_if.buspower,
        ]:
            pwrrail.lv.connect(gnd)
            pwrrail.decoupled.decouple()

        # set parameters
        # self.io_vdd.voltage.merge(F.Range(1.8*P.V, 3.63*P.V))

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf"
    )
