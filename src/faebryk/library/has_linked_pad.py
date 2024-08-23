# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from abc import abstractmethod

from faebryk.core.moduleinterface import ModuleInterface
from faebryk.library.Pad import Pad


class has_linked_pad(ModuleInterface.TraitT):
    @abstractmethod
    def get_pad(self) -> Pad: ...
