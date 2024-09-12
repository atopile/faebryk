# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module
from faebryk.library.is_multi_module import is_multi_module

logger = logging.getLogger(__name__)


class is_multi_module_defined(is_multi_module.impl()):
    def __init__(self, children: list[Module]):
        self._children = children

    def get(self) -> list[Module]:
        return self._children
