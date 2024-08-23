# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


class has_linked_pad_defined(has_linked_pad.impl()):
    def __init__(self, pad: Pad) -> None:
        super().__init__()
        self.pad = pad

    def get_pad(self) -> Pad:
        return self.pad
