# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from itertools import chain

import pytest

import faebryk.library._F as F
from faebryk.core.graphinterface import GraphInterface
from faebryk.core.link import LinkDirectConditional, LinkDirectDerived
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.libs.app.erc import ERCPowerSourcesShortedError, simple_erc
from faebryk.libs.library import L
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


def test_up_connect():
    class UARTBuffer(Module):
        bus_in: F.UART_Base
        bus_out: F.UART_Base

        def __preinit__(self) -> None:
            self.bus_in.rx.signal.connect(self.bus_out.rx.signal)
            self.bus_in.tx.signal.connect(self.bus_out.tx.signal)
            self.bus_in.rx.reference.connect(self.bus_out.rx.reference)

    app = UARTBuffer()

    assert app.bus_in.rx.signal.is_connected_to(app.bus_out.rx.signal)
    assert app.bus_in.rx.reference.is_connected_to(app.bus_out.rx.reference)
    assert app.bus_in.rx.is_connected_to(app.bus_out.rx)
    assert app.bus_in.tx.is_connected_to(app.bus_out.tx)
    assert app.bus_in.is_connected_to(app.bus_out)


def test_chains():
    mifs = times(3, ModuleInterface)
    mifs[0].connect(mifs[1])
    mifs[1].connect(mifs[2])
    assert mifs[0].is_connected_to(mifs[2])

    mifs = times(3, ModuleInterface)
    mifs[0].connect_shallow(mifs[1])
    mifs[1].connect_shallow(mifs[2])
    assert mifs[0].is_connected_to(mifs[2])

    mifs = times(3, ModuleInterface)
    mifs[0].connect_shallow(mifs[1])
    mifs[1].connect(mifs[2])
    assert mifs[0].is_connected_to(mifs[2])

    # Test hierarchy down filter & chain resolution
    mifs = times(3, F.ElectricLogic)
    mifs[0].connect_shallow(mifs[1])
    mifs[1].connect(mifs[2])
    assert mifs[0].is_connected_to(mifs[2])

    assert mifs[1].signal.is_connected_to(mifs[2].signal)
    assert mifs[1].reference.is_connected_to(mifs[2].reference)
    assert not mifs[0].signal.is_connected_to(mifs[1].signal)
    assert not mifs[0].reference.is_connected_to(mifs[1].reference)
    assert not mifs[0].signal.is_connected_to(mifs[2].signal)
    assert not mifs[0].reference.is_connected_to(mifs[2].reference)

    # Test duplicate resolution
    mifs[0].signal.connect(mifs[1].signal)
    mifs[0].reference.connect(mifs[1].reference)
    assert mifs[0].is_connected_to(mifs[1])
    assert mifs[0].is_connected_to(mifs[2])


