# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module
from faebryk.library.is_multi_module import is_multi_module

logger = logging.getLogger(__name__)


class is_multi_module_defined_by_type(is_multi_module.impl()):
    def __init__(self, children_type: type[Module]):
        self._children_type = children_type

    def get(self) -> list[Module]:
        return list(self.obj.get_children(direct_only=False, types=self._children_type))
