# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from pathlib import Path

from faebryk.core.core import Module, Parameter
from faebryk.core.util import get_all_modules

logger = logging.getLogger(__name__)


def export_parameters_to_file(module: Module, path: Path):
    """Write all parameters of the given module to a file."""

    # {module_name: [{param_name: param_value}, {param_name: param_value},...]}
    parameters = dict[str, list[dict[str, Parameter]]]()

    for m in {
        _m.get_most_special() for _m in get_all_modules(module.get_most_special())
    }:
        parameters[m.get_full_name(types=True)] = [
            {param.get_full_name().split(".")[-1]: param}
            for param in m.PARAMs.get_all()
        ]

    logger.info(f"Writing parameters to {path}")
    with open(path, "w") as f:
        for module_name, paras in sorted(parameters.items()):
            if paras:
                f.write(f"{module_name}\n")
                f.writelines(
                    [
                        f"    {par_name}: {par_value}\n"
                        for par_dict in paras
                        for par_name, par_value in par_dict.items()
                    ]
                )
                f.write("\n")
        f.close()
