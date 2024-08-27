# This file is part of the faebryk project
# SPDX-License-Identifier: MIT
import logging
from itertools import chain
from typing import TYPE_CHECKING, Any, Callable, Type, get_args, get_origin

from deprecated import deprecated

from faebryk.core.core import ID_REPR, FaebrykLibObject
from faebryk.core.graphinterface import (
    GraphInterface,
    GraphInterfaceHierarchical,
    GraphInterfaceSelf,
)
from faebryk.core.link import LinkNamedParent, LinkSibling
from faebryk.libs.util import KeyErrorNotFound, find, times, try_avoid_endless_recursion

if TYPE_CHECKING:
    from faebryk.core.trait import Trait, TraitImpl

logger = logging.getLogger(__name__)


class FieldError(Exception):
    pass


class FieldExistsError(FieldError):
    pass


class FieldContainerError(FieldError):
    pass


def if_list[T](n: int, if_type: Callable[[], T]) -> list[T]:
    return d_field(lambda: times(n, if_type))


class fab_field:
    pass


class rt_field[T](property, fab_field):
    def __init__(self, fget: Callable[[T], Any]) -> None:
        super().__init__()
        self.func = fget

    def _construct(self, obj: T):
        self.constructed = self.func(obj)
        return self.constructed

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        return self.constructed


class _d_field[T](fab_field):
    def __init__(self, default_factory: Callable[[], T]) -> None:
        self.type = None
        self.default_factory = default_factory

    def __repr__(self) -> str:
        return f"{super().__repr__()}({self.type=}, {self.default_factory=})"


def d_field[T](default_factory: Callable[[], T]) -> T:
    return _d_field(default_factory)  # type: ignore


def f_field[T, **P](con: Callable[P, T]) -> Callable[P, T]:
    assert isinstance(con, type)

    def _(*args: P.args, **kwargs: P.kwargs) -> Callable[[], T]:
        def __() -> T:
            return con(*args, **kwargs)

        out = _d_field(__)
        out.type = con
        return out

    return _


# -----------------------------------------------------------------------------
class PostInitCaller(type):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__post_init__(*args, **kwargs)
        return obj


