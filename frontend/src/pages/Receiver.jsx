import React, { useState, useRef } from "react";
import axios from "axios";

export default function Receiver() {
  const [privateKey, setPrivateKey] = useState(null);
  const [stegoFile, setStegoFile] = useState(null);
  const [decodedMessage, setDecodedMessage] = useState("");
  const [status, setStatus] = useState("");

  const privateKeyRef = useRef();
  const stegoFileRef = useRef();

  const BACKEND = "http://127.0.0.1:8000";

  // ---------------- KEY GENERATION ----------------
  const handleGenerateKeys = async () => {
    try {
      setStatus("🔐 Generating quantum-safe keys...");

      const res = await axios.post(`${BACKEND}/generate-keys`);
      const { public_key, private_key } = res.data;

      const downloadBinary = (filename, base64Data) => {
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);

        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }

        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: "application/octet-stream" });

        const link = document.createElement("a");
        link.href = window.URL.createObjectURL(blob);
        link.download = filename;
        link.click();
      };

      downloadBinary("public_key.bin", public_key);
      downloadBinary("private_key.bin", private_key);

      setStatus("✅ Quantum Key Pair Generated Successfully!");
    } catch (err) {
      setStatus("❌ Key generation failed!");
    }
  };

  // ---------------- EXTRACTION ----------------
  const handleExtractDecrypt = async () => {
    if (!privateKey || !stegoFile) {
      alert("⚠ Upload Private Key and Stego File!");
      return;
    }

    const formData = new FormData();
    formData.append("private_key", privateKey);
    formData.append("stego_file", stegoFile);

    try {
      setStatus("🛡 Extracting and decrypting secure payload...");

      const res = await axios.post(
        `${BACKEND}/receiver/extract`,
        formData
      );

      setDecodedMessage(res.data.message);
      setStatus("✅ Decryption Successful! Secure Channel Verified.");

      // 🔥 AUTO RESET FILE INPUTS AFTER SUCCESS
      setPrivateKey(null);
      setStegoFile(null);
      privateKeyRef.current.value = "";
      stegoFileRef.current.value = "";

    } catch (err) {
      if (err.response?.data?.error) {
        setStatus(`❌ ${err.response.data.error}`);
      } else {
        setStatus("❌ Extraction failed!");
      }
      setDecodedMessage("");
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0f2027, #203a43, #2c5364)",
      color: "#00ffcc",
      padding: "40px",
      fontFamily: "Courier New"
    }}>

      <h1 style={{
        textAlign: "center",
        color: "#00ffcc",
        textShadow: "0 0 10px #00ffcc"
      }}>
        🔐 Quantum Secure Receiver Terminal
      </h1>

      {/* KEY GENERATION */}
      <div style={cardStyle}>
        <h3>Step 1: Generate Kyber Key Pair</h3>

        <button style={buttonStyle} onClick={handleGenerateKeys}>
          Generate Keys
        </button>

        <p style={{ marginTop: "15px", color: "#ccc" }}>
          Public Key → Share with Sender <br />
          Private Key → Keep Secret
        </p>
      </div>

      {/* EXTRACTION */}
      <div style={cardStyle}>
        <h3>Step 2: Extract & Decrypt</h3>

        <div>
          <label>Upload Private Key (.bin)</label>
          <input
            type="file"
            accept=".bin"
            ref={privateKeyRef}
            onChange={(e) => setPrivateKey(e.target.files[0])}
            style={inputStyle}
          />
        </div>

        <div style={{ marginTop: "15px" }}>
          <label>Upload Stego File</label>
          <input
            type="file"
            accept="image/png,image/jpeg,.txt,.wav,.avi"
            ref={stegoFileRef}
            onChange={(e) => setStegoFile(e.target.files[0])}
            style={inputStyle}
          />
        </div>

        <button
          style={{ ...buttonStyle, marginTop: "20px" }}
          onClick={handleExtractDecrypt}
        >
          Extract + Decrypt
        </button>

        <div style={{
          marginTop: "20px",
          background: "#000",
          padding: "15px",
          borderRadius: "8px",
          border: "1px solid #00ffcc",
          boxShadow: "0 0 10px #00ffcc"
        }}>
          <h4 style={{ color: "#00ffcc" }}>Decrypted Payload:</h4>
          <div style={{
            minHeight: "60px",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            maxHeight: "200px",
            overflowY: "auto"
          }}>
            {decodedMessage || "Awaiting secure transmission..."}
          </div>
        </div>
      </div>

      {status && (
        <p style={{
          marginTop: "25px",
          fontWeight: "bold",
          textAlign: "center",
          color: status.includes("✅") ? "#00ff00" : "#ff4d4d",
          textShadow: status.includes("✅")
            ? "0 0 10px #00ff00"
            : "0 0 10px #ff0000"
        }}>
          {status}
        </p>
      )}
    </div>
  );
}

// 🔥 Styles
const cardStyle = {
  background: "rgba(0,0,0,0.7)",
  padding: "25px",
  borderRadius: "10px",
  marginBottom: "30px",
  border: "1px solid #00ffcc",
  boxShadow: "0 0 15px rgba(0,255,204,0.4)"
};

const buttonStyle = {
  padding: "10px 20px",
  background: "#00ffcc",
  color: "#000",
  border: "none",
  borderRadius: "5px",
  cursor: "pointer",
  fontWeight: "bold",
  boxShadow: "0 0 10px #00ffcc"
};

const inputStyle = {
  display: "block",
  marginTop: "8px",
  padding: "5px",
  background: "#111",
  color: "#00ffcc",
  border: "1px solid #00ffcc"
};