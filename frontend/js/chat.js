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
    addMsg("bot", t("chat_welcome"));
}

function addMsg(role, text) {
    const msgs = document.getElementById("chatMsgs");
    if (!msgs) return;
    const div = document.createElement("div");
    div.className = `msg ${role}`;
    div.textContent = text;
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
    addTyping();
    try {
        const reply = await callBackendChat(msg);
        rmTyping();
        addMsg("bot", reply);
    } catch (err) {
        rmTyping();
        addMsg("bot", fallback(msg));
    }
}

async function callBackendChat(userMsg) {
    const resp = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message: userMsg,
            lang: _lang,
            context: _chatContext,
            user_lat: userPos.lat,
            user_lon: userPos.lon,
        }),
    });
    if (!resp.ok) throw new Error("Chat backend error");
    const data = await resp.json();
    return data.reply ?? fallback(userMsg);
}

function fallback(msg) {
    const m = msg.toLowerCase();
    if (m.includes("yogur") || m.includes("leche") || m.includes("lacteo") || m.includes("lacti")) return t("fb_milk");
    if (m.includes("pan") || m.includes("bread") || m.includes("pa ")) return t("fb_bread");
    if (m.includes("manzana") || m.includes("apple") || m.includes("poma")) return t("fb_apple");
    if (m.includes("temporada") || m.includes("season")) return t("fb_seasonal");
    if (m.includes("bio") || m.includes("ecol") || m.includes("organic")) return t("fb_organic");
    return t("fb_general");
}
