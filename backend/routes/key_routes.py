from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pqcrypto.kem import ml_kem_512
import base64

router = APIRouter()

@router.post("/generate-keys")
def generate_keys():
    pk, sk = ml_kem_512.generate_keypair()

    return JSONResponse({
        "public_key": base64.b64encode(pk).decode(),
        "private_key": base64.b64encode(sk).decode()
    })