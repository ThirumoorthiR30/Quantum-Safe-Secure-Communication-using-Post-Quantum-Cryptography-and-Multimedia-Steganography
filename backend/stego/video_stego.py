import cv2
import numpy as np
import hashlib
from io import BytesIO
import random


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


# ---------------- RANDOM GENERATOR ----------------

def get_random_indices(capacity, seed, offset, count):
    rng_seed = int.from_bytes(hashlib.sha256(seed).digest(), "big")

    indices = list(range(offset, capacity))

    for i in range(len(indices) - 1, 0, -1):
        rng_seed = (1103515245 * rng_seed + 12345) & 0x7fffffff
        j = rng_seed % (i + 1)
        indices[i], indices[j] = indices[j], indices[i]

    return indices[:count]


# ---------------- FRAME FLATTEN ----------------

def flatten_frames(frames):
    pixels = []

    for frame in frames:
        h, w, _ = frame.shape
        for y in range(h):
            for x in range(w):
                for c in range(3):
                    pixels.append((frame, y, x, c))

    return pixels


# ---------------- EMBED VIDEO ----------------

def embed_video(video_bytes: bytes, header: bytes, body: bytes, seed: bytes):

    # Save video temporarily in memory
    temp_input = "temp_input.avi"

    with open(temp_input, "wb") as f:
        f.write(video_bytes)

    cap = cv2.VideoCapture(temp_input)

    frames = []
    fps = cap.get(cv2.CAP_PROP_FPS)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()

    if len(frames) == 0:
        raise ValueError("Video contains no frames")

    h, w, _ = frames[0].shape

    pixels = flatten_frames(frames)
    capacity = len(pixels)

    header_bits = list(bytes_to_bits(header))
    body_bits = list(bytes_to_bits(body))

    if len(header_bits) + len(body_bits) > capacity:
        raise ValueError("Video too small for payload")

    # ---------------- HEADER EMBED ----------------

    for i, bit in enumerate(header_bits):
        frame, y, x, c = pixels[i]
        frame[y, x, c] = (frame[y, x, c] & 0xFE) | bit

    used_bits = len(header_bits)

    # ---------------- RANDOM BODY EMBED ----------------

    rand_indices = get_random_indices(capacity, seed, used_bits, len(body_bits))

    for bit, idx in zip(body_bits, rand_indices):
        frame, y, x, c = pixels[idx]
        frame[y, x, c] = (frame[y, x, c] & 0xFE) | bit

    # ---------------- REBUILD VIDEO ----------------

    temp_output = "temp_output.avi"

    fourcc = cv2.VideoWriter_fourcc(*"FFV1")
    out = cv2.VideoWriter(temp_output, fourcc, fps, (w, h))

    for frame in frames:
        out.write(frame)

    out.release()

    with open(temp_output, "rb") as f:
        return f.read()


# ---------------- EXTRACT VIDEO ----------------

def extract_video(video_bytes: bytes, seed: bytes, header_bits_count: int, body_bits_count: int):

    temp_input = "temp_extract.avi"

    with open(temp_input, "wb") as f:
        f.write(video_bytes)

    cap = cv2.VideoCapture(temp_input)

    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()

    pixels = flatten_frames(frames)

    # ---------------- READ HEADER ----------------

    header_bits = []

    for i in range(header_bits_count):
        frame, y, x, c = pixels[i]
        header_bits.append(frame[y, x, c] & 1)

    header_data = bits_to_bytes(header_bits)

    # ---------------- RANDOM BODY ----------------

    rand_indices = get_random_indices(
        len(pixels),
        seed,
        header_bits_count,
        body_bits_count
    )

    body_bits = []

    for idx in rand_indices:
        frame, y, x, c = pixels[idx]
        body_bits.append(frame[y, x, c] & 1)

    body_data = bits_to_bytes(body_bits)

    return header_data, body_data

def get_video_capacity(video_bytes, header_size):
    import cv2
    import tempfile
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".avi") as temp:
        temp.write(video_bytes)
        path = temp.name

    cap = cv2.VideoCapture(path)

    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()

    capacity_bits = frames * width * height * 3
    capacity_bytes = capacity_bits // 8

    usable = capacity_bytes - header_size

    return max(0, usable)