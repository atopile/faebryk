# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


import faebryk.library._F as F
from faebryk.libs.library import L
from faebryk.libs.units import P, Quantity


class DIP(F.Footprint):
    pins = L.if_list(0, F.Pad)

    def __init__(self, pin_cnt: int, spacing: Quantity, long_pads: bool) -> None:
        super().__init__()

        self.add_to_container(pin_cnt, F.Pad, self.pins)

        self.spacing = spacing
        self.long_pads = long_pads

    @L.rt_field
    def kicad_footprint(self):
        class _has_kicad_footprint(F.has_kicad_footprint_equal_ifs):
            @staticmethod
            def get_kicad_footprint() -> str:
                return "Package_DIP:DIP-{leads}_W{spacing:.2f}mm{longpads}".format(
                    leads=len(self.pins),
                    spacing=self.spacing.to(P.mm).m,
                    longpads="_LongPads" if self.long_pads else "",
                )

        return _has_kicad_footprint

    equal_pins_in_ifs: F.has_equal_pins_in_ifs
    attach_via_pinmap: F.can_attach_via_pinmap_equal
