/**
 * AuthForm — login / register UI.
 */
import { useState } from "react";

const inputStyle = {
  width: "100%", background: "#1A1D27", border: "1px solid #2A2D3A",
  borderRadius: 8, padding: "10px 14px", color: "#E2E8F0", fontSize: 14,
  outline: "none", boxSizing: "border-box", fontFamily: "'Inter', sans-serif",
  marginBottom: 12, transition: "border-color 0.2s",
};

export default function AuthForm({ onLogin, onRegister }) {
  const [mode, setMode]     = useState("login");
  const [form, setForm]     = useState({ email: "", password: "", username: "", fullName: "" });
  const [error, setError]   = useState("");
  const [loading, setLoading] = useState(false);

  const update = (k) => (e) => setForm(p => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.email.includes("@")) { setError("Please enter a valid email address."); return; }
    if (form.password.length < 6) { setError("Password must be at least 6 characters."); return; }

    setLoading(true);
    try {
      if (mode === "login") {
        await onLogin(form.email, form.password);
      } else {
        if (!form.username) { setError("Username is required."); setLoading(false); return; }
        await onRegister(form.username, form.email, form.password, form.fullName);
      }
    } catch (err) {
      setError(err.message || "An error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setError("");
    setLoading(true);
    try {
      await onLogin("guest@techmart.com", "guest123");
    } catch (err) {
      setError(err.message || "Guest login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", background: "#0A0C14",
      display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
    }}>
      <div style={{
        background: "#0F1117", border: "1px solid #1E2130", borderRadius: 20,
        padding: "40px 36px", width: "100%", maxWidth: 420,
      }}>
        {/* Logo */}
        <div style={{ textAlign: "center", fontFamily: "'Space Grotesk', sans-serif", fontSize: 28, fontWeight: 700, color: "#fff", marginBottom: 6 }}>
          TechMart<span style={{ color: "#6366F1" }}>.</span>AI
        </div>
        <div style={{ textAlign: "center", fontSize: 14, color: "#64748B", marginBottom: 32 }}>
          AI-Powered Multi-Agent Customer Support
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", background: "#1A1D27", borderRadius: 10, padding: 3, marginBottom: 28 }}>
          {["login", "register"].map(m => (
            <button key={m} onClick={() => { setMode(m); setError(""); }}
              style={{
                flex: 1, padding: "8px 0", borderRadius: 8, border: "none",
                cursor: "pointer", fontSize: 14, fontWeight: 500,
                background: mode === m ? "#6366F1" : "transparent",
                color: mode === m ? "#fff" : "#64748B",
                fontFamily: "'Inter', sans-serif", transition: "all 0.15s",
              }}>
              {m === "login" ? "Sign In" : "Create Account"}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div style={{ background: "#EF444415", border: "1px solid #EF444430", color: "#FCA5A5", padding: "10px 14px", borderRadius: 8, fontSize: 13, marginBottom: 16 }}>
            ⚠️ {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          {mode === "register" && (
            <>
              <input style={inputStyle} placeholder="Full Name (optional)"
                value={form.fullName} onChange={update("fullName")} />
              <input style={inputStyle} placeholder="Username *"
                value={form.username} onChange={update("username")} />
            </>
          )}
          <input style={inputStyle} type="email" placeholder="Email Address *"
            value={form.email} onChange={update("email")} autoComplete="email" />
          <input style={inputStyle} type="password" placeholder="Password * (min 6 chars)"
            value={form.password} onChange={update("password")} autoComplete={mode === "login" ? "current-password" : "new-password"} />

          <button type="submit" disabled={loading}
            style={{
              width: "100%", padding: 12, marginTop: 4,
              background: loading ? "#4B4E6A" : "#6366F1", color: "#fff",
              border: "none", borderRadius: 10, fontSize: 15, fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer", fontFamily: "'Inter', sans-serif",
              transition: "background 0.15s",
            }}>
            {loading ? "Please wait…" : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        {/* Guest */}
        <div style={{ marginTop: 12, textAlign: "center", fontSize: 13, color: "#475569" }}>
          <span
            style={{ cursor: "pointer", textDecoration: "underline", color: "#64748B" }}
            onClick={handleGuestLogin}
          >
            Continue as Guest
          </span>
        </div>
      </div>
    </div>
  );
}
