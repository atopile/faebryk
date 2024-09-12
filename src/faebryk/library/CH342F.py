# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.picker.picker import DescriptiveProperties
from faebryk.libs.units import P  # noqa: F401
from faebryk.libs.util import NotNone

logger = logging.getLogger(__name__)


class CH342F(Module):
    """
    Dual UART-USB converter
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    usb: F.USB2_0
    uart = L.list_field(2, F.UART)

    tnow = L.list_field(2, F.ElectricLogic)
    ri = L.list_field(2, F.ElectricLogic)
    dcd = L.list_field(2, F.ElectricLogic)

    reset: F.ElectricLogic
    active: F.ElectricLogic

    vdd_5v: F.ElectricPower
    v_io: F.ElectricPower
    v_3v: F.ElectricPower

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://wch-ic.com/downloads/CH342DS1_PDF.html"
    )

    @L.rt_field
    def can_attach_to_footprint(self):
        return F.can_attach_to_footprint_via_pinmap(
            {
                "1": self.ri[0].signal,
                "2": self.usb.usb_if.buspower.lv,
                "3": self.usb.usb_if.d.p,
                "4": self.usb.usb_if.d.n,
                "5": self.v_io.hv,
                "6": self.v_3v.hv,
                "7": self.vdd_5v.hv,
                "8": self.usb.usb_if.buspower.hv,
                "9": self.reset.signal,
                "10": self.uart[1].cts.signal,
                "11": self.uart[1].rts.signal,
                "12": self.uart[1].base_uart.rx.signal,
                "13": self.uart[1].base_uart.tx.signal,
                "14": self.uart[1].dsr.signal,
                "15": self.uart[1].dtr.signal,
                "16": self.dcd[1].signal,
                "17": self.ri[1].signal,
                "18": self.uart[0].cts.signal,
                "19": self.uart[0].rts.signal,
                "20": self.uart[0].base_uart.rx.signal,
                "21": self.uart[0].base_uart.tx.signal,
                "22": self.uart[0].dsr.signal,
                "23": self.uart[0].dtr.signal,
                "24": self.dcd[0].signal,
                "25": self.usb.usb_if.buspower.lv,
            }
        )

    @L.rt_field
    def descriptive_properties(self):
        return F.has_descriptive_properties_defined(
            {
                DescriptiveProperties.manufacturer: "WCH",
                DescriptiveProperties.partno: "CH342F",
            },
        )

    def __init__(
        self,
        duplex_mode_uart_0: F.CH342.DuplexMode = F.CH342.DuplexMode.FULL,
        duplex_mode_uart_1: F.CH342.DuplexMode = F.CH342.DuplexMode.FULL,
    ):
        super().__init__()
        self._duplex_mode_uart_0 = duplex_mode_uart_0
        self._duplex_mode_uart_1 = duplex_mode_uart_1

    def __preinit__(self) -> None:
        # ----------------------------------------
        #                aliasess
        # ----------------------------------------
        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        self.vdd_5v.voltage.merge(F.Range(4 * P.V, 5.5 * P.V))
        self.v_3v.voltage.merge(F.Range.from_center(3.3 * P.V, 0.3 * P.V))
        self.v_io.voltage.merge(F.Range(1.7 * P.V, 5.5 * P.V))

        # set the duplex mode
        if self._duplex_mode_uart_0 == F.CH342.DuplexMode.HALF:
            self.uart[0].dtr.get_trait(F.ElectricLogic.can_be_pulled).pull(up=False)
            NotNone(
                self.uart[0].dtr.get_trait(F.ElectricLogic.has_pulls).get_pulls()[1]
            ).resistance.merge(4.7 * P.kohm)
            self.tnow[0].connect(self.uart[0].dtr)
        if self._duplex_mode_uart_1 == F.CH342.DuplexMode.HALF:
            self.uart[1].dtr.get_trait(F.ElectricLogic.can_be_pulled).pull(up=False)
            NotNone(
                self.uart[1].dtr.get_trait(F.ElectricLogic.has_pulls).get_pulls()[1]
            ).resistance.merge(4.7 * P.kohm)
            self.tnow[1].connect(self.uart[1].dtr)

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        # configure for 3.3V GPIO operation with internal LDO
        self.vdd_5v.connect(self.usb.usb_if.buspower)
        self.v_3v.connect(self.v_io)

        self.vdd_5v.get_trait(F.can_be_decoupled).decouple().capacitance.merge(1 * P.uF)
        self.v_3v.get_trait(F.can_be_decoupled).decouple().capacitance.merge(0.1 * P.uF)
        self.v_io.get_trait(F.can_be_decoupled).decouple().capacitance.merge(1 * P.uF)

        F.can_attach_to_footprint().attach(
            F.QFN(
                pin_cnt=24,
                exposed_thermal_pad_cnt=1,
                size_xy=(4 * P.mm, 4 * P.mm),
                pitch=0.5 * P.mm,
                exposed_thermal_pad_dimensions=(2.65 * P.mm, 2.65 * P.mm),
                has_thermal_vias=False,
            )
        )
