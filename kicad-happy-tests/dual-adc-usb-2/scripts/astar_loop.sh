#!/bin/bash
# Repeated DRC -> A* (with cost-based rip-up) passes on kicad/dual_adc_usb.kicad_pcb; keeps the best.
HERE=$(cd "$(dirname "$0")" && pwd)
KPY=~/bin/kicad10-root/bin/python3.11; K=~/bin/kicad10-root/bin/kicad-cli
cd $HERE/../kicad
best=999
for pass in $(seq 1 ${1:-8}); do
  $K pcb drc --schematic-parity --format json -o drc.json dual_adc_usb.kicad_pcb > /dev/null 2>&1
  n=$(python3 -c "import json;print(len([u for u in json.load(open('drc.json'))['unconnected_items'] if not u['items'][0]['description'].startswith('Zone')]))")
  echo "pass $pass: unconnected $n"
  if [ "$n" -lt "$best" ]; then best=$n; cp dual_adc_usb.kicad_pcb .astar_best.kicad_pcb; fi
  [ "$n" = 0 ] && break
  ASTAR_RIPUP=1 ASTAR_MAX_EXP=${ASTAR_MAX_EXP:-600000} $KPY $HERE/astar_fix.py dual_adc_usb.kicad_pcb drc.json dual_adc_usb.kicad_pcb 2>&1 | grep -v -i "debug\|leak\|window"
done
cp .astar_best.kicad_pcb dual_adc_usb.kicad_pcb
$KPY $HERE/finish_pcb.py dual_adc_usb.kicad_pcb dual_adc_usb.kicad_pcb 2>&1 | grep finished
echo "best: $best"
rm -f .astar_best.kicad_pcb
