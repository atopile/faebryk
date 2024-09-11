import logging
from dataclasses import dataclass, field

from faebryk.libs.kicad.fileformats import (
    C_arc,
    C_circle,
    C_footprint,
    C_fp_text,
    C_kicad_footprint_file,
    C_line,
    C_rect,
    C_stroke,
    C_text,
    C_xy,
    E_fill,
    gen_uuid,
)
from faebryk.libs.sexp.dataclass_sexp import SEXP_File, sexp_field

logger = logging.getLogger(__name__)


@dataclass
class C_line_old:
    start: C_xy
    end: C_xy
    layer: str
    width: float

    def convert_to_new(self) -> C_line:
        return C_line(
            start=self.start,
            end=self.end,
            uuid=gen_uuid(),
            layer=self.layer,
            stroke=C_stroke(
                width=self.width,
                type=C_stroke.E_type.solid,
            ),
        )


@dataclass(kw_only=True)
class C_circle_old:
    center: C_xy
    end: C_xy
    width: float
    fill: E_fill = field(default=E_fill.none)
    layer: str

    def convert_to_new(self) -> C_circle:
        return C_circle(
            center=self.center,
            end=self.end,
            uuid=gen_uuid(),
            stroke=C_stroke(
                width=self.width,
                type=C_stroke.E_type.solid,
            ),
            fill=self.fill,
            layer=self.layer,
        )


@dataclass
class C_arc_old:
    start: C_xy
    end: C_xy
    width: float
    layer: str
    angle: float

    def _calculate_midpoint(self) -> tuple[C_xy, C_xy, C_xy]:
        start = self.end
        center = self.start

        mid = start.rotate(center, -self.angle / 2.0)
        end = start.rotate(center, -self.angle)

        return start, mid, end

    def convert_to_new(self) -> C_arc:
        start, mid, end = self._calculate_midpoint()
        return C_arc(
            start=start,
            mid=mid,
            end=end,
            uuid=gen_uuid(),
            stroke=C_stroke(
                width=self.width,
                type=C_stroke.E_type.solid,
            ),
            layer=self.layer,
        )


@dataclass
class C_rect_old:
    start: C_xy
    end: C_xy
    width: float
    fill: E_fill
    layer: str

    def convert_to_new(self) -> C_rect:
        return C_rect(
            start=self.start,
            end=self.end,
            uuid=gen_uuid(),
            stroke=C_stroke(
                width=self.width,
                type=C_stroke.E_type.solid,
            ),
            fill=self.fill,
            layer=self.layer,
        )


@dataclass
class C_kicad_footprint_file_easyeda(SEXP_File):
    @dataclass(kw_only=True)
    class C_footprint_in_file(C_footprint):
        tedit: str

        fp_lines: list[C_line_old] = field(
            **sexp_field(multidict=True), default_factory=list
        )
        fp_arcs: list[C_arc_old] = field(
            **sexp_field(multidict=True), default_factory=list
        )
        fp_circles: list[C_circle_old] = field(
            **sexp_field(multidict=True), default_factory=list
        )
        fp_rects: list[C_rect_old] = field(
            **sexp_field(multidict=True), default_factory=list
        )

        def convert_to_new(self) -> C_kicad_footprint_file.C_footprint_in_file:
            propertys: dict[str, C_footprint.C_property] = {
                name: C_footprint.C_property(
                    name=name,
                    value=k.text,
                    at=k.at,
                    layer=k.layer,
                    uuid=k.uuid,
                    effects=k.effects,
                )
                for k in self.fp_texts
                if (name := k.type.capitalize()) in ("Reference", "Value")
            } | self.propertys

            texts = [t for t in self.fp_texts if t.type not in ("reference", "value")]
            for t in self.fp_texts:
                if t.type == "reference":
                    texts.append(
                        C_fp_text(
                            type=C_fp_text.E_type.user,
                            text=t.text.replace("REF**", "${REFERENCE}"),
                            at=t.at,
                            layer=t.layer,
                            uuid=t.uuid,
                            effects=t.effects,
                        )
                    )

            return C_kicad_footprint_file.C_footprint_in_file(
                fp_lines=[line.convert_to_new() for line in self.fp_lines],
                fp_arcs=[arc.convert_to_new() for arc in self.fp_arcs],
                fp_circles=[circle.convert_to_new() for circle in self.fp_circles],
                fp_rects=[rect.convert_to_new() for rect in self.fp_rects],
                # fp-file
                descr="",
                tags=[],
                version=0,
                generator="",
                generator_version="",
                # fp
                name=self.name,
                layer=self.layer,
                propertys=propertys,
                attr=self.attr,
                fp_texts=texts,
                fp_poly=self.fp_poly,
                pads=self.pads,
                model=self.model,
            )

    module: C_footprint_in_file

    def convert_to_new(self) -> C_kicad_footprint_file:
        return C_kicad_footprint_file(footprint=self.module.convert_to_new())
