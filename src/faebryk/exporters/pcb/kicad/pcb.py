# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import logging
from dataclasses import asdict
from pathlib import Path

from faebryk.libs.kicad.fileformats import (
    C_footprint,
    C_kicad_footprint_file,
    C_kicad_fp_lib_table_file,
    C_kicad_netlist_file,
    C_kicad_pcb_file,
    C_xyr,
)
from faebryk.libs.kicad.fileformats_old import C_kicad_footprint_file_easyeda
from faebryk.libs.sexp.dataclass_sexp import get_parent
from faebryk.libs.util import NotNone, find, find_or

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


def _get_footprint(
    identifier: str, fp_lib_path: Path
) -> C_kicad_footprint_file.C_footprint_in_file:
    fp_lib_table = C_kicad_fp_lib_table_file.loads(fp_lib_path)
    lib_id, fp_name = identifier.split(":")
    lib = find(fp_lib_table.fp_lib_table.libs, lambda x: x.name == lib_id)
    dir_path = Path(lib.uri.replace("${KIPRJMOD}", str(fp_lib_path.parent)))
    path = dir_path / f"{fp_name}.kicad_mod"

    # TODO this should be handled in fileformats itself
    if path.read_text().startswith("(module"):
        return C_kicad_footprint_file_easyeda.loads(path).convert_to_new().footprint

    return C_kicad_footprint_file.loads(path).footprint


# TODO remove prints
# TODO use G instead of netlist intermediary


class PCB:
    @staticmethod
    def apply_netlist(pcb_path: Path, netlist_path: Path):
        from faebryk.exporters.pcb.kicad.transformer import gen_uuid

        fp_lib_path = pcb_path.parent / "fp-lib-table"

        pcb = C_kicad_pcb_file.loads(pcb_path)
        netlist = C_kicad_netlist_file.loads(netlist_path)

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

        # Nets
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
                    lambda x: _nets_same(pcb_nets[NotNone(x)], nl_nets[nl_net_name]),
                    default=None,
                )
            )
        }
        nets_added.difference_update(matched_nets.keys())
        nets_removed.difference_update(matched_nets.values())

        if nets_removed:
            # TODO
            raise NotImplementedError(
                f"Nets removed from netlist not implemented: {nets_removed}"
            )

        # Rename nets
        print("Renamed nets:", matched_nets)
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

        # Add new nets
        print("New nets", nets_added)
        for net_name in nets_added:
            # nl_net = nl_nets[net_name]
            pcb_net = C_kicad_pcb_file.C_kicad_pcb.C_net(
                name=net_name,
                number=len(pcb.kicad_pcb.nets),
            )
            pcb.kicad_pcb.nets.append(pcb_net)
            pcb_nets[net_name] = (pcb_net, [])

        # Components
        pcb_comps = {
            c.propertys["Reference"].value: c for c in pcb.kicad_pcb.footprints
        }
        nl_comps = {c.ref: c for c in netlist.export.components.comps}
        comps_added = nl_comps.keys() - pcb_comps.keys()
        comps_removed = pcb_comps.keys() - nl_comps.keys()

        print("Comps removed:", comps_removed)
        for comp_name in comps_removed:
            comp = pcb_comps[comp_name]
            pcb.kicad_pcb.footprints.remove(comp)

        print("Comps added:", comps_added)
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

            texts = [t for t in footprint.fp_texts if t.type not in ("user", "value")]
            for t in texts:
                if t.type == "reference":
                    t.text = comp_name

            propertys: dict[str, C_footprint.C_property] = {
                name: C_footprint.C_property(
                    name=name,
                    value=k.text,
                    at=k.at,
                    layer=k.layer,
                    uuid=k.uuid,
                    effects=k.effects,
                )
                for k in footprint.fp_texts
                if (name := k.type.capitalize()) in ("Reference", "Value")
            }

            propertys["Reference"].value = comp_name
            propertys["Value"].value = comp.value

            pcb_comp = C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint(
                uuid=gen_uuid(mark=""),
                at=C_xyr(x=0, y=0, r=0),
                pads=[
                    C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint.C_pad(
                        uuid=gen_uuid(mark=""),
                        net=C_kicad_pcb_file.C_kicad_pcb.C_pcb_footprint.C_pad.C_net(
                            number=pcb_nets[pads[p.name].name][0].number,
                            name=pads[p.name].name,
                        )
                        if p.name in pads
                        else None,
                        #
                        **asdict(p),
                    )
                    for p in footprint.pads
                ],
                #
                name=footprint_identifier,
                layer=footprint.layer,
                propertys=propertys,
                attr=footprint.attr,
                fp_lines=footprint.fp_lines,
                fp_arcs=footprint.fp_arcs,
                fp_circles=footprint.fp_circles,
                fp_rects=footprint.fp_rects,
                fp_texts=texts,
                fp_poly=footprint.fp_poly,
                model=footprint.model,
            )

            pcb.kicad_pcb.footprints.append(pcb_comp)

        # ---
        print("Save PCB", pcb_path)
        pcb.dumps(pcb_path)
