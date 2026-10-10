#!/bin/bash
# Usage: scripts/finalize.sh <routed.kicad_pcb>
# routed board -> kicad/dual_adc_usb.kicad_pcb: leftover plane fanout, outer pours, A* completion
# (plain, then cost-based rip-up keeping the best state), cleanup, fields, fiducials, refill, DRC.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
KPY=~/bin/kicad10-root/bin/python3.11
K=~/bin/kicad10-root/bin/kicad-cli
F="grep -v -i -e leak -e debug -e window"
cd $HERE/../kicad
cp "$1" dual_adc_usb.kicad_pcb
cp "${1%.kicad_pcb}.kicad_pro" dual_adc_usb.kicad_pro
python3 $HERE/netclasses.py dual_adc_usb.kicad_pro
$KPY $HERE/fanout.py dual_adc_usb.kicad_pcb dual_adc_usb.kicad_pcb 2>&1 | $F || true
$KPY $HERE/finish_pcb.py dual_adc_usb.kicad_pcb dual_adc_usb.kicad_pcb 2>&1 | $F || true
$K pcb drc --schematic-parity --format json -o drc.json dual_adc_usb.kicad_pcb > /dev/null 2>&1 || true
echo "== after Freerouting"; python3 $HERE/drc_summary.py drc.json | head -1
ASTAR_MAX_EXP=600000 $KPY $HERE/astar_fix.py dual_adc_usb.kicad_pcb drc.json dual_adc_usb.kicad_pcb 2>&1 | $F || true
$HERE/astar_loop.sh ${2:-10} 2>&1 | grep -E "^pass|^best" || true
$KPY $HERE/cleanup_dangling.py dual_adc_usb.kicad_pcb dual_adc_usb.kicad_pcb 2>&1 | $F || true
$KPY $HERE/widen_narrow.py dual_adc_usb.kicad_pcb 2>&1 | $F || true
$KPY $HERE/sync_fields.py dual_adc_usb.kicad_pcb dual_adc_usb.net 2>&1 | $F || true
$KPY $HERE/add_fiducials.py dual_adc_usb.kicad_pcb 2>&1 | $F || true
$KPY $HERE/finish_pcb.py dual_adc_usb.kicad_pcb dual_adc_usb.kicad_pcb 2>&1 | $F || true
python3 $HERE/netclasses.py dual_adc_usb.kicad_pro
$K pcb drc --schematic-parity --format json -o drc.json dual_adc_usb.kicad_pcb > /dev/null 2>&1 || true
echo "== final DRC"; python3 $HERE/drc_summary.py drc.json
