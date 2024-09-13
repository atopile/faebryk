# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
import pprint
import re
import subprocess
from abc import abstractmethod
from dataclasses import fields
from enum import Enum, auto
from itertools import pairwise
from typing import Any, Callable, Iterable, List, Optional, Sequence, TypeVar

import numpy as np
from shapely import Polygon

import faebryk.library._F as F
from faebryk.core.graphinterface import Graph
from faebryk.core.module import Module
from faebryk.core.moduleinterface import ModuleInterface
from faebryk.core.node import Node
from faebryk.libs.geometry.basic import Geometry
from faebryk.libs.kicad.fileformats import (
    gen_uuid as _gen_uuid,
)
from faebryk.libs.kicad.fileformats_common import C_effects, C_wh, C_xy, C_xyr
from faebryk.libs.kicad.fileformats_sch import (
    UUID,
    C_arc,
    C_circle,
    C_kicad_sch_file,
    C_polyline,
    C_rect,
    C_stroke,
)
from faebryk.libs.sexp.dataclass_sexp import dataclass_dfs
from faebryk.libs.util import KeyErrorNotFound, cast_assert, find, get_key

logger = logging.getLogger(__name__)


SCH = C_kicad_sch_file.C_kicad_sch

Geom = C_polyline | C_arc | C_rect | C_circle
Symbol = SCH.C_lib_symbols.C_symbol.C_symbol
Font = C_effects.C_font

Point = Geometry.Point
Point2D = Geometry.Point2D

Justify = C_effects.C_justify.E_justify
Alignment = tuple[Justify, Justify, Justify]
Alignment_Default = (Justify.center_horizontal, Justify.center_vertical, Justify.normal)


def gen_uuid(mark: str = "") -> UUID:
    return _gen_uuid(mark)


def is_marked(uuid: UUID, mark: str):
    suffix = mark.encode().hex()
    return uuid.replace("-", "").endswith(suffix)


T = TypeVar("T", C_xy, C_xyr)
T2 = TypeVar("T2", C_xy, C_xyr)


def round_coord(coord: T, ndigits=2) -> T:
    fs = fields(coord)
    return type(coord)(
        **{f.name: round(getattr(coord, f.name), ndigits=ndigits) for f in fs}
    )


def round_line(line: tuple[Point2D, Point2D], ndigits=2):
    return per_point(line, lambda c: round_point(c, ndigits))


P = TypeVar("P", Point, Point2D)


def round_point(point: P, ndigits=2) -> P:
    return tuple(round(c, ndigits) for c in point)  # type: ignore


def coord_to_point(coord: T) -> Point:
    return tuple(getattr(coord, f.name) for f in fields(coord))


def coord_to_point2d(coord: T) -> Point2D:
    return coord.x, coord.y


def point2d_to_coord(point: Point2D) -> C_xy:
    return C_xy(x=point[0], y=point[1])


def abs_pos(origin: T, vector: T2):
    return Geometry.abs_pos(coord_to_point(origin), coord_to_point(vector))


def abs_pos2d(origin: T, vector: T2) -> Point2D:
    return Geometry.as2d(
        Geometry.abs_pos(coord_to_point2d(origin), coord_to_point2d(vector))
    )


def per_point[R](
    line: tuple[Point2D, Point2D], func: Callable[[Point2D], R]
) -> tuple[R, R]:
    return func(line[0]), func(line[1])


def get_all_geo_containers(obj: SCH | Symbol) -> list[Sequence[Geom]]:
    if isinstance(obj, SCH):
        return [
            obj.junctions,
            obj.wires,
            obj.texts,
            obj.symbols,
            obj.sheets,
            obj.global_labels,
            obj.no_connects,
            obj.buss,
            obj.labels,
            obj.bus_entrys,
        ]

    elif isinstance(obj, Symbol):
        return [obj.pins]

    raise TypeError()


def get_all_geos(obj: SCH | Symbol) -> list[Geom]:
    candidates = get_all_geo_containers(obj)

    return [geo for geos in candidates for geo in geos]


