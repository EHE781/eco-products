/* ── AI Chat (Gemini 2.0 Flash) ── */
// Key is loaded from the backend config; for static-only mode it falls back to
// the hardcoded value below. In production, remove the fallback and serve via the
// /api/chat endpoint instead so the key never reaches the browser.
const GEMINI_KEY = "AIzaSyDemo_replace_me";  // ← replace or proxy via /api/chat

let _chatOpen = false;
let _chatContext = "";   // current product context injected from cardClick

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
        const reply = await callGemini(msg);
        rmTyping();
        addMsg("bot", reply);
    } catch (err) {
        rmTyping();
        addMsg("bot", fallback(msg));
    }
}

async function callGemini(userMsg) {
    const catalog = P.map(p =>
        `[${p.id}] ${pname(p)} | ${p.cat} | ${p.origin} | ${p._km ?? 0}km | NS:${p.ns} ES:${p.es} | €${p.price}/${p.unit} | CO2:${p.co2}kg | ${pdesc(p)}`
    ).join("\n");

    const systemInstruction = `Eres EcoScan, un asistente experto en productos ecológicos y alimentación sostenible en Barcelona.
Catálogo actual (solo alimentos):
${catalog}
${_chatContext ? `\nContexto del producto seleccionado:\n${_chatContext}` : ""}
Responde siempre en ${_lang === "ca" ? "catalán" : _lang === "en" ? "inglés" : "español"}. Sé conciso y útil.`;

    const resp = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_KEY}`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                system_instruction: { parts: [{ text: systemInstruction }] },
                contents: [{ role: "user", parts: [{ text: userMsg }] }],
            }),
        }
    );
    if (!resp.ok) throw new Error("Gemini error");
    const data = await resp.json();
    return data.candidates?.[0]?.content?.parts?.[0]?.text ?? fallback(userMsg);
}

function fallback(msg) {
    const m = msg.toLowerCase();
    if (m.includes("yogur") || m.includes("leche") || m.includes("lácteo") || m.includes("lacti")) return t("fb_milk");
    if (m.includes("pan") || m.includes("bread") || m.includes("pa ")) return t("fb_bread");
    if (m.includes("manzana") || m.includes("apple") || m.includes("poma")) return t("fb_apple");
    if (m.includes("temporada") || m.includes("season") || m.includes("temporada")) return t("fb_seasonal");
    if (m.includes("bio") || m.includes("ecol") || m.includes("orgànic")) return t("fb_organic");
    return t("fb_general");
}
