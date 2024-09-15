# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import ModuleException
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.picker.picker import DescriptiveProperties
from faebryk.libs.util import assert_once, times

logger = logging.getLogger(__name__)


class CH342F(F.CH342):
    """
    USB to double Base UART converter

    QFN-24-EP(4x4)
    """

    @assert_once
    def enable_tnow_mode(self, uart: F.UART):
        """
        Set TNOW mode for specified UART for use with RS485 tranceivers.
        The TNOW pin can be connected to the tx_enable and rx_enable
        pins of the RS485 tranceiver for automatic half-duplex control.
        """
        if uart not in self.uart:
            raise ModuleException(
                self, f"{uart.get_full_name()} is not a part of this module"
            )

        uart.dtr.set_weak(on=False)
        uart.dtr.connect(self.tnow[self.uart.index(uart)])

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    tnow = L.list_field(2, F.ElectricLogic)
    vbus_detect: F.ElectricLogic

    reset: F.ElectricLogic
    active: F.ElectricLogic

    uart = times(2, F.UART)

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    @L.rt_field
    def can_attach_to_footprint(self):
        return F.can_attach_to_footprint_via_pinmap(
            {
                "1": self.uart[0].ri.signal,
                "2": self.usb.usb_if.buspower.lv,
                "3": self.usb.usb_if.d.p,
                "4": self.usb.usb_if.d.n,
                "5": self.power_io.hv,
                "6": self.power_3v.hv,
                "7": self.integrated_regulator.power_in.hv,
                "8": self.usb.usb_if.buspower.hv,
                "9": self.reset.signal,
                "10": self.uart[1].cts.signal,
                "11": self.uart[1].rts.signal,
                "12": self.uart[1].base_uart.rx.signal,
                "13": self.uart[1].base_uart.tx.signal,
                "14": self.uart[1].dsr.signal,
                "15": self.uart[1].dtr.signal,
                "16": self.uart[1].dcd.signal,
                "17": self.uart[1].ri.signal,
                "18": self.uart[0].cts.signal,
                "19": self.uart[0].rts.signal,
                "20": self.uart[0].base_uart.rx.signal,
                "21": self.uart[0].base_uart.tx.signal,
                "22": self.uart[0].dsr.signal,
                "23": self.uart[0].dtr.signal,
                "24": self.uart[0].dcd.signal,
                "25": self.usb.usb_if.buspower.lv,
            }
        )

    @L.rt_field
    def pin_association_heuristic(self):
        return F.has_pin_association_heuristic_lookup_table(
            mapping={
                self.uart[0].cts.signal: ["CTS0"],
                self.uart[1].cts.signal: ["CTS1"],
                self.uart[0].dcd.signal: ["DCD0"],
                self.uart[1].dcd.signal: ["DCD1"],
                self.uart[0].dsr.signal: ["DSR0"],
                self.uart[1].dsr.signal: ["DSR1"],
                self.uart[0].dtr.signal: ["DTR0"],
                self.uart[1].dtr.signal: ["DTR1"],
                # self.power_3v.lv: ["EP"],
                self.power_3v.lv: ["GND"],
                self.uart[0].ri.signal: ["RI0"],
                self.uart[1].ri.signal: ["RI1"],
                self.reset.signal: ["RST"],
                self.uart[0].rts.signal: ["RTS0"],
                self.uart[1].rts.signal: ["RTS1"],
                self.uart[0].base_uart.rx.signal: ["RXD0"],
                self.uart[1].base_uart.rx.signal: ["RXD1"],
                self.uart[0].base_uart.tx.signal: ["TXD0"],
                self.uart[1].base_uart.tx.signal: ["TXD1"],
                self.usb.usb_if.d.p: ["UD+"],
                self.usb.usb_if.d.n: ["UD-"],
                self.power_3v.hv: ["V3"],
                self.vbus_detect.signal: ["VBUS"],
                self.integrated_regulator.power_in.hv: ["VDD5"],
                self.power_io.hv: ["VIO"],
            },
            accept_prefix=False,
            case_sensitive=False,
        )

    descriptive_properties = L.f_field(F.has_descriptive_properties_defined)(
        {
            DescriptiveProperties.manufacturer: "WCH(Jiangsu Qin Heng)",
            DescriptiveProperties.partno: "CH342F",
        }
    )

    def __preinit__(self) -> None:
        # ----------------------------------------
        #                aliasess
        # ----------------------------------------

        # ----------------------------------------
        #            parametrization
        # ----------------------------------------

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        pass
        # TODO: specialize base uarts from CH342 base class
        # uarts = times(2, F.UART)
        # for uart, uart_base in zip(uarts, self.uart_base):
        #    uart_base.specialize(uart)
        #    self.add(uart)
