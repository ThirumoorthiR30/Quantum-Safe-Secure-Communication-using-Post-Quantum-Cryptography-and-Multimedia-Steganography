from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.stego_routes import router as stego_router
from routes.key_routes import router as key_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stego_router)
app.include_router(key_router)

@app.get("/")
def root():
    return {"message": "Quantum-Safe Multi-Media Steganography Backend Running"}