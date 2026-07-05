/**
 * MessageBubble — renders a single chat message with agent badge,
 * markdown-like formatting, source chips, and escalation banner.
 */

const AGENT_CONFIG = {
  billing:   { label: "Billing Agent",   color: "#6366F1", bg: "#6366F115", icon: "💳" },
  technical: { label: "Tech Support",    color: "#10B981", bg: "#10B98115", icon: "🔧" },
  product:   { label: "Product Agent",   color: "#F59E0B", bg: "#F59E0B15", icon: "📦" },
  complaint: { label: "Complaint Agent", color: "#EF4444", bg: "#EF444415", icon: "📢" },
  faq:       { label: "FAQ Agent",       color: "#8B5CF6", bg: "#8B5CF615", icon: "❓" },
};

/** Minimal inline markdown renderer */
function renderInline(text) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((chunk, i) =>
    chunk.startsWith("**") && chunk.endsWith("**")
      ? <strong key={i} style={{ color: "#F1F5F9", fontWeight: 600 }}>{chunk.slice(2, -2)}</strong>
      : chunk
  );
}

function renderContent(text) {
  const lines = text.split("\n");
  const elements = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (/^\d+\.\s/.test(line)) {
      const items = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        items.push(<li key={i} style={{ marginBottom: 4 }}>{renderInline(lines[i].replace(/^\d+\.\s/, ""))}</li>);
        i++;
      }
      elements.push(<ol key={`ol-${i}`} style={{ paddingLeft: 20, margin: "8px 0" }}>{items}</ol>);
    } else if (/^[-*•]\s/.test(line)) {
      const items = [];
      while (i < lines.length && /^[-*•]\s/.test(lines[i])) {
        items.push(<li key={i} style={{ marginBottom: 4 }}>{renderInline(lines[i].replace(/^[-*•]\s/, ""))}</li>);
        i++;
      }
      elements.push(<ul key={`ul-${i}`} style={{ paddingLeft: 20, margin: "8px 0" }}>{items}</ul>);
    } else if (line.trim()) {
      elements.push(
        <p key={i} style={{ margin: "0 0 8px 0", lineHeight: 1.65 }}>
          {renderInline(line)}
        </p>
      );
      i++;
    } else {
      i++;
    }
  }
  return elements;
}

export default function MessageBubble({ message, userInitial = "U" }) {
  const isUser = message.role === "user";
  const agConf = message.agent ? AGENT_CONFIG[message.agent] : null;
  const secConf = message.secondaryAgents?.length > 0
    ? AGENT_CONFIG[message.secondaryAgents[0]]
    : null;

  return (
    <div
      className="animate-fade-in"
      style={{
        display: "flex",
        gap: 10,
        flexDirection: isUser ? "row-reverse" : "row",
        alignItems: "flex-start",
      }}
    >
      {/* Avatar */}
      <div style={{
        width: 34, height: 34, borderRadius: "50%", flexShrink: 0,
        background: isUser ? "#6366F1" : (agConf?.bg || "#1A1D27"),
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 15, fontWeight: 700, color: "#fff",
        border: isUser ? "none" : "1px solid #2A2D3A",
      }}>
        {isUser ? userInitial : (agConf?.icon || "🤖")}
      </div>

      {/* Content column */}
      <div style={{ maxWidth: "70%", minWidth: 60 }}>
        {/* Agent meta (assistant only) */}
        {!isUser && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5, flexWrap: "wrap" }}>
            {agConf && (
              <span style={{
                display: "inline-flex", alignItems: "center", gap: 5,
                background: agConf.bg, border: `1px solid ${agConf.color}40`,
                color: agConf.color, padding: "2px 9px", borderRadius: 12,
                fontSize: 11, fontWeight: 600,
              }}>
                {agConf.icon} {agConf.label}
              </span>
            )}
            {secConf && (
              <span style={{
                display: "inline-flex", alignItems: "center", gap: 5,
                background: secConf.bg, border: `1px solid ${secConf.color}40`,
                color: secConf.color, padding: "2px 9px", borderRadius: 12,
                fontSize: 11, fontWeight: 600,
              }}>
                + {secConf.icon} {secConf.label}
              </span>
            )}
            {message.timestamp && (
              <span style={{ fontSize: 11, color: "#475569" }}>
                {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            )}
          </div>
        )}

        {/* Bubble */}
        <div style={{
          background: isUser ? "#6366F1" : "#1A1D27",
          color: isUser ? "#fff" : "#CBD5E1",
          padding: "12px 16px",
          borderRadius: 14,
          borderBottomRightRadius: isUser ? 4 : 14,
          borderBottomLeftRadius: isUser ? 14 : 4,
          fontSize: 14,
          lineHeight: 1.6,
          border: isUser ? "none" : "1px solid #2A2D3A",
        }}>
          {isUser ? message.content : renderContent(message.content)}
        </div>

        {/* Escalation banner */}
        {message.escalated && (
          <div style={{
            background: "#EF444415", border: "1px solid #EF444430", color: "#FCA5A5",
            padding: "7px 12px", borderRadius: 8, fontSize: 12, marginTop: 7,
            display: "flex", alignItems: "center", gap: 6,
          }}>
            🔴 Escalated — a human agent will follow up within 24 hours.
          </div>
        )}

        {/* Source chips */}
        {message.sources?.length > 0 && (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 7 }}>
            {message.sources.map((src, i) => (
              <span key={i} style={{
                background: "#0F1117", border: "1px solid #2A2D3A",
                padding: "2px 9px", borderRadius: 10, fontSize: 11, color: "#64748B",
              }}>
                📄 {src}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
