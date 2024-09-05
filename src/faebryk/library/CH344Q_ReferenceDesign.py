# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class CH344Q_ReferenceDesign(Module):
    """
    Minimal implementation of the CH344Q quad UART to USB bridge
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    usb: F.USB2_0
    usb_fuse: F.Fuse
    usb_uart_converter: F.CH344Q
    oscillator: F.Crystal_Oscillator
    ldo: F.LDO
    rx_led: F.PoweredLED
    tx_led: F.PoweredLED
    act_led: F.PoweredLED
    power_led: F.PoweredLED
    # reset_lowpass: F.FilterElectricalRC TODO: implement FilterElectricalRC

    # ----------------------------------------
    #                 traits
    # ----------------------------------------

    def __preinit__(self):
        # ------------------------------------
        #             aliases
        # ------------------------------------
        vbus = self.usb.usb_if.buspower
        vbus_fused = F.ElectricPower()
        gnd = vbus.lv
        pwr_3v3 = self.usb_uart_converter.power
        # ------------------------------------
        #           connections
        # ------------------------------------
        vbus.hv.connect_via(self.usb_fuse, vbus_fused.hv)
        gnd.connect(vbus_fused.lv)
        vbus_fused.connect_via(self.ldo, pwr_3v3)
        # TODO: use protect function

        self.usb.connect(self.usb_uart_converter.usb)
        # TODO: add esd protection to usb

        self.power_led.power.connect(pwr_3v3)
        self.usb_uart_converter.act.signal.connect_via(self.act_led, pwr_3v3.hv)
        self.usb_uart_converter.rx_indicator.signal.connect_via(self.rx_led, pwr_3v3.hv)
        self.usb_uart_converter.tx_indicator.signal.connect_via(self.tx_led, pwr_3v3.hv)

        self.usb_uart_converter.osc[1].connect(self.oscillator.p)
        self.usb_uart_converter.osc[0].connect(self.oscillator.n)
        self.oscillator.power.connect(pwr_3v3)

        # self.usb_uart_converter.reset.signal.filter(type=LOWPASS)
        # TODO: implement FilterElectricalRC
        # ------------------------------------
        #          parametrization
        # ------------------------------------
        self.usb_uart_converter.enable_status_outputs()

        self.oscillator.crystal.frequency.merge(8 * P.MHz)
        self.oscillator.crystal.frequency_tolerance.merge(
            F.Range.upper_bound(40 * P.ppm)
        )

        self.ldo.output_current.merge(F.Range.lower_bound(500 * P.mA))
