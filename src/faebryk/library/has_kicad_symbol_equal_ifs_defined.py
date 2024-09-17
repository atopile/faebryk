# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F


class has_kicad_symbol_equal_ifs_defined(F.has_kicad_symbol_equal_ifs):
    def __init__(self, str) -> None:
        super().__init__()
        self.str = str

    def get_kicad_symbol(self):
        return self.str