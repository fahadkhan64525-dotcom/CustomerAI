/**
 * TechMart Support - API Service
 * Communicates with the FastAPI backend.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiService {
  constructor() {
    this.token = this.getStoredToken();
  }

  getStoredToken() {
    if (typeof window === "undefined") {
      return null;
    }
    return localStorage.getItem("auth_token");
  }

  setToken(token) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
    }
  }

  async request(path, options = {}) {
    if (!this.token) {
      this.token = this.getStoredToken();
    }

    const headers = { "Content-Type": "application/json", ...options.headers };
    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(`${BASE_URL}${path}`, { ...options, headers });
    if (!response.ok) {
      if (response.status === 401) {
        this.clearToken();
      }
      const error = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(error.detail || "Request failed");
    }

    return response.json();
  }

  async register(username, email, password, fullName = "") {
    const data = await this.request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password, full_name: fullName }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async login(email, password) {
    const data = await this.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async getMe() {
    return this.request("/api/auth/me");
  }

  logout() {
    this.clearToken();
  }

  async sendMessage(message, sessionId, conversationHistory = []) {
    return this.request("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        session_id: sessionId,
        conversation_history: conversationHistory,
      }),
    });
  }

  async getHistory(sessionId, limit = 20) {
    return this.request(`/api/chat/history/${sessionId}?limit=${limit}`);
  }

  async getAnalytics() {
    return this.request("/api/analytics");
  }
}

const api = new ApiService();
export default api;
