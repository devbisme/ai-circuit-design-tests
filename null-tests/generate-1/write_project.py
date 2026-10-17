"""Write dual_adc.kicad_pro: design rules and net classes for the board."""
import json

power_nets = ["+5V", "+3V3", "+1V2", "+4V5A", "+3V0A", "VBUS", "VBUS_CONN",
              "VCCPLL0", "VCCPLL1",
              # wired (unlabelled) nets get auto names in the schematic netlist
              "Net-(J3-VBUS)", "Net-(U2-SW)", "Net-(U16-VCCA)", "Net-(U16-VCCCORE)"]


def nc(name, track, clearance, via, drill, prio):
    return {"name": name, "track_width": track, "clearance": clearance,
            "via_diameter": via, "via_drill": drill, "microvia_diameter": 0.3,
            "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12,
            "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": prio}


pro = {
    "meta": {"filename": "dual_adc.kicad_pro", "version": 3},
    "board": {
        "design_settings": {
            "rules": {
                "min_clearance": 0.15, "min_track_width": 0.1,
                "min_via_diameter": 0.5, "min_via_annular_width": 0.1,
                "min_through_hole_diameter": 0.25, "min_hole_clearance": 0.25,
                "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.3,
                "min_silk_clearance": 0.0, "min_text_height": 0.6,
                "min_text_thickness": 0.08, "solder_mask_to_copper_clearance": 0.0,
            },
            "track_widths": [0.0, 0.2, 0.3, 0.5],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0},
                               {"diameter": 0.6, "drill": 0.3},
                               {"diameter": 0.8, "drill": 0.4}],
        },
    },
    "net_settings": {
        "classes": [nc("Default", 0.2, 0.15, 0.6, 0.3, 2147483647),
                    nc("Power", 0.5, 0.2, 0.8, 0.4, 0)],
        "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in power_nets],
        "meta": {"version": 4},
    },
    "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
    "sheets": [],
}
json.dump(pro, open("dual_adc.kicad_pro", "w"), indent=2)
print("wrote dual_adc.kicad_pro")
