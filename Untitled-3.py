# %%
from ast import Param
from typing import Callable, Hashable, Iterable, Self
import z3
from uuid import uuid4
from numbers import Number
import operator


def str_uuid():
    return str(uuid4())


def dfs[T](
    node: T,
    children: Callable[[T], Iterable[T]],
    visited: set[Hashable] | None = None,
    hasher: Callable[[T], Hashable] = lambda x: x,
    ignore_recursion=False,
):
    if visited is None:
        visited = set()
    if hasher(node) in visited:
        if not ignore_recursion:
            raise RecursionError
        return
    visited.add(hasher(node))
    for child in children(node):
        yield from dfs(child, children, visited, hasher, ignore_recursion)
    yield node


class Parameter:
    def __init__(self, name=None) -> None:
        self.name = name or str_uuid()
        self.symbol = z3.Real(self.name)
        self.embodied_constraints = []
        self.dependencies: list[Parameter] = []

    @classmethod
    def ensure(cls, thing) -> "Parameter | Number":
        if isinstance(thing, Parameter):
            return thing
        if isinstance(thing, Number):
            return thing
        if isinstance(thing, tuple):
            return Range(*thing)
        if isinstance(thing, set):
            return Set(*thing)
        raise ValueError("Can't create parameter from literal")

    @classmethod
    def modelled_as(cls, thing) -> z3.ExprRef | Number:
        if isinstance(thing, Parameter):
            return thing.symbol
        return thing

    def build_dependencies(self, candidates) -> Self:
        self.dependencies = [v for v in candidates if isinstance(v, Parameter)]
        return self

    def all_constraints(self) -> list[z3.ExprRef]:
        def _children(v: Parameter):
            return v.dependencies
        dependencies = list(
            dfs(self, _children, hasher=lambda v: v.name, ignore_recursion=True)
        )
        return [
            *[c for d in dependencies for c in d.embodied_constraints],
        ]

    def check(self) -> bool:
        return z3.Solver().check(self.all_constraints()).r == 0

    @classmethod
    def _op(cls, a: "Parameter | Number", b: "Parameter | Number", op) -> "Parameter":
        b = a.ensure(b)
        param = Parameter()
        param.embodied_constraints += [
            param.symbol == op(a.modelled_as(a), a.modelled_as(b)),
        ]
        param.build_dependencies([a, b])
        return param

    def __add__(self, other: "Parameter | Number") -> "Parameter":
        return Parameter._op(self, other, operator.add)

    def __sub__(self, other: "Parameter | Number") -> "Parameter":
        return Parameter._op(self, other, operator.sub)

    def __mul__(self, other: "Parameter | Number") -> "Parameter":
        return Parameter._op(self, other, operator.mul)

    def __truediv__(self, other: "Parameter | Number") -> "Parameter":
        return Parameter._op(self, other, operator.truediv)

    def __ge__(self, other: "Parameter | Number") -> bool:
        return Parameter._op(self, other, operator.ge).check()

    def __le__(self, other: "Parameter | Number") -> "Parameter":
        return Parameter._op(self, other, operator.le).check()

    def __lt__(self, other: "Parameter | Number") -> "Parameter":
        return Parameter._op(self, other, operator.lt).check()

    def __gt__(self, other: "Parameter | Number") -> "Parameter":
        return Parameter._op(self, other, operator.lt).check()


class Range(Parameter):
    def __init__(self, *bounds):
        super().__init__()
        self.bounds: list[Parameter] = sorted([Parameter.ensure(v) for v in bounds])
        self.embodied_constraints += [
            self.modelled_as(self) >= self.modelled_as(self.bounds[0]),
            self.modelled_as(self) <= self.modelled_as(self.bounds[-1]),
        ]
        self.build_dependencies(self.bounds)
        if not z3.Solver().check(*self.embodied_constraints).r == 1:
            raise ValueError("Range isn't valid")


class Set(Parameter):
    def __init__(self, *values: Parameter):
        super().__init__()
        self.values = values
        self.embodied_constraints += [
            z3.Or(*(self.modelled_as(self) == self.modelled_as(v) for v in values))
        ]
        self.build_dependencies(values)
        if not z3.Solver().check(*self.embodied_constraints).r == 1:
            raise ValueError("Set isn't valid")


# %%
s = z3.Solver()
a = Range(1, 10)

c = a + 5
s.add(c.all_constraints())

# %%
s.check()
s.model()

# %%
d = Set(Range(1, 10), 2, 3, 4, 5)
d.all_constraints()

# %%
