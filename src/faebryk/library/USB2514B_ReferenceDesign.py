# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.exporters.pcb.layout.absolute import LayoutAbsolute
from faebryk.exporters.pcb.layout.typehierarchy import LayoutTypeHierarchy
from faebryk.libs.brightness import TypicalLuminousIntensity
from faebryk.libs.library import L
from faebryk.libs.units import P

logger = logging.getLogger(__name__)


class USB2514B_ReferenceDesign(Module):
    """
    Reference implementation of the USB2514B quad port USB hub controller.

    -
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    hub_controller: F.USB2514B
    vbus_voltage_divider: F.ResistorVoltageDivider
    ldo_3v3: F.LDO
    suspend_indicator = L.f_field(F.LEDIndicator)(use_mosfet=False)
    power_3v3_indicator: F.PoweredLED
    power_distribution_switch = L.list_field(4, F.Diodes_Incorporated_AP2552W6_7)
    usb_dfp_power_indicator = L.list_field(4, F.PoweredLED)
    bias_resistor: F.Resistor
    crystal_oscillator: F.Crystal_Oscillator

    usb_ufp: F.USB2_0
    usb_dfp = L.list_field(4, F.USB2_0)

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/BoardDesignFiles/EVB-USB2514BC_A3-sch.pdf"  # noqa: E501
    )

    @L.rt_field
    def has_defined_layout(self):
        Point = F.has_pcb_position.Point
        L = F.has_pcb_position.layer_type
        LVL = LayoutTypeHierarchy.Level

        # TODO:
        layouts = [
            LVL(
                mod_type=F.PoweredLED,
                layout=LayoutAbsolute(
                    Point((2.50, 180, L.NONE)),
                ),
            ),
        ]

        return F.has_pcb_layout_defined(LayoutTypeHierarchy(layouts))

    def __preinit__(self):
        # ----------------------------------------
        #                aliasess
        # ----------------------------------------
        vbus = self.usb_ufp.usb_if.buspower
        gnd = vbus.lv

        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        self.hub_controller.set_non_removable_ports(
            F.USB2514B.NonRemovablePortConfiguration.ALL_PORTS_REMOVABLE
        )
        self.hub_controller.set_configuration_source(
            F.USB2514B.ConfigurationSource.DEFAULT
        )
        for dsf_usb in self.hub_controller.configurable_downstream_usb:
            self.hub_controller.configure_usb_port(
                dsf_usb,
                enable_usb=True,
                enable_battery_charging=True,
            )

        # TODO: load_capacitance is a property of the crystal. remove this
        self.crystal_oscillator.crystal.load_capacitance.merge(
            F.Range(8 * P.pF, 15 * P.pF)
        )
        self.crystal_oscillator.crystal.frequency.merge(
            F.Range.from_center_rel(24 * P.MHz, 0.01)
        )
        self.crystal_oscillator.crystal.frequency_tolerance.merge(
            F.Range.upper_bound(50 * P.ppm)
        )

        # usb transceiver bias resistor
        self.bias_resistor.resistance.merge(F.Range.from_center_rel(12 * P.kohm, 0.01))

        for led in [self.suspend_indicator.led, self.power_3v3_indicator]:
            led.led.color.merge(F.LED.Color.GREEN)
            led.led.brightness.merge(
                TypicalLuminousIntensity.APPLICATION_LED_INDICATOR_INSIDE.value.value
            )

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        # crystal oscillator
        self.crystal_oscillator.xtal_if.connect(self.hub_controller.xtal_if)
        self.crystal_oscillator.gnd.connect(gnd)

        for i, dfp in enumerate(self.usb_dfp):
            vbus.connect_via(self.power_distribution_switch[i], dfp.usb_if.buspower)
            dfp.usb_if.d.connect(self.hub_controller.configurable_downstream_usb[i].usb)
            # TODO: connect hub controller overcurrent and power control signals
            self.power_distribution_switch[i].enable.connect(
                self.hub_controller.configurable_downstream_usb[i].usb_power_enable
            )
            self.power_distribution_switch[i].fault.connect(
                self.hub_controller.configurable_downstream_usb[i].over_current_sense
            )
            dfp.usb_if.buspower.connect(self.usb_dfp_power_indicator[i].power)
            self.usb_dfp_power_indicator[i].led.color.merge(F.LED.Color.YELLOW)
            self.usb_dfp_power_indicator[i].led.brightness.merge(
                TypicalLuminousIntensity.APPLICATION_LED_INDICATOR_INSIDE.value.value
            )
            self.power_distribution_switch[i].set_current_limit(
                F.Range.from_center_rel(520 * P.mA, 0.01)
            )

        # Bias resistor
        self.hub_controller.usb_bias_resistor_input.signal.connect_via(
            self.bias_resistor, gnd
        )  # TODO: replace with pull?

        self.usb_ufp.usb_if.d.connect(self.hub_controller.usb_upstream)

        # LEDs
        self.power_3v3_indicator.power.connect(self.ldo_3v3.power_out)
        self.hub_controller.suspense_indicator.connect(self.suspend_indicator.logic_in)
