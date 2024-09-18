from pathlib import Path

import pytest

from faebryk.core.module import Module
from faebryk.exporters.schematic.kicad.transformer import SchTransformer
from faebryk.libs.kicad.fileformats_sch import C_kicad_sch_file
from faebryk.libs.util import find


@pytest.fixture
def test_dir():
    return find(
        Path(__file__).parents,
        lambda p: p.name == "test" and (p / "common/resources").is_dir(),
    )


@pytest.fixture
def fp_lib_path_path(test_dir: Path):
    return test_dir / "common/resources/fp-lib-table"


@pytest.fixture
def sch(test_dir: Path):
    return C_kicad_sch_file.loads(test_dir / "common/resources/test.kicad_sch").kicad_sch


@pytest.fixture
def transformer(sch: C_kicad_sch_file.C_kicad_sch, fp_lib_path_path: Path):
    app = Module()
    return SchTransformer(sch, app.get_graph(), app, fp_lib_path_path)


def test_wire_transformer(transformer: SchTransformer):
    start_wire_count = len(transformer.sch.wires)

    transformer.insert_wire([
        (0, 0),
        (1, 0),
        (1, 1),
    ])

    # 2 because we have 3 waypoints
    assert len(transformer.sch.wires) == start_wire_count + 2
    assert [(pt.x, pt.y) for pt in  transformer.sch.wires[-2].pts.xys] == [
        (0, 0),
        (1, 0),
    ]
