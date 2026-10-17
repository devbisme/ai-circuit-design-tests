"""Run boardforge's own SPICE path checker (spice_path.check) on build/netlist.json with ONE
change: the OPA2810 custom-symbol pin names (VIN1+/VIN1-/VO1, VIN2+/VIN2-/VO2) are added to
its pin-role tables. Writes work files to argv[2]; does not touch build/reports."""
import json, os, sys
sys.path.insert(0, '/home/devb/.local/share/uv/tools/boardforge/lib/python3.12/site-packages')
from boardforge.review import spice_path as sp
from boardforge.review import constraints as cons
from boardforge import datasheets
from boardforge.config import Project
if "--patch" in sys.argv:
    R = sp.OPAMP_ROLES
    R["inp"] += ("VIN1+", "VIN2+"); R["inn"] += ("VIN1-", "VIN2-")
    _o = sp.role_is_out
    sp.role_is_out = lambda n, t: _o(n, t) or (t == "output" and n.upper() in ("VO1", "VO2"))
proj = Project.load(sys.argv[1]); out = sys.argv[2]
cfg = proj.cfg.get("review", {})
net = json.load(open(os.path.join(proj.out, "netlist.json")))
store, _ = datasheets.stores(proj)
facts = {}
for c in net["components"]:
    m = datasheets.mpn_of(c)
    if m and m not in facts: facts[m] = datasheets.amp_facts(store, m)
cs, _ = cons.load(cons.path(proj))
for c in cs:
    if c.get("kind") != "ac_gain": continue
    r = sp.check(net, c, cfg.get("models", {}), sp.find_ngspice(cfg.get("ngspice", "")), cfg.get("dc", {}),
                 os.path.join(out, c["id"]), {k: v for k, v in facts.items() if v})
    print(f"{r['status']:12s} {c['tag']:8s} {c['id']:12s} gain={r.get('gain_db')} ref={r.get('ref_db')} lim={r.get('limit')} {r.get('why','')[:120]}")
    for n in r["notes"]:
        if "GBW" not in n: print("     ", n)
