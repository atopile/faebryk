# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from pathlib import Path

from faebryk.libs.kicad.fileformats import (
    C_footprint,
    C_kicad_fp_lib_table_file,
    C_kicad_netlist_file,
    C_kicad_pcb_file,
    C_text_layer,
    C_xyr,
)
from faebryk.libs.kicad.fileformats_common import C_effects, C_wh
from faebryk.libs.kicad.fileformats_version import kicad_footprint_file
from faebryk.libs.kicad.paths import GLOBAL_FP_DIR_PATH, GLOBAL_FP_LIB_PATH
from faebryk.libs.sexp.dataclass_sexp import get_parent
from faebryk.libs.util import (
    KeyErrorNotFound,
    dataclass_as_kwargs,
    find,
    find_or,
    not_none,
)

logger = logging.getLogger(__name__)


def _nets_same(
    pcb_net: tuple[
        C_kicad_pcb_file.C_kicad_pcb.C_net,
        list[C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint.C_pad],
    ],
    nl_net: C_kicad_netlist_file.C_netlist.C_nets.C_net,
) -> bool:
    pcb_pads = {
        f"{get_parent(p, C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint)
           .propertys['Reference'].value}.{p.name}"
        for p in pcb_net[1]
    }
    nl_pads = {f"{n.ref}.{n.pin}" for n in nl_net.nodes}
    return pcb_pads == nl_pads


def _get_footprint(identifier: str, fp_lib_path: Path) -> C_footprint:
    fp_lib_table = C_kicad_fp_lib_table_file.loads(fp_lib_path)
    lib_id, fp_name = identifier.split(":")
    try:
        lib = find(fp_lib_table.fp_lib_table.libs, lambda x: x.name == lib_id)
        dir_path = Path(lib.uri.replace("${KIPRJMOD}", str(fp_lib_path.parent)))
    except KeyErrorNotFound:
        # non-local lib, search in kicad global lib
        global_fp_lib_table = C_kicad_fp_lib_table_file.loads(GLOBAL_FP_LIB_PATH)
        lib = find(global_fp_lib_table.fp_lib_table.libs, lambda x: x.name == lib_id)
        dir_path = Path(
            lib.uri.replace("${KICAD8_FOOTPRINT_DIR}", str(GLOBAL_FP_DIR_PATH))
        )

    path = dir_path / f"{fp_name}.kicad_mod"
    return kicad_footprint_file(path).footprint


# TODO use G instead of netlist intermediary


