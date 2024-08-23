from dataclasses import field

import typer

from faebryk.core.module import Module
from faebryk.core.node import d_field, if_list, rt_field
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Electrical import Electrical
from faebryk.library.has_designator_prefix import has_designator_prefix
from faebryk.library.has_designator_prefix_defined import has_designator_prefix_defined
from faebryk.library.TBD import TBD
from faebryk.libs.units import Quantity
from faebryk.libs.util import times

# -----------------------------------------------------------------------------


class Diode2(Module):
    forward_voltage: TBD[Quantity]
    max_current: TBD[Quantity]
    current: TBD[Quantity]
    reverse_working_voltage: TBD[Quantity]
    reverse_leakage_current: TBD[Quantity]

    anode: Electrical
    cathode: Electrical

    XXXXX: Electrical = d_field(Electrical)

    # static trait
    designator_prefix: has_designator_prefix = d_field(
        lambda: has_designator_prefix_defined("D")
    )

    # dynamic trait
    @rt_field
    def bridge(self):
        return can_bridge_defined(self.anode, self.cathode)

    def __preinit__(self):
        print("Called Diode __preinit__")

        # anonymous dynamic trait
        # self.add(
        #     has_simple_value_representation_based_on_param(
        #         self.forward_voltage,
        #         lambda p: as_unit(p, "V"),
        #     )  # type: ignore
        # )


class LED2(Diode2):
    color: TBD[float]

    def __preinit__(self):
        print("Called LED __preinit__")


class LED2_NOINT(LED2, init=False):
    def __preinit__(self):
        print("Called LED_NOINT __preinit__")


class LED2_WITHEXTRAT_IFS(LED2):
    extra: list[Electrical] = field(default_factory=lambda: times(2, Electrical))
    extra2: list[Electrical] = if_list(Electrical, 2)

    @rt_field
    def bridge(self):
        return can_bridge_defined(self.extra2[0], self.extra2[1])

    def __preinit__(self):
        print("Called LED_WITHEXTRAT_IFS __preinit__")


def main():
    print("Diode init ----")
    _D = Diode2()
    print("LED init ----")
    _L = LED2()
    print("LEDNOINIT init ----")
    L2 = LED2_NOINT()
    print("LEDEXTRA init ----")
    L3 = LED2_WITHEXTRAT_IFS()

    L3.cathode.connect(L2.cathode)

    assert L3.cathode.is_connected_to(L2.cathode)


typer.run(main)
