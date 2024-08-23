# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module




from faebryk.libs.units import P


class QWIIC(Module):
    """
    Sparkfun QWIIC connection spec. Also compatible with Adafruits STEMMA QT.
    Delivers 3.3V power + I2C over JST SH 1mm pitch 4 pin connectors
    """



        # interfaces

            i2c = I2C()
            power: F.ElectricPower

        # set constraints
        self.power.voltage.merge(F.Constant(3.3 * P.V))
        # TODO: self.power.source_current.merge(F.Constant(226 * P.mA))

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("J")

        self.add_trait(has_datasheet_defined("https://www.sparkfun.com/qwiic"))
