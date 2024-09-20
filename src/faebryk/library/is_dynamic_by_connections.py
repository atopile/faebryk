# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from typing import Callable

from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.node import NodeException
from faebryk.core.parameter import Parameter
from faebryk.libs.util import NotNone, cast_assert

logger = logging.getLogger(__name__)


class is_dynamic_by_connections(Parameter.is_dynamic.impl()):
    def __init__(self, key: Callable[[ModuleInterface], Parameter]) -> None:
        super().__init__()
        self._key = key
        self._guard = False

    def exec(self):
        mif_parent = cast_assert(ModuleInterface, NotNone(self.obj.get_parent())[0])
        param = self.get_obj(Parameter)
        if self._key(mif_parent) is not param:
            raise NodeException(self, "Key not mapping to parameter")

        if self._guard:
            return

        print(f"EXEC {param.get_full_name()}")
        mifs = mif_parent.get_connected()

        # Disable guards to prevent infinite recursion
        guards = [
            trait
            for mif in mifs
            if self._key(mif).has_trait(Parameter.is_dynamic)
            and isinstance(
                trait := self._key(mif).get_trait(Parameter.is_dynamic),
                is_dynamic_by_connections,
            )
            and not trait._guard
        ] + [self]
        for guard in guards:
            guard._guard = True

        # Merge parameters
        for mif in mifs:
            mif_param = self._key(mif)
            param.merge(mif_param)

        # Enable guards again
        for guard in guards:
            guard._guard = False