# TODO: consider common transformer base
class SCH_Transformer:
    class has_linked_kicad_symbol(Module.TraitT):
        """
        Module has symbol (which has kicad symbol) and that symbol
        is found in the current PCB file.
        """

        @abstractmethod
        def get_transformer(self) -> "SCH_Transformer": ...

        @abstractmethod
        def get_fp(self) -> Symbol: ...

    class has_linked_kicad_symbol_defined(has_linked_kicad_symbol.impl()):
        def __init__(self, fp: Symbol, transformer: "SCH_Transformer") -> None:
            super().__init__()
            self.fp = fp
            self.transformer = transformer

        def get_fp(self):
            return self.fp

        def get_transformer(self):
            return self.transformer

    # class has_linked_kicad_pad(ModuleInterface.TraitT):
    #     @abstractmethod
    #     def get_pad(self) -> tuple[Symbol, list[Pad]]: ...

    #     @abstractmethod
    #     def get_transformer(self) -> "SCH_Transformer": ...

    # class has_linked_kicad_pad_defined(has_linked_kicad_pad.impl()):
    #     def __init__(
    #         self, fp: Symbol, pad: list[Pad], transformer: "SCH_Transformer"
    #     ) -> None:
    #         super().__init__()
    #         self.fp = fp
    #         self.pad = pad
    #         self.transformer = transformer

    #     def get_pad(self):
    #         return self.fp, self.pad

    #     def get_transformer(self):
    #         return self.transformer

    def __init__(
        self, pcb: SCH, graph: Graph, app: Module, cleanup: bool = True
    ) -> None:
        self.sch = pcb
        self.graph = graph
        self.app = app

        self.dimensions = None

        FONT_SCALE = 8
        FONT = Font(
            size=C_wh(1 / FONT_SCALE, 1 / FONT_SCALE),
            thickness=0.15 / FONT_SCALE,
        )
        self.font = FONT

        self.cleanup()
        self.attach()

    def attach(self):
        """This function matches and binds symbols to their """
        symbols = {
            (f.propertys["Reference"].value, f.name): f for f in self.sch.symbols
        }
        for node, fpt in self.graph.nodes_with_trait(F.has_footprint):
            if not node.has_trait(F.has_overriden_name):
                continue
            g_fp = fpt.get_footprint()
            if not g_fp.has_trait(F.has_kicad_footprint):
                continue

            fp_ref = node.get_trait(F.has_overriden_name).get_name()
            fp_name = g_fp.get_trait(F.has_kicad_footprint).get_kicad_footprint()

            assert (
                fp_ref,
                fp_name,
            ) in symbols, (
                f"Footprint ({fp_ref=}, {fp_name=}) not found in footprints dictionary."
                f" Did you import the latest NETLIST into KiCad?"
            )
            fp = footprints[(fp_ref, fp_name)]

            g_fp.add(self.has_linked_kicad_footprint_defined(fp, self))
            node.add(self.has_linked_kicad_footprint_defined(fp, self))

            pin_names = g_fp.get_trait(F.has_kicad_footprint).get_pin_names()
            for fpad in g_fp.get_children(direct_only=True, types=ModuleInterface):
                pads = [
                    pad
                    for pad in fp.pads
                    if pad.name == pin_names[cast_assert(FPad, fpad)]
                ]
                fpad.add(SCH_Transformer.has_linked_kicad_pad_defined(fp, pads, self))

        attached = {
            n: t.get_fp()
            for n, t in self.graph.nodes_with_trait(
                SCH_Transformer.has_linked_kicad_symbol
            )
        }
        logger.debug(f"Attached: {pprint.pformat(attached)}")

    def cleanup(self):
        # delete faebryk objects in pcb

        # find all objects with path_len 2 (direct children of a list in pcb)
        candidates = [o for o in dataclass_dfs(self.sch) if len(o[1]) == 2]
        for obj, path, _ in candidates:
            if not self.is_marked(obj):
                continue

            # delete object by removing it from the container they are in
            holder = path[-1]
            if isinstance(holder, list):
                holder.remove(obj)
            elif isinstance(holder, dict):
                del holder[get_key(obj, holder)]

    @staticmethod
    def flipped[T](input_list: list[tuple[T, int]]) -> list[tuple[T, int]]:
        return [(x, (y + 180) % 360) for x, y in reversed(input_list)]

    @staticmethod
    def gen_uuid(mark: bool = False):
        return gen_uuid(mark="FBRK" if mark else "")

    @staticmethod
    def is_marked(obj) -> bool:
        if not hasattr(obj, "uuid"):
            return False
        return is_marked(obj.uuid, "FBRK")

    # Getter ---------------------------------------------------------------------------
    @staticmethod
    def get_fp(cmp: Node) -> Footprint:
        return cmp.get_trait(SCH_Transformer.has_linked_kicad_symbol).get_fp()

    def get_all_footprints(self) -> List[tuple[Module, Footprint]]:
        return [
            (cast_assert(Module, cmp), t.get_fp())
            for cmp, t in self.graph.nodes_with_trait(
                SCH_Transformer.has_linked_kicad_symbol
            )
        ]

    def get_net(self, net: FNet) -> Net:
        nets = {pcb_net.name: pcb_net for pcb_net in self.sch.nets}
        return nets[net.get_trait(F.has_overriden_name).get_name()]

    # TODO: make universal fp bbox getter (also take into account pads)
    def get_footprint_silkscreen_bbox(
        self, cmp: Node
    ) -> None | tuple[Point2D, Point2D]:
        fp = self.get_fp(cmp)
        silk_outline = [
            geo
            for geo in get_all_geos(fp)
            if geo.layer == ("F.SilkS" if fp.layer.startswith("F") else "B.SilkS")
        ]

        extremes = list[C_xy]()

        for geo in silk_outline:
            if isinstance(geo, C_line):
                extremes.extend([geo.start, geo.end])
            elif isinstance(geo, C_arc):
                # TODO: calculate extremes.extend([geo.start, geo.mid, geo.end])
                ...
            elif isinstance(geo, C_rect):
                extremes.extend([geo.start, geo.end])
            elif isinstance(geo, C_circle):
                # TODO: calculate extremes.extend([geo.center, geo.end])
                ...

        if not extremes:
            logger.warn(f"{cmp} with fp:{fp.name} has no silk outline")
            return None

        return Geometry.bbox([Point2D((point.x, point.y)) for point in extremes])

    def get_edge(self) -> list[Point2D]:
        def geo_to_lines(
            geo: Geom, fp: Footprint | None = None
        ) -> list[tuple[Point2D, Point2D]]:
            lines: list[tuple[Point2D, Point2D]] = []

            if isinstance(geo, GR_Line):
                lines = [(coord_to_point2d(geo.start), coord_to_point2d(geo.end))]
            elif isinstance(geo, Arc):
                arc = map(coord_to_point2d, (geo.start, geo.mid, geo.end))
                lines = Geometry.approximate_arc(*arc, resolution=10)
            elif isinstance(geo, Rect):
                rect = (coord_to_point2d(geo.start), coord_to_point2d(geo.end))

                c0 = (rect[0][0], rect[1][1])
                c1 = (rect[1][0], rect[0][1])

                l0 = (rect[0], c0)
                l1 = (rect[0], c1)
                l2 = (rect[1], c0)
                l3 = (rect[1], c1)

                lines = [l0, l1, l2, l3]
            else:
                raise NotImplementedError(f"Unsupported type {type(geo)}: {geo}")

            if fp:
                fpat = coord_to_point(fp.at)
                lines = [
                    per_point(
                        line,
                        lambda c: Geometry.as2d(Geometry.abs_pos(fpat, c)),
                    )
                    for line in lines
                ]

            return lines

        lines: list[tuple[Point2D, Point2D]] = [
            round_line(line)
            for sub_lines in [
                geo_to_lines(pcb_geo)
                for pcb_geo in get_all_geos(self.sch)
                if pcb_geo.layer == "Edge.Cuts"
            ]
            + [
                geo_to_lines(fp_geo, fp)
                for fp in self.sch.footprints
                for fp_geo in get_all_geos(fp)
                if fp_geo.layer == "Edge.Cuts"
            ]
            for line in sub_lines
        ]

        if not lines:
            return []

        from shapely import (
            LineString,
            get_geometry,
            get_num_geometries,
            polygonize_full,
        )

        polys, cut_edges, dangles, invalid_rings = polygonize_full(
            [LineString(line) for line in lines]
        )

        if get_num_geometries(cut_edges) != 0:
            raise Exception(f"EdgeCut: Cut edges: {cut_edges}")

        if get_num_geometries(dangles) != 0:
            raise Exception(f"EdgeCut: Dangling lines: {dangles}")

        if get_num_geometries(invalid_rings) != 0:
            raise Exception(f"EdgeCut: Invald rings: {invalid_rings}")

        if (n := get_num_geometries(polys)) != 1:
            if n == 0:
                logger.warning(f"EdgeCut: No closed polygons found in {lines}")
                assert False  # TODO remove
                return []
            raise Exception(f"EdgeCut: Ambiguous polygons {polys}")

        poly = get_geometry(polys, 0)
        assert isinstance(poly, Polygon)
        return list(poly.exterior.coords)

    @staticmethod
    def _get_pad(ffp: FFootprint, intf: F.Electrical):
        pin_map = ffp.get_trait(F.has_kicad_footprint).get_pin_names()
        pin_name = find(
            pin_map.items(),
            lambda pad_and_name: intf.is_connected_to(pad_and_name[0].net) is not None,
        )[1]

        fp = SCH_Transformer.get_fp(ffp)
        pad = find(fp.pads, lambda p: p.name == pin_name)

        return fp, pad

    @staticmethod
    def get_pad(intf: F.Electrical) -> tuple[Footprint, Pad, Node]:
        obj, ffp = FFootprint.get_footprint_of_parent(intf)
        fp, pad = SCH_Transformer._get_pad(ffp, intf)

        return fp, pad, obj

    @staticmethod
    def get_pad_pos_any(intf: F.Electrical) -> list[tuple[FPad, Point]]:
        try:
            fpads = FPad.find_pad_for_intf_with_parent_that_has_footprint(intf)
        except KeyErrorNotFound:
            # intf has no parent with footprint
            return []

        return [SCH_Transformer.get_fpad_pos(fpad) for fpad in fpads]

    @staticmethod
    def get_pad_pos(intf: F.Electrical) -> tuple[FPad, Point] | None:
        try:
            fpad = FPad.find_pad_for_intf_with_parent_that_has_footprint_unique(intf)
        except ValueError:
            return None

        return SCH_Transformer.get_fpad_pos(fpad)

    @staticmethod
    def get_fpad_pos(fpad: FPad):
        fp, pad = fpad.get_trait(SCH_Transformer.has_linked_kicad_pad).get_pad()
        if len(pad) > 1:
            raise NotImplementedError(
                f"Multiple same pads is not implemented: {fpad} {pad}"
            )
        pad = pad[0]

        point3d = abs_pos(fp.at, pad.at)

        transformer = fpad.get_trait(
            SCH_Transformer.has_linked_kicad_pad
        ).get_transformer()

        layers = transformer.get_copper_layers_pad(pad)
        if len(layers) != 1:
            layer = 0
        else:
            copper_layers = {
                layer: i for i, layer in enumerate(transformer.get_copper_layers())
            }
            layer = copper_layers[layers.pop()]

        return fpad, point3d[:3] + (layer,)

    def get_copper_layers(self):
        COPPER = re.compile(r"^.*\.Cu$")

        return {
            layer.name
            for layer in self.sch.layers
            if COPPER.match(layer.name) is not None
        }

    def get_copper_layers_pad(self, pad: Pad):
        COPPER = re.compile(r"^.*\.Cu$")

        all_layers = [layer.name for layer in self.sch.layers]

        def dewildcard(layer: str):
            if "*" not in layer:
                return {layer}
            pattern = re.compile(layer.replace(".", r"\.").replace("*", r".*"))
            return {
                global_layer
                for global_layer in all_layers
                if pattern.match(global_layer) is not None
            }

        layers = pad.layers
        dewildcarded_layers = {
            sub_layer for layer in layers for sub_layer in dewildcard(layer)
        }
        matching_layers = {
            layer for layer in dewildcarded_layers if COPPER.match(layer) is not None
        }

        return matching_layers

    def get_layer_id(self, layer: str) -> int:
        copper_layers = {layer: i for i, layer in enumerate(self.get_copper_layers())}
        return copper_layers[layer]

    def get_layer_name(self, layer_id: int) -> str:
        copper_layers = {i: layer for i, layer in enumerate(self.get_copper_layers())}
        return copper_layers[layer_id]

    # Insert ---------------------------------------------------------------------------
    @staticmethod
    def mark[R](node: R) -> R:
        if hasattr(node, "uuid"):
            node.uuid = SCH_Transformer.gen_uuid(mark=True)  # type: ignore

        return node

    def _get_list_field[R](self, node: R, prefix: str = "") -> list[R]:
        root = self.sch
        key = prefix + type(node).__name__.removeprefix("C_") + "s"

        assert hasattr(root, key)

        target = getattr(root, key)
        assert isinstance(target, list)
        assert all(isinstance(x, type(node)) for x in target)
        return target

    def _insert(self, obj: Any, prefix: str = ""):
        obj = SCH_Transformer.mark(obj)
        self._get_list_field(obj, prefix=prefix).append(obj)

    def _delete(self, obj: Any, prefix: str = ""):
        self._get_list_field(obj, prefix=prefix).remove(obj)

    def insert_via(
        self, coord: tuple[float, float], net: int, size_drill: tuple[float, float]
    ):
        self.sch.vias.append(
            Via(
                at=C_xy(*coord),
                size=size_drill[0],
                drill=size_drill[1],
                layers=["F.Cu", "B.Cu"],
                net=net,
                uuid=self.gen_uuid(mark=True),
            )
        )

    def insert_text(
        self,
        text: str,
        at: C_xyr,
        font: Font,
        layer: str = "F.SilkS",
        alignment: Alignment | None = None,
        knockout: bool = False,
    ):
        if not alignment:
            if layer.startswith("F."):
                alignment = Alignment_Default
            else:
                alignment = (
                    Justify.center_horizontal,
                    Justify.center_vertical,
                    Justify.mirror,
                )

        self.sch.gr_texts.append(
            GR_Text(
                text=text,
                at=at,
                layer=C_text_layer(layer, C_text_layer.E_knockout.knockout)
                if knockout
                else C_text_layer(layer),
                effects=C_effects(
                    font=font,
                    justify=alignment,
                ),
                uuid=self.gen_uuid(mark=True),
            )
        )

    def insert_track(
        self,
        net_id: int,
        points: list[Point2D],
        width: float,
        layer: str,
        arc: bool,
    ):
        points_ = [point2d_to_coord(p) for p in points]
        if arc:
            start_and_ends = points_[::2]
            for s, e, m in zip(start_and_ends[:-1], start_and_ends[1:], points_[1::2]):
                self.sch.arcs.append(
                    SCH.C_arc_segment(
                        start=s,
                        mid=m,
                        end=e,
                        width=width,
                        layer=layer,
                        net=net_id,
                        uuid=self.gen_uuid(mark=True),
                    )
                )
        else:
            for s, e in zip(points_[:-1], points_[1:]):
                self.sch.segments.append(
                    SCH.C_segment(
                        start=s,
                        end=e,
                        width=width,
                        layer=layer,
                        net=net_id,
                        uuid=self.gen_uuid(mark=True),
                    )
                )

    def insert_line(self, start: C_xy, end: C_xy, width: float, layer: str):
        self.insert_geo(
            Line(
                start=start,
                end=end,
                stroke=C_stroke(width, C_stroke.E_type.solid),
                layer=layer,
                uuid=self.gen_uuid(mark=True),
            )
        )

    def insert_geo(self, geo: Geom):
        self._insert(geo, prefix="gr_")

    def delete_geo(self, geo: Geom):
        self._delete(geo, prefix="gr_")

    def get_net_obj_bbox(self, net: Net, layer: str, tolerance=0.0):
        vias = self.sch.vias
        pads = [(pad, fp) for fp in self.sch.footprints for pad in fp.pads]

        net_vias = [via for via in vias if via.net == net.number]
        net_pads = [
            (pad, fp)
            for pad, fp in pads
            if pad.net == net.number and layer in pad.layers
        ]
        coords: list[Point2D] = [coord_to_point2d(via.at) for via in net_vias] + [
            abs_pos2d(fp.at, pad.at) for pad, fp in net_pads
        ]

        # TODO ugly, better get pcb boundaries
        if not coords:
            coords = [(-1e3, -1e3), (1e3, 1e3)]

        bbox = Geometry.bbox(coords, tolerance=tolerance)

        return Geometry.rect_to_polygon(bbox)

    # Positioning ----------------------------------------------------------------------
    def move_footprints(self):
        # position modules with defined positions
        pos_mods = self.graph.nodes_with_traits(
            (F.has_pcb_position, self.has_linked_kicad_symbol)
        )

        logger.info(f"Positioning {len(pos_mods)} footprints")

        for module, _ in pos_mods:
            fp = module.get_trait(self.has_linked_kicad_symbol).get_fp()
            coord = module.get_trait(F.has_pcb_position).get_position()
            layer_name = {
                F.has_pcb_position.layer_type.TOP_LAYER: "F.Cu",
                F.has_pcb_position.layer_type.BOTTOM_LAYER: "B.Cu",
            }

            if coord[3] == F.has_pcb_position.layer_type.NONE:
                raise Exception(f"Component {module}({fp.name}) has no layer defined")

            logger.debug(f"Placing {fp.name} at {coord} layer {layer_name[coord[3]]}")
            self.move_fp(fp, C_xyr(*coord[:3]), layer_name[coord[3]])

    def move_fp(self, fp: Footprint, coord: C_xyr, layer: str):
        if any([x.text == "FBRK:notouch" for x in fp.fp_texts]):
            logger.warning(f"Skipped no touch component: {fp.name}")
            return

        # Rotate
        rot_angle = (coord.r - fp.at.r) % 360

        if rot_angle:
            # Rotation vector in kicad footprint objs not relative to footprint rotation
            #  or is it?
            for obj in fp.pads:
                obj.at.r = (obj.at.r + rot_angle) % 360
            # For some reason text rotates in the opposite direction
            #  or maybe not?
            for obj in fp.fp_texts + list(fp.propertys.values()):
                obj.at.r = (obj.at.r + rot_angle) % 360

        fp.at = coord

        # Flip
        flip = fp.layer != layer

        if flip:

            def _flip(x: str):
                return x.replace("F.", "<F>.").replace("B.", "F.").replace("<F>.", "B.")

            fp.layer = _flip(fp.layer)

            # TODO: sometimes pads are being rotated by kicad ?!??
            for obj in fp.pads:
                obj.layers = [_flip(x) for x in obj.layers]

            for obj in get_all_geos(fp) + fp.fp_texts + list(fp.propertys.values()):
                if isinstance(obj, C_footprint.C_property):
                    obj = obj.layer
                if isinstance(obj, C_fp_text):
                    obj = obj.layer
                obj.layer = _flip(obj.layer)

        # Label
        if not any([x.text == "FBRK:autoplaced" for x in fp.fp_texts]):
            fp.fp_texts.append(
                C_fp_text(
                    type=C_fp_text.E_type.user,
                    text="FBRK:autoplaced",
                    at=C_xyr(0, 0, rot_angle),
                    effects=C_effects(self.font),
                    uuid=self.gen_uuid(mark=True),
                    layer=C_text_layer("User.5"),
                )
            )

    # Edge -----------------------------------------------------------------------------
    # TODO: make generic
    def connect_line_pair_via_radius(
        self,
        line1: C_line,
        line2: C_line,
        radius: float,
    ) -> tuple[Line, Arc, Line]:
        # Assert if the endpoints of the lines are not connected
        assert line1.end == line2.start, "The endpoints of the lines are not connected."

        # Assert if the radius is less than or equal to zero
        assert radius > 0, "The radius must be greater than zero."

        l1s = line1.start.x, line1.start.y
        l1e = line1.end.x, line1.end.y
        l2s = line2.start.x, line2.start.y
        l2e = line2.end.x, line2.end.y

        v1 = np.array(l1s) - np.array(l1e)
        v2 = np.array(l2e) - np.array(l2s)
        v1 = v1 / np.linalg.norm(v1)
        v2 = v2 / np.linalg.norm(v2)

        v_middle = v1 * radius + v2 * radius
        v_middle_norm = v_middle / np.linalg.norm(v_middle)
        v_center = v_middle - v_middle_norm * radius

        # calculate the arc center
        arc_center = np.array(l1e) + v_center

        # calculate the arc start and end points
        arc_end = np.array(l2s) + v2 * radius
        arc_start = np.array(l1e) + v1 * radius

        # convert to tuples
        arc_start = point2d_to_coord(tuple(arc_start))
        arc_center = point2d_to_coord(tuple(arc_center))
        arc_end = point2d_to_coord(tuple(arc_end))

        logger.debug(f"{v_middle=}")
        logger.debug(f"{v_middle_norm=}")
        logger.debug(f"{v_center=}")

        logger.debug(f"line intersection: {l1e} == {l2s}")
        logger.debug(f"line1: {l1s} -> {l1e}")
        logger.debug(f"line2: {l2s} -> {l2e}")
        logger.debug(f"v1: {v1}")
        logger.debug(f"v2: {v2}")
        logger.debug(f"v_middle: {v_middle}")
        logger.debug(f"radius: {radius}")
        logger.debug(f"arc_start: {arc_start}")
        logger.debug(f"arc_center: {arc_center}")
        logger.debug(f"arc_end: {arc_end}")

        # Create the arc
        arc = Arc(
            start=arc_start,
            mid=arc_center,
            end=arc_end,
            stroke=C_stroke(0.05, C_stroke.E_type.solid),
            layer="Edge.Cuts",
            uuid=self.gen_uuid(mark=True),
        )

        # Create new lines
        new_line1 = Line(
            start=line1.start,
            end=arc_start,
            stroke=C_stroke(0.05, C_stroke.E_type.solid),
            layer="Edge.Cuts",
            uuid=self.gen_uuid(mark=True),
        )
        new_line2 = Line(
            start=arc_end,
            end=line2.end,
            stroke=C_stroke(0.05, C_stroke.E_type.solid),
            layer="Edge.Cuts",
            uuid=self.gen_uuid(mark=True),
        )

        return new_line1, arc, new_line2

    def round_corners(
        self, geometry: Sequence[Geom], corner_radius_mm: float
    ) -> list[Geom]:
        """
        Round the corners of a geometry by replacing line pairs with arcs.
        """

        def _transform(geo1: Geom, geo2: Geom) -> Iterable[Geom]:
            if not isinstance(geo1, Line) or not isinstance(geo2, Line):
                return (geo1,)

            new_line1, arc, new_line2 = self.connect_line_pair_via_radius(
                geo1,
                geo2,
                corner_radius_mm,
            )
            return new_line1, new_line2, arc

        return [
            t_geo
            for pair in pairwise(list(geometry) + [geometry[0]])
            for t_geo in _transform(*pair)
        ]

    def create_rectangular_edgecut(
        self,
        width_mm: float,
        height_mm: float,
        rounded_corners: bool = False,
        corner_radius_mm: float = 0.0,
    ) -> list[Geom] | list[Line]:
        """
        Create a rectengular board outline (edge cut)
        """
        # make 4 line objects where the end of the last line is the begining of the next
        lines = [
            Line(
                start=C_xy(0, 0),
                end=C_xy(width_mm, 0),
                stroke=C_stroke(0.05, C_stroke.E_type.solid),
                layer="Edge.Cuts",
                uuid=self.gen_uuid(mark=True),
            ),
            Line(
                start=C_xy(width_mm, 0),
                end=C_xy(width_mm, height_mm),
                stroke=C_stroke(0.05, C_stroke.E_type.solid),
                layer="Edge.Cuts",
                uuid=self.gen_uuid(mark=True),
            ),
            Line(
                start=C_xy(width_mm, height_mm),
                end=C_xy(0, height_mm),
                stroke=C_stroke(0.05, C_stroke.E_type.solid),
                layer="Edge.Cuts",
                uuid=self.gen_uuid(mark=True),
            ),
            Line(
                start=C_xy(0, height_mm),
                end=C_xy(0, 0),
                stroke=C_stroke(0.05, C_stroke.E_type.solid),
                layer="Edge.Cuts",
                uuid=self.gen_uuid(mark=True),
            ),
        ]
        if rounded_corners:
            rounded_geometry = self.round_corners(lines, corner_radius_mm)
            return rounded_geometry
        else:
            return lines

    # plot the board outline with matplotlib
    # TODO: remove
    def plot_board_outline(self, geometry: List[Any]):
        import matplotlib.patches as patches
        import matplotlib.pyplot as plt
        from matplotlib.path import Path

        def plot_arc(start, mid, end):
            verts = [start, mid, end]
            codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]  # , Path.CLOSEPOLY]

            path = Path(verts, codes)
            shape = patches.PathPatch(path, facecolor="none", lw=0.75)
            plt.gca().add_patch(shape)

        fig, ax = plt.subplots()
        for geo in geometry:
            if isinstance(geo, Line):
                # plot a line
                plt.plot([geo.start.x, geo.end.x], [geo.start.y, geo.end.y])
            elif isinstance(geo, Arc):
                plot_arc(geo.start, geo.mid, geo.end)
                plt.plot([geo.start.x, geo.end.x], [geo.start.y, geo.end.y])
        plt.show()

    def set_pcb_outline_complex(
        self,
        geometry: List[Geom],
        remove_existing_outline: bool = True,
        corner_radius_mm: float = 0.0,
    ):
        """
        Create a board outline (edge cut) consisting out of
        different geometries
        """

        # TODO: remove
        # self.plot_board_outline(geometry)

        # remove existing lines on Egde.cuts layer
        if remove_existing_outline:
            for geo in get_all_geos(self.sch):
                if not isinstance(geo, (Line, Arc)):
                    continue
                if geo.layer != "Edge.Cuts":
                    continue
                self.delete_geo(geo)

        # round corners between lines
        if corner_radius_mm > 0:
            geometry = self.round_corners(geometry, corner_radius_mm)

        # create Edge.Cuts geometries
        for geo in geometry:
            assert geo.layer == "Edge.Cuts", f"Geometry {geo} is not on Edge.Cuts layer"

            self.insert_geo(geo)

        # find bounding box

    # Silkscreen -----------------------------------------------------------------------
    class Side(Enum):
        TOP = auto()
        BOTTOM = auto()
        LEFT = auto()
        RIGHT = auto()

    def set_designator_position(
        self,
        offset: float,
        displacement: C_xy = C_xy(0, 0),
        rotation: Optional[float] = None,
        offset_side: Side = Side.BOTTOM,
        layer: Optional[C_text_layer] = None,
        font: Optional[Font] = None,
        knockout: Optional[C_text_layer.E_knockout] = None,
        justify: Alignment | None = None,
    ):
        for mod, fp in self.get_all_footprints():
            reference = fp.propertys["Reference"]
            reference.layer = (
                layer
                if layer
                else C_text_layer(
                    layer="F.SilkS" if fp.layer.startswith("F") else "B.SilkS"
                )
            )
            if knockout:
                reference.layer.knockout = knockout
            if font:
                reference.effects.font = font
            if justify:
                reference.effects.justifys = [C_effects.C_justify(justify)]

            rot = rotation if rotation else reference.at.r

            footprint_bbox = self.get_footprint_silkscreen_bbox(mod)
            if not footprint_bbox:
                continue
            max_coord = C_xy(*footprint_bbox[1])
            min_coord = C_xy(*footprint_bbox[0])

            if offset_side == self.Side.BOTTOM:
                reference.at = C_xyr(
                    displacement.x, max_coord.y + offset - displacement.y, rot
                )
            elif offset_side == self.Side.TOP:
                reference.at = C_xyr(
                    displacement.x, min_coord.y - offset - displacement.y, rot
                )
            elif offset_side == self.Side.LEFT:
                reference.at = C_xyr(
                    min_coord.x - offset - displacement.x, displacement.y, rot
                )
            elif offset_side == self.Side.RIGHT:
                reference.at = C_xyr(
                    max_coord.x + offset + displacement.x, displacement.y, rot
                )

    def add_git_version(
        self,
        center_at: C_xyr,
        layer: str = "F.SilkS",
        font: Font = Font(size=C_wh(1, 1), thickness=0.2),
        knockout: bool = True,
        alignment: Alignment = Alignment_Default,
    ):
        # check if gitcli is available
        try:
            subprocess.check_output(["git", "--version"])
        except subprocess.CalledProcessError:
            logger.warning("git is not installed")
            git_human_version = "git is not installed"

        try:
            git_human_version = (
                subprocess.check_output(["git", "describe", "--always"])
                .strip()
                .decode("utf-8")
            )
        except subprocess.CalledProcessError:
            logger.warning("Cannot get git project version")
            git_human_version = "Cannot get git project version"

        self.insert_text(
            text=git_human_version,
            at=center_at,
            layer=layer,
            font=font,
            alignment=alignment,
            knockout=knockout,
        )
