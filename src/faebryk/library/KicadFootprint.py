# This file is part of the faebryk project
# SPDX-License-Identifier: MIT





class KicadF.Footprint(Footprint):
    def __init__(self, kicad_identifier: str, pin_names: list[str]) -> None:
        super().__init__()

        unique_pin_names = sorted(set(pin_names))


            pins = L.if_list(len(unique_pin_names), Pad)

        pin_names_sorted = list(enumerate(unique_pin_names))

        self.add_trait(
            can_attach_via_pinmap_pinlist(
                {pin_name: self.pins[i] for i, pin_name in pin_names_sorted}
            )
        )
        self.add_trait(
            has_kicad_manual_footprint(
                kicad_identifier,
                {self.pins[i]: pin_name for i, pin_name in pin_names_sorted},
            )
        )

    @classmethod
    def with_simple_names(cls, kicad_identifier: str, pin_cnt: int):
        return cls(kicad_identifier, [str(i + 1) for i in range(pin_cnt)])
