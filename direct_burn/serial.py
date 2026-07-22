# direct_burn/serial.py — 18-byte LE 帧解析 + 数码管解码

SEGMENT_MAP = {
    '1111110': '0', '0110000': '1', '1101101': '2', '1111001': '3',
    '0110011': '4', '1011011': '5', '1011111': '6', '1110000': '7',
    '1111111': '8', '1111011': '9',
}


def parse_18byte_frame(hex_bytes):
    """Parse 18 hex byte strings into LE-structured frame.

    帧结构 (18 bytes, 小端序):
        [0:5]   seg  (5 bytes → 40-bit 数码管段码)
        [5:6]   key  (1 byte  →  8-bit 按键)
        [6:14]  sw   (8 bytes → 64-bit 拨码开关)
        [14:18] led  (4 bytes → 32-bit LED)

    Returns dict(seg, key, sw, led) as ints, or None if not enough bytes.
    """
    if len(hex_bytes) < 18:
        return None

    raw = [int(h, 16) for h in hex_bytes[:18]]

    seg_val = sum(raw[i] << (8 * i) for i in range(5))       # 40-bit LE
    key_val = raw[5]                                           # 8-bit
    sw_val  = sum(raw[6 + i] << (8 * i) for i in range(8))   # 64-bit LE
    led_val = sum(raw[14 + i] << (8 * i) for i in range(4))  # 32-bit LE

    return {'seg': seg_val, 'key': key_val, 'sw': sw_val, 'led': led_val}


def parse_seg_display(seg_val):
    """从 40-bit seg 值解析 4 位数码管 + 左右侧.

    40 bits = 4 groups × 10 bits: [a-g(7) + dp(1) + cs_r(1) + cs_l(1)]

    Returns (digit_string, side) or (None, None).
    """
    groups = [(seg_val >> (10 * i)) & 0x3FF for i in range(4)]

    cs_right = (groups[0] >> 8) & 1
    cs_left  = (groups[0] >> 9) & 1
    side = 'L' if cs_left else 'R' if cs_right else '?'

    digits = []
    for g in groups:
        seg_bits = g & 0x7F
        seg_str = ''.join(str((seg_bits >> i) & 1) for i in range(7))
        d = SEGMENT_MAP.get(seg_str, '?')
        digits.append(d)

    return ''.join(digits), side
