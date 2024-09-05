# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging

import faebryk.library._F as F  # noqa: F401
from faebryk.libs.library import L  # noqa: F401
from faebryk.libs.units import P  # noqa: F401

logger = logging.getLogger(__name__)


class DE9RS232Connector(F.DE9Connector):
    """
    Standard RS232 bus on DE-9 connector
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    rs232: F.RS232
    gnd: F.Electrical
    shield: F.Electrical

    # ----------------------------------------
    #                 traits
    # ----------------------------------------
    @L.rt_field
    def can_attach_to_footprint(self):
        pinmap = {f"{i}": ei for i, ei in enumerate(self.unnamed)}
        pinmap.update({"10": self.shield})
        return F.can_attach_to_footprint_via_pinmap(pinmap)

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        self.rs232.tx.signal.connect(self.unnamed[3])
        self.rs232.rx.signal.connect(self.unnamed[2])
        self.rs232.dtr.signal.connect(self.unnamed[4])
        self.rs232.dcd.signal.connect(self.unnamed[1])
        self.rs232.dsr.signal.connect(self.unnamed[6])
        self.rs232.ri.signal.connect(self.unnamed[9])
        self.rs232.rts.signal.connect(self.unnamed[7])
        self.rs232.cts.signal.connect(self.unnamed[8])

        self.gnd.connect(self.unnamed[5])

        # ------------------------------------
        #          parametrization
        # ------------------------------------
