# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
import re
from typing import Type

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.e_series import E_SERIES_VALUES
from faebryk.libs.picker.api.api import (
    ApiClient,
    check_compatible_parameters,
    get_footprint_candidates,
    try_attach,
)

# re-use the existing model for components from the jlcparts dataset, but as the data
# schema diverges over time we'll migrate this to separate models
from faebryk.libs.picker.jlcpcb.jlcpcb import Component
from faebryk.libs.picker.jlcpcb.picker_lib import _MAPPINGS_BY_TYPE
from faebryk.libs.picker.picker import DescriptiveProperties, PickError
from faebryk.libs.picker.util import generate_si_values

logger = logging.getLogger(__name__)
client = ApiClient()


# TODO add trait to module that specifies the quantity of the part
qty: int = 1


def find_lcsc_part(module: Module):
    """
    Find a part by LCSC part number
    """
    if not module.has_trait(F.has_descriptive_properties):
        raise PickError("Module does not have any descriptive properties", module)
    if "LCSC" not in module.get_trait(F.has_descriptive_properties).get_properties():
        raise PickError("Module does not have an LCSC part number", module)

    def get_lcsc_pn(module: Module) -> int:
        pn = module.get_trait(F.has_descriptive_properties).get_properties()["LCSC"]
        match = re.match(r"C(\d+)", pn)
        if match is None:
            raise PickError(f"Invalid LCSC part number {pn}", module)
        return int(match[1])

    lcsc_pn = get_lcsc_pn(module)
    parts = client.fetch_parts("find_by_lcsc", {"lcsc": lcsc_pn})

    # TODO: pass through errors from API
    match parts:
        case []:
            raise PickError(
                f"Could not find part with LCSC part number {lcsc_pn}", module
            )
        case [part]:
            if part.stock < qty:
                raise PickError(
                    f"Part with LCSC part number {lcsc_pn} has insufficient stock",
                    module,
                )
            part.attach(module, [])
        case _:
            raise PickError(
                f"Found no exact match for LCSC part number {lcsc_pn}", module
            )


def find_manufacturer_part(module: Module):
    """
    Find a part by manufacturer and manufacturer part number
    """
    if not module.has_trait(F.has_descriptive_properties):
        raise PickError("Module does not have any descriptive properties", module)

    properties = module.get_trait(F.has_descriptive_properties).get_properties()

    if DescriptiveProperties.manufacturer not in properties:
        raise PickError("Module does not have a manufacturer", module)

    if DescriptiveProperties.partno not in properties:
        raise PickError("Module does not have a manufacturer part number", module)

    manufacturer = properties[DescriptiveProperties.manufacturer]
    partno = properties[DescriptiveProperties.partno]

    parts = client.fetch_parts(
        "find_by_manufacturer_part",
        {"manufacturer_name": manufacturer, "mfr": partno, "qty": qty},
    )

    if not parts:
        raise PickError(
            f"Could not find part with manufacturer part number {partno}", module
        )

    for part in parts:
        try:
            part.attach(module, [])
            return
        except ValueError as e:
            logger.warning(f"Failed to attach component: {e}")
            continue

    return PickError(
        f"Could not attach any part with manufacturer part number {partno}", module
    )


def _filter_by_module_params_and_attach(
    cmp: Module, component_type: Type[Module], parts: list[Component]
):
    """
    Find a component with matching parameters
    """
    mapping = _MAPPINGS_BY_TYPE[component_type]
    parts = [part for part in parts if check_compatible_parameters(cmp, part, mapping)]

    if not try_attach(cmp, parts, mapping, qty):
        raise PickError(
            "No components found that match the parameters and that can be attached",
            cmp,
        )


