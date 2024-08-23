# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from typing import Callable, Generic, TypeVar

from faebryk.core.core import (
    Module,
    ModuleInterface,
)




T = TypeVar("T", bound=ModuleInterface)


class GenericBusProtection(Generic[T], Module):
    def __init__(self, bus_factory: Callable[[], T]) -> None:
        super().__init__()


            bus_unprotected = bus_factory()
            bus_protected = bus_factory()

        U = TypeVar("U", bound=ModuleInterface)

        def get_mifs(bus: T, mif_type: type[U]) -> list[U]:
            return [i for i in bus.get_all() if isinstance(i, mif_type)]

        raw = list(
            zip(
                get_mifs(self.bus_unprotected, F.Electrical),
                get_mifs(self.bus_protected, F.Electrical),
            )
        )
        signals = list(
            zip(
                get_mifs(self.bus_unprotected, F.ElectricLogic),
                get_mifs(self.bus_protected, F.ElectricLogic),
            )
        )
        power = list(
            zip(
                get_mifs(self.bus_unprotected, F.ElectricPower),
                get_mifs(self.bus_protected, F.ElectricPower),
            )
        )


            fuse = L.if_list(len(power), Fuse)

        # Pass through except hv
        for power_unprotected, power_protected in power:
            power_unprotected.lv.connect(power_protected.lv)
        for logic_unprotected, logic_protected in signals:
            logic_unprotected.connect_shallow(logic_protected, signal=True, lv=True)
        for raw_unprotected, raw_protected in raw:
            raw_unprotected.connect(raw_protected)

        # Fuse
        for (power_unprotected, power_protected), fuse in zip(power, self.fuse):
            power_unprotected.hv.connect_via(fuse, power_protected.hv)
            # TODO maybe shallow connect?
            power_protected.voltage.merge(power_unprotected.voltage)

        # TVS
        if self.bus_protected.has_trait(can_be_surge_protected):
            self.bus_protected.get_trait(can_be_surge_protected).protect()
        else:
            for line_unprotected, line_protected in signals + power + raw:
                line_protected.get_trait(can_be_surge_protected).protect()

        # TODO add shallow connect
    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.bus_unprotected, self.bus_protected)
