# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
import unittest
from itertools import chain

from faebryk.core.core import logger as core_logger
from faebryk.core.link import LinkDirect, LinkDirectShallow, _TLinkDirectShallow
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.util import specialize_interface
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.has_single_electric_reference_defined import (
    has_single_electric_reference_defined,
)
from faebryk.library.UART_Base import UART_Base
from faebryk.libs.util import print_stack, times

logger = logging.getLogger(__name__)
core_logger.setLevel(logger.getEffectiveLevel())


class TestHierarchy(unittest.TestCase):
    def test_up_connect(self):
        class UARTBuffer(Module):
            def __init__(self) -> None:
                super().__init__()

                class _IFs(super().IFS()):
                    bus_in = UART_Base()
                    bus_out = UART_Base()

                self.IFs = _IFs(self)

                bus_in = self.bus_in
                bus_out = self.bus_out

                bus_in.rx.signal.connect(bus_out.rx.signal)
                bus_in.tx.signal.connect(bus_out.tx.signal)
                bus_in.rx.reference.connect(bus_out.rx.reference)

        app = UARTBuffer()

        self.assertTrue(app.bus_in.rx.is_connected_to(app.bus_out.rx))
        self.assertTrue(app.bus_in.tx.is_connected_to(app.bus_out.tx))
        self.assertTrue(app.bus_in.is_connected_to(app.bus_out))

    def test_chains(self):
        mifs = times(3, ModuleInterface)
        mifs[0].connect(mifs[1])
        mifs[1].connect(mifs[2])
        self.assertTrue(mifs[0].is_connected_to(mifs[2]))

        mifs = times(3, ModuleInterface)
        mifs[0].connect_shallow(mifs[1])
        mifs[1].connect_shallow(mifs[2])
        self.assertTrue(mifs[0].is_connected_to(mifs[2]))
        self.assertIsInstance(mifs[0].is_connected_to(mifs[2]), _TLinkDirectShallow)

        mifs = times(3, ModuleInterface)
        mifs[0].connect_shallow(mifs[1])
        mifs[1].connect(mifs[2])
        self.assertTrue(mifs[0].is_connected_to(mifs[2]))
        self.assertIsInstance(mifs[0].is_connected_to(mifs[2]), _TLinkDirectShallow)

        # Test hierarchy down filter & chain resolution
        mifs = times(3, ElectricLogic)
        mifs[0].connect_shallow(mifs[1])
        mifs[1].connect(mifs[2])
        self.assertTrue(mifs[0].is_connected_to(mifs[2]))
        self.assertIsInstance(mifs[0].is_connected_to(mifs[2]), _TLinkDirectShallow)

        self.assertTrue(mifs[1].signal.is_connected_to(mifs[2].signal))
        self.assertTrue(mifs[1].reference.is_connected_to(mifs[2].reference))
        self.assertFalse(mifs[0].signal.is_connected_to(mifs[1].signal))
        self.assertFalse(mifs[0].reference.is_connected_to(mifs[1].reference))
        self.assertFalse(mifs[0].signal.is_connected_to(mifs[2].signal))
        self.assertFalse(mifs[0].reference.is_connected_to(mifs[2].reference))

        # Test duplicate resolution
        mifs[0].signal.connect(mifs[1].signal)
        mifs[0].reference.connect(mifs[1].reference)
        self.assertIsInstance(mifs[0].is_connected_to(mifs[1]), LinkDirect)
        self.assertIsInstance(mifs[0].is_connected_to(mifs[2]), LinkDirect)

    def test_bridge(self):
        class Buffer(Module):
            def __init__(self) -> None:
                super().__init__()

                class _IFs(super().IFS()):
                    ins = times(2, Electrical)
                    outs = times(2, Electrical)

                    ins_l = times(2, ElectricLogic)
                    outs_l = times(2, ElectricLogic)

                self.IFs = _IFs(self)

                ref = ElectricLogic.connect_all_module_references(self)
                self.add_trait(has_single_electric_reference_defined(ref))

                for el, lo in chain(
                    zip(self.ins, self.ins_l),
                    zip(self.outs, self.outs_l),
                ):
                    lo.signal.connect(el)

                for l1, l2 in zip(self.ins_l, self.outs_l):
                    l1.connect_shallow(l2)

        class UARTBuffer(Module):
            def __init__(self) -> None:
                super().__init__()

                class _NODES(super().NODES()):
                    buf = Buffer()

                class _IFs(super().IFS()):
                    bus_in = UART_Base()
                    bus_out = UART_Base()

                self.IFs = _IFs(self)
                self.NODEs = _NODES(self)

                ElectricLogic.connect_all_module_references(self)

                bus1 = self.bus_in
                bus2 = self.bus_out
                buf = self.buf

                bus1.tx.signal.connect(buf.ins[0])
                bus1.rx.signal.connect(buf.ins[1])
                bus2.tx.signal.connect(buf.outs[0])
                bus2.rx.signal.connect(buf.outs[1])

        import faebryk.core.core as c

        # Enable to see the stack trace of invalid connections
        # c.LINK_TB = True
        app = UARTBuffer()

        def _assert_no_link(mif1, mif2):
            link = mif1.is_connected_to(mif2)
            err = ""
            if link and c.LINK_TB:
                err = "\n" + print_stack(link.tb)
            self.assertFalse(link, err)

        bus1 = app.bus_in
        bus2 = app.bus_out
        buf = app.buf

        # Check that the two buffer sides are not connected electrically
        _assert_no_link(buf.ins[0], buf.outs[0])
        _assert_no_link(buf.ins[1], buf.outs[1])
        _assert_no_link(bus1.rx.signal, bus2.rx.signal)
        _assert_no_link(bus1.tx.signal, bus2.tx.signal)

        # Check that the two buffer sides are connected logically
        self.assertTrue(bus1.rx.is_connected_to(bus2.rx))
        self.assertTrue(bus1.tx.is_connected_to(bus2.tx))
        self.assertTrue(bus1.is_connected_to(bus2))

    def test_specialize(self):
        class Specialized(ModuleInterface): ...

        # general connection -> specialized connection
        mifs = times(3, ModuleInterface)
        mifs_special = times(3, Specialized)

        mifs[0].connect(mifs[1])
        mifs[1].connect(mifs[2])

        specialize_interface(mifs[0], mifs_special[0])
        specialize_interface(mifs[2], mifs_special[2])

        self.assertTrue(mifs_special[0].is_connected_to(mifs_special[2]))

        # specialized connection -> general connection
        mifs = times(3, ModuleInterface)
        mifs_special = times(3, Specialized)

        mifs_special[0].connect(mifs_special[1])
        mifs_special[1].connect(mifs_special[2])

        specialize_interface(mifs[0], mifs_special[0])
        specialize_interface(mifs[2], mifs_special[2])

        self.assertTrue(mifs[0].is_connected_to(mifs[2]))

        # test special link
        class _Link(LinkDirectShallow(lambda link, gif: True)): ...

        mifs = times(3, ModuleInterface)
        mifs_special = times(3, Specialized)

        mifs[0].connect(mifs[1], linkcls=_Link)
        mifs[1].connect(mifs[2])

        specialize_interface(mifs[0], mifs_special[0])
        specialize_interface(mifs[2], mifs_special[2])

        self.assertIsInstance(mifs_special[0].is_connected_to(mifs_special[2]), _Link)


if __name__ == "__main__":
    unittest.main()
