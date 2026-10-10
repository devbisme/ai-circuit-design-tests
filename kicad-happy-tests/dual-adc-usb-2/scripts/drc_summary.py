"""Summarize a kicad-cli DRC JSON report."""
import collections
import json
import sys

d = json.load(open(sys.argv[1]))
print("violations", len(d["violations"]), "unconnected", len(d.get("unconnected_items", [])),
      "parity", len(d.get("schematic_parity", [])))
print(collections.Counter((v["type"], v["severity"]) for v in d["violations"]))
for v in d["violations"]:
    if v["severity"] == "error":
        print("E", v["type"], v["description"][:90], [(i["description"][:50], i["pos"]) for i in v["items"]][:2])
for u in d.get("unconnected_items", []):
    print("U", [(i["description"][:55], i["pos"]) for i in u["items"]])
for u in d.get("schematic_parity", [])[:10]:
    print("P", u["description"][:90], [i["description"][:50] for i in u["items"]])
