from dataclasses import dataclass, field, fields
from itertools import chain
from typing import Any, Callable

from faebryk.core.core import Node
from faebryk.core.util import as_unit
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Electrical import Electrical
from faebryk.library.has_designator_prefix import has_designator_prefix
from faebryk.library.has_designator_prefix_defined import has_designator_prefix_defined
from faebryk.library.has_simple_value_representation_based_on_param import (
    has_simple_value_representation_based_on_param,
)
from faebryk.library.LED import LED
from faebryk.library.TBD import TBD
from faebryk.libs.units import Quantity
from faebryk.libs.util import times


class FieldExistsError(Exception):
    pass


def if_list[T](if_type: type[T], n: int) -> list[T]:
    return field(default_factory=lambda: [if_type() for _ in range(n)])


class rt_field[T](property):
    def __init__(self, fget: Callable[[T], Any]) -> None:
        super().__init__()
        self.func = fget

    def _construct(self, obj: T, holder: type):
        self.constructed = self.func(holder, obj)

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        return self.constructed()


def dfield(default_factory: Callable[[], Any], **kwargs):
    return field(default_factory=default_factory, **kwargs)


# -----------------------------------------------------------------------------


@dataclass
class Node2:
    runtime_anon: list["Node2"] = field(default_factory=list)
    runtime: dict[str, "Node2"] = field(default_factory=dict)

    def add(self, obj: "Node2| Node", name: str | None = None):
        if name:
            if name in self.runtime:
                raise FieldExistsError(name)
            self.runtime[name] = obj
        self.runtime_anon.append(obj)

    _init: bool = False

    def __init_subclass__(cls, *, init: bool = True) -> None:
        print("Called Node __subclass__", "-" * 20)

        cls_d = dataclass(init=False)(cls)

        for name, obj in chain(
            # vars(cls).items(),
            [(f.name, f.type) for f in fields(cls_d)],
            # cls.__annotations__.items(),
            [(name, f) for name, f in vars(cls).items() if isinstance(f, rt_field)],
        ):
            if name.startswith("_"):
                continue
            print(f"{cls.__qualname__}.{name} = {obj}, {type(obj)}")

        # node_fields = [
        #     f
        #     for f in fields(cls)
        #     if not f.name.startswith("_") and issubclass(f.type, (Node, Node2))
        # ]
        # for f in node_fields:
        #     print(f"{cls.__qualname__}.{f.name} = {f.type.__qualname__}")

    def __post_init__(self) -> None:
        print("Called Node init", "-" * 20)
        if self._init:
            for base in reversed(type(self).mro()):
                if hasattr(base, "_init"):
                    base._init(self)


class Module2(Node2):
    pass


# -----------------------------------------------------------------------------


class Diode2(Module2):
    forward_voltage: TBD[Quantity]
    max_current: TBD[Quantity]
    current: TBD[Quantity]
    reverse_working_voltage: TBD[Quantity]
    reverse_leakage_current: TBD[Quantity]

    anode: Electrical
    cathode: Electrical

    # static trait
    designator_prefix: has_designator_prefix = dfield(
        lambda: has_designator_prefix_defined("D")
    )

    # dynamic trait
    @rt_field
    def bridge(self):
        return can_bridge_defined(self.anode, self.cathode)

    def _init(self):
        print("Called Diode post_init")

        # anonymous dynamic trait
        self.add(
            has_simple_value_representation_based_on_param(
                self.forward_voltage,
                lambda p: as_unit(p, "V"),
            )  # type: ignore
        )


class LED2(Diode2):
    color: TBD[LED.Color]

    def _init(self):
        print("Called LED post_init")


class LED2_NOINT(LED2, init=False):
    def _init(self):
        print("Called LED_NOINT post_init")


class LED2_WITHEXTRAT_IFS(LED2):
    extra: list[Electrical] = field(default_factory=lambda: times(2, Electrical))
    extra2: list[Electrical] = if_list(Electrical, 2)

    def _init(self):
        print("Called LED_WITHEXTRAT_IFS post_init")


print("Diode init ----")
D = Diode2()
print("LED init ----")
L = LED2()
print("LEDNOINIT init ----")
L2 = LED2_NOINT()
print("LEDEXTRA init ----")
L3 = LED2_WITHEXTRAT_IFS()
