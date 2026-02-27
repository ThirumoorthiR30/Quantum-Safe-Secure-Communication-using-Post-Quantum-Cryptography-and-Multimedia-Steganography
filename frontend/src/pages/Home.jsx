import React from "react";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        fontFamily: "Arial",
        background: "linear-gradient(135deg, #252629 0%, #764ba2 100%)",
        color: "white",
      }}
    >
      <h1 style={{ fontSize: "48px", marginBottom: "20px",textAlign:"center" }}>
        Quantum-Safe Secure Communication using Post Quantum Cryptography and Multimedia Steganography
      </h1>
      <p style={{ fontSize: "20px", marginBottom: "50px" }}>
        ML-KEM (Kyber) + AES-256-GCM
      </p>

      <div style={{ display: "flex", gap: "30px" }}>
        <button
          onClick={() => navigate("/sender")}
          style={{
            padding: "20px 40px",
            fontSize: "20px",
            cursor: "pointer",
            backgroundColor: "#ff6b6b",
            color: "white",
            border: "none",
            borderRadius: "10px",
            boxShadow: "0 4px 6px rgba(0,0,0,0.3)",
          }}
        >
          Sender Mode
        </button>

        <button
          onClick={() => navigate("/receiver")}
          style={{
            padding: "20px 40px",
            fontSize: "20px",
            cursor: "pointer",
            backgroundColor: "#51cf66",
            color: "white",
            border: "none",
            borderRadius: "10px",
            boxShadow: "0 4px 6px rgba(0,0,0,0.3)",
          }}
        >
          Receiver Mode
        </button>
      </div>
    </div>
  );
}