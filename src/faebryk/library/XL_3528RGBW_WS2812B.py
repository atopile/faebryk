# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.parameter import Parameter
from faebryk.libs.library import L


class XL_3528RGBW_WS2812B(Module):
    @dataclass
    class _ws2812b_esphome_config(F.has_esphome_config.impl()):
        update_interval_s: Parameter = field(default_factory=F.TBD)

        def __post_init__(self) -> None:
            super().__init__()

        def get_config(self) -> dict:
            assert isinstance(
                self.update_interval_s, F.Constant
            ), "No update interval set!"

            obj = self.obj
            assert isinstance(obj, XL_3528RGBW_WS2812B), "This is not a WS2812B RGBW!"

            data_pin = F.is_esphome_bus.find_connected_bus(obj.di.signal)

            return {
                "light": [
                    {
                        "platform": "esp32_rmt_led_strip",
                        "update_interval": f"{self.update_interval_s.value}s",
                        "num_leds": 1,  # TODO: make dynamic
                        "rmt_channel": 0,  # TODO: make dynamic
                        "chipset": "WS2812",
                        "rgb_order": "RGB",
                        "is_rgbw": "true",
                        "pin": data_pin.get_trait(F.is_esphome_bus).get_bus_id(),
                    }
                ]
            }

    # interfaces

    power: F.ElectricPower
    do: F.ElectricLogic
    di: F.ElectricLogic

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("LED")

    # Add bridge trait
    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.di, self.do)

    @L.rt_field
    def attach_to_footprint(self):
        return F.can_attach_to_footprint_via_pinmap(
            {
                "1": self.power.lv,
                "2": self.di.signal,
                "3": self.power.hv,
                "4": self.do.signal,
            }
        )

    datasheet = L.f_field(F.has_datasheet_defined)(
        "https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2402181504_XINGLIGHT-XL-3528RGBW-WS2812B_C2890364.pdf"
    )

    esphome_config: _ws2812b_esphome_config
