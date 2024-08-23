# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


class has_kicad_manual_footprint(has_kicad_footprint.impl()):
    def __init__(self, str, pinmap: dict[Pad, str]) -> None:
        super().__init__()
        self.str = str
        self.pinmap = pinmap

    def get_kicad_footprint(self):
        return self.str

    def get_pin_names(self):
        return self.pinmap
