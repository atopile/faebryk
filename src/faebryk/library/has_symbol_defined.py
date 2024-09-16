# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F


class has_symbol_defined(F.has_symbol.impl()):
    def __init__(self, sym: F.Symbol) -> None:
        super().__init__()
        self.sym = sym

    def on_obj_set(self):
        self._set_symbol(self.sym)

    def _set_symbol(self, sym: F.Symbol):
        self.obj.add(sym, name="symbol")

    def get_symbol(self) -> F.Symbol:
        syms = self.obj.get_children(direct_only=True, types=F.Symbol)
        assert len(syms) == 1, f"In obj: {self.obj}: candidates: {syms}"
        return next(iter(syms))
