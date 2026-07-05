/**
 * useChat - manages conversation state, session, and API calls.
 * Usage:
 *   const { messages, sendMessage, isLoading, currentAgent, newSession } = useChat();
 */
import { useCallback, useRef, useState } from "react";
import api from "../services/api";

export const AGENT_CONFIG = {
  billing: { label: "Billing Agent", color: "#6366F1", bg: "#6366F115", icon: "💳" },
  technical: { label: "Tech Support", color: "#10B981", bg: "#10B98115", icon: "🔧" },
  product: { label: "Product Agent", color: "#F59E0B", bg: "#F59E0B15", icon: "📦" },
  complaint: { label: "Complaint Agent", color: "#EF4444", bg: "#EF444415", icon: "📢" },
  faq: { label: "FAQ Agent", color: "#8B5CF6", bg: "#8B5CF615", icon: "❓" },
};

const generateSessionId = () =>
  `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState(null);
  const [sessionId, setSessionId] = useState(generateSessionId);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ total: 0, agents: {} });
  const messagesRef = useRef([]);

  const addMessage = useCallback((msg) => {
    setMessages((prev) => {
      const next = [...prev, { ...msg, timestamp: new Date() }];
      messagesRef.current = next;
      return next;
    });
  }, []);

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) {
      return;
    }

    setError(null);

    const userMsg = { role: "user", content: trimmed };
    const history = messagesRef.current.map((message) => ({
      role: message.role,
      content: message.content,
    }));

    addMessage(userMsg);
    setIsLoading(true);

    try {
      const response = await api.sendMessage(trimmed, sessionId, history);

      setCurrentAgent(response.agent);
      addMessage({
        role: "assistant",
        content: response.response,
        agent: response.agent,
        secondaryAgents: response.secondary_agents || [],
        escalated: response.escalated,
        sources: response.sources || [],
      });

      setStats((prev) => ({
        total: prev.total + 1,
        agents: {
          ...prev.agents,
          [response.agent]: (prev.agents[response.agent] || 0) + 1,
        },
      }));
    } catch (err) {
      setError(err.message || "Failed to get a response. Please try again.");
      addMessage({
        role: "assistant",
        content:
          "I'm sorry, I encountered an issue processing your request. Please try again or contact support@techmart.com.",
        agent: "faq",
      });
    } finally {
      setIsLoading(false);
    }
  }, [addMessage, isLoading, sessionId]);

  const newSession = useCallback(() => {
    messagesRef.current = [];
    setMessages([]);
    setCurrentAgent(null);
    setSessionId(generateSessionId());
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    currentAgent,
    sessionId,
    error,
    stats,
    sendMessage,
    newSession,
    agentConfig: AGENT_CONFIG,
  };
}
