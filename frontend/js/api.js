const API = {
  base() {
    return window.API_BASE_URL || "http://localhost:8000";
  },

  async request(path, options = {}) {
    const res = await fetch(`${this.base()}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) {
        /* no json body */
      }
      throw new Error(detail);
    }
    if (res.status === 204) return null;
    return res.json();
  },

  getSummary() {
    return this.request("/api/data/summary");
  },
  listData() {
    return this.request("/api/data");
  },
  createData(payload) {
    return this.request("/api/data", { method: "POST", body: JSON.stringify(payload) });
  },
  updateData(id, payload) {
    return this.request(`/api/data/${id}`, { method: "PUT", body: JSON.stringify(payload) });
  },
  deleteData(id) {
    return this.request(`/api/data/${id}`, { method: "DELETE" });
  },

  listConversations() {
    return this.request("/api/conversations");
  },
  getConversation(id) {
    return this.request(`/api/conversations/${id}`);
  },
  deleteConversation(id) {
    return this.request(`/api/conversations/${id}`, { method: "DELETE" });
  },

  sendChat(message, conversationId) {
    return this.request("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId || null }),
    });
  },
};
