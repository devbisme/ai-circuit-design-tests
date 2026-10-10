"""Write net classes and basic board rules into dual_adc_usb.kicad_pro.

(pcbnew board.Save() rewrites the .kicad_pro, so re-run this after any pcbnew save.)
"""
import json, sys
p = sys.argv[1]
d = json.load(open(p))
def cls(name, track, clear, via_d, via_h, prio):
    return {"name": name, "priority": prio, "clearance": clear, "track_width": track,
            "via_diameter": via_d, "via_drill": via_h, "microvia_diameter": 0.3,
            "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12,
            "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)"}
power = ['+5V', 'VBUS', '/USB/VBUS_F', '+3V3', '+1V2', '+3.3VA', '+4V5A', '-4V5A',
         '/USB/VCORE', '/USB/VPLL_PHY', '/FPGA/VCCPLL0', '/FPGA/VCCPLL1', '/Power/VCP']
d['net_settings'] = {
    "classes": [cls("Default", 0.15, 0.15, 0.45, 0.2, 2147483647), cls("Power", 0.4, 0.15, 0.6, 0.3, 0)],
    "meta": {"version": 4},
    "net_colors": None, "netclass_assignments": None,
    "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in power],
}
ds = d.setdefault('board', {}).setdefault('design_settings', {})
ds.setdefault('rules', {}).update({
    "min_clearance": 0.15, "min_track_width": 0.1, "min_via_diameter": 0.45,
    "min_through_hole_diameter": 0.2, "min_via_annular_width": 0.1,
    "min_copper_edge_clearance": 0.3, "min_hole_to_hole": 0.25, "min_hole_clearance": 0.2,
})
json.dump(d, open(p, 'w'), indent=2)
print('net classes written')
