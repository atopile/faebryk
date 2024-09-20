import pytest

from faebryk.core.node import InitVar, Node, magic_pointer


def test_points_to_correct_node():
    class A(Node):
        pass

    class B(Node):
        x: InitVar[A] = magic_pointer(A)

    a = A()
    b = B()
    b.x = a
    assert b.x is a


def test_immutable():
    class A(Node):
        pass

    class B(Node):
        x: InitVar[A] = magic_pointer(A)

    b = B()
    a = A()
    b.x = a
    assert b.x is a

    with pytest.raises(TypeError):
        b.x = A()


def test_unset():
    class A(Node):
        pass

    class B(Node):
        x: InitVar[A] = magic_pointer(A)

    b = B()
    with pytest.raises(AttributeError):
        b.x


def test_wrong_type():
    class A(Node):
        pass

    class B(Node):
        x: InitVar[A] = magic_pointer(A)

    b = B()
    with pytest.raises(TypeError):
        b.x = 1
