import sys, kcaa_call
for spec in sys.argv[1:]:
    lib, sym = spec.split(":")
    r = kcaa_call.call("get_symbol_pins", library_name=lib, symbol_name=sym, project_path="/home/devb/projects/AI/ai-circuit-design-tests/kicad-ai-assistant-tests/dual-adc-usb-2")
    if not r.get("success", True) or "pins" not in r:
        print(spec, r); continue
    print(f"== {spec} ({len(r['pins'])} pins) units={r.get('unit_count')}")
    print("  " + " ".join(f"{p['number']}:{p['name']}[{str(p.get('type',p.get('electrical_type','')))[:3]}]" for p in r["pins"]))
