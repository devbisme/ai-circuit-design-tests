#!/bin/bash
# Usage: scripts/route_pipeline.sh <netlist> <workdir> [maxpasses]
# Builds the board, fans out plane nets, routes with Freerouting, imports the session.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
KPY=~/bin/kicad10-root/bin/python3.11
FR=~/bin/freerouting/linux-x64/freerouting-2.4.1-linux-x64/bin/freerouting
NET=$(realpath "$1"); W=$2; MP=${3:-30}
mkdir -p "$W"; cd "$W"
B=board.kicad_pcb
$KPY $HERE/build_pcb.py "$NET" $B
$KPY $HERE/fanout.py $B $B
$KPY $HERE/preroute_usb.py $B 2>&1 | grep -v -i "leak\|debug"
python3 $HERE/netclasses.py board.kicad_pro
$KPY $HERE/dsn_tools.py export $B board.dsn
python3 $HERE/dsn_tools.py trim board.dsn board_trim.dsn GND +3V3
echo "routing..."
$FR -de board_trim.dsn -do board.ses -mp $MP -mt 1 > freerouting.log 2>&1 || true
$KPY $HERE/dsn_tools.py import $B board.ses routed.kicad_pcb
cp board.kicad_pro routed.kicad_pro
python3 $HERE/netclasses.py routed.kicad_pro
