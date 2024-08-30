# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.moduleinterface import ModuleInterface


class Power(ModuleInterface):
    class PowerSourcesShortedError(Exception): ...

    class IsPowerSource(ModuleInterface.TraitT): ...

    class IsPowerSourceDefined(IsPowerSource.impl()): ...

    def make_source(self):
        self.add(self.IsPowerSourceDefined())
        return self

    def _on_connect(self, other: "Power"):
        print(f"Power._on_connect({self}, {other})")  # TODO remove
        if self.has_trait(self.IsPowerSource) and other.has_trait(self.IsPowerSource):
            raise self.PowerSourcesShortedError(self, other)
