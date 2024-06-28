# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

"""
This file contains a faebryk sample.
"""

import logging

import faebryk.library._F as F
import typer
from faebryk.core.core import Module
from faebryk.core.util import specialize_module
from faebryk.libs.experiments.buildutil import (
    tag_and_export_module_to_netlist,
)
from faebryk.libs.logging import setup_basic_logging

logger = logging.getLogger(__name__)


class App(Module):
    def __init__(self) -> None:
        super().__init__()

        class _NODES(Module.NODES()):
            lowpass = F.Filter()

        self.NODEs = _NODES(self)

        # TODO actually do something with the filter

        # Parametrize
        self.NODEs.lowpass.PARAMs.cutoff_frequency.merge(200)
        self.NODEs.lowpass.PARAMs.response.merge(F.Filter.Response.LOWPASS)

        # Specialize
        specialize_module(self.NODEs.lowpass, F.FilterElectricalLC())


def main():
    logger.info("Building app")
    app = App()

    logger.info("Export")
    tag_and_export_module_to_netlist(app)


if __name__ == "__main__":
    setup_basic_logging()
    logger.info("Running experiment")

    typer.run(main)
