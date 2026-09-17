// ---- 상태 ----
let currentConversationId = null;
let currentDataPoints = [];

// ---- 탭 전환 ----
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");

    if (btn.dataset.tab === "data") loadDataPoints();
    if (btn.dataset.tab === "history") loadHistory();
  });
});

// ---- 다크 모드 ----
const darkToggle = document.getElementById("dark-toggle");
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  darkToggle.textContent = theme === "dark" ? "☀️" : "🌙";
}
(function initTheme() {
  let saved = "light";
  try {
    saved = localStorage.getItem("theme") || "light";
  } catch (_) {}
  applyTheme(saved);
})();
darkToggle.addEventListener("click", () => {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  applyTheme(next);
  try {
    localStorage.setItem("theme", next);
  } catch (_) {}
});

// ---- 데이터 요약 ----
async function loadSummary() {
  const el = document.getElementById("summary-card");
  try {
    const s = await API.getSummary();
    el.innerHTML = `
      <div><strong>기간</strong> ${s.period} · <strong>${s.count}개</strong> 데이터</div>
      <div>평균 <strong>${formatNum(s.metrics.average)}</strong> · 최대 ${formatNum(s.metrics.max)} · 최소 ${formatNum(s.metrics.min)}</div>
      <div>트렌드: <strong>${s.trend}</strong></div>
    `;
  } catch (err) {
    el.innerHTML = `<span>요약을 불러오지 못했습니다: ${escapeHtml(err.message)}</span>`;
  }
}

function formatNum(n) {
  return Number(n).toLocaleString("ko-KR");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---- 채팅 ----
const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatLoading = document.getElementById("chat-loading");
const conversationLabel = document.getElementById("current-conversation-label");

function appendBubble(role, content) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.textContent = content;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendBubble("user", message);
  chatInput.value = "";
  chatLoading.classList.remove("hidden");

  try {
    const res = await API.sendChat(message, currentConversationId);
    currentConversationId = res.conversation_id;
    appendBubble("assistant", res.reply);
    conversationLabel.textContent = "대화 중 (자동 저장됨)";
  } catch (err) {
    appendBubble("assistant", `오류가 발생했습니다: ${err.message}`);
  } finally {
    chatLoading.classList.add("hidden");
  }
});

document.getElementById("new-chat-btn").addEventListener("click", () => {
  currentConversationId = null;
  chatLog.innerHTML = "";
  conversationLabel.textContent = "새 대화";
});

// ---- 데이터 관리 ----
const dataForm = document.getElementById("data-form");
const dataTableBody = document.getElementById("data-table-body");

async function loadDataPoints() {
  try {
    currentDataPoints = await API.listData();
    renderDataTable();
    drawTrendChart();
  } catch (err) {
    dataTableBody.innerHTML = `<tr><td colspan="4">데이터를 불러오지 못했습니다: ${escapeHtml(err.message)}</td></tr>`;
  }
}

function renderDataTable() {
  if (!currentDataPoints.length) {
    dataTableBody.innerHTML = `<tr><td colspan="4" class="empty-hint">등록된 데이터가 없습니다.</td></tr>`;
    return;
  }
  dataTableBody.innerHTML = currentDataPoints
    .map(
      (p) => `
      <tr data-id="${p.id}">
        <td>${p.date}</td>
        <td>${formatNum(p.value)}</td>
        <td>${escapeHtml(p.memo || "")}</td>
        <td class="actions-cell">
          <button class="edit-btn" data-id="${p.id}">수정</button>
          <button class="delete-btn" data-id="${p.id}">삭제</button>
        </td>
      </tr>`
    )
    .join("");
}

dataForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const date = document.getElementById("data-date").value;
  const value = Number(document.getElementById("data-value").value);
  const memo = document.getElementById("data-memo").value || null;

  try {
    await API.createData({ date, value, memo });
    dataForm.reset();
    await loadDataPoints();
    await loadSummary();
  } catch (err) {
    alert(`추가 실패: ${err.message}`);
  }
});

