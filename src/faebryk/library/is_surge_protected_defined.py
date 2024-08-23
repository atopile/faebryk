# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from typing import Sequence


logger = logging.getLogger(__name__)


class is_surge_protected_defined(is_surge_protected.impl()):
    def __init__(self, tvss: Sequence[TVS]) -> None:
        super().__init__()
        self.tvss = tvss

    def get_tvs(self):
        return self.tvss
