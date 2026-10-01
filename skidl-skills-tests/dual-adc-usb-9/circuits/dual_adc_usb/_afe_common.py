"""Shared AFE channel builder for afe_ch_a / afe_ch_b (not a block; helper only).
Topology from architecture/net_plan.md §afe_ch_a: BNC -> 910k/100k (x0.099) compensated
attenuator with BAV199 clamp -> OPA810 follower -> THS4521 MFB anti-alias FDA -> 33R/270pF -> ADC.
Ch B uses refs +20 relative to ch A.
"""
from skidl import Part, Net

_R = 'Resistor_SMD:R_0402_1005Metric'
_C = 'Capacitor_SMD:C_0402_1005Metric'


def _r(ref, value, mpn, lcsc, fp=_R):
    return Part('Device', 'R', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)


def _c(ref, value, mpn, lcsc, fp=_C):
    return Part('Device', 'C', ref=ref, value=value, footprint=fp, MPN=mpn, LCSC=lcsc)


def build_afe_channel(ch, base, j_ref, ain_p, ain_n, adc_vcm, vafe_p, vafe_n, v3v3a, gnd):
    """Build one AFE channel. ch='A'/'B' (net suffix), base=20/40 (ref base), j_ref='J2'/'J3'."""
    R = lambda k: f'R{base + k}'
    C = lambda k: f'C{base + k}'

    bnc = Net(f'BNC_{ch}')
    att = Net(f'ATT_{ch}')
    buf_in = Net(f'BUF_IN_{ch}')
    buf_out = Net(f'BUF_OUT_{ch}')
    mfb_ms = Net(f'MFB_MS_{ch}')
    mfb_mr = Net(f'MFB_MR_{ch}')
    fda_inp = Net(f'FDA_INP_{ch}')
    fda_inn = Net(f'FDA_INN_{ch}')
    fda_outp = Net(f'FDA_OUTP_{ch}')
    fda_outn = Net(f'FDA_OUTN_{ch}')

    # --- BNC input (custom footprint in footprints/ProjectLocal.pretty; verify pads vs physical part before fab) ---
    j = Part('Connector', 'Conn_Coaxial', ref=j_ref, value='BNC',
             footprint='ProjectLocal:KH-BNC50-3511', MPN='KH-BNC50-3511', LCSC='C2837587')
    j[1] += bnc          # In (centre)
    j[2] += gnd          # Ext (shell)

    # --- Compensated 1 MOhm attenuator, ratio 100k/1010k = 0.09901 ---
    r_top = _r(R(0), '910k', 'FRC1206F9103TS', 'C2933768', 'Resistor_SMD:R_1206_3216Metric')
    c_top = _c(C(0), '18pF', 'GCM1885C2A180JA16D', 'C913624', 'Capacitor_SMD:C_0603_1608Metric')
    c_trim = Part('Device', 'C_Trim', ref=C(1), value='2-6pF',
                  footprint='Capacitor_SMD:C_Trimmer_Voltronics_JZ', MPN='STC3MA06-T1', LCSC='C22468120')
    for p in (r_top, c_top, c_trim):
        bnc & p & att
    r_bot = _r(R(1), '100k', '0402WGF1003TCE', 'C25741')
    c_bot = _c(C(2), '200pF', '0402CG201J500NT', 'C301951')
    for p in (r_bot, c_bot):
        att & p & gnd

    # --- BAV199 clamp to AFE rails (by pin number; KiCad BAV99 names unusable) ---
    d = Part('Diode', 'BAV99', ref=f'D{base}', value='BAV199',
             footprint='Package_TO_SOT_SMD:SOT-23', MPN='BAV199', LCSC='C5184419')
    d[1] += vafe_n
    d[2] += vafe_p
    d[3] += att

    # --- Series input resistor + OPA810 unity-gain follower ---
    att & _r(R(2), '1k', '0402WGF1001TCE', 'C11702') & buf_in
    u_buf = Part('Amplifier_Operational', 'OPA810xDBV', ref=f'U{base}', value='OPA810IDBVR',
                 footprint='Package_TO_SOT_SMD:SOT-23-5', MPN='OPA810IDBVR', LCSC='C2833513')
    u_buf[3] += buf_in    # IN+
    u_buf[1] += buf_out   # OUT
    u_buf[4] += buf_out   # IN- (follower)
    u_buf[5] += vafe_p    # V+
    u_buf[2] += vafe_n    # V-
    vafe_p & _c(C(3), '100nF', 'CL05B104KO5NNNC', 'C1525') & gnd
    vafe_n & _c(C(4), '100nF', 'CL05B104KO5NNNC', 'C1525') & gnd

    # --- THS4521 MFB anti-alias FDA (gain 0.909, positive input -> positive code) ---
    u_fda = Part('Amplifier_Difference', 'THS4521IDGK', ref=f'U{base + 1}', value='THS4521IDGKR',
                 footprint='Package_SO:MSOP-8_3x3mm_P0.65mm', MPN='THS4521IDGKR', LCSC='C170157')
    # signal leg: BUF_OUT -> R23 -> MS ; MS -> R27 -> VIN+ ; feedback from VOUT-
    buf_out & _r(R(3), '1.1k', '0402WGF1101TCE', 'C25860') & mfb_ms
    mfb_ms & _c(C(5), '100pF', '0402CG101J500NT', 'C1546') & gnd
    mfb_ms & _r(R(5), '1k', '0402WGF1001TCE', 'C11702') & fda_outn
    mfb_ms & _r(R(7), '270', 'FRC0402F2700TS', 'C2909342') & fda_inp
    fda_inp & _c(C(7), '12pF', '0402CG120J500NT', 'C1547') & fda_outn
    # reference leg: GND -> R24 -> MR ; MR -> R28 -> VIN- ; feedback from VOUT+
    gnd & _r(R(4), '1.1k', '0402WGF1101TCE', 'C25860') & mfb_mr
    mfb_mr & _c(C(6), '100pF', '0402CG101J500NT', 'C1546') & gnd
    mfb_mr & _r(R(6), '1k', '0402WGF1001TCE', 'C11702') & fda_outp
    mfb_mr & _r(R(8), '270', 'FRC0402F2700TS', 'C2909342') & fda_inn
    fda_inn & _c(C(8), '12pF', '0402CG120J500NT', 'C1547') & fda_outp
    u_fda[8] += fda_inp    # VIN+
    u_fda[1] += fda_inn    # VIN-
    u_fda[4] += fda_outp   # VOUT+
    u_fda[5] += fda_outn   # VOUT-
    u_fda[2] += adc_vcm    # VOCM
    u_fda[3] += v3v3a      # VS+
    u_fda[7] += v3v3a      # PD (enabled)
    u_fda[6] += gnd        # VS-
    v3v3a & _c(C(9), '100nF', 'CL05B104KO5NNNC', 'C1525') & gnd
    adc_vcm & _c(C(11), '100nF', 'CL05B104KO5NNNC', 'C1525') & gnd

    # --- Output RC (3rd pole) to ADC ---
    fda_outp & _r(R(9), '33', '0402WGF330JTCE', 'C25105') & ain_p
    fda_outn & _r(R(10), '33', '0402WGF330JTCE', 'C25105') & ain_n
    ain_p & _c(C(10), '270pF', '0402CG271J500NT', 'C501825') & ain_n
