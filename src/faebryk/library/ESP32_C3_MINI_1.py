# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.library import L

logger = logging.getLogger(__name__)


class ESP32_C3_MINI_1(Module):
    """ESP32-C3-MINI-1 module"""

    esp32_c3: F.ESP32_C3
    # TODO: add components as described in the datasheet

    rf_output: F.Electrical
    chip_enable: F.ElectricLogic
    gpio = L.if_list(
        22, F.ElectricLogic
    )  # TODO: Only GPIO 0 to 10 and 18, 19 are exposed
    uart: F.UART_Base
    vdd3v3: F.ElectricPower

    # TODO: connect all components (nodes)

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

    def __preinit__(self):
        # connect power decoupling caps
        self.vdd3v3.decoupled.decouple()

        for lhs, rhs in zip(self.gpio, self.esp32_c3.gpio):
            lhs.connect(rhs)

        # TODO: set the following in the pinmux
        # UART0 gpio 20/21

    @L.rt_field
    def attach_to_footprint(self):
        gnd = self.vdd3v3.lv
        self.pinmap_default = {
            "1": gnd,
            "2": gnd,
            "3": self.vdd3v3.hv,
            # 4 is not connected
            "5": self.gpio[2].signal,
            "6": self.gpio[3].signal,
            # 7 is not connected
            "8": self.chip_enable.signal,
            # 9 is not connected
            # 10 is not connected
            "11": gnd,
            "12": self.gpio[0].signal,
            "13": self.gpio[1].signal,
            "14": gnd,
            # 15 is not connected
            "16": self.gpio[10].signal,
            # 17 is not connected
            "18": self.gpio[4].signal,
            "19": self.gpio[5].signal,
            "20": self.gpio[6].signal,
            "21": self.gpio[7].signal,
            "22": self.gpio[8].signal,
            "23": self.gpio[9].signal,
            # 24 is not connected
            # 25 is not connected
            "26": self.gpio[18].signal,
            "27": self.gpio[19].signal,
            # 28 is not connected
            # 29 is not connected
            "30": self.uart.rx.signal,
            "31": self.uart.tx.signal,
            # 32 is not connected
            # 33 is not connected
            # 34 is not connected
            # 35 is not connected
            "36": gnd,
            "37": gnd,
            "38": gnd,
            "39": gnd,
            "40": gnd,
            "41": gnd,
            "42": gnd,
            "43": gnd,
            "44": gnd,
            "45": gnd,
            "46": gnd,
            "47": gnd,
            "48": gnd,
            "49": gnd,
            "50": gnd,
            "51": gnd,
            "52": gnd,
            "53": gnd,
            "54": gnd,
            "55": gnd,
            "56": gnd,
            "57": gnd,
            "58": gnd,
            "59": gnd,
            "60": gnd,
            "61": gnd,
        }
        self.pinmap = dict(self.pinmap_default)

        return F.can_attach_to_footprint_via_pinmap(self.pinmap)

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://www.espressif.com/sites/default/files/russianDocumentation/esp32-c3-mini-1_datasheet_en.pdf"
    )
