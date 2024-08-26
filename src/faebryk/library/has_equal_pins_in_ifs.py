# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F


class has_equal_pins_in_ifs(F.has_equal_pins.impl()):
    def get_pin_map(self):
        return {
            p: str(i + 1)
            for i, p in enumerate(self.get_obj().get_all())
            if isinstance(p, F.Pad)
        }
