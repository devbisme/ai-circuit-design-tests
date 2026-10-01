"""AFE Channel B — BNC -> compensated attenuator -> OPA810 buffer -> THS4521 MFB AAF/FDA -> ADC ch B
Block from: architecture/block_diagram.md
Interface nets: ADC_AINB_P, ADC_AINB_N, ADC_VCM, VAFE_P, VAFE_N, +3V3A, GND
"""
from skidl import *
from ._afe_common import build_afe_channel


@SubCircuit
def afe_ch_b(ain_p, ain_n, adc_vcm, vafe_p, vafe_n, v3v3a, gnd):
    """Ch B front end, identical to ch A with refs +20. Refs J3, U40, U41, D40, R40-R50, C40-C51.
    Drives ain_p/ain_n; consumes adc_vcm (from ADC CM), vafe_p/vafe_n, v3v3a, gnd."""
    build_afe_channel('B', 40, 'J3', ain_p, ain_n, adc_vcm, vafe_p, vafe_n, v3v3a, gnd)
