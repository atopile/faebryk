# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


class can_attach_via_pinmap_pinlist(can_attach_via_pinmap.impl()):
    def __init__(self, pin_list: dict[str, Pad]) -> None:
        super().__init__()
        self.pin_list = pin_list

    def attach(self, pinmap: dict[str, F.Electrical]):
        for no, intf in pinmap.items():
            assert (
                no in self.pin_list
            ), f"Pin {no} not in pin list: {self.pin_list.keys()}"
            self.pin_list[no].attach(intf)
