ZWSP = "\u200B"
ZWNJ = "\u200C"

def bits_to_zwc(bits):
    return "".join(ZWNJ if bit else ZWSP for bit in bits)

def zwc_to_bits(text):
    bits = []
    for ch in text:
        if ch == ZWSP:
            bits.append(0)
        elif ch == ZWNJ:
            bits.append(1)
    return bits