"""Check every symbol pin in the plan is either on a net or marked no-connect."""
import json, os, sys
import symlib
HERE = os.path.dirname(os.path.abspath(__file__))
plan = json.load(open(os.path.join(HERE, "../plan/dual_adc_plan.json")))
ncs = {(r, p) for r, p in json.load(open(os.path.join(HERE, "../plan/no_connects.json")))}
used = {}
for n in plan["nets"]:
    for p in n["pins"]:
        used[(p["refdes"], p["pin"])] = n["name"]
bad = 0
cache = {}
for part in plan["parts"]:
    lib, name = part["lib_ref"].split(":")
    if part["lib_ref"] not in cache:
        cache[part["lib_ref"]] = symlib.pins(symlib.load_symbol(lib, name))
    nums = {p["number"] for p in cache[part["lib_ref"]]}
    for num in sorted(nums):
        k = (part["refdes"], num)
        if k not in used and k not in ncs:
            print("UNCONNECTED", k); bad += 1
        if k in used and k in ncs:
            print("BOTH", k); bad += 1
    for (r, p) in list(used) + list(ncs):
        if r == part["refdes"] and p not in nums:
            print("NO SUCH PIN", r, p); bad += 1
print("problems:", bad)