class PCB:
    @staticmethod
    def apply_netlist(pcb_path: Path, netlist_path: Path):
        from faebryk.exporters.pcb.kicad.transformer import gen_uuid

        fp_lib_path = pcb_path.parent / "fp-lib-table"

        pcb = C_kicad_pcb_file.loads(pcb_path)
        netlist = C_kicad_netlist_file.loads(netlist_path)

        # footprint properties
        def fill_fp_property(
            fp: C_footprint, property_name: str, layer: str, value: str
        ) -> C_footprint.C_property:
            return C_footprint.C_property(
                name=property_name,
                value=value,
                layer=C_text_layer(layer=layer),
                uuid=gen_uuid(),
                effects=C_effects(
                    font=C_effects.C_font(size=C_wh(w=1.27, h=1.27), thickness=0.15),
                    hide=True,
                ),
                at=C_xyr(x=0, y=0, r=0),
            )

        def get_property_value(
            comp: C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint
            | C_kicad_netlist_file.C_netlist.C_components.C_component,
            property_name: str,
            default: str,
        ) -> str:
            try:
                return comp.propertys[property_name].value
            except KeyError:
                return default

        # update nets
        # load footprints
        #   - set layer & pos
        #   - per pad set net
        #   - load ref & value from netlist
        #   - set uuid for all (pads, geos, ...)
        #   - drop fp_text value & fp_text user

        # notes:
        # - netcode in netlist unrelated to netcode in pcb
        #   - matched by name + check for same pads
        #       - only works if net nodes not changed
        #   - what happens if net is renamed?
        #   - segments & vias etc use netcodes
        #       - if net code removed, recalculated
        #           -> DIFFICULT: need to know which net/pads they are touching
        #   - zone & pads uses netcode & netname
        # - empty nets ignored (consider removing them from netlist export)
        # - components matched by ref (no fallback)
        # - if pad no net, just dont put net in sexp

        # Nets =========================================================================
        nl_nets = {n.name: n for n in netlist.export.nets.nets if n.nodes}
        pcb_nets = {
            n.name: (
                n,
                [
                    p
                    for f in pcb.kicad_pcb.footprints
                    for p in f.pads
                    if p.net and p.net.name == n.name
                ],
            )
            for n in pcb.kicad_pcb.nets
            if n.name
        }

        nets_added = nl_nets.keys() - pcb_nets.keys()
        nets_removed = pcb_nets.keys() - nl_nets.keys()

        # Match renamed nets by pads
        matched_nets = {
            nl_net_name: pcb_net_name
            for nl_net_name in nets_added
            if (
                pcb_net_name := find_or(
                    nets_removed,
                    lambda x: _nets_same(pcb_nets[not_none(x)], nl_nets[nl_net_name]),
                    default=None,
                )
            )
        }
        nets_added.difference_update(matched_nets.keys())
        nets_removed.difference_update(matched_nets.values())

        # Remove nets ------------------------------------------------------------------
        logger.debug(f"Removed nets: {nets_removed}")
        removed_net_numbers = list[int]()
        for net_name in nets_removed:
            pcb_net, pads = pcb_nets[net_name]
            removed_net_numbers.append(pcb_net.number)
            pcb.kicad_pcb.nets.remove(pcb_net)
            for pad in pads:
                assert pad.net
                pad.net.name = ""
                pad.net.number = 0
            for route in (
                pcb.kicad_pcb.segments + pcb.kicad_pcb.arcs + pcb.kicad_pcb.vias
            ):
                if route.net == pcb_net.number:
                    route.net = 0
            for zone in pcb.kicad_pcb.zones:
                if zone.net_name == net_name:
                    zone.net_name = ""
                    zone.net = 0

        # Rename nets ------------------------------------------------------------------
        logger.debug(f"Renamed nets: {matched_nets}")
        for new_name, old_name in matched_nets.items():
            pcb_net, pads = pcb_nets[old_name]
            pcb_net.name = new_name
            pcb_nets[new_name] = (pcb_net, pads)
            del pcb_nets[old_name]
            for pad in pads:
                assert pad.net
                pad.net.name = new_name
            for zone in pcb.kicad_pcb.zones:
                if zone.net_name == old_name:
                    zone.net_name = new_name

        # Add new nets -----------------------------------------------------------------
        logger.debug(f"New nets: {nets_added}")
        for net_name in nets_added:
            # nl_net = nl_nets[net_name]
            if removed_net_numbers:
                net_number = removed_net_numbers.pop()
            else:
                net_number = len(pcb.kicad_pcb.nets)
            pcb_net = C_kicad_pcb_file.C_kicad_pcb.C_net(
                name=net_name,
                number=net_number,
            )
            pcb.kicad_pcb.nets.append(pcb_net)
            pcb_nets[net_name] = (pcb_net, [])
        pcb.kicad_pcb.nets.sort(key=lambda x: x.number)

        # Components ===================================================================
        pcb_comps = {
            c.propertys["Reference"].value: c for c in pcb.kicad_pcb.footprints
        }
        nl_comps = {c.ref: c for c in netlist.export.components.comps}
        comps_added = nl_comps.keys() - pcb_comps.keys()
        comps_removed = pcb_comps.keys() - nl_comps.keys()
        comps_matched = nl_comps.keys() & pcb_comps.keys()
        comps_changed: dict[str, C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint] = {}

        # Update components ------------------------------------------------------------
        logger.debug(f"Comps matched: {comps_matched}")
        for comp_name in comps_matched:
            nl_comp = nl_comps[comp_name]
            pcb_comp = pcb_comps[comp_name]

            # update
            if pcb_comp.name != nl_comp.footprint:
                comps_removed.add(comp_name)
                comps_added.add(comp_name)
                comps_changed[comp_name] = pcb_comp
                continue

            pcb_comp.propertys["Value"].value = nl_comp.value
            pcb_comp.propertys["faebryk module name"] = fill_fp_property(
                fp=pcb_comp,
                property_name="faebryk module name",
                layer="User.9",
                value=get_property_value(nl_comp, "faebryk_name", "No faebryk_name"),
            )

            pcb_comp.propertys["LCSC"] = fill_fp_property(
                fp=pcb_comp,
                property_name="LCSC",
                layer="User.9",
                value=get_property_value(nl_comp, "LCSC", "No LCSC number"),
            )

            # update pad nets
            pads = {
                p.pin: n
                for n in nl_nets.values()
                for p in n.nodes
                if p.ref == comp_name
            }
            for p in pcb_comp.pads:
                if p.name not in pads:
                    continue
                net = C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint.C_pad.C_net(
                    number=pcb_nets[pads[p.name].name][0].number,
                    name=pads[p.name].name,
                )
                p.net = net

        # Remove components ------------------------------------------------------------
        logger.debug(f"Comps removed: {comps_removed}")
        for comp_name in comps_removed:
            comp = pcb_comps[comp_name]
            pcb.kicad_pcb.footprints.remove(comp)

        # Add new components -----------------------------------------------------------
        logger.debug(f"Comps added: {comps_added}")
        for comp_name in comps_added:
            comp = nl_comps[comp_name]
            footprint_identifier = comp.footprint
            footprint = _get_footprint(footprint_identifier, fp_lib_path)
            pads = {
                p.pin: n
                for n in nl_nets.values()
                for p in n.nodes
                if p.ref == comp_name
            }

            # Fill in variables
            footprint.propertys["Reference"].value = comp_name
            footprint.propertys["Value"].value = comp.value
            footprint.propertys["faebryk module name"] = fill_fp_property(
                fp=footprint,
                property_name="faebryk module name",
                layer="User.9",
                value=get_property_value(comp, "faebryk_name", "No faebryk_name"),
            )
            footprint.propertys["LCSC"] = fill_fp_property(
                fp=footprint,
                property_name="LCSC",
                layer="User.9",
                value=get_property_value(comp, "LCSC", "No LCSC number"),
            )

            at = C_xyr(x=0, y=0, r=0)
            if comp_name in comps_changed:
                # TODO also need to do geo rotations and stuff
                at = comps_changed[comp_name].at

            pcb_comp = C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint(
                uuid=gen_uuid(mark=""),
                at=at,
                pads=[
                    C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint.C_pad(
                        uuid=gen_uuid(mark=""),
                        net=C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint.C_pad.C_net(
                            number=pcb_nets[pads[p.name].name][0].number,
                            name=pads[p.name].name,
                        )
                        if p.name in pads
                        else None,
                        # rest of fields
                        **dataclass_as_kwargs(p),
                    )
                    for p in footprint.pads
                ],
                #
                name=footprint_identifier,
                layer=footprint.layer,
                propertys=footprint.propertys,
                attr=footprint.attr,
                fp_lines=footprint.fp_lines,
                fp_arcs=footprint.fp_arcs,
                fp_circles=footprint.fp_circles,
                fp_rects=footprint.fp_rects,
                fp_texts=footprint.fp_texts,
                fp_poly=footprint.fp_poly,
                model=footprint.model,
            )

            pcb.kicad_pcb.footprints.append(pcb_comp)

        # ---
        logger.debug(f"Save PCB: {pcb_path}")
        pcb.dumps(pcb_path)
