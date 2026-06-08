let _chatOpen = false;
let _chatContext = "";
let _chatMessages = [];
let _showingHistory = false;
let _sessionId = Date.now();

const _HIST_KEY = "ecoscan_chat_history";
const _HIST_MAX = 20;

function toggleChat() {
    _chatOpen ? closeChat() : openChat();
}

function openChat(context = "") {
    _chatContext = context;
    _chatOpen = true;
    const panel = document.getElementById("chatPanel");
    panel.classList.add("open");
    panel.setAttribute("aria-hidden", "false");
    const fab = document.getElementById("fab");
    if (fab) fab.setAttribute("aria-expanded", "true");
    document.getElementById("chatInput").focus();
    if (context) {
        addMsg("bot", context);
    }
}

function closeChat() {
    _chatOpen = false;
    const panel = document.getElementById("chatPanel");
    panel.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
    const fab = document.getElementById("fab");
    if (fab) {
        fab.setAttribute("aria-expanded", "false");
        fab.focus();
    }
    if (_showingHistory) toggleHistory();
}

function initChat() {
    const msgs = document.getElementById("chatMsgs");
    if (!msgs) return;
    msgs.innerHTML = "";
    _chatMessages = [];
    _sessionId = Date.now();
    addMsg("bot", translate("chat_welcome"));
}

function newChat() {
    _saveToHistory();
    if (_showingHistory) toggleHistory();
    initChat();
}

function toggleHistory() {
    _showingHistory = !_showingHistory;
    const msgsEl = document.getElementById("chatMsgs");
    const histEl = document.getElementById("chatHistoryPanel");
    const inpEl = document.querySelector(".chat-inp");
    const btn = document.getElementById("chatHistBtn");

    msgsEl.style.display = _showingHistory ? "none" : "";
    inpEl.style.display = _showingHistory ? "none" : "";
    histEl.classList.toggle("open", _showingHistory);
    btn?.classList.toggle("active", _showingHistory);

    if (_showingHistory) {
        _saveToHistory();
        _renderHistory();
    }
}

function _renderHistory() {
    const histEl = document.getElementById("chatHistoryPanel");
    const history = JSON.parse(localStorage.getItem(_HIST_KEY) || "[]");

    if (history.length === 0) {
        histEl.innerHTML = `<p class="chat-hist-empty">${translate("chat_hist_empty")}</p>`;
        return;
    }

    histEl.innerHTML = history.map(c => {
        const d = new Date(c.ts);
        const date = d.toLocaleDateString(undefined, { day: "numeric", month: "short" })
            + " " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
        return `<button class="chat-hist-item" onclick="_loadConversation(${c.id})" aria-label="${c.title.replace(/"/g, '&quot;')} - ${date}">
            <div class="chi-title">${c.title}</div>
            <div class="chi-date">${date}</div>
        </button>`;
    }).join("");
}

function _saveToHistory() {
    const userMsgs = _chatMessages.filter(m => m.role === "user");
    if (userMsgs.length === 0) return;

    const history = JSON.parse(localStorage.getItem(_HIST_KEY) || "[]");
    const existing = history.findIndex(c => c.id === _sessionId);

    if (existing !== -1) {
        // Update in place — conversation grew since last save
        history[existing] = { ...history[existing], messages: [..._chatMessages], ts: Date.now() };
    } else {
        history.unshift({
            id: _sessionId,
            title: userMsgs[0].text.slice(0, 60),
            messages: [..._chatMessages],
            ts: Date.now(),
        });
    }

    if (history.length > _HIST_MAX) history.length = _HIST_MAX;
    localStorage.setItem(_HIST_KEY, JSON.stringify(history));
}

function _loadConversation(id) {
    const history = JSON.parse(localStorage.getItem(_HIST_KEY) || "[]");
    const conv = history.find(c => c.id === id);
    if (!conv) return;

    _chatMessages = [...conv.messages];
    _sessionId = conv.id;
    const msgs = document.getElementById("chatMsgs");
    msgs.innerHTML = "";
    for (const m of _chatMessages) {
        const div = document.createElement("div");
        div.className = `msg ${m.role}`;
        if (m.role === "bot") div.innerHTML = _md(m.text);
        else div.textContent = m.text;
        msgs.appendChild(div);
    }
    msgs.scrollTop = msgs.scrollHeight;

    if (_showingHistory) toggleHistory();
}

