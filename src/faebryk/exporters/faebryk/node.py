import ast
import logging
from typing import cast

import astor
import black
from faebryk.core.core import GraphInterface, Node
from faebryk.libs.util import _wrapper

logger = logging.getLogger(__name__)


# TODO move to util
def _is_field_from_class(cls, field):
    print(field, cls)
    if field in cls.__dict__:
        return True
    for base in cls.mro()[1:]:
        print(field, base)
        if field in base.__dict__:
            return False
    raise KeyError(f"Field '{field}' not found in {cls}")


def _highest_level_fields(holder: _wrapper):
    """
    Return only fields that are not defined in super classes
    """

    fields: list[GraphInterface | Node] = holder.get_all()

    fields = [
        f
        for f in fields
        if _is_field_from_class(type(holder), f.get_full_name().split(".")[-1])
    ]

    return fields


# namespace
class AST:
    @staticmethod
    def _attr(*hierarchy: str):
        levels = list(hierarchy)
        return ast.Attribute(
            AST._attr(*levels[:-1]) if len(levels) > 2 else ast.Name(levels[0]),
            levels[-1],
        )

    @staticmethod
    def _import(base: str, *modules: str):
        return ast.ImportFrom(
            module=base,
            names=[ast.alias(name=module, asname=None) for module in modules],
            level=0,
        )

    class _Generator(astor.SourceGenerator):
        def visit(self, node, abort=astor.SourceGenerator.abort_visit):
            # check if faebryk ast node
            # can also be done by adding mixing everywhere but thats more effort
            if type(node).__qualname__.startswith("AST"):
                # reconstruct super class
                node = type(node).mro()[1](**node.__dict__)

            return super().visit(node, abort)

    @staticmethod
    def to_source(obj):
        src = astor.to_source(obj, source_generator_class=AST._Generator)
        try:
            return black.format_str(
                src,
                mode=black.FileMode(),
            )
        except Exception as e:
            print(src)
            raise e

    # objects --------------------------------------------------------------------------
    class Field(ast.Assign):
        def __init__(self, val: GraphInterface | Node):
            # TODO lists / containers
            # TODO find import

            modname = type(val).__name__
            name = val.get_full_name().split(".")[-1]

            super().__init__(
                targets=[ast.Name(name)],
                value=ast.Call(
                    func=ast.Name(modname),
                    args=[],
                    keywords=[],
                ),
            )

    class Holder(ast.FunctionDef):
        def __init__(self, name: str, holder: _wrapper):
            parent = holder.get_parent()

            # TODO this only works if the Node is creating its Holders in the class body
            # instead of in the constructor
            try:
                in_in_class = _is_field_from_class(type(parent), name.upper())
            except KeyError:
                fields = _highest_level_fields(holder)
            else:
                if in_in_class:
                    fields = _highest_level_fields(holder)
                else:
                    fields = []

            anonymous_class_name = f"_{name}"

            super().__init__(
                name=name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg="cls")],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[],
                ),
                body=[
                    ast.ClassDef(
                        name=anonymous_class_name,
                        bases=[
                            ast.Attribute(
                                value=ast.Call(
                                    func=ast.Name(id="super"),
                                    args=[],
                                    keywords=[],
                                ),
                                attr="GIFs",
                            )
                        ],
                        keywords=[],
                        body=[AST.Field(f) for f in fields] or [ast.Pass()],
                        decorator_list=[],
                        type_params=[],
                    ),
                    ast.Return(ast.Name(anonymous_class_name)),
                ],
                decorator_list=[ast.Name(id="classmethod")],
                type_params=[],
            )

    class Node(ast.ClassDef):
        class Constructor(ast.FunctionDef):
            def __init__(self, node: Node):
                holders = [
                    (name, val)
                    for name, val in vars(node).items()
                    if isinstance(val, _wrapper)
                ]

                super().__init__(
                    name="__init__",
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg("self")],
                        kwonlyargs=[],
                        kw_defaults=[],
                        kwarg=None,
                        defaults=[],
                    ),
                    body=[
                        # instantiate holders
                        ast.Assign(
                            targets=[AST._attr("self", holder_name)],
                            value=ast.Call(
                                func=AST._attr("self", holder_name.upper()),
                                args=[ast.Name("self")],
                                keywords=[],
                            ),
                        )
                        for holder_name, _ in holders
                    ]
                    or [ast.Pass()],
                    decorator_list=[],
                    returns=None,
                    type_comment=None,
                    type_params=[],
                )

        def __init__(self, node: Node):
            cls = type(node)
            class_name = cls.__name__
            base_name = cls.mro()[1].__name__

            holders = [
                (name, val)
                for name, val in vars(node).items()
                if isinstance(val, _wrapper)
            ]

            super().__init__(
                name=class_name,
                bases=[ast.Name(base_name)],
                keywords=[],
                # holders
                body=[
                    AST.Holder(name=holder_name, holder=holder)
                    for holder_name, holder in holders
                ]
                +
                # constructor
                [cast(ast.stmt, AST.Node.Constructor(node))],
                # TODO connections
                # TODO traits
                # strategy: only serialize traits that have defined in name
                decorator_list=[],
                type_params=[],
            )


def faebryk_node_to_python(node: Node) -> str:
    """
    Converts runtime faebryk Nodes back into code.
    Careful, only works for very simple nodes!
    """

    class_ast = AST.Node(node)
    out = AST.to_source(class_ast)

    # TODO remove debug
    print(out)
    return out
