# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field

from faebryk.core.module import Module, Parameter








from faebryk.libs.units import P


class HLK_LD2410B_P(Module):
    @dataclass
    class _ld2410b_esphome_config(has_esphome_config.impl()):
        throttle_ms: Parameter = field(default_factory=F.TBD)

        def __post_init__(self) -> None:
            super().__init__()

        def get_config(self) -> dict:
            assert isinstance(self.throttle_ms, F.Constant), "No update interval set!"

            obj = self.get_obj()
            assert isinstance(obj, HLK_LD2410B_P), "This is not an HLK_LD2410B_P!"

            uart_candidates = {
                mif
                for mif in obj.uart.get_direct_connections()
                if mif.has_trait(is_esphome_bus) and mif.has_trait(has_esphome_config)
            }

            assert len(uart_candidates) == 1, f"Expected 1 UART, got {uart_candidates}"
            uart = uart_candidates.pop()
            uart_cfg = uart.get_trait(has_esphome_config).get_config()["uart"][0]
            assert (
                uart_cfg["baud_rate"] == 256000
            ), f"Baudrate not 256000 but {uart_cfg['baud_rate']}"

            return {
                "ld2410": {
                    "throttle": f"{self.throttle_ms.value}ms",
                    "uart_id": uart_cfg["id"],
                },
                "binary_sensor": [
                    {
                        "platform": "ld2410",
                        "has_target": {
                            "name": "Presence",
                        },
                        "has_moving_target": {
                            "name": "Moving Target",
                        },
                        "has_still_target": {
                            "name": "Still Target",
                        },
                        "out_pin_presence_status": {
                            "name": "Out pin presence status",
                        },
                    },
                ],
            }



        # interfaces

            power: F.ElectricPower
            uart = F.UART_Base()
            out: F.ElectricLogic

        x = self
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "5": x.power.hv,
                    "4": x.power.lv,
                    "3": x.uart.rx.signal,
                    "2": x.uart.tx.signal,
                    "1": x.out.signal,
                }
            )
        )

        # connect all logic references
        ref = F.ElectricLogic.connect_all_module_references(self, gnd_only=True)
        self.add_trait(has_single_electric_reference_defined(ref))

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")

        self.esphome = self._ld2410b_esphome_config()
        self.add_trait(self.esphome)
    datasheet = L.f_field(F.has_datasheet_defined)("https://datasheet.lcsc.com/lcsc/2209271801_HI-LINK-HLK-LD2410B-P_C5183132.pdf")

        self.uart.baud.merge(F.Constant(256 * P.kbaud))
