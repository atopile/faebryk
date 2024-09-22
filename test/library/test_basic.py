# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import pytest

from faebryk.core.core import Namespace
from faebryk.core.node import Node
from faebryk.libs.library import L

try:
    import faebryk.library._F as F
except ImportError:
    F = None


def test_load_library():
    assert F is not None, "Failed to load library"


@pytest.mark.skipif(F is None, reason="Library not loaded")
@pytest.mark.parametrize("name, module", list(vars(F).items()))
def test_symbol_types(name: str, module):
    # private symbols get a pass
    if name.startswith("_"):
        return

    # skip once wrappers
    # allow once wrappers for type generators
    if getattr(module, "_is_once_wrapper", False):
        return

    # otherwise, only allow Node or Namespace class objects
    assert isinstance(module, type) and issubclass(module, (Node, Namespace))


@pytest.mark.skipif(F is None, reason="Library not loaded")
@pytest.mark.parametrize("name, module", list(vars(F).items()))
def test_init_args(name: str, module):
    """Make sure we can instantiate all classes without error"""
    from faebryk.core.trait import Trait, TraitImpl

    if name.startswith("_"):
        return

    if not isinstance(module, type):
        return

    if not issubclass(module, Node):
        return

    if issubclass(module, Trait) and not issubclass(module, TraitImpl):
        return

    # check if constructor has no args & no varargs
    if (
        module.__init__.__code__.co_argcount == 1
        and not module.__init__.__code__.co_flags & 0x04
    ):
        try:
            module()
        except L.AbstractclassError:
            pass
