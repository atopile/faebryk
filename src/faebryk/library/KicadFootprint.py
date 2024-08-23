# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.library.can_attach_via_pinmap_pinlist import can_attach_via_pinmap_pinlist
from faebryk.library.Footprint import Footprint
from faebryk.library.has_kicad_manual_footprint import has_kicad_manual_footprint
from faebryk.library.Pad import Pad
from faebryk.libs.util import times


class KicadFootprint(Footprint):
    def __init__(self, kicad_identifier: str, pin_names: list[str]) -> None:
        super().__init__()

        unique_pin_names = sorted(set(pin_names))

        class _IFS(Footprint.IFS()):
            pins = L.if_list(len(unique_pin_names), Pad)

        pin_names_sorted = list(enumerate(unique_pin_names))

        self.IFs = _IFS(self)
        self.add_trait(
            can_attach_via_pinmap_pinlist(
                {pin_name: self.IFs.pins[i] for i, pin_name in pin_names_sorted}
            )
        )
        self.add_trait(
            has_kicad_manual_footprint(
                kicad_identifier,
                {self.IFs.pins[i]: pin_name for i, pin_name in pin_names_sorted},
            )
        )

    @classmethod
    def with_simple_names(cls, kicad_identifier: str, pin_cnt: int):
        return cls(kicad_identifier, [str(i + 1) for i in range(pin_cnt)])
