# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

from faebryk.core.module import Module


logger = logging.getLogger(__name__)


class QWIIC_Connector(Module):





            power: F.ElectricPower
            i2c = I2C()



    designator_prefix = L.f_field(F.has_designator_prefix_defined)("J")
