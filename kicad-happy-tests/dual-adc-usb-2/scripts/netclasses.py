"""Write net classes into a .kicad_pro (pcbnew's Save() regenerates the project file without them)."""
import json
import sys

POWER = ["+5V", "VBUS", "VBUS_F", "+1V2", "+3V3_ADC", "+3V3A", "-3V3A", "FT_VCORE", "FT_VPHY",
         "VCCPLL0", "VCCPLL1", "GNDPLL0", "GNDPLL1", "CP_OUT", "BUCK_SW", "GND", "+3V3"]


# ADC data bus: 0.1/0.1 mm so the QFN top/bottom rows can escape on two signal layers.
FINE = ["DA*", "DB*", "OFA", "OFB"]


def patch(pro):
    d = json.load(open(pro))
    ns = d["net_settings"]
    base = dict(ns["classes"][0])
    pw = dict(base, name="Power", track_width=0.3, clearance=0.15, priority=0)
    fine = dict(base, name="Fine", track_width=0.1, clearance=0.1, priority=1)
    ns["classes"] = [c for c in ns["classes"] if c["name"] not in ("Power", "Fine")] + [pw, fine]
    # Local nets are hierarchical in KiCad ("/fpga1/VCCPLL0"), so also match on the tail.
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in POWER] + \
        [{"netclass": "Power", "pattern": "*/" + n} for n in POWER] + \
        [{"netclass": "Fine", "pattern": p} for p in FINE]
    json.dump(d, open(pro, "w"), indent=2)


if __name__ == "__main__":
    patch(sys.argv[1])
