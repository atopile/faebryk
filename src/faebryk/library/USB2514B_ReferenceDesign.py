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
    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    hub_controller: F.USB2514B
    vbus_voltage_divider: F.ResistorVoltageDivider
    ldo_3v3: F.LDO
    suspend_indicator: F.PoweredLED
    power_3v3_indicator: F.PoweredLED
    power_distribution_switch = L.list_field(4, F.Diodes_Incorporated_AP2552W6_7)
    usb_dfp_power_indicator = L.list_field(4, F.PoweredLED)
    bias_resistor: F.Resistor
    crystal_oscillator: F.Crystal_Oscillator  # TODO: Connect Crystal oscillator

    usb_ufp: F.USB2_0
    usb_dfp = L.list_field(4, F.USB2_0)

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    @L.rt_field
    def has_defined_layout(self):
        Point = F.has_pcb_position.Point
        L = F.has_pcb_position.layer_type
        LVL = LayoutTypeHierarchy.Level

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
        # crystal oscillator
        self.hub_controller.XTALOUT.connect_via(
            self.crystal_oscillator, self.hub_controller.XTALIN
        )
        # TODO: this is a property of the crystal. remove this
        self.crystal_oscillator.crystal.load_capacitance.merge(
            F.Range(8 * P.pF, 15 * P.pF)
        )
        self.crystal_oscillator.crystal.frequency.merge(
            F.Range.from_center_rel(24 * P.MHz, 0.01)
        )
        self.crystal_oscillator.crystal.frequency_tolerance.merge(
            F.Range.upper_bound(50 * P.ppm)
        )

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        for i, dfp in enumerate(self.usb_dfp):
            vbus.connect_via(self.power_distribution_switch[i], dfp.usb_if.buspower)
            dfp.usb_if.d.connect(self.hub_controller.usb_downstream[i])
            # TODO: connect hub controller overcurrent and power control signals
            self.power_distribution_switch[i].enable.connect(
                self.hub_controller.PRTPWR[i]
            )
            self.power_distribution_switch[i].fault.connect(
                self.hub_controller.OCS_N[i]
            )
            self.power_distribution_switch[i].power_out.hv.connect_via(
                self.usb_dfp_power_indicator[i], gnd
            )
            self.usb_dfp_power_indicator[i].led.color.merge(F.LED.Color.YELLOW)
            self.usb_dfp_power_indicator[i].led.brightness.merge(
                # F.Range(
                #    10 * P.millicandela, 100 * P.millicandela
                # )  #
                TypicalLuminousIntensity.APPLICATION_LED_INDICATOR_INSIDE.value.value
            )
            for pds in self.power_distribution_switch:
                pds.set_current_limit(F.Range.from_center_rel(520 * P.mA, 0.01))

        # Bias resistor
        self.bias_resistor.resistance.merge(F.Range.from_center_rel(12 * P.kohm, 0.01))
        self.hub_controller.RBIAS.connect_via(self.bias_resistor, gnd)

        self.usb_ufp.usb_if.d.connect(self.hub_controller.usb_upstream)

        # LEDs
        self.power_3v3_indicator.power.connect(self.ldo_3v3.power_out)
        self.hub_controller.SUSP_IND.signal.connect_via(self.suspend_indicator, gnd)
        # TODO: remove, should be fixed by using LEDIndicator
        self.suspend_indicator.power.voltage.merge(self.ldo_3v3.power_out.voltage)

        # TODO: do elsewhere
        for led in [self.suspend_indicator, self.power_3v3_indicator]:
            led.led.color.merge(F.LED.Color.GREEN)
            led.led.brightness.merge(
                TypicalLuminousIntensity.APPLICATION_LED_INDICATOR_INSIDE.value.value
            )
