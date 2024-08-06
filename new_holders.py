from dataclasses import dataclass, field
from typing import Any, Callable

from faebryk.core.core import ModuleInterface, Parameter, Trait
from faebryk.core.util import as_unit
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Electrical import Electrical
from faebryk.library.has_designator_prefix_defined import has_designator_prefix_defined
from faebryk.library.has_simple_value_representation_based_on_param import (
    has_simple_value_representation_based_on_param,
)
from faebryk.library.LED import LED
from faebryk.library.TBD import TBD
from faebryk.libs.util import times


@dataclass(init=False)
class Holder2[T]:
    runtime: list[T] = field(default_factory=list)

    def add(self, obj: T):
        self.runtime.append(obj)


@dataclass(init=False)
class Node2:
    class PARAMS(Holder2[Parameter]):
        pass

    class NODES(Holder2["Node2"]):
        pass

    class TRAITS(Holder2[Trait]):
        pass

    PARAMs: PARAMS
    NODEs: NODES
    TRAITs: TRAITS

    _init: bool

    def __init_subclass__(cls, *, init: bool = True) -> None:
        print("Called Node __subclass__")
        cls._init = init

    def __init__(self) -> None:
        print("Called Node init")
        if self._init:
            for base in reversed(type(self).mro()):
                if hasattr(base, "__post_init__"):
                    base.__post_init__(self)


class Module2(Node2):
    class IFS(Holder2[ModuleInterface]):
        pass

    IFs: IFS


# TODO can we get rid of the explicit bases in the holders?

# -----------------------------------------------------------------------------


def if_list[T](if_type: type[T], n: int) -> list[T]:
    return field(default_factory=lambda: [if_type() for _ in range(n)])


class rt_field[T](property):
    def __init__(self, fget: Callable[[Any, T], Any]) -> None:
        super().__init__()
        self.func = fget

    def _construct(self, obj: T, holder: type):
        self.constructed = self.func(holder, obj)

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        return self.constructed()


# -----------------------------------------------------------------------------


class Diode2(Module2):
    class PARAMS(Module2.PARAMS):
        forward_voltage: TBD[float]
        max_current: TBD[float]
        current: TBD[float]
        reverse_working_voltage: TBD[float]
        reverse_leakage_current: TBD[float]

    class IFS(Module2.IFS):
        anode: Electrical
        cathode: Electrical

    class TRAITS(Module2.TRAITS):
        # static trait
        designator_prefix = has_designator_prefix_defined("D")

        # dynamic trait
        @rt_field
        def bridge(cls, obj: "Diode2"):
            return can_bridge_defined(obj.IFs.anode, obj.IFs.cathode)

    PARAMs: PARAMS
    IFs: IFS
    TRAITs: TRAITS

    def __post_init__(self):
        print("Called Diode post_init")

        # anonymous dynamic trait
        self.TRAITs.add(
            has_simple_value_representation_based_on_param(
                self.PARAMs.forward_voltage,
                lambda p: as_unit(p, "V"),
            )
        )


class LED2(Diode2):
    class PARAMS(Diode2.PARAMS):
        color: TBD[LED.Color]

    PARAMs: PARAMS

    def __post_init__(self):
        print("Called LED post_init")


class LED2_NOINT(LED2, init=False):
    def __post_init__(self):
        print("Called LED_NOINT post_init")


class LED2_WITHEXTRAIFS(LED2):
    class IFS(LED2.IFS):
        extra = field(default_factory=lambda: times(2, Electrical))
        extra2 = if_list(Electrical, 2)

    IFs: IFS

    def __post_init__(self):
        print("Called LED_WITHEXTRAIFS post_init")


print("Diode init ----")
D = Diode2()
print("LED init ----")
L = LED2()
print("LEDNOINIT init ----")
L2 = LED2_NOINT()
print("LEDEXTRA init ----")
L3 = LED2_WITHEXTRAIFS()
