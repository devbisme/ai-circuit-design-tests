import sys
from sexp import load_symbol, symbol_pins
for sid in sys.argv[1:]:
    ps = symbol_pins(load_symbol(sid))
    print("==", sid, "  ".join(f"{p['number']}:{p['name']}:{p['type'][:3]}:u{p['unit']}" for p in ps))
