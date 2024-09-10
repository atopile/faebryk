# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.library.Electrical import Electrical
from faebryk.library.KicadFootprint import KicadFootprint
from faebryk.libs.picker.picker import has_part_picked_remove

logger = logging.getLogger(__name__)


class NetTie[T: ModuleInterface](Module):
    class Size(float, Enum):
        _2_0MM = 2.0
        _0_5MM = 0.5

    unnamed: list[T]

    def __init__(
        self,
        width: Size,
        interface_type: type[T] = Electrical,
    ) -> None:
        super().__init__()

        # dynamically construct the interfaces
        self.unnamed = self.add([interface_type(), interface_type()], "unnamed")

        # add dem trairs
        self.add(F.can_bridge_defined(*self.unnamed))

        width_mm = NetTie.Size(width).value

        self.add(F.can_attach_to_footprint_symmetrically())
        self.add(F.has_designator_prefix_defined("H"))
        # TODO: "removed" isn't really true, but seems to work
        self.add(has_part_picked_remove())

        # TODO: generate the kicad footprint instead of loading it
        self.add(
            F.has_footprint_defined(
                KicadFootprint(
                    f"NetTie:NetTie-2_SMD_Pad{width_mm:.1f}mm", pin_names=["1", "2"]
                )
            )
        )
