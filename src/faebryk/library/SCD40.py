# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.parameter import Parameter
from faebryk.libs.library import L
from faebryk.libs.units import P


class SCD40(Module):
    """
    Sensirion SCD4x NIR CO2 sensor
    """

    @dataclass
    class _scd4x_esphome_config(F.has_esphome_config.impl()):
        update_interval_s: Parameter = field(default_factory=F.TBD)

        def get_config(self) -> dict:
            assert isinstance(
                self.update_interval_s, F.Constant
            ), "No update interval set!"

            obj = self.get_obj()
            assert isinstance(obj, SCD40)

            i2c = F.is_esphome_bus.find_connected_bus(obj.i2c)

            return {
                "sensor": [
                    {
                        "platform": "scd4x",
                        "co2": {
                            "name": "CO2",
                        },
                        "temperature": {
                            "name": "Moving Temperature",
                        },
                        "humidity": {
                            "name": "Humidity",
                        },
                        "address": 0x62,
                        "i2c_id": i2c.get_trait(F.is_esphome_bus).get_bus_id(),
                        "update_interval": f"{self.update_interval_s.value}s",
                    }
                ]
            }

    esphome_config: _scd4x_esphome_config

    # interfaces
    power: F.ElectricPower
    i2c: F.I2C

    @L.rt_field
    def attach_to_footprint(self):
        return F.can_attach_to_footprint_via_pinmap(
            {
                "6": self.power.lv,
                "20": self.power.lv,
                "21": self.power.lv,
                "7": self.power.hv,
                "19": self.power.hv,
                "9": self.i2c.scl.signal,
                "10": self.i2c.sda.signal,
            }
        )

    def __preinit__(self):
        self.power.voltage.merge(F.Constant(3.3 * P.V))
        self.i2c.terminate()
        self.power.decoupled.decouple()
        self.i2c.frequency.merge(
            F.I2C.define_max_frequency_capability(F.I2C.SpeedMode.fast_speed)
        )

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://sensirion.com/media/documents/48C4B7FB/64C134E7/Sensirion_SCD4x_Datasheet.pdf"
    )
