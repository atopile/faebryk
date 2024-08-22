# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging
from dataclasses import field, fields
from itertools import chain
from typing import Any, Callable, Type, overload, type_check_only

from attr import dataclass
from deprecated import deprecated

from faebryk.core.core import ID_REPR, FaebrykLibObject
from faebryk.core.graphinterface import (
    GraphInterface,
    GraphInterfaceHierarchical,
    GraphInterfaceSelf,
)
from faebryk.core.link import LinkNamedParent, LinkSibling
from faebryk.libs.util import try_avoid_endless_recursion

if type_check_only:
    from faebryk.core.trait import Trait, TraitImpl

logger = logging.getLogger(__name__)


class FieldError(Exception):
    pass


class FieldExistsError(FieldError):
    pass


class FieldContainerError(FieldError):
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


def d_field(default_factory: Callable[[], Any], **kwargs):
    return field(default_factory=default_factory, **kwargs)


# -----------------------------------------------------------------------------


@dataclass
class Node(FaebrykLibObject):
    runtime_anon: list["Node"] = field(default_factory=list)
    runtime: dict[str, "Node"] = field(default_factory=dict)
    specialized: list["Node"] = field(default_factory=list)

    self_gif: GraphInterface = d_field(GraphInterfaceSelf)
    children: GraphInterfaceHierarchical = d_field(
        lambda: GraphInterfaceHierarchical(is_parent=True)
    )
    parent: GraphInterfaceHierarchical = d_field(
        lambda: GraphInterfaceHierarchical(is_parent=False)
    )

    def __hash__(self) -> int:
        raise NotImplementedError()

    def add(
        self,
        obj: "Node",
        name: str | None = None,
        container: list | dict[str, Any] | None = None,
    ):
        if container is None:
            container = self.runtime_anon
            if name:
                container = self.runtime

        if name:
            if not isinstance(container, dict):
                raise FieldContainerError(f"Expected dict got {type(container)}")
            if name in container:
                raise FieldExistsError(name)
            container[name] = obj
        else:
            if not isinstance(container, list):
                raise FieldContainerError(f"Expected list got {type(container)}")
            container.append(obj)

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

        # NOTES:
        # - first construct than call handle (for eliminating hazards)

    def __post_init__(self) -> None:
        print("Called Node init", "-" * 20)
        if self._init:
            for base in reversed(type(self).mro()):
                if hasattr(base, "__finit__"):
                    base.__finit__(self)

    @overload
    def _handle_add(self, name: str, gif: GraphInterface):
        gif.node = self
        gif.name = name
        gif.connect(self.self_gif, linkcls=LinkSibling)

    @overload
    def _handle_add(self, name: str, node: "Node"):
        assert not (
            other_p := node.get_parent()
        ), f"{node} already has parent: {other_p}"
        node.parent.connect(self.children, LinkNamedParent.curry(name))

    def handle_added_to_parent(self): ...

    def get_graph(self):
        return self.self_gif.G

    def get_parent(self):
        return self.parent.get_parent()

    def get_name(self):
        p = self.get_parent()
        if not p:
            raise Exception("Parent required for name")
        return p[1]

    def get_hierarchy(self) -> list[tuple["Node", str]]:
        parent = self.get_parent()
        if not parent:
            return [(self, "*")]
        parent_obj, name = parent

        return parent_obj.get_hierarchy() + [(self, name)]

    def get_full_name(self, types: bool = False):
        hierarchy = self.get_hierarchy()
        if types:
            return ".".join([f"{name}|{type(obj).__name__}" for obj, name in hierarchy])
        else:
            return ".".join([f"{name}" for _, name in hierarchy])

    @try_avoid_endless_recursion
    def __str__(self) -> str:
        return f"<{self.get_full_name(types=True)}>"

    @try_avoid_endless_recursion
    def __repr__(self) -> str:
        id_str = f"(@{hex(id(self))})" if ID_REPR else ""
        return f"<{self.get_full_name(types=True)}>{id_str}"

    # Trait stuff ----------------------------------------------------------------------

    # TODO type checking InterfaceTrait -> Interface
    @deprecated("Just use add")
    def add_trait[_TImpl: "TraitImpl"](self, trait: _TImpl) -> _TImpl:
        from faebryk.core.trait import Trait, TraitImpl

        assert isinstance(trait, TraitImpl), ("not a traitimpl:", trait)
        assert isinstance(trait, Trait)

        self.add(trait)

        return trait

    def _find(self, trait, only_implemented: bool):
        from faebryk.core.util import get_children

        traits = get_children(self, direct_only=True, types=TraitImpl)

        return [
            impl
            for impl in traits
            if impl.implements(trait)
            and (impl.is_implemented() or not only_implemented)
        ]

    def del_trait(self, trait):
        candidates = self._find(trait, only_implemented=False)
        assert len(candidates) <= 1
        if len(candidates) == 0:
            return
        assert len(candidates) == 1, "{} not in {}[{}]".format(trait, type(self), self)
        impl = candidates[0]
        impl.parent.disconnect(impl)

    def has_trait(self, trait) -> bool:
        return len(self._find(trait, only_implemented=True)) > 0

    def get_trait[V: "Trait"](self, trait: Type[V]) -> V:
        assert not issubclass(
            trait, TraitImpl
        ), "You need to specify the trait, not an impl"

        candidates = self._find(trait, only_implemented=True)
        assert len(candidates) <= 1
        assert len(candidates) == 1, "{} not in {}[{}]".format(trait, type(self), self)

        out = candidates[0]
        assert isinstance(out, trait)
        return out
