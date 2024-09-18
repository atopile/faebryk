# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F


class has_kicad_footprint_equal_ifs_defined(F.has_kicad_footprint.impl()):
    def __init__(self, str) -> None:
        super().__init__()
        self.str = str

    def get_pin_names(self):
        return self.obj.get_trait(F.has_equal_pins).get_pin_map()


    def get_kicad_footprint(self):
        return self.str
