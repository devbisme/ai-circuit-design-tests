# Local environment (verified by the orchestrator, 2026-09-08)

There is NO `.venv/` in this project. Use the system interpreter.

- Python: `python3` on PATH is pyenv 3.14.6, with SKiDL **3.0.0** installed.
- KiCad symbol libraries: `/usr/share/kicad/symbols` (224 `.kicad_sym` files).
  WARNING: the ambient `KICAD_SYMBOL_DIR` env var points at `/usr/share/kicad/library`,
  which holds only LEGACY KiCad-5 `.lib`/`.dcm` files. Do NOT use it. Always pass
  `KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols` explicitly.
- Footprints: `/usr/share/kicad/footprints`

## Run a circuit

Monolithic:
```bash
\
KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols \
KICAD9_FOOTPRINT_DIR=/usr/share/kicad/footprints \
python3 circuits/dual_adc_usb.py
```

Modular:
```bash
cd /home/devb/projects/AI/skidl-skills-tests/dual-adc-usb-2 && \
KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols \
KICAD9_FOOTPRINT_DIR=/usr/share/kicad/footprints \
python3 -m circuits.dual_adc_usb
```

SKiDL is **3.0.0**, not 2.x — verify symbol/API details against the installed package
(`python3 -c "import skidl, os; print(os.path.dirname(skidl.__file__))"`) rather than
assuming 2.x behavior. Always confirm a symbol exists in the installed libraries before
using it:
```bash
grep -l "SYMBOLNAME" /usr/share/kicad/symbols/*.kicad_sym
```
