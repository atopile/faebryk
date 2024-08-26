# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


class can_attach_to_footprint_via_pinmap(can_attach_to_footprint.impl()):
    def __init__(self, pinmap: dict[str, F.Electrical]) -> None:
        super().__init__()
        self.pinmap = pinmap

    def attach(self, footprint: F.Footprint):
        self.get_obj().add_trait(F.has_defined_footprint(footprint))
        footprint.get_trait(can_attach_via_pinmap).attach(self.pinmap)
