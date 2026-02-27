import wave
import struct
import hashlib
from io import BytesIO


# ---------------- BIT UTILS ----------------
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


# ---------------- RANDOM INDEX GENERATOR ----------------
def get_random_indices(capacity, seed, offset, count):
    rng_seed = int.from_bytes(hashlib.sha256(seed).digest(), "big")
    indices = list(range(offset, capacity))

    for i in range(len(indices) - 1, 0, -1):
        rng_seed = (1103515245 * rng_seed + 12345) & 0x7fffffff
        j = rng_seed % (i + 1)
        indices[i], indices[j] = indices[j], indices[i]

    return indices[:count]


# ---------------- EMBED AUDIO ----------------
def embed_audio(wav_bytes: bytes, header: bytes, body: bytes, seed: bytes) -> bytes:
    input_buffer = BytesIO(wav_bytes)
    output_buffer = BytesIO()

    with wave.open(input_buffer, 'rb') as wf:
        params = wf.getparams()
        frames = wf.readframes(wf.getnframes())

    samples = list(struct.unpack("<" + "h" * (len(frames) // 2), frames))
    capacity = len(samples)

    header_bits = list(bytes_to_bits(header))
    body_bits = list(bytes_to_bits(body))

    if len(header_bits) + len(body_bits) > capacity:
        raise ValueError("Audio file too small for payload")

    # 1️⃣ Embed header sequentially
    for i, bit in enumerate(header_bits):
        samples[i] = (samples[i] & ~1) | bit

    used_bits = len(header_bits)

    # 2️⃣ Embed body randomly AFTER header
    rand_indices = get_random_indices(capacity, seed, used_bits, len(body_bits))

    for bit, idx in zip(body_bits, rand_indices):
        samples[idx] = (samples[idx] & ~1) | bit

    modified_frames = struct.pack("<" + "h" * len(samples), *samples)

    with wave.open(output_buffer, 'wb') as wf:
        wf.setparams(params)
        wf.writeframes(modified_frames)

    return output_buffer.getvalue()


# ---------------- EXTRACT AUDIO ----------------
def extract_audio_header(wav_bytes: bytes, num_bits: int):
    input_buffer = BytesIO(wav_bytes)

    with wave.open(input_buffer, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())

    samples = list(struct.unpack("<" + "h" * (len(frames) // 2), frames))

    bits = []
    for i in range(num_bits):
        bits.append(samples[i] & 1)

    return bits


def extract_audio_body(wav_bytes: bytes, seed: bytes, offset: int, num_bits: int):
    input_buffer = BytesIO(wav_bytes)

    with wave.open(input_buffer, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())

    samples = list(struct.unpack("<" + "h" * (len(frames) // 2), frames))

    rand_indices = get_random_indices(len(samples), seed, offset, num_bits)

    bits = []
    for idx in rand_indices:
        bits.append(samples[idx] & 1)

    return bits

def get_audio_capacity(wav_bytes: bytes, header_size_bytes: int):
    from io import BytesIO
    import wave

    buffer = BytesIO(wav_bytes)

    with wave.open(buffer, 'rb') as wf:
        frames = wf.getnframes()

    capacity_bits = frames
    capacity_bytes = capacity_bits // 8

    usable_bytes = capacity_bytes - header_size_bytes

    return max(0, usable_bytes)