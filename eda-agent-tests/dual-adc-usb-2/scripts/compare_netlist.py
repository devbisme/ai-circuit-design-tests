"""Compare a kicad-cli netlist export with the DesignPlan (pin sets per net)."""
import json, sys
import symlib
net = symlib.parse(open(sys.argv[1]).read())
plan = json.load(open(sys.argv[2]))
got = {}
for n in symlib.find1(net, "nets")[1:]:
    name = str(symlib.find1(n, "name")[1]).lstrip("/")
    pins = frozenset((str(symlib.find1(x, "ref")[1]), str(symlib.find1(x, "pin")[1]))
                     for x in symlib.find(n, "node"))
    if name.startswith("unconnected-"):
        continue
    got[pins] = name
want = {frozenset((p["refdes"], p["pin"]) for p in n["pins"]): n["name"] for n in plan["nets"]}
bad = 0
for pins, name in want.items():
    if pins not in got:
        bad += 1; print("MISSING/DIFFERENT", name)
    elif got[pins] != name:
        print("renamed", name, "->", got[pins])
for pins, name in got.items():
    if pins not in want:
        bad += 1; print("EXTRA", name, sorted(pins)[:6])
print(f"plan nets {len(want)}, netlist nets {len(got)}, problems {bad}")
