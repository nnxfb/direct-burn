'''
帧结构 (18 bytes, 小端序):
        [0:5]   seg  (5 bytes -> 40-bit 数码管段码)
        [5:6]   key  (1 byte  ->  8-bit 按键)
        [6:14]  sw   (8 bytes -> 64-bit 拨码开关)
        [14:18] led  (4 bytes -> 32-bit LED)
'''

SEGMENT_MAP = {
    '1111110': '0', '0110000': '1', '1101101': '2', '1111001': '3',
    '0110011': '4', '1011011': '5', '1011111': '6', '1110000': '7',
    '1111111': '8', '1111011': '9',
}


def parse_data_frame(hex_bytes: list[str]) -> dict[str, int]:
    """Parse 18 hex byte strings into LE-structured frame.

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

    40 bits = 4 groups x 10 bits: [a-g(7) + dp(1) + cs_r(1) + cs_l(1)]

    Returns (digit_string, side) or (None, None).
    """
    groups = [(seg_val >> (10 * i)) & 0x3FF for i in range(4)]

    cs_right = (groups[0] >> 8) & 1
    cs_left  = (groups[0] >> 9) & 1
    side = 'L' if cs_left else 'R' if cs_right else '?'

    digits = []
    for g in reversed(groups):
        seg_bits = g & 0x7F
        seg_str = ''.join(str((seg_bits >> i) & 1) for i in range(7))
        d = SEGMENT_MAP.get(seg_str, '?')
        digits.append(d)

    return ''.join(digits), side

def parse_led_bits(led_val: int) -> list[str]:
    """解析 32-bit LED 值, 返回 4x8 位图字符串.

    led_val 为 32-bit LE 整数 (frame bytes [14:18]).
    返回格式: '00000000 00000000 00000000 00001111'
    从左到右: byte[17] byte[16] byte[15] byte[14] (高位→低位)
    """
    led_groups = []
    for i in range(3, -1, -1):  # byte 17,16,15,14 从高到低
        byte_val = (led_val >> (8 * i)) & 0xFF
        led_groups.append(f'{byte_val:08b}')
    return led_groups