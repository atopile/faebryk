# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


class has_kicad_footprint_equal_ifs_defined(has_kicad_footprint_equal_ifs):
    def __init__(self, str) -> None:
        super().__init__()
        self.str = str

    def get_kicad_footprint(self):
        return self.str
