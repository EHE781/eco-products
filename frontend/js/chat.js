let _chatOpen = false;
let _chatContext = "";

function toggleChat() {
    _chatOpen ? closeChat() : openChat();
}

function openChat(context = "") {
    _chatContext = context;
    _chatOpen = true;
    document.getElementById("chatPanel").classList.add("open");
    document.getElementById("chatInput").focus();
    if (context) {
        addMsg("bot", context);
    }
}

function closeChat() {
    _chatOpen = false;
    document.getElementById("chatPanel").classList.remove("open");
}

function initChat() {
    const msgs = document.getElementById("chatMsgs");
    if (!msgs) return;
    msgs.innerHTML = "";
    addMsg("bot", translate("chat_welcome"));
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
        .replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
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
}

function addTyping() {
    const msgs = document.getElementById("chatMsgs");
    if (!msgs) return;
    const div = document.createElement("div");
    div.className = "typing";
    div.id = "typingIndicator";
    div.innerHTML = `<div class="td"></div><div class="td"></div><div class="td"></div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
}

function rmTyping() {
    const el = document.getElementById("typingIndicator");
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
        if (result?.filtered?.products?.length > 0) {
            P_ALL = result.filtered.products.map(_mapProduct);
            addIAFilters(result.filters ?? {});
            list();
        }
    } catch (err) {
        addMsg("bot", fallback(msg));
    }
}

async function callBackendChat(userMsg) {
    const msgs = document.getElementById("chatMsgs");
    const resp = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message:    userMsg,
            lang:       _lang,
            context:    _chatContext,
            page_query: currentQuery.join(","),
            user_lat:   userPos.lat,
            user_lon:   userPos.lon,
        }),
    });
    if (!resp.ok) throw new Error("Chat backend error");

    // Create bot bubble immediately — will show progress then final reply
    const botDiv = document.createElement("div");
    botDiv.className = "msg bot";
    const progressEl = document.createElement("p");
    progressEl.className = "tool-progress";
    progressEl.textContent = "…";
    botDiv.appendChild(progressEl);
    msgs.appendChild(botDiv);
    msgs.scrollTop = msgs.scrollHeight;

    const reader  = resp.body.getReader();
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
