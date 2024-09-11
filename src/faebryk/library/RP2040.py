# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.libs.library import L
from faebryk.libs.units import P

logger = logging.getLogger(__name__)


class RP2040(Module):
    class PIO(F.ElectricLogic):
        pass

    class ADC(F.SignalElectrical):
        pass

    class PWM(ModuleInterface):
        A: F.ElectricLogic
        B: F.ElectricLogic

    class CoreRegulator(Module):
        power_in: F.ElectricPower
        power_out: F.ElectricPower

        def __preinit__(self):
            F.ElectricLogic.connect_all_module_references(self, gnd_only=True)

            # TODO get tolerance
            self.power_out.voltage.merge(F.Range.from_center_rel(1.1 * P.V, 0.05))
            self.power_in.voltage.merge(F.Range(1.8 * P.V, 3.3 * P.V))

    class Pinmux(Module):
        def __init__(self, mcu: "RP2040"):
            self._mcu = mcu

        def __preinit__(self):
            # TODO
            x = self._mcu
            matrix = {
                x.gpio[0]: [
                    x.spi[0].miso,
                    x.uart[0].tx,
                    x.i2c[0].sda,
                    x.pwm[0].A,
                    x.gpio_digital[0],  # TODO is this correct?
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB OVCUR DET",  # TODO
                ],
                x.gpio[1]: [
                    x.spi[0].csn,
                    x.uart[0].rx,
                    x.i2c[0].scl,
                    x.pwm[0].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS DET",
                ],
                x.gpio[2]: [
                    x.spi[0].sclk,
                    x.uart[0].cts,
                    x.i2c[1].sda,
                    x.pwm[1].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS EN",
                ],
                x.gpio[3]: [
                    x.spi[0].mosi,
                    x.uart[0].rts,
                    x.i2c[1].scl,
                    x.pwm[1].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB OVCUR DET",
                ],
                x.gpio[4]: [
                    x.spi[0].miso,
                    x.uart[1].tx,
                    x.i2c[0].sda,
                    x.pwm[2].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS DET",
                ],
                x.gpio[5]: [
                    x.spi[0].csn,
                    x.uart[1].rx,
                    x.i2c[0].scl,
                    x.pwm[2].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS EN",
                ],
                x.gpio[6]: [
                    x.spi[0].sclk,
                    x.uart[1].cts,
                    x.i2c[1].sda,
                    x.pwm[3].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB OVCUR DET",
                ],
                x.gpio[7]: [
                    x.spi[0].mosi,
                    x.uart[1].rts,
                    x.i2c[1].scl,
                    x.pwm[3].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS DET",
                ],
                x.gpio[8]: [
                    x.spi[1].miso,
                    x.uart[0].tx,
                    x.i2c[0].sda,
                    x.pwm[4].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS EN",
                ],
                x.gpio[9]: [
                    x.spi[1].csn,
                    x.uart[0].rx,
                    x.i2c[0].scl,
                    x.pwm[4].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB OVCUR DET",
                ],
                x.gpio[10]: [
                    x.spi[1].sclk,
                    x.uart[0].cts,
                    x.i2c[1].sda,
                    x.pwm[5].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS DET",
                ],
                x.gpio[11]: [
                    x.spi[1].mosi,
                    x.uart[0].rts,
                    x.i2c[1].scl,
                    x.pwm[5].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS EN",
                ],
                x.gpio[12]: [
                    x.spi[1].miso,
                    x.uart[1].tx,
                    x.i2c[0].sda,
                    x.pwm[6].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB OVCUR DET",
                ],
                x.gpio[13]: [
                    x.spi[1].csn,
                    x.uart[1].rx,
                    x.i2c[0].scl,
                    x.pwm[6].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS DET",
                ],
                x.gpio[14]: [
                    x.spi[1].sclk,
                    x.uart[1].cts,
                    x.i2c[1].sda,
                    x.pwm[7].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS EN",
                ],
                x.gpio[15]: [
                    x.spi[1].mosi,
                    x.uart[1].rts,
                    x.i2c[1].scl,
                    x.pwm[7].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB OVCUR DET",
                ],
                x.gpio[16]: [
                    x.spi[0].miso,
                    x.uart[0].tx,
                    x.i2c[0].sda,
                    x.pwm[0].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS DET",
                ],
                x.gpio[17]: [
                    x.spi[0].csn,
                    x.uart[0].rx,
                    x.i2c[0].scl,
                    x.pwm[0].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS EN",
                ],
                x.gpio[18]: [
                    x.spi[0].sclk,
                    x.uart[0].cts,
                    x.i2c[1].sda,
                    x.pwm[1].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB OVCUR DET",
                ],
                x.gpio[19]: [
                    x.spi[0].mosi,
                    x.uart[0].rts,
                    x.i2c[1].scl,
                    x.pwm[1].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS DET",
                ],
                x.gpio[20]: [
                    x.spi[0].miso,
                    x.uart[1].tx,
                    x.i2c[0].sda,
                    x.pwm[2].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS EN",
                ],
                x.gpio[21]: [
                    x.spi[0].csn,
                    x.uart[1].rx,
                    x.i2c[0].scl,
                    x.pwm[2].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    x.clock.gpout0,
                    "USB OVCUR DET",
                ],
                x.gpio[22]: [
                    x.spi[0].sclk,
                    x.uart[1].cts,
                    x.i2c[1].sda,
                    x.pwm[3].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    x.clock.gpin1,
                    "USB VBUS DET",
                ],
                x.gpio[23]: [
                    x.spi[0].mosi,
                    x.uart[1].rts,
                    x.i2c[1].scl,
                    x.pwm[3].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    x.clock.gpout1,
                    "USB VBUS EN",
                ],
                x.gpio[24]: [
                    x.spi[1].miso,
                    x.uart[0].tx,
                    x.i2c[0].sda,
                    x.pwm[4].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    x.clock.gpout2,
                    "USB OVCUR DET",
                ],
                x.gpio[25]: [
                    x.spi[1].csn,
                    x.uart[0].rx,
                    x.i2c[0].scl,
                    x.pwm[4].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    x.clock.gpout3,
                    "USB VBUS DET",
                ],
                x.gpio[26]: [
                    x.spi[1].sclk,
                    x.uart[0].cts,
                    x.i2c[1].sda,
                    x.pwm[5].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS EN",
                ],
                x.gpio[27]: [
                    x.spi[1].mosi,
                    x.uart[0].rts,
                    x.i2c[1].scl,
                    x.pwm[5].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB OVCUR DET",
                ],
                x.gpio[28]: [
                    x.spi[1].miso,
                    x.uart[1].tx,
                    x.i2c[0].sda,
                    x.pwm[6].A,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS DET",
                ],
                x.gpio[29]: [
                    x.spi[1].csn,
                    x.uart[1].rx,
                    x.i2c[0].scl,
                    x.pwm[6].B,
                    x.gpio_digital[0],
                    x.pio[0],
                    x.pio[1],
                    None,
                    "USB VBUS EN",
                ],
            }

    # power
    power_io: F.ElectricPower
    power_adc: F.ElectricPower
    power_core: F.ElectricPower
    power_usb: F.ElectricPower
    core_regulator: CoreRegulator

    gpio = L.list_field(30, F.Electrical)
    gpio_soft = L.list_field(6, F.Electrical)

    # IO
    qspi = L.f_field(F.MultiSPI)(data_lane_count=4)
    swd: F.SWD
    xtal_if: F.XtalIF

    run: F.ElectricLogic
    usb: F.USB2_0
    factory_test_enable: F.Electrical

    # peripherals
    spi = L.list_field(2, F.SPI)
    pwm = L.list_field(8, F.PWM)
    i2c = L.list_field(2, F.I2C)
    uart = L.list_field(2, F.UART_Base)
    pio = L.list_field(2, PIO)
    adc = L.list_field(4, ADC)
    gpio_digital = L.list_field(30 + 6, F.Electrical)

    def __preinit__(self):
        # TODO get tolerance
        self.power_adc.voltage.merge(F.Range.from_center_rel(3.3 * P.V, 0.05))
        self.power_usb.voltage.merge(F.Range.from_center_rel(3.3 * P.V, 0.05))
        self.power_core.voltage.merge(F.Range.from_center_rel(1.1 * P.V, 0.05))
        self.power_io.voltage.merge(F.Range(1.8 * P.V, 3.3 * P.V))

        F.ElectricLogic.connect_all_module_references(self, gnd_only=True)

        # QSPI pins reusable for soft gpio
        self.qspi.data[3].signal.connect(self.gpio_soft[0])
        self.qspi.clk.signal.connect(self.gpio_soft[1])
        self.qspi.data[0].signal.connect(self.gpio_soft[2])
        self.qspi.data[2].signal.connect(self.gpio_soft[3])
        self.qspi.data[1].signal.connect(self.gpio_soft[4])
        self.qspi.cs.signal.connect(self.gpio_soft[5])

        # ADC pins shared with GPIO
        self.adc[0].signal.connect(self.gpio[26])
        self.adc[1].signal.connect(self.gpio[27])
        self.adc[2].signal.connect(self.gpio[28])
        self.adc[3].signal.connect(self.gpio[29])

        F.ElectricLogic.connect_all_node_references([self.power_adc] + self.adc)

    @L.rt_field
    def pinmux(self):
        return self.Pinmux(self)

    @L.rt_field
    def decoupled(self):
        return F.can_be_decoupled_rails(self.power_io, self.power_core)

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf"
    )

    @L.rt_field
    def attach_to_footprint(self):
        return F.can_attach_to_footprint_via_pinmap(
            {
                "1": self.power_io.hv,
                "2": self.gpio[0],
                "3": self.gpio[1],
                "4": self.gpio[2],
                "5": self.gpio[3],
                "6": self.gpio[4],
                "7": self.gpio[5],
                "8": self.gpio[6],
                "9": self.gpio[7],
                "10": self.power_io.hv,
                "11": self.gpio[8],
                "12": self.gpio[9],
                "13": self.gpio[10],
                "14": self.gpio[11],
                "15": self.gpio[12],
                "16": self.gpio[13],
                "17": self.gpio[14],
                "18": self.gpio[15],
                "19": self.xtal_if.xin,
                "20": self.xtal_if.xout,
                "21": self.factory_test_enable,
                "22": self.power_io.hv,
                "23": self.power_core.hv,
                "24": self.swd.clk.signal,
                "25": self.swd.dio.signal,
                "26": self.run.signal,
                "27": self.gpio[16],
                "28": self.gpio[17],
                "29": self.gpio[18],
                "30": self.gpio[19],
                "31": self.gpio[20],
                "32": self.gpio[21],
                "33": self.power_io.hv,
                "34": self.gpio[22],
                "35": self.gpio[23],
                "36": self.gpio[24],
                "37": self.gpio[25],
                "38": self.gpio[26],
                "39": self.gpio[27],
                "40": self.gpio[28],
                "41": self.gpio[29],
                "42": self.power_io.hv,
                "43": self.power_adc.hv,
                "44": self.core_regulator.power_in.hv,
                "45": self.core_regulator.power_out.hv,
                "46": self.usb.usb_if.d.n,
                "47": self.usb.usb_if.d.p,
                "48": self.usb.usb_if.buspower.hv,
                "49": self.power_io.hv,
                "50": self.power_core.hv,
                "51": self.qspi.data[3].signal,
                "52": self.qspi.clk.signal,
                "53": self.qspi.data[0].signal,
                "54": self.qspi.data[2].signal,
                "55": self.qspi.data[1].signal,
                "56": self.qspi.cs.signal,
                "57": self.power_io.lv,
            }
        )
