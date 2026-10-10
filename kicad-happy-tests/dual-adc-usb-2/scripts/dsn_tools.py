"""
Specctra helpers (run with KiCad 10's python for export/import; trim works with any python).

  export  board.kicad_pcb out.dsn          -> KiCad-native DSN export
  trim    in.dsn out.dsn GND +3V3          -> cut plane nets to a single pin so Freerouting
                                              ignores them (their pads are already fanned out
                                              to locked vias that land on the planes)
  import  board.kicad_pcb in.ses out.kicad_pcb
"""
import re
import sys


def trim(src, dst, nets):
    text = open(src).read()
    for net in nets:
        # (net GND\n (pins U1-1 U1-2 ...)) ; KiCad quotes names with special chars.
        pat = re.compile(r'(\(net\s+"?' + re.escape(net) + r'"?\s*\(pins\s+)([^)]*)(\))')
        m = pat.search(text)
        if not m:
            print("net not found in DSN:", net)
            continue
        pins = m.group(2).split()
        text = text[: m.start()] + m.group(1) + pins[0] + m.group(3) + text[m.end():]
        print(f"{net}: {len(pins)} pins -> 1")
    # Inner layers are planes only: forbid signal routing there.
    text = re.sub(r'(\(layer (In1|In2)\.Cu\s*\(type )signal\)', r'\1power)', text)
    # Drop outer-layer plane declarations (none expected, but they would block F/B routing).
    text = re.sub(r'\(plane [^\n]*\((polygon (F|B)\.Cu)[^)]*\)\)\n?', '', text)
    open(dst, "w").write(text)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "trim":
        trim(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        import pcbnew

        board = pcbnew.LoadBoard(sys.argv[2])
        if cmd == "export":
            print("export", pcbnew.ExportSpecctraDSN(board, sys.argv[3]))
        elif cmd == "import":
            print("import", pcbnew.ImportSpecctraSES(board, sys.argv[3]))
            board.Save(sys.argv[4])
