from dataclasses import dataclass, field, fields
from typing import Any, Callable

from faebryk.core.core import GraphInterface, ModuleInterface, Parameter, Trait
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Electrical import Electrical
from faebryk.library.has_designator_prefix_defined import has_designator_prefix_defined
from faebryk.library.LED import LED
from faebryk.library.TBD import TBD
from faebryk.libs.util import times


class FieldExistsError(Exception):
    pass


@dataclass(init=False)
class Holder2[T]:
    runtime_anon: list[T] = field(default_factory=list)
    runtime: dict[str, T] = field(default_factory=dict)

    def add(self, obj: T, name: str | None = None):
        if name:
            if name in self.runtime:
                raise FieldExistsError(name)
            self.runtime[name] = obj
        self.runtime_anon.append(obj)


@dataclass(init=False)
class Node2[T: type[Node2]]:
    class T_PARAMS(Holder2[Parameter]):
        pass

    class T_NODES(Holder2["Node2"]):
        pass

    class T_TRAITS(Holder2[Trait]):
        pass

    class T_GIFS(Holder2[GraphInterface]):
        pass

    P: T_PARAMS
    N: T_NODES
    T: T_TRAITS
    G: T_GIFS

    _init: bool

    def __init_subclass__(cls, *, init: bool = True) -> None:
        print("Called Node __subclass__", "-" * 20)
        holders_types = [
            f
            for name, f in vars(cls).items()
            if not name.startswith("_") and issubclass(f, Holder2)
        ]

        holder_fields = [
            f
            for f in fields(cls)
            if not f.name.startswith("_") and issubclass(f.type, Holder2)
        ]

        for f in holders_types:
            # setattr(cls, f, field(default_factory=getattr(cls, f)))
            print("", f.__qualname__, f)

        for f in holder_fields:
            print("", f"{cls.__qualname__}.{f.name}", f.type)

    def __init__(self) -> None:
        print("Called Node init")
        if self._init:
            for base in reversed(type(self).mro()):
                if hasattr(base, "__post_init__"):
                    base.__post_init__(self)


class Module2(Node2):
    class T_IFS(Holder2[ModuleInterface]):
        pass

    F: T_IFS


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
    class T_PARAMS(Module2.T_PARAMS):
        forward_voltage: TBD[float]
        max_current: TBD[float]
        current: TBD[float]
        reverse_working_voltage: TBD[float]
        reverse_leakage_current: TBD[float]

    class T_IFS(Module2.T_IFS):
        anode: Electrical
        cathode: Electrical

    class T_TRAITS(Module2.T_TRAITS):
        # static trait
        designator_prefix = has_designator_prefix_defined("D")

        # dynamic trait
        @rt_field
        def bridge(cls, obj: "Diode2"):
            return can_bridge_defined(obj.F.anode, obj.F.cathode)

    P: T_PARAMS
    F: T_IFS
    T: T_TRAITS

    def __post_init__(self):
        print("Called Diode post_init")

        # anonymous dynamic trait
        # self.T.add(
        #    has_simple_value_representation_based_on_param(
        #        self.P.forward_voltage,
        #        lambda p: as_unit(p, "V"),
        #    )
        # )


class LED2(Diode2):
    class T_PARAMS(Diode2.T_PARAMS):
        color: TBD[LED.Color]

    P: T_PARAMS

    def __post_init__(self):
        print("Called LED post_init")


class LED2_NOINT(LED2, init=False):
    def __post_init__(self):
        print("Called LED_NOINT post_init")


class LED2_WITHEXTRAT_IFS(LED2):
    class T_IFS(LED2.T_IFS):
        extra = field(default_factory=lambda: times(2, Electrical))
        extra2 = if_list(Electrical, 2)

    F: T_IFS

    def __post_init__(self):
        print("Called LED_WITHEXTRAT_IFS post_init")


print("Diode init ----")
D = Diode2()
print("LED init ----")
L = LED2()
print("LEDNOINIT init ----")
L2 = LED2_NOINT()
print("LEDEXTRA init ----")
L3 = LED2_WITHEXTRAT_IFS()
