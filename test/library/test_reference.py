import pytest

from faebryk.core.node import Node
from faebryk.library.Reference import Reference


def test_points_to_correct_node():
    class A(Node):
        pass

    class B(Node):
        x = Reference(A)

    a = A()
    b = B()
    b.x = a
    assert b.x is a


def test_immutable():
    class A(Node):
        pass

    class B(Node):
        x = Reference(A)

    b = B()
    a = A()
    b.x = a

    with pytest.raises(TypeError):
        b.x = A()


def test_unset():
    class A(Node):
        pass

    class B(Node):
        x = Reference(A)

    b = B()
    with pytest.raises(Reference.UnboundError):
        b.x


def test_wrong_type():
    class A(Node):
        pass

    class B(Node):
        x = Reference(A)

    b = B()
    with pytest.raises(TypeError):
        b.x = 1


def test_set_value_before_constuction():
    class A(Node):
        pass

    class B(Node):
        x = Reference(A)

        def __init__(self, x):
            self.x = x

    a = A()
    b = B(a)
    assert b.x is a


def test_typed_construction():
    class A(Node):
        pass

    class B(Node):
        x: Reference[A]

    a = A()
    b = B()
    b.x = a
    assert b.x is a