def test_bridge():
    """
    Test the bridge connection between two UART interfaces through a buffer:

    ```
    U1 ---> _________B________ ---> U2
     TX          IL ===> OL          TX
      S -->  I -> S       S -> O -->  S
      R --------  R ----- R --------  R
    ```

    Where:
    - U1, U2: UART interfaces
    - B: Buffer
    - TX: Transmit
    - S: Signal
    - R: Reference
    - I: Input
    - O: Output
    - IL: Input Logic
    - OL: Output Logic
    """

    class Buffer(Module):
        ins = L.list_field(2, F.Electrical)
        outs = L.list_field(2, F.Electrical)

        ins_l = L.list_field(2, F.ElectricLogic)
        outs_l = L.list_field(2, F.ElectricLogic)

        def __preinit__(self) -> None:
            assert (
                self.ins_l[0].reference
                is self.ins_l[0].single_electric_reference.get_reference()
            )

            for el, lo in chain(
                zip(self.ins, self.ins_l),
                zip(self.outs, self.outs_l),
            ):
                lo.signal.connect(el)

            for l1, l2 in zip(self.ins_l, self.outs_l):
                l1.connect_shallow(l2)

        @L.rt_field
        def single_electric_reference(self):
            return F.has_single_electric_reference_defined(
                F.ElectricLogic.connect_all_module_references(self)
            )

    class UARTBuffer(Module):
        buf: Buffer
        bus_in: F.UART_Base
        bus_out: F.UART_Base

        def __preinit__(self) -> None:
            bus_i = self.bus_in
            bus_o = self.bus_out
            buf = self.buf

            bus_i.tx.signal.connect(buf.ins[0])
            bus_i.rx.signal.connect(buf.ins[1])
            bus_o.tx.signal.connect(buf.outs[0])
            bus_o.rx.signal.connect(buf.outs[1])

        @L.rt_field
        def single_electric_reference(self):
            return F.has_single_electric_reference_defined(
                F.ElectricLogic.connect_all_module_references(self)
            )

    app = UARTBuffer()

    bus_i = app.bus_in
    bus_o = app.bus_out
    buf = app.buf

    # Check that the two buffer sides are not connected electrically
    assert not list(buf.ins[0].get_paths_to(buf.outs[0]))
    assert not buf.ins[1].is_connected_to(buf.outs[1])
    assert not bus_i.rx.signal.is_connected_to(bus_o.rx.signal)
    assert not bus_i.tx.signal.is_connected_to(bus_o.tx.signal)

    # direct connect
    assert bus_i.tx.signal.is_connected_to(buf.ins[0])
    assert bus_i.rx.signal.is_connected_to(buf.ins[1])
    assert bus_o.tx.signal.is_connected_to(buf.outs[0])
    assert bus_o.rx.signal.is_connected_to(buf.outs[1])

    # connect through trait
    assert (
        buf.ins_l[0].single_electric_reference.get_reference() is buf.ins_l[0].reference
    )
    assert buf.ins_l[0].reference.is_connected_to(buf.outs_l[0].reference)
    assert buf.outs_l[1].reference.is_connected_to(buf.ins_l[0].reference)
    assert bus_i.rx.reference.is_connected_to(bus_o.rx.reference)

    # connect through up
    assert bus_i.tx.is_connected_to(buf.ins_l[0])
    assert bus_o.tx.is_connected_to(buf.outs_l[0])

    # connect shallow
    assert buf.ins_l[0].is_connected_to(buf.outs_l[0])

    # Check that the two buffer sides are connected logically
    assert bus_i.tx.is_connected_to(bus_o.tx)
    assert bus_i.rx.is_connected_to(bus_o.rx)
    assert bus_i.is_connected_to(bus_o)


def test_specialize():
    class Specialized(ModuleInterface): ...

    class DoubleSpecialized(Specialized): ...

    # general connection -> specialized connection
    mifs = times(3, ModuleInterface)
    mifs_special = times(3, Specialized)

    mifs[0].connect(mifs[1])
    mifs[1].connect(mifs[2])

    mifs[0].specialize(mifs_special[0])
    mifs[2].specialize(mifs_special[2])

    assert mifs_special[0].is_connected_to(mifs_special[2])

    # specialized connection -> general connection
    mifs = times(3, ModuleInterface)
    mifs_special = times(3, Specialized)

    mifs_special[0].connect(mifs_special[1])
    mifs_special[1].connect(mifs_special[2])

    mifs[0].specialize(mifs_special[0])
    mifs[2].specialize(mifs_special[2])

    assert mifs[0].is_connected_to(mifs[2])

    # test special link
    class _Link(LinkDirectConditional):
        def is_filtered(self, path: list[GraphInterface]):
            return LinkDirectConditional.FilterResult.PASS

    mifs = times(3, ModuleInterface)
    mifs_special = times(3, Specialized)

    mifs[0].connect(mifs[1], linkcls=_Link)
    mifs[1].connect(mifs[2])

    mifs[0].specialize(mifs_special[0])
    mifs[2].specialize(mifs_special[2])

    assert mifs_special[0].is_connected_to(mifs_special[2])

    # double specialization with gap
    mifs = times(2, ModuleInterface)
    mifs_special = times(1, Specialized)
    mifs_double_special = times(2, DoubleSpecialized)

    mifs[0].connect(mifs[1])
    mifs[0].specialize(mifs_special[0])
    mifs_special[0].specialize(mifs_double_special[0])
    mifs[1].specialize(mifs_double_special[1])

    assert mifs_double_special[0].is_connected_to(mifs_double_special[1])

    mifs = times(2, ModuleInterface)
    mifs_special = times(1, Specialized)
    mifs_double_special = times(2, DoubleSpecialized)

    mifs_double_special[0].connect(mifs_double_special[1])
    mifs[0].specialize(mifs_special[0])
    mifs_special[0].specialize(mifs_double_special[0])
    mifs[1].specialize(mifs_double_special[1])

    assert mifs[0].is_connected_to(mifs[1])


