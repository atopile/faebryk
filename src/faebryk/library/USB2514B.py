# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum, auto

import faebryk.library._F as F
from faebryk.core.module import Module, ModuleException
from faebryk.libs.library import L
from faebryk.libs.picker.picker import DescriptiveProperties
from faebryk.libs.units import P

# from faebryk.libs.util import assert_once

logger = logging.getLogger(__name__)


class USB2514B(Module):
    class ConfigurableUSB(Module):
        """
        USB port wrapper with configuration pins and power enable pin.
        """

        usb: F.USB2_0_IF.Data
        usb_power_enable: F.ElectricLogic
        usb_port_disable_p: F.ElectricLogic
        usb_port_disable_n: F.ElectricLogic
        over_current_sense: F.ElectricLogic
        battery_charging_enable: F.ElectricLogic

    class ConfigurationSource(Enum):
        DEFAULT = auto()
        """
        - Strap options enabled
        - Self-powered operation enabled
        - Individual power switching
        - Individual over-current sensing
        """
        BUS_POWERED = auto()
        """
        Default configuration with the following overrides:
        - Bus-powered operation
        """
        SMBUS = auto()
        """"
        The hub is configured externally over SMBus (as an SMBus slave device):
        - Strap options disabled
        - All registers configured over SMBus
        """
        EEPROM = auto()
        """
        The hub is configured over 2-wire I2C EEPROM:
        - Strap options disabled
        - All registers configured by I2C EEPROM
        """

    # @assert_once
    def set_configuration_source(
        self,
        configuration_source: ConfigurationSource = ConfigurationSource.DEFAULT,
    ):
        """
        Set the source of configuration settings for the USB2514B.
        """
        if configuration_source == USB2514B.ConfigurationSource.DEFAULT:
            self.configuration_source_input[0].pulled.pull(up=False)
            self.configuration_source_input[1].pulled.pull(up=False)
        elif configuration_source == USB2514B.ConfigurationSource.BUS_POWERED:
            self.configuration_source_input[0].pulled.pull(up=False)
            self.configuration_source_input[1].pulled.pull(up=True)
        elif configuration_source == USB2514B.ConfigurationSource.SMBUS:
            self.configuration_source_input[0].pulled.pull(up=True)
            self.configuration_source_input[1].pulled.pull(up=False)
        elif configuration_source == USB2514B.ConfigurationSource.EEPROM:
            self.configuration_source_input[0].pulled.pull(up=True)
            self.configuration_source_input[1].pulled.pull(up=True)

    class NonRemovablePortConfiguration(Enum):
        ALL_PORTS_REMOVABLE = auto()
        PORT_0_NOT_REMOVABLE = auto()
        PORT_0_1_NOT_REMOVABLE = auto()
        PORT_0_1_2_NOT_REMOVABLE = auto()

    # @assert_once
    def set_non_removable_ports(
        self,
        non_removable_port_configuration: NonRemovablePortConfiguration,
    ):
        """
        Set the non-removable port configuration of the USB2514.
        """
        if (
            non_removable_port_configuration
            == USB2514B.NonRemovablePortConfiguration.ALL_PORTS_REMOVABLE
        ):
            self.usb_removability_configuration_intput[0].set_weak(on=False)
            self.usb_removability_configuration_intput[1].set_weak(on=False)
        elif (
            non_removable_port_configuration
            == USB2514B.NonRemovablePortConfiguration.PORT_0_NOT_REMOVABLE
        ):
            self.usb_removability_configuration_intput[0].set_weak(on=True)
            self.usb_removability_configuration_intput[1].set_weak(on=False)
        elif (
            non_removable_port_configuration
            == USB2514B.NonRemovablePortConfiguration.PORT_0_1_NOT_REMOVABLE
        ):
            self.usb_removability_configuration_intput[0].set_weak(on=False)
            self.usb_removability_configuration_intput[1].set_weak(on=True)
        elif (
            non_removable_port_configuration
            == USB2514B.NonRemovablePortConfiguration.PORT_0_1_2_NOT_REMOVABLE
        ):
            self.usb_removability_configuration_intput[0].set_weak(on=True)
            self.usb_removability_configuration_intput[1].set_weak(on=True)

    # @assert_once  # TODO: this function can be called 1ce per port
    def configure_usb_port(
        self,
        usb_port: ConfigurableUSB,
        enable_usb: bool = True,
        enable_battery_charging: bool = True,
    ):
        """
        Configure the specified USB port.
        """
        if usb_port not in self.configurable_downstream_usb:
            raise ModuleException(
                self, f"{usb_port.get_full_name()} is not part of this module"
            )

        # enable/disable usb port
        if not enable_usb:
            usb_port.usb_port_disable_p.set_weak(on=True)
            usb_port.usb_port_disable_n.set_weak(on=True)

        # enable/disable battery charging
        if not enable_battery_charging:
            usb_port.battery_charging_enable.set_weak(on=False)

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    power_3v3: F.ElectricPower
    power_3v3_analog: F.ElectricPower
    power_pll: F.ElectricPower
    power_core: F.ElectricPower

    usb_upstream: F.USB2_0_IF.Data

    xtal_if: F.XtalIF
    external_clock_input: F.ElectricLogic

    usb_bias_resistor_input: F.SignalElectrical
    vbus_detect: F.SignalElectrical

    test: F.Electrical
    reset: F.ElectricLogic
    local_power_detection: F.SignalElectrical

    usb_removability_configuration_intput = L.list_field(2, F.ElectricLogic)
    configuration_source_input = L.list_field(2, F.ElectricLogic)

    suspense_indicator: F.ElectricLogic
    high_speed_upstream_indicator: F.ElectricLogic

    configurable_downstream_usb = L.list_field(4, ConfigurableUSB)

    i2c: F.I2C

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    designator_prefix = L.f_field(F.has_designator_prefix_defined)(
        F.has_designator_prefix.Prefix.U
    )
    descriptive_properties = L.f_field(F.has_descriptive_properties_defined)(
        {
            DescriptiveProperties.manufacturer: "Microchip Tech",
            DescriptiveProperties.partno: "USB2514B-AEZC-TR",
        }
    )
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://ww1.microchip.com/downloads/aemDocuments/documents/UNG/ProductDocuments/DataSheets/USB251xB-xBi-Data-Sheet-DS00001692.pdf"
    )

    @L.rt_field
    def pin_association_heuristic(self):
        return F.has_pin_association_heuristic_lookup_table(
            mapping={
                self.power_core.hv: ["CRFILT"],
                self.power_core.lv: ["EP"],
                self.configuration_source_input[1].signal: ["HS_IND/CFG_SEL1"],
                self.configurable_downstream_usb[0].over_current_sense.signal: [
                    "OCS_N1"
                ],
                self.configurable_downstream_usb[1].over_current_sense.signal: [
                    "OCS_N2"
                ],
                self.configurable_downstream_usb[2].over_current_sense.signal: [
                    "OCS_N3"
                ],
                self.configurable_downstream_usb[3].over_current_sense.signal: [
                    "OCS_N4"
                ],
                self.power_pll.hv: ["PLLFILT"],
                self.configurable_downstream_usb[0].battery_charging_enable.signal: [
                    "PRTPWR1/BC_EN1"
                ],
                self.configurable_downstream_usb[1].battery_charging_enable.signal: [
                    "PRTPWR2/BC_EN2"
                ],
                self.configurable_downstream_usb[2].battery_charging_enable.signal: [
                    "PRTPWR3/BC_EN3"
                ],
                self.configurable_downstream_usb[3].battery_charging_enable.signal: [
                    "PRTPWR4/BC_EN4"
                ],
                self.usb_bias_resistor_input.signal: ["RBIAS"],
                self.reset.signal: ["RESET_N"],
                self.configuration_source_input[0].signal: ["SCL/SMBCLK/CFG_SEL0"],
                self.usb_removability_configuration_intput[1].signal: [
                    "SDA/SMBDATA/NON_REM1"
                ],
                self.usb_removability_configuration_intput[0].signal: [
                    "SUSP_IND/LOCAL_PWR/NON_REM0"
                ],
                self.test: ["TEST"],
                self.configurable_downstream_usb[0].usb.n: ["USBDM_DN1/PRT_DIS_M1"],
                self.configurable_downstream_usb[1].usb.n: ["USBDM_DN2/PRT_DIS_M2"],
                self.configurable_downstream_usb[2].usb.n: ["USBDM_DN3/PRT_DOS_M3"],
                self.configurable_downstream_usb[3].usb.n: ["USBDM_DN4/PRT_DIS_M4"],
                self.usb_upstream.p: ["USBDM_UP"],
                self.configurable_downstream_usb[0].usb.n: ["USBDP_DN1/PRT_DIS_P1"],
                self.configurable_downstream_usb[1].usb.n: ["USBDP_DN2/PRT_DIS_P2"],
                self.configurable_downstream_usb[2].usb.n: ["USBDP_DN3/PRT_DIS_P3"],
                self.configurable_downstream_usb[3].usb.n: ["USBDP_DN4/PRT_DIS_P4"],
                self.usb_upstream.p: ["USBDP_UP"],
                self.vbus_detect.signal: ["VBUS_DET"],
                self.power_3v3.hv: ["VDD33"],
                self.power_3v3_analog.hv: ["VDDA33"],
                self.xtal_if.xin: ["XTALIN/CLKIN"],
                self.xtal_if.xout: ["XTALOUT"],
            },
            accept_prefix=False,
            case_sensitive=False,
        )

    def __preinit__(self):
        # ----------------------------------------
        #              connections
        # ----------------------------------------
        self.configuration_source_input[0].connect(self.i2c.scl)
        self.configuration_source_input[1].connect(self.high_speed_upstream_indicator)
        self.usb_removability_configuration_intput[0].signal.connect(
            self.suspense_indicator.signal,
            self.local_power_detection.signal,
        )
        self.usb_removability_configuration_intput[1].connect(self.i2c.sda)
        for usb_port in self.configurable_downstream_usb:
            usb_port.usb.p.connect(usb_port.usb_port_disable_p.signal)
            usb_port.usb.n.connect(usb_port.usb_port_disable_n.signal)
            usb_port.usb_power_enable.connect(usb_port.battery_charging_enable)
        self.test.connect(self.power_core.lv)

        F.ElectricLogic.connect_all_module_references(self, gnd_only=True)
        F.ElectricLogic.connect_all_module_references(
            self,
            exclude={
                self.power_3v3_analog,
                self.power_pll,
                self.power_core,
            },
        )

        # ----------------------------------------
        #              parametrization
        # ----------------------------------------
        self.power_pll.voltage.merge(
            F.Range.from_center_rel(1.8 * P.V, 0.05)
        )  # datasheet does not specify a voltage range
        self.power_core.voltage.merge(
            F.Range.from_center_rel(1.8 * P.V, 0.05)
        )  # datasheet does not specify a voltage range
        self.power_3v3.voltage.merge(F.Range.from_center(3.3 * P.V, 0.3 * P.V))
        self.power_3v3_analog.voltage.merge(F.Range.from_center(3.3 * P.V, 0.3 * P.V))
