# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from enum import IntEnum

import faebryk.library._F as F
from faebryk.libs.library import L


class Logic(F.Signal):
    class ActiveState(IntEnum):
        ACTIVE_HIGH = True
        ACTIVE_LOW = False

    state = L.f_field(F.Range)(False, True)
    active_state = L.f_field(F.Range)(ActiveState.ACTIVE_HIGH, ActiveState.ACTIVE_LOW)

    def set(self, on: bool):
        self.state.merge(on)
