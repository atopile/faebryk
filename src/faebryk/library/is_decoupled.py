# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from abc import abstractmethod

from faebryk.core.trait import Trait


logger = logging.getLogger(__name__)


class is_decoupled(Trait):
    @abstractmethod
    def get_capacitor(self) -> F.Capacitor: ...
