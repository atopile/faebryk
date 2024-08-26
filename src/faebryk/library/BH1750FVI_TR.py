# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from dataclasses import dataclass, field

import faebryk.library._F as F
from faebryk.core.module import Module, Parameter
from faebryk.libs.units import P

logger = logging.getLogger(__name__)


class BH1750FVI_TR(Module):
    @dataclass
    class _bh1750_esphome_config(has_esphome_config.impl()):
        update_interval_s: Parameter = field(default_factory=F.TBD)

        def __post_init__(self) -> None:
            super().__init__()

        def get_config(self) -> dict:
            assert isinstance(
                self.update_interval_s, F.Constant
            ), "No update interval set!"

            obj = self.get_obj()
            assert isinstance(obj, BH1750FVI_TR)

            i2c = is_esphome_bus.find_connected_bus(obj.i2c)

            return {
                "sensor": [
                    {
                        "platform": "bh1750",
                        "name": "BH1750 Illuminance",
                        "address": "0x23",
                        "i2c_id": i2c.get_trait(is_esphome_bus).get_bus_id(),
                        "update_interval": f"{self.update_interval_s.value}s",
                    }
                ]
            }

    def set_address(self, addr: int):
        raise NotImplementedError()
        # ADDR = ‘H’ ( ADDR ≧ 0.7VCC ) “1011100“
        # ADDR = 'L' ( ADDR ≦ 0.3VCC ) “0100011“
        ...
        # assert addr < (1 << len(self.e))

        # for i, e in enumerate(self.e):
        #    e.set(addr & (1 << i) != 0)




            dvi_capacitor : F.Capacitor
            dvi_resistor : F.Resistor


            power: F.ElectricPower
            addr: F.ElectricLogic
            dvi: F.ElectricLogic
            ep: F.ElectricLogic
            i2c = F.I2C()



        self.dvi_capacitor.capacitance.merge(1 * P.uF)
        self.dvi_resistor.resistance.merge(1 * P.kohm)

        self.i2c.terminate()

        self.i2c.frequency.merge(
            F.I2C.define_max_frequency_capability(F.I2C.SpeedMode.fast_speed)
        )

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": self.power.hv,
                    "2": self.addr.signal,
                    "3": self.power.lv,
                    "4": self.i2c.sda.signal,
                    "5": self.dvi.signal,
                    "6": self.i2c.scl.signal,
                    "7": self.ep.signal,
                }
            )
        )
    datasheet = L.f_field(F.has_datasheet_defined)("https://datasheet.lcsc.com/lcsc/1811081611_ROHM-Semicon-BH1750FVI-TR_C78960.pdf")

        # set constraints
        self.power.voltage.merge(F.Range(2.4 * P.V, 3.6 * P.V))

        # internal connections
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))
        ref.connect(self.power)

        self.power.decoupled.decouple().capacitance.merge(0.1 * P.uF)
        # TODO: self.dvi.low_pass(self.IF.dvi_capacitor, self.IF.dvi_resistor)

        # self.i2c.add_trait(is_esphome_bus.impl()())
        self.esphome = self._bh1750_esphome_config()
        self.add_trait(self.esphome)
