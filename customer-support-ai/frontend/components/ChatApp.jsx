/**
 * ChatApp.jsx
 * Full chat UI that communicates with the FastAPI backend.
 * For the self-contained demo, see the TechMartSupport.jsx artifact.
 */
import { useEffect, useRef, useState } from "react";
import api from "../services/api";

const AGENTS = {
  billing: { label: "Billing Agent", color: "#6366F1", icon: "💳" },
  technical: { label: "Tech Support", color: "#10B981", icon: "🔧" },
  product: { label: "Product Agent", color: "#F59E0B", icon: "📦" },
  complaint: { label: "Complaint Agent", color: "#EF4444", icon: "📢" },
  faq: { label: "FAQ Agent", color: "#8B5CF6", icon: "❓" },
};

const createSessionId = () =>
  `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

const centeredShellStyle = {
  minHeight: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  background: "#0A0C14",
};

const authCardStyle = {
  background: "#0F1117",
  border: "1px solid #1E2130",
  borderRadius: 20,
  padding: 40,
  width: 380,
};

export default function ChatApp() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [sessionId] = useState(createSessionId);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [authForm, setAuthForm] = useState({ email: "", password: "" });
  const [authError, setAuthError] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    let cancelled = false;

    const restoreSession = async () => {
      const token = api.getStoredToken();
      if (!token) {
        if (!cancelled) {
          setAuthLoading(false);
        }
        return;
      }

      api.setToken(token);

      try {
        const currentUser = await api.getMe();
        if (!cancelled) {
          setUser(currentUser);
        }
      } catch {
        api.logout();
        if (!cancelled) {
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setAuthLoading(false);
        }
      }
    };

    restoreSession();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogin = async (event) => {
    event.preventDefault();
    setAuthError("");

    try {
      const data = await api.login(authForm.email, authForm.password);
      setUser(data.user);
    } catch (err) {
      setAuthError(err.message || "Unable to sign in.");
    }
  };

  const send = async () => {
    const text = input.trim();
    if (!text || loading) {
      return;
    }

    setInput("");

    const userMessage = { role: "user", content: text, timestamp: new Date() };
    const history = messages.map((message) => ({
      role: message.role,
      content: message.content,
    }));

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await api.sendMessage(text, sessionId, history);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.response,
          agent: response.agent,
          secondaryAgents: response.secondary_agents || [],
          escalated: response.escalated,
          sources: response.sources || [],
          timestamp: new Date(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
          agent: "faq",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div style={centeredShellStyle}>
        <div style={authCardStyle}>
          <h2
            style={{
              color: "#fff",
              textAlign: "center",
              marginBottom: 8,
              fontFamily: "Space Grotesk, sans-serif",
            }}
          >
            TechMart.AI
          </h2>
          <p style={{ color: "#64748B", textAlign: "center", margin: 0, fontSize: 14 }}>
            Restoring your session...
          </p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div style={centeredShellStyle}>
        <div style={authCardStyle}>
          <h2
            style={{
              color: "#fff",
              textAlign: "center",
              marginBottom: 8,
              fontFamily: "Space Grotesk, sans-serif",
            }}
          >
            TechMart.AI
          </h2>
          <p style={{ color: "#64748B", textAlign: "center", marginBottom: 28, fontSize: 14 }}>
            Sign in to continue
          </p>
          {authError && (
            <div
              style={{
                background: "#EF444415",
                border: "1px solid #EF444430",
                color: "#FCA5A5",
                padding: "10px 14px",
                borderRadius: 8,
                marginBottom: 16,
                fontSize: 13,
              }}
            >
              {authError}
            </div>
          )}
          <form onSubmit={handleLogin}>
            <input
              style={{
                width: "100%",
                background: "#1A1D27",
                border: "1px solid #2A2D3A",
                borderRadius: 8,
                padding: "10px 14px",
                color: "#E2E8F0",
                fontSize: 14,
                marginBottom: 12,
                outline: "none",
                boxSizing: "border-box",
              }}
              type="email"
              placeholder="Email"
              value={authForm.email}
              onChange={(event) => setAuthForm((prev) => ({ ...prev, email: event.target.value }))}
            />
            <input
              style={{
                width: "100%",
                background: "#1A1D27",
                border: "1px solid #2A2D3A",
                borderRadius: 8,
                padding: "10px 14px",
                color: "#E2E8F0",
                fontSize: 14,
                marginBottom: 16,
                outline: "none",
                boxSizing: "border-box",
              }}
              type="password"
              placeholder="Password"
              value={authForm.password}
              onChange={(event) => setAuthForm((prev) => ({ ...prev, password: event.target.value }))}
            />
            <button
              type="submit"
              style={{
                width: "100%",
                padding: 12,
                background: "#6366F1",
                color: "#fff",
                border: "none",
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Sign In
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "#0A0C14",
        color: "#E2E8F0",
        fontFamily: "Inter, sans-serif",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
          height: 60,
          background: "#0F1117",
          borderBottom: "1px solid #1E2130",
          flexShrink: 0,
        }}
      >
        <span style={{ fontFamily: "Space Grotesk, sans-serif", fontWeight: 700, fontSize: 18, color: "#fff" }}>
          TechMart<span style={{ color: "#6366F1" }}>.</span>AI
        </span>
        <button
          onClick={() => {
            api.logout();
            setUser(null);
          }}
          style={{
            background: "transparent",
            border: "1px solid #2A2D3A",
            color: "#64748B",
            padding: "5px 12px",
            borderRadius: 6,
            cursor: "pointer",
            fontSize: 12,
          }}
        >
          Sign out
        </button>
      </div>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        {messages.length === 0 && (
          <div style={{ textAlign: "center", marginTop: "20vh", color: "#64748B" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🤖</div>
            <div style={{ fontSize: 20, color: "#fff", marginBottom: 8 }}>How can I help you today?</div>
            <div style={{ fontSize: 14 }}>I&apos;ll route your question to the right specialist.</div>
          </div>
        )}
        {messages.map((message, index) => {
          const isUser = message.role === "user";
          const agentConfig = message.agent ? AGENTS[message.agent] : null;

          return (
            <div
              key={index}
              style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", gap: 10 }}
            >
              {!isUser && (
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    background: "#1A1D27",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 16,
                    flexShrink: 0,
                  }}
                >
                  {agentConfig?.icon || "🤖"}
                </div>
              )}
              <div style={{ maxWidth: "70%" }}>
                {!isUser && agentConfig && (
                  <div style={{ fontSize: 11, color: agentConfig.color, marginBottom: 4, fontWeight: 600 }}>
                    {agentConfig.icon} {agentConfig.label}
                  </div>
                )}
                <div
                  style={{
                    background: isUser ? "#6366F1" : "#1A1D27",
                    color: isUser ? "#fff" : "#CBD5E1",
                    padding: "12px 16px",
                    borderRadius: 14,
                    fontSize: 14,
                    lineHeight: 1.6,
                    border: isUser ? "none" : "1px solid #2A2D3A",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {message.content}
                </div>
                {message.escalated && (
                  <div
                    style={{
                      background: "#EF444415",
                      border: "1px solid #EF444430",
                      color: "#FCA5A5",
                      padding: "6px 10px",
                      borderRadius: 6,
                      fontSize: 12,
                      marginTop: 6,
                    }}
                  >
                    🔴 Escalated to human agent
                  </div>
                )}
                {message.sources?.length > 0 && (
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
                    {message.sources.map((source, sourceIndex) => (
                      <span
                        key={sourceIndex}
                        style={{
                          background: "#0F1117",
                          border: "1px solid #2A2D3A",
                          padding: "2px 8px",
                          borderRadius: 10,
                          fontSize: 11,
                          color: "#64748B",
                        }}
                      >
                        📄 {source}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {loading && (
          <div style={{ display: "flex", gap: 10 }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: "#1A1D27",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              🤖
            </div>
            <div
              style={{
                background: "#1A1D27",
                border: "1px solid #2A2D3A",
                padding: "14px 18px",
                borderRadius: 14,
              }}
            >
              <div style={{ display: "flex", gap: 5 }}>
                {[0, 200, 400].map((delay) => (
                  <div
                    key={delay}
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: "50%",
                      background: "#6366F1",
                      animation: `bounce 1.2s ease-in-out ${delay}ms infinite`,
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div
        style={{
          padding: "16px 24px",
          borderTop: "1px solid #1E2130",
          background: "#0F1117",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            gap: 10,
            background: "#1A1D27",
            border: "1px solid #2A2D3A",
            borderRadius: 12,
            padding: "10px 14px",
          }}
        >
          <textarea
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#E2E8F0",
              fontSize: 14,
              resize: "none",
              fontFamily: "Inter, sans-serif",
              lineHeight: 1.5,
            }}
            placeholder="Ask about billing, technical issues, products, or anything else..."
            rows={1}
            value={input}
            disabled={loading}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                send();
              }
            }}
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            style={{
              width: 36,
              height: 36,
              background: loading || !input.trim() ? "#2A2D3A" : "#6366F1",
              border: "none",
              borderRadius: 8,
              cursor: loading || !input.trim() ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="white"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>

      <style>{`@keyframes bounce { 0%,80%,100%{transform:scale(0.6);opacity:0.4} 40%{transform:scale(1);opacity:1} }`}</style>
    </div>
  );
}
