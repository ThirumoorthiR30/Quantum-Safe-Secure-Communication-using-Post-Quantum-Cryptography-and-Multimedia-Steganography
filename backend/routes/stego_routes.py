from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from io import BytesIO
import struct

from crypto.crypto_utils import *
from stego.image_stego import *
from stego.text_stego import *

router = APIRouter()


# ===========================
# UNIFIED SENDER (IN-MEMORY)
# ===========================
@router.post("/sender/hide")
async def hide_file(
    public_key: UploadFile = File(...),
    cover_file: UploadFile = File(...),
    message: str = Form(...)
):
    pk = await public_key.read()
    file_bytes = await cover_file.read()
    filename = cover_file.filename.lower()

    kyber_ct, shared_secret = kyber_encapsulate(pk)
    aes_key = derive_aes_key(shared_secret)
    nonce, ciphertext = aes_encrypt(message.encode(), aes_key)

    header = (
        MAGIC +
        struct.pack(">I", len(kyber_ct)) +
        kyber_ct +
        nonce +
        struct.pack(">I", len(ciphertext))
    )

    # IMAGE MODE
    if filename.endswith((".png", ".jpg", ".jpeg")):
        from PIL import Image

        img = Image.open(BytesIO(file_bytes)).convert("RGB")
        pixels = [list(p) for p in img.getdata()]

        header_bits = list(bytes_to_bits(header))
        body_bits = list(bytes_to_bits(ciphertext))

        used_bits = embed_sequential_lsb(pixels, header_bits, 0)
        embed_random_lsb(pixels, body_bits, aes_key, used_bits)

        img.putdata([tuple(p) for p in pixels])

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return StreamingResponse(buffer, media_type="image/png")

    # TEXT MODE
    elif filename.endswith(".txt"):
        original_text = file_bytes.decode("utf-8")

        payload_bits = list(bytes_to_bits(header + ciphertext))
        zwc_payload = bits_to_zwc(payload_bits)

        stego_text = original_text + "\n\n" + zwc_payload

        return StreamingResponse(
            BytesIO(stego_text.encode("utf-8")),
            media_type="text/plain"
        )
        
    elif filename.endswith(".wav"):
        from stego.audio_stego import embed_audio, get_audio_capacity

        payload_header = header
        payload_body = ciphertext

        header_size = len(header)
        max_bytes = get_audio_capacity(file_bytes, header_size)

        if len(ciphertext) > max_bytes:
            return JSONResponse({
                "error": "Message too large for this audio",
                "max_bytes": max_bytes,
                "ciphertext_bytes": len(ciphertext)
            }, status_code=400)

        try:
            stego_audio = embed_audio(
                file_bytes,
                payload_header,
                payload_body,
                aes_key
            )
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        return StreamingResponse(
            BytesIO(stego_audio),
            media_type="audio/wav"
        )
    
    elif filename.endswith(".mp3"):
        from pydub import AudioSegment
        from stego.audio_stego import embed_audio

        try:
            audio = AudioSegment.from_file(BytesIO(file_bytes), format="mp3")
            wav_buffer = BytesIO()
            audio.export(wav_buffer, format="wav")
            wav_bytes = wav_buffer.getvalue()
        except Exception:
            return JSONResponse({"error": "MP3 conversion failed"}, status_code=400)

        payload_header = header
        payload_body = ciphertext

        try:
            stego_audio = embed_audio(
                wav_bytes,
                payload_header,
                payload_body,
                aes_key
            )
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        return StreamingResponse(
            BytesIO(stego_audio),
            media_type="audio/wav"
        )
    
    elif filename.endswith((".mp4", ".avi", ".mov", ".mkv")):

        import cv2
        from stego.video_stego import embed_video, get_video_capacity
        from tempfile import NamedTemporaryFile

        # Convert uploaded video to AVI
        with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_in:
            temp_in.write(file_bytes)
            temp_in_path = temp_in.name

        cap = cv2.VideoCapture(temp_in_path)

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"XVID")

        with NamedTemporaryFile(delete=False, suffix=".avi") as temp_out:
            temp_out_path = temp_out.name

        out = cv2.VideoWriter(temp_out_path, fourcc, fps, (width, height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        cap.release()
        out.release()

        with open(temp_out_path, "rb") as f:
            avi_bytes = f.read()

        # -------- CAPACITY CHECK --------
        header_size = len(header)

        max_bytes = get_video_capacity(avi_bytes, header_size)

        if len(ciphertext) > max_bytes:
            return JSONResponse({
                "error": "Message too large for this video",
                "max_bytes": max_bytes,
                "ciphertext_bytes": len(ciphertext)
            }, status_code=400)

        # -------- EMBED VIDEO --------
        try:
            stego_video = embed_video(
                avi_bytes,
                header,
                ciphertext,
                aes_key
            )
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)

        return StreamingResponse(
            BytesIO(stego_video),
            media_type="video/x-msvideo"
        )

    else:
        return JSONResponse({"error": "Unsupported file type"}, status_code=400)


# ===========================
# UNIFIED RECEIVER (IN-MEMORY)
# ===========================
@router.post("/receiver/extract")
async def extract_file(
    private_key: UploadFile = File(...),
    stego_file: UploadFile = File(...)
):
    sk = await private_key.read()
    file_bytes = await stego_file.read()
    filename = stego_file.filename.lower()

    # IMAGE MODE
    if filename.endswith((".png", ".jpg", ".jpeg")):
        from PIL import Image

        img = Image.open(BytesIO(file_bytes)).convert("RGB")
        pixels = [list(p) for p in img.getdata()]

        magic_bits, idx = extract_sequential_lsb(pixels, 4 * 8, 0)
        magic = bits_to_bytes(magic_bits)

        if magic != MAGIC:
            return JSONResponse({"error": "No hidden data found"}, status_code=400)

        ctlen_bits, idx = extract_sequential_lsb(pixels, 4 * 8, idx)
        ct_len = struct.unpack(">I", bits_to_bytes(ctlen_bits))[0]

        kyber_ct_bits, idx = extract_sequential_lsb(pixels, ct_len * 8, idx)
        kyber_ct = bits_to_bytes(kyber_ct_bits)

        nonce_bits, idx = extract_sequential_lsb(pixels, 12 * 8, idx)
        nonce = bits_to_bytes(nonce_bits)

        msglen_bits, idx = extract_sequential_lsb(pixels, 4 * 8, idx)
        msg_len = struct.unpack(">I", bits_to_bytes(msglen_bits))[0]

        shared_secret = kyber_decapsulate(sk, kyber_ct)
        aes_key = derive_aes_key(shared_secret)

        body_bits = extract_random_lsb(pixels, aes_key, idx, msg_len * 8)
        ciphertext = bits_to_bytes(body_bits)

        plaintext = aes_decrypt(nonce, ciphertext, aes_key).decode()

        return JSONResponse({"message": plaintext})

    # TEXT MODE
    elif filename.endswith(".txt"):
        text = file_bytes.decode("utf-8")
        bits = zwc_to_bits(text)
        data = bits_to_bytes(bits)

        if data[:4] != MAGIC:
            return JSONResponse({"error": "No hidden data found"}, status_code=400)

        idx = 4
        ct_len = struct.unpack(">I", data[idx:idx+4])[0]
        idx += 4

        kyber_ct = data[idx:idx+ct_len]
        idx += ct_len

        nonce = data[idx:idx+12]
        idx += 12

        msg_len = struct.unpack(">I", data[idx:idx+4])[0]
        idx += 4

        ciphertext = data[idx:idx+msg_len]

        shared_secret = kyber_decapsulate(sk, kyber_ct)
        aes_key = derive_aes_key(shared_secret)

        plaintext = aes_decrypt(nonce, ciphertext, aes_key).decode()

        return JSONResponse({"message": plaintext})

    elif filename.endswith(".wav"):
        from stego.audio_stego import extract_audio_header, extract_audio_body

        # Step 1: extract sequential header bits
        header_bits = extract_audio_header(file_bytes, 8192)
        header_data = bits_to_bytes(header_bits)

        if header_data[:4] != MAGIC:
            return JSONResponse({"error": "No hidden data found"}, status_code=400)

        idx = 4
        ct_len = struct.unpack(">I", header_data[idx:idx+4])[0]
        idx += 4

        kyber_ct = header_data[idx:idx+ct_len]
        idx += ct_len

        nonce = header_data[idx:idx+12]
        idx += 12

        msg_len = struct.unpack(">I", header_data[idx:idx+4])[0]
        idx += 4

        # Step 2: derive AES key
        shared_secret = kyber_decapsulate(sk, kyber_ct)
        aes_key = derive_aes_key(shared_secret)

        # Step 3: extract ciphertext randomly
        body_bits = extract_audio_body(
            file_bytes,
            aes_key,
            idx * 8,
            msg_len * 8
        )

        ciphertext = bits_to_bytes(body_bits)

        # Step 4: decrypt
        plaintext = aes_decrypt(nonce, ciphertext, aes_key).decode()

        return JSONResponse({"message": plaintext})
    
    elif filename.endswith(".avi"):

        from stego.video_stego import extract_video

        # Read first large chunk for header
        header_bits_count = 65536

        header_data, _ = extract_video(
            file_bytes,
            b"temp",
            header_bits_count,
            0
        )

        if header_data[:4] != MAGIC:
            return JSONResponse({"error": "No hidden data found"}, status_code=400)

        idx = 4

        ct_len = struct.unpack(">I", header_data[idx:idx+4])[0]
        idx += 4

        kyber_ct = header_data[idx:idx+ct_len]
        idx += ct_len

        nonce = header_data[idx:idx+12]
        idx += 12

        msg_len = struct.unpack(">I", header_data[idx:idx+4])[0]
        idx += 4

        shared_secret = kyber_decapsulate(sk, kyber_ct)
        aes_key = derive_aes_key(shared_secret)

        total_bits = (4 + 4 + ct_len + 12 + 4 + msg_len) * 8

        header_data, body_data = extract_video(
            file_bytes,
            aes_key,
            idx * 8,
            msg_len * 8
        )

        ciphertext = body_data

        plaintext = aes_decrypt(nonce, ciphertext, aes_key).decode()

        return JSONResponse({"message": plaintext})

    else:
        return JSONResponse({"error": "Unsupported file type"}, status_code=400)