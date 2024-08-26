# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.moduleinterface import ModuleInterface


class UART(ModuleInterface):
    base_uart: F.UART_Base
    rts: F.Electrical
    cts: F.Electrical
    dtr: F.Electrical
    dsr: F.Electrical
