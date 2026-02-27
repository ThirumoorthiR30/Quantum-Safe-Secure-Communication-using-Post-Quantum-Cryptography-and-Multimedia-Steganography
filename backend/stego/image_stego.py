from PIL import Image
import hashlib

def bytes_to_bits(data: bytes):
    for b in data:
        for i in range(7, -1, -1):
            yield (b >> i) & 1

def bits_to_bytes(bits):
    out = bytearray()
    b = 0
    count = 0
    for bit in bits:
        b = (b << 1) | bit
        count += 1
        if count == 8:
            out.append(b)
            b = 0
            count = 0
    return bytes(out)

def embed_sequential_lsb(pixels, payload_bits, start_index=0):
    idx = start_index
    for bit in payload_bits:
        px = idx // 3
        ch = idx % 3
        pixels[px][ch] = (pixels[px][ch] & 0xFE) | bit
        idx += 1
    return idx

def extract_sequential_lsb(pixels, num_bits, start_index=0):
    bits = []
    idx = start_index
    for _ in range(num_bits):
        px = idx // 3
        ch = idx % 3
        bits.append(pixels[px][ch] & 1)
        idx += 1
    return bits, idx

def get_random_indices(capacity, seed, offset, count):
    rng_seed = int.from_bytes(hashlib.sha256(seed).digest(), "big")
    available = list(range(offset, capacity))

    if count > len(available):
        raise ValueError("Not enough capacity")

    for i in range(len(available) - 1, 0, -1):
        rng_seed = (1103515245 * rng_seed + 12345) & 0x7fffffff
        j = rng_seed % (i + 1)
        available[i], available[j] = available[j], available[i]

    return available[:count]

def embed_random_lsb(pixels, bits, seed, used_bits):
    capacity = len(pixels) * 3
    indices = get_random_indices(capacity, seed, used_bits, len(bits))
    for bit, idx in zip(bits, indices):
        px = idx // 3
        ch = idx % 3
        pixels[px][ch] = (pixels[px][ch] & 0xFE) | bit

def extract_random_lsb(pixels, seed, used_bits, num_bits):
    capacity = len(pixels) * 3
    indices = get_random_indices(capacity, seed, used_bits, num_bits)
    bits = []
    for idx in indices:
        px = idx // 3
        ch = idx % 3
        bits.append(pixels[px][ch] & 1)
    return bits