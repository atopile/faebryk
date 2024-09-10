from faebryk.libs.util import FuncDict, FuncSet


def test_func_dict_contains():
    a = FuncDict([(1, 2), (FuncDict, 4), (FuncSet, 5)])
    assert 1 in a
    assert FuncDict in a
    assert FuncSet in a

    assert a[1] == 2
    assert a[FuncDict] == 4
    assert a[FuncSet] == 5

    a[id] = 10
    assert a[id] == 10
