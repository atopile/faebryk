# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from functools import cache
from typing import Generic, TypeGuard, TypeVar

from faebryk.core.module import Module, ModuleInterface





T = TypeVar("T", bound=ModuleInterface)


class _TSwitch(Generic[T], Module):
    def __init__(self, t: type[T]):
        super().__init__()
        self.t = t

    @staticmethod
    def is_instance(obj: Module, t: type[T]) -> bool:
        return isinstance(obj, _TSwitch) and issubclass(obj.t, t)


@cache  # This means we can use a normal "isinstance" to test for them
def Switch(interface_type: type[T]):
    class _Switch(_TSwitch[interface_type]):
        def __init__(self) -> None:
            super().__init__(interface_type)

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("SW")
            self.add_trait(can_attach_to_footprint_symmetrically())


                unnamed = L.if_list(2, interface_type)

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(*self.unnamed)

        @staticmethod
        def is_instance(obj: Module) -> "TypeGuard[_Switch]":
            return _TSwitch.is_instance(obj, interface_type)

    return _Switch
