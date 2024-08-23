# This file is part of the faebryk project
# SPDX-License-Identifier: MIT


from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.util import get_parent_of_type


class Pad(ModuleInterface):



            net: F.Electrical
            pcb = ModuleInterface()

    def attach(self, intf: F.Electrical):
        self.net.connect(intf)
        intf.add_trait(has_linked_pad_defined(self))

    @staticmethod
    def find_pad_for_intf_with_parent_that_has_footprint_unique(
        intf: ModuleInterface,
    ) -> "Pad":
        pads = Pad.find_pad_for_intf_with_parent_that_has_footprint(intf)
        if len(pads) != 1:
            raise ValueError
        return next(iter(pads))

    @staticmethod
    def find_pad_for_intf_with_parent_that_has_footprint(
        intf: ModuleInterface,
    ) -> list["Pad"]:
        # This only finds directly attached pads
        # -> misses from parents / children nodes
        if intf.has_trait(has_linked_pad):
            return [intf.get_trait(has_linked_pad).get_pad()]

        # This is a bit slower, but finds them all
        _, footprint = F.Footprint.get_footprint_of_parent(intf)
        pads = [
            pad
            for pad in footprint.get_all()
            if isinstance(pad, Pad) and pad.net.is_connected_to(intf) is not None
        ]
        return pads

    def get_fp(self) -> F.Footprint:
        fp = get_parent_of_type(self, F.Footprint)
        assert fp
        return fp