dataTableBody.addEventListener("click", async (e) => {
  const id = e.target.dataset.id;
  if (!id) return;

  if (e.target.classList.contains("delete-btn")) {
    if (!confirm("이 데이터를 삭제할까요?")) return;
    try {
      await API.deleteData(id);
      await loadDataPoints();
      await loadSummary();
    } catch (err) {
      alert(`삭제 실패: ${err.message}`);
    }
  }

  if (e.target.classList.contains("edit-btn")) {
    const point = currentDataPoints.find((p) => p.id === id);
    if (!point) return;
    const newValue = prompt("새 값을 입력하세요", point.value);
    if (newValue === null) return;
    try {
      await API.updateData(id, { value: Number(newValue) });
      await loadDataPoints();
      await loadSummary();
    } catch (err) {
      alert(`수정 실패: ${err.message}`);
    }
  }
});

// ---- 시각화 (bonus): 간단한 라인 차트 ----
function drawTrendChart() {
  const canvas = document.getElementById("trend-chart");
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || 600;
  const height = canvas.clientHeight || 160;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);

  const points = [...currentDataPoints].sort((a, b) => (a.date > b.date ? 1 : -1));
  if (points.length < 2) return;

  const values = points.map((p) => p.value);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const padding = 16;
  const range = max - min || 1;

  const styles = getComputedStyle(document.documentElement);
  ctx.strokeStyle = styles.getPropertyValue("--accent").trim() || "#4f46e5";
  ctx.lineWidth = 2;
  ctx.beginPath();

  points.forEach((p, i) => {
    const x = padding + (i / (points.length - 1)) * (width - padding * 2);
    const y = height - padding - ((p.value - min) / range) * (height - padding * 2);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

// ---- 내보내기 ----
function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

document.getElementById("export-csv-btn").addEventListener("click", () => {
  const rows = [["date", "value", "memo"], ...currentDataPoints.map((p) => [p.date, p.value, p.memo || ""])];
  const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
  downloadFile("data.csv", csv, "text/csv;charset=utf-8;");
});

document.getElementById("export-json-btn").addEventListener("click", () => {
  downloadFile("data.json", JSON.stringify(currentDataPoints, null, 2), "application/json");
});

// ---- 대화 기록 ----
const historyList = document.getElementById("history-list");

async function loadHistory() {
  try {
    const conversations = await API.listConversations();
    if (!conversations.length) {
      historyList.innerHTML = `<li class="empty-hint">저장된 대화가 없습니다.</li>`;
      return;
    }
    historyList.innerHTML = conversations
      .map(
        (c) => `
        <li class="history-item" data-id="${c.id}">
          <div>
            <div class="title">${escapeHtml(c.title)}</div>
            <div class="meta">${new Date(c.updated_at).toLocaleString("ko-KR")} · 메시지 ${c.message_count}개</div>
          </div>
          <div class="actions">
            <button class="load-btn" data-id="${c.id}">불러오기</button>
            <button class="delete-btn" data-id="${c.id}">삭제</button>
          </div>
        </li>`
      )
      .join("");
  } catch (err) {
    historyList.innerHTML = `<li class="empty-hint">대화 목록을 불러오지 못했습니다: ${escapeHtml(err.message)}</li>`;
  }
}

historyList.addEventListener("click", async (e) => {
  const id = e.target.dataset.id;
  if (!id) return;

  if (e.target.classList.contains("delete-btn")) {
    if (!confirm("이 대화를 삭제할까요?")) return;
    try {
      await API.deleteConversation(id);
      await loadHistory();
    } catch (err) {
      alert(`삭제 실패: ${err.message}`);
    }
  }

  if (e.target.classList.contains("load-btn")) {
    try {
      const conv = await API.getConversation(id);
      currentConversationId = conv.id;
      chatLog.innerHTML = "";
      conv.messages.forEach((m) => appendBubble(m.role, m.content));
      conversationLabel.textContent = conv.title;
      document.querySelector('.tab-btn[data-tab="chat"]').click();
    } catch (err) {
      alert(`불러오기 실패: ${err.message}`);
    }
  }
});

// ---- 초기화 ----
loadSummary();
