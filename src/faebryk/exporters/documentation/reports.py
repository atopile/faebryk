# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

"""
This file contains BOM generation utilities.
"""

import logging

from rich.console import Console
from rich.table import Table

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.picker.picker import DescriptiveProperties

logger = logging.getLogger(__name__)

# At module level
REQUIRED_TRAITS = (F.has_designator, F.has_footprint, F.has_descriptive_properties)

BOM_COLUMNS = [
    ("Name", "white"),
    ("Designator", "cyan"),
    ("Footprint", "green"),
    ("LCSC", "yellow"),
    ("Manufacturer PN", "magenta"),
]


def print_bom(root_module: Module) -> None:
    """Print a Bill of Materials table for the given root module.

    Generates a rich-formatted table containing component information including
    names, designators, footprints, and part numbers. Only processes components
    that have designator, footprint, and descriptive properties traits.

    Args:
        root_module: The root module containing the components to list in the BOM

    Required component traits:
        - has_designator
        - has_footprint
        - has_descriptive_properties
    """
    console = Console()
    table = Table(title="BOM")

    # Simplify column addition
    for column_name, style in BOM_COLUMNS:
        table.add_column(column_name, style=style)

    components = root_module.get_children_modules(types=(Module,))

    for comp in components:
        # Only process components that have required traits
        if not all(
            [
                comp.has_trait(F.has_designator),
                comp.has_trait(F.has_footprint),
                comp.has_trait(F.has_descriptive_properties),
            ]
        ):
            continue

        # Get component name
        comp_name = comp.get_name()

        # Get designator
        designator = comp.get_trait(F.has_designator).get_designator()

        # Get footprint
        footprint = comp.get_trait(F.has_footprint).get_footprint()
        footprint_name = (
            footprint.get_trait(F.has_kicad_footprint).get_kicad_footprint_name()
            if footprint.has_trait(F.has_kicad_footprint)
            else str(footprint)
        )

        # Get part numbers
        properties = comp.get_trait(F.has_descriptive_properties).get_properties()
        mfr_pn = properties.get(DescriptiveProperties.partno, "N/A")
        lcsc_pn = properties.get("LCSC", "N/A")

        # Add row to table
        table.add_row(comp_name, designator, footprint_name, lcsc_pn, mfr_pn)

    console.print(table)
