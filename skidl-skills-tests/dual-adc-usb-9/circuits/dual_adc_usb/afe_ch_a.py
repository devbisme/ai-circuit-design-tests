"""AFE Channel A — BNC -> compensated attenuator -> OPA810 buffer -> THS4521 MFB AAF/FDA -> ADC ch A
Block from: architecture/block_diagram.md
Interface nets: ADC_AINA_P, ADC_AINA_N, ADC_VCM, VAFE_P, VAFE_N, +3V3A, GND
"""
from skidl import *
from ._afe_common import build_afe_channel


@SubCircuit
def afe_ch_a(ain_p, ain_n, adc_vcm, vafe_p, vafe_n, v3v3a, gnd):
    """Ch A front end. Refs J2, U20, U21, D20, R20-R30, C20-C31.
    Drives ain_p/ain_n; consumes adc_vcm (from ADC CM), vafe_p/vafe_n, v3v3a, gnd."""
    build_afe_channel('A', 20, 'J2', ain_p, ain_n, adc_vcm, vafe_p, vafe_n, v3v3a, gnd)
