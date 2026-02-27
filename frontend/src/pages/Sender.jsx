import React, { useState, useRef } from "react";
import axios from "axios";

export default function Sender() {
  const [publicKey, setPublicKey] = useState(null);
  const [coverFile, setCoverFile] = useState(null);
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");

  const publicKeyRef = useRef();
  const coverFileRef = useRef();
  const messageRef = useRef();

  const BACKEND = "http://127.0.0.1:8000";

  const handleEncryptHide = async () => {
    if (!publicKey || !coverFile || !message) {
      alert("⚠ Upload public key, cover file and enter message!");
      return;
    }

    const formData = new FormData();
    formData.append("public_key", publicKey);
    formData.append("cover_file", coverFile);
    formData.append("message", message);

    try {
      setStatus("🛡 Encrypting with Kyber + Embedding payload...");

      const res = await axios.post(`${BACKEND}/sender/hide`, formData, {
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;

      const originalExt = coverFile.name.split(".").pop().toLowerCase();

      const imageTypes = ["png", "jpg", "jpeg"];
      const audioTypes = ["wav", "mp3"];
      const videoTypes = ["mp4", "avi", "mkv", "mov"];

      let outputExt;
      if (originalExt === "txt") outputExt = "txt";
      else if (audioTypes.includes(originalExt)) outputExt = "wav";
      else if (videoTypes.includes(originalExt)) outputExt = "avi";
      else if (imageTypes.includes(originalExt)) outputExt = "png";
      else outputExt = originalExt;

      link.setAttribute("download", `stego_${Date.now()}.${outputExt}`);
      document.body.appendChild(link);
      link.click();

      setStatus("✅ Stego file generated successfully!");

      // 🔥 AUTO RESET AFTER SUCCESS
      setPublicKey(null);
      setCoverFile(null);
      setMessage("");
      publicKeyRef.current.value = "";
      coverFileRef.current.value = "";
      messageRef.current.value = "";

    } catch (err) {
      if (err.response?.data) {
        const reader = new FileReader();
        reader.onload = () => {
          try {
            const data = JSON.parse(reader.result);
            setStatus(`❌ ${data.error}`);
          } catch {
            setStatus("❌ Encryption failed!");
          }
        };
        reader.readAsText(err.response.data);
      } else {
        setStatus("❌ Encryption failed!");
      }
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
        textShadow: "0 0 10px #00ffcc"
      }}>
        🔒 Quantum Secure Sender Terminal
      </h1>

      <div style={cardStyle}>

        <label>Upload Receiver Public Key (.bin)</label>
        <input
          type="file"
          accept=".bin"
          ref={publicKeyRef}
          onChange={(e) => setPublicKey(e.target.files[0])}
          style={inputStyle}
        />

        <div style={{ marginTop: "20px" }}>
          <label>Upload Cover File</label>
          <input
            type="file"
            accept="image/png,image/jpeg,.txt,.wav,.mp3,.mp4,.avi,.mov,.mkv"
            ref={coverFileRef}
            onChange={(e) => setCoverFile(e.target.files[0])}
            style={inputStyle}
          />
        </div>

        <div style={{ marginTop: "20px" }}>
          <label>Enter Secret Message</label>
          <textarea
            rows="5"
            ref={messageRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            style={textareaStyle}
          />
        </div>

        <button
          onClick={handleEncryptHide}
          style={{ ...buttonStyle, marginTop: "25px" }}
        >
          Encrypt + Hide
        </button>
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
  background: "rgba(0,0,0,0.75)",
  padding: "30px",
  borderRadius: "10px",
  border: "1px solid #00ffcc",
  boxShadow: "0 0 15px rgba(0,255,204,0.4)",
  maxWidth: "700px",
  margin: "40px auto"
};

const buttonStyle = {
  padding: "12px 25px",
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
  padding: "6px",
  background: "#111",
  color: "#00ffcc",
  border: "1px solid #00ffcc",
  width: "100%"
};

const textareaStyle = {
  width: "100%",
  marginTop: "8px",
  padding: "10px",
  background: "#111",
  color: "#00ffcc",
  border: "1px solid #00ffcc",
  fontFamily: "Courier New"
};