/**
 * TypingIndicator — animated dots shown while the AI agent is responding.
 */

const AGENT_CONFIG = {
  billing:   { label: "Billing Agent",   color: "#6366F1", bg: "#6366F115", icon: "💳" },
  technical: { label: "Tech Support",    color: "#10B981", bg: "#10B98115", icon: "🔧" },
  product:   { label: "Product Agent",   color: "#F59E0B", bg: "#F59E0B15", icon: "📦" },
  complaint: { label: "Complaint Agent", color: "#EF4444", bg: "#EF444415", icon: "📢" },
  faq:       { label: "FAQ Agent",       color: "#8B5CF6", bg: "#8B5CF615", icon: "❓" },
};

const keyframes = `
  @keyframes typingBounce {
    0%, 80%, 100% { transform: scale(0.55); opacity: 0.35; }
    40%           { transform: scale(1);    opacity: 1;    }
  }
  @keyframes routingPulse {
    0%, 100% { opacity: 0.4; }
    50%      { opacity: 1;   }
  }
`;

export default function TypingIndicator({ agentType }) {
  const agConf = agentType ? AGENT_CONFIG[agentType] : null;
  const dotColor = agConf?.color || "#6366F1";
  const label = agConf
    ? `${agConf.icon} ${agConf.label} is typing…`
    : "🤖 Routing to the right agent…";

  return (
    <>
      <style>{keyframes}</style>
      <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
        {/* Avatar */}
        <div style={{
          width: 34, height: 34, borderRadius: "50%", flexShrink: 0,
          background: agConf?.bg || "#1A1D27",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 15, border: "1px solid #2A2D3A",
        }}>
          {agConf?.icon || "🤖"}
        </div>

        {/* Bubble */}
        <div style={{
          background: "#1A1D27", border: "1px solid #2A2D3A",
          padding: "13px 18px", borderRadius: 14, borderBottomLeftRadius: 4,
          display: "flex", alignItems: "center", gap: 12,
        }}>
          {/* Bouncing dots */}
          <div style={{ display: "flex", gap: 5 }}>
            {[0, 200, 400].map(delay => (
              <div key={delay} style={{
                width: 7, height: 7, borderRadius: "50%", background: dotColor,
                animation: `typingBounce 1.2s ease-in-out ${delay}ms infinite`,
              }} />
            ))}
          </div>
          {/* Label */}
          <span style={{
            fontSize: 12, color: "#64748B",
            animation: "routingPulse 1.6s ease-in-out infinite",
          }}>
            {label}
          </span>
        </div>
      </div>
    </>
  );
}
