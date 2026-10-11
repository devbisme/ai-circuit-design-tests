"""Write net classes and board design-rule minimums into kicad/dual_adc.kicad_pro.

Run after any pcbnew board.Save(), which rewrites the project file.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PRO = os.path.join(HERE, "..", "kicad", "dual_adc.kicad_pro")
POWER = ["+5V", "VBUS", "VBUS_F", "+1V2", "+4V", "-4V", "LM_CP", "LM_CPF", "LM_CN",
         "FT_VPHY", "VCCPLL0", "VCCPLL1", "OSC_VDD", "FT_VCCA", "FT_VCORE"]

pro = json.load(open(PRO))


def nc(name, width, prio):
    return {"name": name, "priority": prio, "clearance": 0.15, "track_width": width,
            "via_diameter": 0.45, "via_drill": 0.2, "microvia_diameter": 0.3,
            "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12,
            "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)",
            "pcb_color": "rgba(0, 0, 0, 0.000)"}


ns = pro.setdefault("net_settings", {})
ns["classes"] = [nc("Default", 0.2, 2147483647), nc("Power", 0.4, 0)]
ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in POWER]
ns.setdefault("meta", {"version": 4})
rules = pro.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {})
rules.update({"min_track_width": 0.1, "min_clearance": 0.15, "min_via_diameter": 0.45,
              "min_through_hole_diameter": 0.2, "min_via_annular_width": 0.1,
              "min_hole_to_hole": 0.25, "min_copper_edge_clearance": 0.3,
              "min_hole_clearance": 0.2})
json.dump(pro, open(PRO, "w"), indent=2)
print("patched", PRO)
