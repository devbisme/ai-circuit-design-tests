import json,subprocess,sys
for sid in sys.argv[1:]:
    d=json.loads(subprocess.run(["kh","sym","--pins",sid],capture_output=True,text=True).stdout)
    print(f"== {sid} fp={d.get('default_footprint')} filt={d.get('footprint_filters')} units={sorted(set(p['unit'] for p in d['pins']))}")
    print("  ".join(f"{p['number']}:{p['name']}:{p['type'][:3]}" for p in d['pins']))
