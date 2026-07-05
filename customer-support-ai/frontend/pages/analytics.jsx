/**
 * Analytics Dashboard (/analytics)
 * Shows conversation stats, agent usage, escalation rate.
 */
import { useState, useEffect } from "react";
import Head from "next/head";
import Link from "next/link";
import api from "../services/api";

const AGENT_COLORS = {
  billing:   "#6366F1",
  technical: "#10B981",
  product:   "#F59E0B",
  complaint: "#EF4444",
  faq:       "#8B5CF6",
};

const AGENT_ICONS = {
  billing: "💳", technical: "🔧", product: "📦", complaint: "📢", faq: "❓",
};

function StatCard({ label, value, sub, color = "#6366F1" }) {
  return (
    <div style={{
      background: "#0F1117", border: "1px solid #1E2130", borderRadius: 16,
      padding: "24px", flex: 1, minWidth: 160,
    }}>
      <div style={{ fontSize: 13, color: "#64748B", marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 36, fontWeight: 700, color, fontFamily: "'Space Grotesk', sans-serif" }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: "#475569", marginTop: 6 }}>{sub}</div>}
    </div>
  );
}

function AgentBar({ agent, count, total }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  const color = AGENT_COLORS[agent] || "#6366F1";
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 13, color: "#CBD5E1" }}>
          {AGENT_ICONS[agent] || "🤖"} {agent.charAt(0).toUpperCase() + agent.slice(1)} Agent
        </span>
        <span style={{ fontSize: 13, color, fontWeight: 600 }}>{count} ({pct}%)</span>
      </div>
      <div style={{ background: "#1A1D27", borderRadius: 6, height: 8, overflow: "hidden" }}>
        <div style={{
          width: `${pct}%`, height: "100%",
          background: `linear-gradient(90deg, ${color}CC, ${color})`,
          borderRadius: 6, transition: "width 0.8s ease",
        }} />
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData]   = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getAnalytics()
      .then(setData)
      .catch(err => setError(err.message || "Could not load analytics. Please log in."));
  }, []);

  const totalConvos = data?.total_conversations ?? 0;

  return (
    <>
      <Head><title>Analytics — TechMart AI Support</title></Head>
      <div style={{ minHeight: "100vh", background: "#0A0C14", color: "#E2E8F0", fontFamily: "'Inter', sans-serif" }}>
        {/* NAV */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 32px", height: 60, background: "#0F1117", borderBottom: "1px solid #1E2130" }}>
          <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 18, color: "#fff" }}>
            TechMart<span style={{ color: "#6366F1" }}>.</span>AI
          </div>
          <div style={{ display: "flex", gap: 16 }}>
            <Link href="/" style={{ color: "#64748B", fontSize: 13, textDecoration: "none" }}>← Back to Chat</Link>
          </div>
        </div>

        <div style={{ maxWidth: 960, margin: "0 auto", padding: "40px 24px" }}>
          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 28, fontWeight: 700, marginBottom: 8 }}>
            Analytics Dashboard
          </h1>
          <p style={{ color: "#64748B", fontSize: 14, marginBottom: 36 }}>
            Real-time conversation metrics and agent performance
          </p>

          {error && (
            <div style={{ background: "#EF444415", border: "1px solid #EF444430", color: "#FCA5A5", padding: "14px 20px", borderRadius: 12, marginBottom: 32, fontSize: 14 }}>
              ⚠️ {error}
            </div>
          )}

          {/* STAT CARDS */}
          <div style={{ display: "flex", gap: 16, marginBottom: 32, flexWrap: "wrap" }}>
            <StatCard
              label="Total Conversations"
              value={data ? totalConvos.toLocaleString() : "—"}
              sub="All time"
              color="#6366F1"
            />
            <StatCard
              label="Avg Response Time"
              value={data ? `${data.avg_response_time_ms}ms` : "—"}
              sub="Per message"
              color="#10B981"
            />
            <StatCard
              label="Escalation Rate"
              value={data ? `${data.escalation_rate}%` : "—"}
              sub="Needed human agent"
              color="#F59E0B"
            />
            <StatCard
              label="Active Agents"
              value={data ? Object.keys(data.agent_usage).length : "—"}
              sub="Specialized agents"
              color="#8B5CF6"
            />
          </div>

          {/* AGENT USAGE */}
          <div style={{ background: "#0F1117", border: "1px solid #1E2130", borderRadius: 16, padding: 28, marginBottom: 32 }}>
            <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 18, fontWeight: 600, marginBottom: 24 }}>
              Agent Usage Breakdown
            </h2>
            {data && Object.keys(data.agent_usage).length > 0 ? (
              Object.entries(data.agent_usage)
                .sort(([, a], [, b]) => b - a)
                .map(([agent, count]) => (
                  <AgentBar key={agent} agent={agent} count={count} total={totalConvos} />
                ))
            ) : (
              <div style={{ color: "#475569", fontSize: 14, textAlign: "center", padding: "32px 0" }}>
                No conversation data yet. Start chatting to see stats here.
              </div>
            )}
          </div>

          {/* TOP INTENTS */}
          {data?.top_intents?.length > 0 && (
            <div style={{ background: "#0F1117", border: "1px solid #1E2130", borderRadius: 16, padding: 28 }}>
              <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 18, fontWeight: 600, marginBottom: 20 }}>
                Top Intent Categories
              </h2>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {data.top_intents.map((intent, i) => (
                  <div key={i} style={{
                    background: (AGENT_COLORS[intent] || "#6366F1") + "15",
                    border: `1px solid ${AGENT_COLORS[intent] || "#6366F1"}40`,
                    color: AGENT_COLORS[intent] || "#6366F1",
                    padding: "8px 16px", borderRadius: 20, fontSize: 13, fontWeight: 500,
                  }}>
                    {AGENT_ICONS[intent] || "🤖"} {intent}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
