# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from faebryk.core.module import Module, ModuleInterface


from faebryk.libs.units import Quantity


class SPIFlash(Module):



            power: F.ElectricPower
            spi = MultiSPI()


            memory_size: F.TBD[Quantity]

    designator_prefix = L.f_field(F.has_designator_prefix_defined)("U")
