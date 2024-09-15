# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.core.module import Module
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class DE9RS232Connector(Module):
    """
    Standard RS232 bus on DE-9 connector
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    connector: F.DE9Connector
    rs232: F.RS232

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    @L.rt_field
    def can_attach_to_footprint(self):
        pinmap = {f"{i+1}": ei for i, ei in enumerate(self.connector.contact)}
        pinmap.update({"10": self.connector.shield})
        return F.can_attach_to_footprint_via_pinmap(pinmap)

    @L.rt_field
    def single_electric_reference(self):
        return F.has_single_electric_reference_defined(
            F.ElectricLogic.connect_all_module_references(self)
        )

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        self.rs232.tx.signal.connect(self.connector.contact[2])
        self.rs232.rx.signal.connect(self.connector.contact[1])
        self.rs232.dtr.signal.connect(self.connector.contact[3])
        self.rs232.dcd.signal.connect(self.connector.contact[0])
        self.rs232.dsr.signal.connect(self.connector.contact[5])
        self.rs232.ri.signal.connect(self.connector.contact[8])
        self.rs232.rts.signal.connect(self.connector.contact[6])
        self.rs232.cts.signal.connect(self.connector.contact[7])

        self.rs232.get_trait(
            F.has_single_electric_reference
        ).get_reference().lv.connect(self.connector.contact[4])

        # ------------------------------------
        #          parametrization
        # ------------------------------------
