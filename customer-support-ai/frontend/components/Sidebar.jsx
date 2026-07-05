/**
 * Sidebar — session list, new conversation button, agent status panel.
 */

const AGENT_CONFIG = {
  billing:   { label: "Billing Agent",   color: "#6366F1", icon: "💳" },
  technical: { label: "Tech Support",    color: "#10B981", icon: "🔧" },
  product:   { label: "Product Agent",   color: "#F59E0B", icon: "📦" },
  complaint: { label: "Complaint Agent", color: "#EF4444", icon: "📢" },
  faq:       { label: "FAQ Agent",       color: "#8B5CF6", icon: "❓" },
};

function SessionItem({ session, active, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: "10px 12px", borderRadius: 8, cursor: "pointer",
        background: active ? "#1E2130" : "transparent",
        border: active ? "1px solid #2A2D3A" : "1px solid transparent",
        marginBottom: 3, transition: "all 0.12s",
      }}
      onMouseEnter={e => { if (!active) e.currentTarget.style.background = "#1A1D27"; }}
      onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}
    >
      <div style={{ fontSize: 13, color: active ? "#CBD5E1" : "#94A3B8", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {session.preview || "New conversation"}
      </div>
      <div style={{ fontSize: 11, color: "#475569", marginTop: 3 }}>
        {new Date(session.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
      </div>
    </div>
  );
}

export default function Sidebar({ sessions, currentSessionId, onNewSession, onSelectSession }) {
  return (
    <aside style={{
      width: 248, background: "#0F1117", borderRight: "1px solid #1E2130",
      display: "flex", flexDirection: "column", flexShrink: 0,
    }}>
      {/* Header + New button */}
      <div style={{ padding: 14, borderBottom: "1px solid #1E2130" }}>
        <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.1em", color: "#475569", textTransform: "uppercase", marginBottom: 10 }}>
          Conversations
        </div>
        <button
          onClick={onNewSession}
          style={{
            width: "100%", padding: "9px 14px", background: "#6366F1", color: "#fff",
            border: "none", borderRadius: 8, fontSize: 13, fontWeight: 500,
            cursor: "pointer", display: "flex", alignItems: "center", gap: 8,
            fontFamily: "'Inter', sans-serif", transition: "background 0.15s",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "#5558E3"}
          onMouseLeave={e => e.currentTarget.style.background = "#6366F1"}
        >
          <span style={{ fontSize: 16, lineHeight: 1 }}>✚</span> New Conversation
        </button>
      </div>

      {/* Sessions list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "8px 8px 0" }}>
        {sessions.length === 0 ? (
          <div style={{ fontSize: 12, color: "#334155", padding: "16px 8px", textAlign: "center" }}>
            No conversations yet
          </div>
        ) : (
          sessions.map(s => (
            <SessionItem
              key={s.id}
              session={s}
              active={s.id === currentSessionId}
              onClick={() => onSelectSession(s.id)}
            />
          ))
        )}
      </div>

      {/* Agents panel */}
      <div style={{ padding: "14px 14px 18px", borderTop: "1px solid #1E2130" }}>
        <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.1em", color: "#475569", textTransform: "uppercase", marginBottom: 10 }}>
          AI Agents
        </div>
        {Object.entries(AGENT_CONFIG).map(([key, agent]) => (
          <div key={key} style={{
            display: "flex", alignItems: "center", gap: 8,
            padding: "5px 8px", borderRadius: 6,
            background: agent.color + "10", marginBottom: 4,
          }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: agent.color, flexShrink: 0 }} />
            <span style={{ fontSize: 12, color: agent.color }}>{agent.icon} {agent.label}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}