def find_resistor(cmp: Module):
    """
    Find a resistor with matching parameters
    """
    if not isinstance(cmp, F.Resistor):
        raise PickError("Module is not a resistor", cmp)

    parts = client.fetch_parts(
        "find_resistors",
        {
            "resistances": generate_si_values(
                cmp.PARAMs.resistance, "Ω", E_SERIES_VALUES.E96
            ),
            "footprint_candidates": get_footprint_candidates(cmp),
            "qty": qty,
        },
    )

    _filter_by_module_params_and_attach(cmp, F.Resistor, parts)


def find_capacitor(cmp: Module):
    """
    Find a capacitor with matching parameters
    """
    if not isinstance(cmp, F.Capacitor):
        raise PickError("Module is not a capacitor", cmp)

    parts = client.fetch_parts(
        "find_capacitors",
        {
            "capacitances": generate_si_values(
                cmp.PARAMs.capacitance, "F", E_SERIES_VALUES.E6
            ),
            "footprint_candidates": get_footprint_candidates(cmp),
            "qty": qty,
        },
    )

    _filter_by_module_params_and_attach(cmp, F.Capacitor, parts)


def find_inductor(cmp: Module):
    """
    Find an inductor with matching parameters
    """
    if not isinstance(cmp, F.Inductor):
        raise PickError("Module is not an inductor", cmp)

    parts = client.fetch_parts(
        "find_inductors",
        {
            "inductances": generate_si_values(
                cmp.PARAMs.inductance, "H", E_SERIES_VALUES.E24
            ),
            "footprint_candidates": get_footprint_candidates(cmp),
            "qty": qty,
        },
    )

    _filter_by_module_params_and_attach(cmp, F.Inductor, parts)


def find_tvs(cmp: Module):
    """
    Find a TVS diode with matching parameters
    """
    if not isinstance(cmp, F.TVS):
        raise PickError("Module is not a TVS diode", cmp)

    parts = client.fetch_parts(
        "find_tvs",
        {
            "footprint_candidates": get_footprint_candidates(cmp),
            "qty": qty,
        },
    )

    _filter_by_module_params_and_attach(cmp, F.TVS, parts)


def find_diode(cmp: Module):
    """
    Find a diode with matching parameters
    """
    if not isinstance(cmp, F.Diode):
        raise PickError("Module is not a diode", cmp)

    parts = client.fetch_parts(
        "find_diodes",
        {
            "footprint_candidates": get_footprint_candidates(cmp),
            "qty": qty,
        },
    )

    _filter_by_module_params_and_attach(cmp, F.Diode, parts)


def find_led(cmp: Module):
    """
    Find an LED with matching parameters
    """
    if not isinstance(cmp, F.LED):
        raise PickError("Module is not an LED", cmp)

    parts = client.fetch_parts(
        "find_leds",
        {
            "footprint_candidates": get_footprint_candidates(cmp),
            "qty": qty,
        },
    )

    _filter_by_module_params_and_attach(cmp, F.LED, parts)


def find_mosfet(cmp: Module):
    """
    Find a MOSFET with matching parameters
    """

    if not isinstance(cmp, F.MOSFET):
        raise PickError("Module is not a MOSFET", cmp)

    parts = client.fetch_parts(
        "find_mosfets",
        {
            "footprint_candidates": get_footprint_candidates(cmp),
            "qty": qty,
        },
    )

    _filter_by_module_params_and_attach(cmp, F.MOSFET, parts)


def find_ldo(cmp: Module):
    """
    Find an LDO with matching parameters
    """

    if not isinstance(cmp, F.LDO):
        raise PickError("Module is not a LDO", cmp)

    parts = client.fetch_parts(
        "find_ldos",
        {
            "footprint_candidates": get_footprint_candidates(cmp),
            "qty": qty,
        },
    )

    _filter_by_module_params_and_attach(cmp, F.LDO, parts)


TYPE_SPECIFIC_LOOKUP = {
    F.Resistor: find_resistor,
    F.Capacitor: find_capacitor,
    F.Inductor: find_inductor,
    F.TVS: find_tvs,
    F.LED: find_led,
    F.Diode: find_diode,
    F.MOSFET: find_mosfet,
    F.LDO: find_ldo,
}
