# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

from enum import Enum, auto

from faebryk.core.core import Module
from faebryk.library.Signal import Signal
from faebryk.library.TBD import TBD


class Filter(Module):
    class Response(Enum):
        LOWPASS = auto()
        HIGHPASS = auto()
        BANDPASS = auto()
        BANDSTOP = auto()
        OTHER = auto()

    @classmethod
    def PARAMS(cls):
        class _PARAMs(super().PARAMS()):
            cutoff_frequency = TBD[float]()
            order = TBD[int]()
            response = TBD[Filter.Response]()

        return _PARAMs

    def __init__(self):
        super().__init__()

        self.PARAMs = self.PARAMS()(self)

        class _IFs(super().IFS()):
            in_ = Signal()
            out = Signal()

        self.IFs = _IFs(self)
