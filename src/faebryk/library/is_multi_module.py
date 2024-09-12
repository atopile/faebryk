# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from abc import abstractmethod

from faebryk.core.module import Module
from faebryk.core.trait import Trait

logger = logging.getLogger(__name__)


class is_multi_module(Trait):
    """
    Docstring describing your module
    """

    @abstractmethod
    def get(self) -> list[Module]:
        """
        Docstring describing the function
        """
        pass
