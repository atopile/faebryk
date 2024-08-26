# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


import faebryk.library._F as F


class has_linked_pad_defined(F.has_linked_pad.impl()):
    def __init__(self, pad: F.Pad) -> None:
        super().__init__()
        self.pad = pad

    def get_pad(self) -> F.Pad:
        return self.pad