class Node(FaebrykLibObject, metaclass=PostInitCaller):
    runtime_anon: list["Node"]
    runtime: dict[str, "Node"]
    specialized: list["Node"]

    self_gif: GraphInterfaceSelf
    children: GraphInterfaceHierarchical = d_field(
        lambda: GraphInterfaceHierarchical(is_parent=True)
    )
    parent: GraphInterfaceHierarchical = d_field(
        lambda: GraphInterfaceHierarchical(is_parent=False)
    )

    _init: bool = False

    def __hash__(self) -> int:
        # TODO proper hash
        return hash(id(self))

    def add[T: Node](
        self,
        obj: T,
        name: str | None = None,
        container: list | dict[str, Any] | None = None,
    ) -> T:
        assert obj is not None

        if container is None:
            container = self.runtime_anon
            if name:
                container = self.runtime

        try:
            container_name = find(vars(self).items(), lambda x: x[1] is container)[0]
        except KeyErrorNotFound:
            raise FieldContainerError("Container not in fields")

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
            name = f"{container_name}[{len(container) - 1}]"

        self._handle_add_node(name, obj)
        return obj

    def add_to_container[T: Node](
        self, n: int, factory: Callable[[], T], container: list[T] | None = None
    ):
        if container is None:
            container = self.runtime_anon

        constr = [factory() for _ in range(n)]
        for obj in constr:
            self.add(obj, container=container)
        return constr

    def __init_subclass__(cls, *, init: bool = True) -> None:
        super().__init_subclass__()
        cls._init = init

    def _setup_fields(self, cls):
        def all_vars(cls):
            return {k: v for c in reversed(cls.__mro__) for k, v in vars(c).items()}

        def all_anno(cls):
            return {
                k: v
                for c in reversed(cls.__mro__)
                if hasattr(c, "__annotations__")
                for k, v in c.__annotations__.items()
            }

        LL_Types = (Node, GraphInterface)

        annos = all_anno(cls)
        vars_ = all_vars(cls)
        for name, obj in vars_.items():
            if isinstance(obj, _d_field) and obj.type is None:
                obj.type = annos[name]

        def is_node_field(obj):
            def is_genalias_node(obj):
                origin = get_origin(obj)
                assert origin is not None

                if issubclass(origin, LL_Types):
                    return True

                if issubclass(origin, (list, dict)):
                    arg = get_args(obj)[-1]
                    return is_node_field(arg)

            if isinstance(obj, LL_Types):
                raise FieldError("Node instances not allowed")

            if isinstance(obj, str):
                return obj in [L.__name__ for L in LL_Types]

            if isinstance(obj, type):
                return issubclass(obj, LL_Types)

            if isinstance(obj, _d_field):
                t = obj.type
                if isinstance(t, type):
                    return issubclass(t, LL_Types)

                if get_origin(t):
                    return is_genalias_node(t)

            if get_origin(obj):
                return is_genalias_node(obj)

            if isinstance(obj, rt_field):
                return True

            return False

        clsfields_unf = {
            name: obj
            for name, obj in chain(
                [(name, f) for name, f in annos.items()],
                [(name, f) for name, f in vars_.items() if isinstance(f, fab_field)],
            )
            if not name.startswith("_")
        }

        clsfields = {
            name: obj for name, obj in clsfields_unf.items() if is_node_field(obj)
        }

        # for name, obj in clsfields_unf.items():
        #    if isinstance(obj, _d_field):
        #        obj = obj.type
        #    filtered = name not in clsfields
        #    filtered_str = "   FILTERED" if filtered else ""
        #    print(
        #        f"{cls.__qualname__+"."+name+filtered_str:<60} = {str(obj):<70} "
        # "| {type(obj)}"
        #    )

        objects: dict[str, Node | GraphInterface] = {}

        def append(name, inst):
            if isinstance(inst, LL_Types):
                objects[name] = inst
            elif isinstance(inst, list):
                for i, obj in enumerate(inst):
                    assert obj is not None
                    objects[f"{name}[{i}]"] = obj
            elif isinstance(inst, dict):
                for k, obj in inst.items():
                    objects[f"{name}[{k}]"] = obj

            return inst

        def setup_field(name, obj):
            def setup_gen_alias(name, obj):
                origin = get_origin(obj)
                assert origin
                if isinstance(origin, type):
                    setattr(self, name, append(name, origin()))
                    return
                raise NotImplementedError(origin)

            if isinstance(obj, str):
                raise NotImplementedError()

            if get_origin(obj):
                setup_gen_alias(name, obj)
                return

            if isinstance(obj, _d_field):
                t = obj.type

                if isinstance(obj, _d_field):
                    inst = append(name, obj.default_factory())
                    setattr(self, name, inst)
                    return

                if isinstance(t, type):
                    setattr(self, name, append(name, t()))
                    return

                if get_origin(t):
                    setup_gen_alias(name, t)
                    return

                raise NotImplementedError()

            if isinstance(obj, type):
                setattr(self, name, append(name, obj()))
                return

            if isinstance(obj, rt_field):
                append(name, obj._construct(self))
                return

            raise NotImplementedError()

        for name, obj in clsfields.items():
            setup_field(name, obj)

        return objects, clsfields

    def __new__(cls, *args, **kwargs):
        out = super().__new__(cls)
        return out

    def _setup(self) -> None:
        cls = type(self)
        # print(f"Called Node init {cls.__qualname__:<20} {'-' * 80}")

        # check if accidentally added a node instance instead of field
        node_instances = [f for f in vars(cls).values() if isinstance(f, Node)]
        if node_instances:
            raise FieldError(f"Node instances not allowed: {node_instances}")

        # Construct Fields
        objects, _ = self._setup_fields(cls)

        # Add Fields to Node
        for name, obj in sorted(
            objects.items(), key=lambda x: isinstance(x[1], GraphInterfaceSelf)
        ):
            if isinstance(obj, GraphInterface):
                self._handle_add_gif(name, obj)
            elif isinstance(obj, Node):
                self._handle_add_node(name, obj)
            else:
                assert False

        # Call 2-stage constructors
        if self._init:
            for base in reversed(type(self).mro()):
                if hasattr(base, "__preinit__"):
                    base.__preinit__(self)
            for base in reversed(type(self).mro()):
                if hasattr(base, "__postinit__"):
                    base.__postinit__(self)

    def __init__(self):
        assert not hasattr(self, "_is_setup")
        self._is_setup = True

    def __preinit__(self): ...
    def __postinit__(self): ...

    def __post_init__(self, *args, **kwargs):
        self._setup()

    def _handle_add_gif(self, name: str, gif: GraphInterface):
        gif.node = self
        gif.name = name
        if not isinstance(gif, GraphInterfaceSelf):
            gif.connect(self.self_gif, linkcls=LinkSibling)

    def _handle_add_node(self, name: str, node: "Node"):
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
        from faebryk.core.trait import TraitImpl
        from faebryk.core.util import get_children

        impls = get_children(self, direct_only=True, types=TraitImpl)

        return [
            impl
            for impl in impls
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
        from faebryk.core.trait import TraitImpl

        assert not issubclass(
            trait, TraitImpl
        ), "You need to specify the trait, not an impl"

        candidates = self._find(trait, only_implemented=True)
        assert len(candidates) <= 1
        assert len(candidates) == 1, "{} not in {}[{}]".format(trait, type(self), self)

        out = candidates[0]
        assert isinstance(out, trait)
        return out
