# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from enum import Enum

from faebryk.core.core import Module, ModuleInterface
from faebryk.library.can_attach_to_footprint_symmetrically import (
    can_attach_to_footprint_symmetrically,
)
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Constant import Constant
from faebryk.library.Electrical import Electrical
from faebryk.library.has_defined_footprint import has_defined_footprint
from faebryk.library.has_designator_prefix_defined import (
    has_designator_prefix_defined,
)
from faebryk.library.KicadFootprint import KicadFootprint
from faebryk.libs.picker.picker import has_part_picked_remove
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


class NetTie[T: ModuleInterface](Module):
    class Size(float, Enum):
        _2_0MM = 2.0
        _0_5MM = 0.5

    def __init__(
        self, width: "NetTie.Size" | Constant[float], interface_type: T = Electrical
    ) -> None:
        super().__init__()

        class _IFs(super().IFS()):
            unnamed = times(2, interface_type)

        self.IFs = _IFs(self)
        self.add_trait(can_bridge_defined(*self.IFs.unnamed))

        width_mm = NetTie.Size(width).value

        self.add_trait(can_attach_to_footprint_symmetrically())
        self.add_trait(has_designator_prefix_defined("H"))
        # TODO: "removed" isn't really true, but seems to work
        self.add_trait(has_part_picked_remove())

        # TODO: generate the kicad footprint instead of loading it
        self.add_trait(
            has_defined_footprint(
                KicadFootprint(
                    f"NetTie:NetTie-2_SMD_Pad{width_mm:.1f}mm", pin_names=["1", "2"]
                )
            )
        )
