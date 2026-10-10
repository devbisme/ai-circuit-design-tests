#!/bin/bash
# Fab + documentation outputs from kicad/ -> fab/, docs/
HERE=$(cd "$(dirname "$0")" && pwd); K=~/bin/kicad10-root/bin/kicad-cli
cd $HERE/../kicad
rm -rf ../fab; mkdir -p ../fab/gerbers ../docs
$K pcb export gerbers -o ../fab/gerbers/ dual_adc_usb.kicad_pcb > /dev/null 2>&1
$K pcb export drill --format excellon --generate-map --map-format pdf -o ../fab/gerbers/ dual_adc_usb.kicad_pcb > /dev/null 2>&1
$K pcb export pos --format csv --units mm --side both -o ../fab/dual_adc_usb-pos.csv dual_adc_usb.kicad_pcb > /dev/null 2>&1
$K sch export bom --fields 'Reference,Value,Footprint,MPN,Tolerance,Dielectric,${QUANTITY}' \
  --labels 'Refs,Value,Footprint,MPN,Tolerance,Dielectric,Qty' --group-by 'Value,Footprint,MPN' \
  -o ../fab/dual_adc_usb-bom.csv dual_adc_usb.kicad_sch > /dev/null 2>&1
(cd ../fab && zip -qj dual_adc_usb-gerbers.zip gerbers/*)
$K sch export pdf -o dual_adc_usb_schematic.pdf dual_adc_usb.kicad_sch > /dev/null 2>&1
$K pcb export pdf --layers F.Cu,F.SilkS,F.Fab,Edge.Cuts --mode-single -o ../docs/pcb_top_assembly.pdf dual_adc_usb.kicad_pcb > /dev/null 2>&1
$K pcb export pdf --layers B.Cu,B.SilkS,B.Fab,Edge.Cuts --mode-single --mirror -o ../docs/pcb_bottom_assembly.pdf dual_adc_usb.kicad_pcb > /dev/null 2>&1
for side in top bottom; do
  $K pcb render --side $side --width 1600 --height 1100 --quality basic -o ../docs/pcb_3d_$side.png dual_adc_usb.kicad_pcb > /dev/null 2>&1
done
$K sch erc --format json -o erc.json dual_adc_usb.kicad_sch > /dev/null 2>&1
$K pcb drc --schematic-parity --format json -o drc.json dual_adc_usb.kicad_pcb > /dev/null 2>&1
ls ../fab ../docs