function _md(text) {
    const lines = text.split("\n");
    let html = "";
    let inList = false;
    for (const line of lines) {
        const li = line.match(/^[-•*]\s+(.+)/);
        if (li) {
            if (!inList) { html += "<ul>"; inList = true; }
            html += `<li>${li[1]}</li>`;
        } else {
            if (inList) { html += "</ul>"; inList = false; }
            html += line.trim() ? `<p>${line}</p>` : "";
        }
    }
    if (inList) html += "</ul>";
    return html
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*([^*\n]+)\*/g, "<em>$1</em>")
        .replace(/\[([^\]]+)\]\(product:([^)]+)\)/g,
            '<button class="chat-product-link" onclick="openProductModal(\'$2\')">$1 🔍</button>');
}

function addMsg(role, text) {
    const msgs = document.getElementById("chatMsgs");
    if (!msgs) return;
    const div = document.createElement("div");
    div.className = `msg ${role}`;
    if (role === "bot") {
        div.innerHTML = _md(text);
    } else {
        div.textContent = text;
    }
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    _chatMessages.push({ role, text });
}

function addTyping(container = null) {
    const msgs = container || document.getElementById("chatMsgs");
    if (!msgs) return;
    const div = document.createElement("div");
    div.className = "typing";
    div.setAttribute("aria-label", "Procesando respuesta");
    div.innerHTML = `<div class="td" aria-hidden="true"></div><div class="td" aria-hidden="true"></div><div class="td" aria-hidden="true"></div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
}

function rmTyping(container = null) {
    const msgs = container || document.getElementById("chatMsgs");
    if (!msgs) return;
    const el = msgs.querySelector(".typing");
    if (el) el.remove();
}

async function send() {
    const inp = document.getElementById("chatInput");
    if (!inp) return;
    const msg = inp.value.trim();
    if (!msg) return;
    inp.value = "";
    addMsg("user", msg);
    logInteraction(null, "chat", msg);
    try {
        const result = await callBackendChat(msg);
        _chatMessages.push({ role: "bot", text: result.reply || fallback(msg) });
        if (result?.filtered?.products?.length > 0) {
            P_ALL = result.filtered.products.map(_mapProduct);
            totalApiCount = P_ALL.length;
            currentPage = 1;
            addIAFilters(result.filters ?? {});
            list();
        }
    } catch (err) {
        addMsg("bot", fallback(msg));
    }
}

async function callBackendChat(userMsg, msgsEl = null, contextOverride = undefined) {
    const msgs = msgsEl || document.getElementById("chatMsgs");
    const context = contextOverride !== undefined ? contextOverride : _chatContext;

    addTyping(msgs);

    const resp = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message: userMsg,
            lang: _lang,
            context: context,
            page_query: currentQuery.join(","),
            user_lat: userPos.lat,
            user_lon: userPos.lon,
        }),
    });
    if (!resp.ok) { rmTyping(msgs); throw new Error("Chat backend error"); }

    rmTyping(msgs);

    // Create bot bubble — will show progress then final reply
    const botDiv = document.createElement("div");
    botDiv.className = "msg bot";
    const progressEl = document.createElement("p");
    progressEl.className = "tool-progress";
    progressEl.textContent = "…";
    botDiv.appendChild(progressEl);
    msgs.appendChild(botDiv);
    msgs.scrollTop = msgs.scrollHeight;

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let result = { reply: "", filtered: null, filters: null };

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() ?? "";
        for (const chunk of chunks) {
            if (!chunk.startsWith("data: ")) continue;
            try {
                const event = JSON.parse(chunk.slice(6));
                if (event.type === "progress") {
                    progressEl.textContent = event.message;
                    msgs.scrollTop = msgs.scrollHeight;
                } else if (event.type === "done") {
                    result = event;
                    botDiv.innerHTML = _md(event.reply || fallback(userMsg));
                    msgs.scrollTop = msgs.scrollHeight;
                }
            } catch { /* ignore malformed chunks */ }
        }
    }

    if (!result.reply) botDiv.innerHTML = _md(fallback(userMsg));
    return result;
}

function fallback(msg) {
    const m = msg.toLowerCase();
    if (m.includes("yogur") || m.includes("leche") || m.includes("lacteo") || m.includes("lacti")) return translate("fb_milk");
    if (m.includes("pan") || m.includes("bread") || m.includes("pa ")) return translate("fb_bread");
    if (m.includes("manzana") || m.includes("apple") || m.includes("poma")) return translate("fb_apple");
    if (m.includes("temporada") || m.includes("season")) return translate("fb_seasonal");
    if (m.includes("bio") || m.includes("ecol") || m.includes("organic")) return translate("fb_organic");
    return translate("fb_general");
}