def test_specialize_module():
    battery = F.Battery()
    power = F.ElectricPower()

    battery.power.connect(power)
    buttoncell = battery.specialize(F.ButtonCell())

    assert buttoncell.power.is_connected_to(battery.power)
    assert power.is_connected_to(buttoncell.power)


def test_isolated_connect():
    x1 = F.ElectricLogic()
    x2 = F.ElectricLogic()
    x1.connect(x2, linkcls=F.ElectricLogic.LinkIsolatedReference)

    assert x1.is_connected_to(x2)
    assert x1.signal.is_connected_to(x2.signal)

    assert not x1.reference.is_connected_to(x2.reference)
    assert not x1.reference.hv.is_connected_to(x2.reference.hv)

    y1 = F.ElectricPower()
    y2 = F.ElectricPower()

    y1.make_source()
    y2.make_source()

    with pytest.raises(ERCPowerSourcesShortedError):
        y1.connect(y2)
        simple_erc(y1.get_graph())

    ldo1 = F.LDO()
    ldo2 = F.LDO()

    with pytest.raises(ERCPowerSourcesShortedError):
        ldo1.power_out.connect(ldo2.power_out)
        simple_erc(ldo1.get_graph())

    a1 = F.I2C()
    b1 = F.I2C()

    a1.connect(b1, linkcls=F.ElectricLogic.LinkIsolatedReference)
    assert a1.is_connected_to(b1)
    assert a1.scl.signal.is_connected_to(b1.scl.signal)
    assert a1.sda.signal.is_connected_to(b1.sda.signal)

    assert not a1.scl.reference.is_connected_to(b1.scl.reference)
    assert not a1.sda.reference.is_connected_to(b1.sda.reference)


def test_direct_implied_paths():
    powers = times(2, F.ElectricPower)

    # direct implied
    powers[0].connect(powers[1])

    assert powers[1].hv in powers[0].hv.get_connected()

    path = powers[0].hv.is_connected_to(powers[1].hv)
    assert path
    assert len(path) == 4
    assert isinstance(path[1].is_connected_to(path[2]), LinkDirectDerived)


def test_children_implied_paths():
    powers = times(3, F.ElectricPower)

    # children implied
    powers[0].connect(powers[1])
    powers[1].hv.connect(powers[2].hv)
    powers[1].lv.connect(powers[2].lv)

    assert powers[2] in powers[0].get_connected()

    paths = list(powers[0].get_paths_to(powers[2]))
    assert paths
    assert len(paths[0]) == 4
    assert isinstance(paths[0][1].is_connected_to(paths[0][2]), LinkDirectDerived)


def test_shallow_implied_paths():
    powers = times(4, F.ElectricPower)

    # shallow implied
    powers[0].connect(powers[1])
    powers[1].hv.connect(powers[2].hv)
    powers[1].lv.connect(powers[2].lv)
    powers[2].connect_shallow(powers[3])

    assert powers[3] in powers[0].get_connected()

    assert not powers[0].hv.is_connected_to(powers[3].hv)
