# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F


class has_equal_pins_in_ifs(F.has_equal_pins.impl()):
    def get_pin_map(self):
        from faebryk.core.util import get_children

        return {
            p: str(i + 1)
            for i, p in enumerate(get_children(self.obj, direct_only=True, types=F.Pad))
        }
