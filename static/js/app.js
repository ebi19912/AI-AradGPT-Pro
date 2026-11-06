// static/js/app.js - AradGPT Pro 2.0 Full-Stack SPA Client

let currentUser = null;
let activeSessionId = localStorage.getItem("aradgpt_active_session_id") || null;
let chatMessages = [];
let attachedFileContext = "";
let attachedFileName = "";
let activeProviderKey = "openrouter";
let activeProviderModels = [];
let mediaRecorder = null;
let audioChunks = [];
let recordedAudioBlob = null;
let selectedSTTFile = null;

// ==========================================
// 1. راه‌اندازی اولیه و بررسی احراز هویت و تم
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    checkAuth();
});

function initTheme() {
    const saved = localStorage.getItem("aradgpt_theme") || "dark";
    applyTheme(saved);
}

function toggleTheme() {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    applyTheme(isLight ? "dark" : "light");
}

function applyTheme(theme) {
    const btn = document.getElementById("theme-toggle-btn");
    if (theme === "light") {
        document.documentElement.setAttribute("data-theme", "light");
        localStorage.setItem("aradgpt_theme", "light");
        if (btn) btn.innerHTML = "☀️ حالت روز (روشن)";
    } else {
        document.documentElement.removeAttribute("data-theme");
        localStorage.setItem("aradgpt_theme", "dark");
        if (btn) btn.innerHTML = "🌙 حالت نئونی (تاریک مدرن)";
    }
}

async function checkAuth() {
    try {
        const res = await fetch("/api/auth/me");
        const data = await res.json();
        if (data.authenticated && data.user) {
            currentUser = data.user;
            showDashboard();
        } else {
            showAuth();
        }
    } catch (e) {
        showAuth();
    }
}

function showAuth() {
    document.getElementById("auth-view").style.display = "flex";
    document.getElementById("dashboard-view").style.display = "none";
}

function showDashboard() {
    document.getElementById("auth-view").style.display = "none";
    document.getElementById("dashboard-view").style.display = "block";

    // بروزرسانی اطلاعات سایدبار
    document.getElementById("sidebar-username").innerText = currentUser.username;
    document.getElementById("sidebar-balance").innerText = `💎 ${Math.floor(currentUser.balance).toLocaleString("fa-IR")} تومان`;
    
    if (currentUser.role === "admin") {
        document.getElementById("user-role-badge").innerText = "🛡️ مدیر ارشد";
        document.getElementById("nav-admin").style.display = "flex";
    } else {
        document.getElementById("user-role-badge").innerText = "👤 کاربر سامانه";
        document.getElementById("nav-admin").style.display = "none";
    }

    // بارگذاری ارائه‌دهنده فعال و مدل‌های مربوطه
    loadProvidersAndModels();
    // بارگذاری سشن‌ها و بازیابی خودکار آخرین گفتگوی فعال کاربر
    loadChatSessions(true);
    // بارگذاری پایگاه‌های دانش سازمانی و کاربر
    loadKnowledgeCollections();
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById("login-form");
    const regForm = document.getElementById("register-form");
    const loginBtn = document.getElementById("auth-tab-login-btn");
    const regBtn = document.getElementById("auth-tab-register-btn");

    if (tab === "login") {
        loginForm.style.display = "block";
        regForm.style.display = "none";
        loginBtn.classList.add("active");
        regBtn.classList.remove("active");
    } else {
        loginForm.style.display = "none";
        regForm.style.display = "block";
        loginBtn.classList.remove("active");
        regBtn.classList.add("active");
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const u = document.getElementById("login-username").value.trim();
    const p = document.getElementById("login-password").value;
    const alertBox = document.getElementById("login-alert");

    alertBox.style.display = "none";
    try {
        const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: u, password: p })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            currentUser = data.user;
            showDashboard();
        } else {
            alertBox.style.display = "block";
            alertBox.style.background = "rgba(239, 68, 68, 0.2)";
            alertBox.style.color = "#f87171";
            alertBox.innerText = data.detail || "نام کاربری یا رمز عبور اشتباه است.";
        }
    } catch (err) {
        alert("خطا در برقراری ارتباط با سرور.");
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const u = document.getElementById("reg-username").value.trim();
    const p = document.getElementById("reg-password").value;
    const cp = document.getElementById("reg-confirm-password").value;
    const alertBox = document.getElementById("register-alert");

    alertBox.style.display = "none";
    try {
        const res = await fetch("/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: u, password: p, confirm_password: cp })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            currentUser = data.user;
            alert(data.message || "حساب کاربری با موفقیت ساخته شد!");
            showDashboard();
        } else {
            alertBox.style.display = "block";
            alertBox.style.background = "rgba(239, 68, 68, 0.2)";
            alertBox.style.color = "#f87171";
            alertBox.innerText = data.detail || "خطا در ثبت نام.";
        }
    } catch (err) {
        alert("خطا در ارتباط با سرور.");
    }
}

async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    currentUser = null;
    chatMessages = [];
    activeSessionId = null;
    localStorage.removeItem("aradgpt_active_session_id");
    showAuth();
}

// ==========================================
// 2. ناوبری بین استودیوها و پنل‌ها
// ==========================================
function switchNav(panelKey) {
    document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
    const navBtn = document.getElementById(`nav-${panelKey}`);
    if (navBtn) navBtn.classList.add("active");

    const panels = ["chat", "knowledge", "explorer", "image", "audio", "wallet", "admin"];
    panels.forEach(p => {
        const el = document.getElementById(`panel-${p}`);
        if (el) el.style.display = (p === panelKey) ? "block" : "none";
    });

    // سایدبار تاریخچه چت فقط در تب چت دیده شود
    const sessionsSection = document.getElementById("sidebar-chat-sessions");
    if (sessionsSection) {
        sessionsSection.style.display = (panelKey === "chat") ? "block" : "none";
    }

    const titleMap = {
        chat: ["استودیو چت هوشمند", "دسترسی به برترین مدل‌های هوش مصنوعی جهان با پشتیبانی از تحلیل اسناد و کدنویسی"],
        knowledge: ["پایگاه دانش سازمانی و شخصی (RAG)", "افزودن اسناد، جستجوی وکتوری معنایی و گفتگوی هوشمند مستند"],
        explorer: ["کاوشگر مدل‌های هوش مصنوعی (۴۵۵ مدل)", "جستجو، مقایسه قیمت، پنجره کانتکست و انتخاب سریع مدل از کاتالوگ بین‌المللی"],
        image: ["استودیو گرافیک و تصویر", "تولید تصاویر واقع‌گرایانه و هنری با DALL-E, Flux و Riverflow"],
        audio: ["استودیو صوتی هوشمند", "تبدیل هوشمند متن به گفتار و پیاده‌سازی صوت به متن با هوش مصنوعی Whisper"],
        wallet: ["کیف پول و مدیریت مالی", "بررسی موجودی زنده، اطلاعات کارت‌های بانکی، ثبت فیش و سوابق تراکنش‌ها"],
        admin: ["کنترل‌پنل مدیریت ارشد", "پیکربندی منعطف API، تایید فیش‌های واریزی، مدیریت کاربران و آمار"]
    };

    if (titleMap[panelKey]) {
        document.getElementById("view-title").innerText = titleMap[panelKey][0];
        document.getElementById("view-subtitle").innerText = titleMap[panelKey][1];
    }

    if (panelKey === "knowledge") loadKnowledgeCollections();
    if (panelKey === "explorer") loadExplorerModels();
    if (panelKey === "wallet") loadWalletData();
    if (panelKey === "admin") loadAdminDashboard();
    if (panelKey === "image") loadImageGallery();
}

// ==========================================
// 3. کاتالوگ مدل‌ها به ازای ارائه‌دهنده فعال
// ==========================================
async function loadProvidersAndModels() {
    try {
        const pRes = await fetch("/api/providers");
        const pData = await pRes.json();
        activeProviderKey = pData.active_provider;

        const currentProvObj = pData.providers.find(p => p.key === activeProviderKey);
        const provName = currentProvObj ? currentProvObj.name.split(" ")[0] : activeProviderKey;
        const pillEl = document.getElementById("active-provider-pill");
        if (pillEl) pillEl.innerText = `● ارائه‌دهنده: ${provName}`;

        // دریافت لیست مدل‌های دقیق این ارائه‌دهنده
        const mRes = await fetch(`/api/models?provider=${activeProviderKey}`);
        const mData = await mRes.json();
        activeProviderModels = mData.models || [];

        populateModelDropdowns();
    } catch (e) {
        console.error("Error loading models:", e);
    }
}

let currentChatCategory = "all";
let currentChatSearch = "";

function filterChatModelsByCategory(category) {
    currentChatCategory = category;
    document.querySelectorAll("#chat-category-chips .chip-btn").forEach(btn => btn.classList.remove("active"));
    const activeBtn = document.getElementById(`chip-${category}`);
    if (activeBtn) activeBtn.classList.add("active");
    updateChatModelDropdown();
}

function onSearchChatModels(query) {
    currentChatSearch = (query || "").trim().toLowerCase();
    updateChatModelDropdown();
}

function updateChatModelDropdown() {
    const chatSelect = document.getElementById("chat-model-select");
    if (!chatSelect) return;
    const previousSelected = chatSelect.value;
    chatSelect.innerHTML = "";

    let chatModels = activeProviderModels.filter(m => m.type === "chat" || !m.type);

    // فیلتر دسته‌بندی
    if (currentChatCategory !== "all") {
        if (currentChatCategory === "free") {
            chatModels = chatModels.filter(m => m.is_free || m.category === "free" || (m.input_price === 0 && m.output_price === 0));
        } else {
            chatModels = chatModels.filter(m => m.category === currentChatCategory);
        }
    }

    // فیلتر جستجو
    if (currentChatSearch) {
        chatModels = chatModels.filter(m => 
            (m.id && m.id.toLowerCase().includes(currentChatSearch)) ||
            (m.name && m.name.toLowerCase().includes(currentChatSearch)) ||
            (m.description && m.description.toLowerCase().includes(currentChatSearch)) ||
            (m.vendor && m.vendor.toLowerCase().includes(currentChatSearch))
        );
    }

    if (chatModels.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.innerText = "⚠️ مدلی با این مشخصات یافت نشد";
        chatSelect.appendChild(opt);
    } else {
        chatModels.forEach(m => {
            const opt = document.createElement("option");
            opt.value = m.id;
            const isFree = m.is_free || (m.input_price === 0 && m.output_price === 0);
            const inT = (m.input_price_toman !== undefined && m.input_price_toman > 0) ? `${m.input_price_toman.toLocaleString()}ت` : "رایگان";
            const outT = (m.output_price_toman !== undefined && m.output_price_toman > 0) ? `${m.output_price_toman.toLocaleString()}ت` : "رایگان";
            const badgeTag = isFree ? "🎁 رایگان" : `💎 ${inT} / ${outT}`;
            opt.innerText = `${m.name}  [${badgeTag} | ${m.context || '128K'}]`;
            chatSelect.appendChild(opt);
        });

        // بازگردانی مدل قبلی در صورت تطابق
        if (previousSelected && chatModels.some(m => m.id === previousSelected)) {
            chatSelect.value = previousSelected;
        } else {
            chatSelect.selectedIndex = 0;
        }
    }
    onChatModelChange();
}

function populateModelDropdowns() {
    // 1. مدل‌های چت بر اساس فیلترهای فعال
    updateChatModelDropdown();

    // 2. مدل‌های تصویر
    const imgSelect = document.getElementById("image-model-select");
    imgSelect.innerHTML = "";
    const imgModels = activeProviderModels.filter(m => m.type === "image");
    if (imgModels.length === 0) {
        // فال‌بک مدل‌های عمومی
        ["dall-e-3", "dall-e-2", "flux.1-schnell"].forEach(mid => {
            imgSelect.innerHTML += `<option value="${mid}">${mid}</option>`;
        });
    } else {
        imgModels.forEach(m => {
            const opt = document.createElement("option");
            opt.value = m.id;
            const priceT = m.output_price_toman ? `${m.output_price_toman.toLocaleString()}ت` : "رایگان";
            opt.innerText = `${m.name} (${priceT})`;
            imgSelect.appendChild(opt);
        });
    }
    onImageModelChange();

    // 3. مدل‌های صدا
    const ttsSelect = document.getElementById("tts-model-select");
    const sttSelect = document.getElementById("stt-model-select");
    ttsSelect.innerHTML = "";
    sttSelect.innerHTML = "";

    const audioModels = activeProviderModels.filter(m => m.type === "audio");
    if (audioModels.length === 0) {
        ttsSelect.innerHTML = `<option value="tts-1">tts-1 (OpenAI)</option><option value="tts-1-hd">tts-1-hd (HD)</option>`;
        sttSelect.innerHTML = `<option value="whisper-1">whisper-1 (Whisper)</option>`;
    } else {
        audioModels.forEach(m => {
            const opt = document.createElement("option");
            opt.value = m.id;
            opt.innerText = m.name;
            if (m.id.includes("whisper") || m.id.includes("stt")) {
                sttSelect.appendChild(opt);
            } else {
                ttsSelect.appendChild(opt);
            }
        });
        if (ttsSelect.options.length === 0) ttsSelect.innerHTML = `<option value="tts-1">tts-1</option>`;
        if (sttSelect.options.length === 0) sttSelect.innerHTML = `<option value="whisper-1">whisper-1</option>`;
    }
}

function onChatModelChange() {
    const sel = document.getElementById("chat-model-select");
    const chosenId = sel.value;
    const modelObj = activeProviderModels.find(m => m.id === chosenId);
    const badge = document.getElementById("chat-model-tariff-badge");
    if (!badge) return;

    if (modelObj) {
        const isFree = modelObj.is_free || (modelObj.input_price === 0 && modelObj.output_price === 0);
        if (isFree) {
            badge.innerHTML = `<span style="color:#10b981; font-weight:700; background:rgba(16,185,129,0.12); padding:4px 10px; border-radius:8px; border:1px solid rgba(16,185,129,0.3);">🎁 ۱۰۰٪ رایگان (بدون کسر از موجودی)</span>`;
        } else {
            const inT = modelObj.input_price_toman ? `${modelObj.input_price_toman.toLocaleString()} تومان` : "رایگان";
            const outT = modelObj.output_price_toman ? `${modelObj.output_price_toman.toLocaleString()} تومان` : "رایگان";
            badge.innerHTML = `<span style="color:#94a3b8;">💎 هر ۱M توکن:</span> <b style="color:#10b981;">ورودی: ${inT}</b> | <b style="color:#38bdf8;">خروجی: ${outT}</b>`;
        }
    } else {
        badge.innerHTML = `<span style="color:#94a3b8;">💎 تعرفه استاندارد</span>`;
    }
}

function onImageModelChange() {
    const sel = document.getElementById("image-model-select");
    const chosenId = sel.value;
    const modelObj = activeProviderModels.find(m => m.id === chosenId);
    const badge = document.getElementById("image-tariff-display");
    if (modelObj && modelObj.output_price_toman) {
        badge.innerText = `💎 هزینه هر تصویر: ${modelObj.output_price_toman.toLocaleString()} تومان`;
    } else {
        badge.innerText = `💎 هزینه هر تصویر: ۳,۴۰۰ تومان`;
    }
}

// ==========================================
// 4. استودیو چت هوشمند و استریم زنده (SSE)
// ==========================================
async function loadChatSessions(autoSelect = false) {
    try {
        const res = await fetch("/api/chat/sessions");
        const sessions = await res.json();
        const container = document.getElementById("sessions-list-container");
        container.innerHTML = "";

        if (sessions.length === 0) {
            container.innerHTML = `<span style="color:var(--text-muted); font-size:0.8rem; padding:4px 8px;">هنوز گفتگویی ثبت نشده است.</span>`;
            if (autoSelect) {
                activeSessionId = null;
                localStorage.removeItem("aradgpt_active_session_id");
                chatMessages = [];
                renderChatMessages();
            }
            return;
        }

        sessions.forEach(s => {
            const div = document.createElement("div");
            div.className = `session-btn ${s.id === activeSessionId ? 'active' : ''}`;
            div.id = `session-item-${s.id}`;
            div.innerHTML = `
                <span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:200px;" title="${s.title}">🗨️ ${s.title}</span>
                <span onclick="event.stopPropagation(); deleteChatSession('${s.id}')" style="cursor:pointer; color:var(--text-muted); font-size:0.8rem;" title="حذف">✕</span>
            `;
            div.onclick = () => loadSessionMessages(s.id);
            container.appendChild(div);
        });

        // بازیابی خودکار سشن فعال در زمان لود برنامه
        if (autoSelect) {
            const savedId = localStorage.getItem("aradgpt_active_session_id");
            if (savedId && sessions.some(s => s.id === savedId)) {
                await loadSessionMessages(savedId);
            } else if (sessions.length > 0) {
                await loadSessionMessages(sessions[0].id);
            }
        }
    } catch (e) {
        console.error("Error loading chat sessions:", e);
    }
}

async function loadSessionMessages(sessionId) {
    try {
        activeSessionId = sessionId;
        localStorage.setItem("aradgpt_active_session_id", sessionId);

        // بروزرسانی کلاس فعال در لیست دکمه‌ها
        document.querySelectorAll(".session-btn").forEach(btn => btn.classList.remove("active"));
        const targetBtn = document.getElementById(`session-item-${sessionId}`);
        if (targetBtn) targetBtn.classList.add("active");

        const res = await fetch(`/api/chat/sessions/${sessionId}`);
        const data = await res.json();
        chatMessages = data.messages || [];
        renderChatMessages();
    } catch (e) {
        console.error("Error loading messages:", e);
    }
}

function startNewChat() {
    activeSessionId = null;
    localStorage.removeItem("aradgpt_active_session_id");
    chatMessages = [];
    removeAttachment();
    renderChatMessages();
    document.querySelectorAll(".session-btn").forEach(btn => btn.classList.remove("active"));
    switchNav("chat");
    const input = document.getElementById("chat-user-input");
    if (input) {
        input.value = "";
        input.focus();
    }
}

async function deleteChatSession(sessionId) {
    if (!confirm("آیا از حذف این گفتگو اطمینان دارید؟")) return;
    await fetch(`/api/chat/sessions/${sessionId}`, { method: "DELETE" });
    if (activeSessionId === sessionId) {
        startNewChat();
    }
    loadChatSessions(false);
}

let allChatSessions = [];

async function openChatHistoryModal() {
    const modal = document.getElementById("chat-history-modal");
    if (!modal) return;
    modal.style.display = "flex";
    const searchInput = document.getElementById("history-modal-search");
    if (searchInput) searchInput.value = "";
    await fetchAndRenderHistoryModal();
}

function closeChatHistoryModal() {
    const modal = document.getElementById("chat-history-modal");
    if (modal) modal.style.display = "none";
}

async function fetchAndRenderHistoryModal() {
    const container = document.getElementById("history-modal-list-container");
    if (!container) return;
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 24px;">⏳ در حال بارگذاری تاریخچه گفتگوها...</div>`;

    try {
        const res = await fetch("/api/chat/sessions");
        allChatSessions = await res.json();
        renderHistoryModalList(allChatSessions);
    } catch (e) {
        container.innerHTML = `<div style="color: #f87171; text-align: center; padding: 20px;">خطا در دریافت تاریخچه گفتگوها.</div>`;
    }
}

function filterHistoryModalList(query) {
    const q = (query || "").trim().toLowerCase();
    if (!q) {
        renderHistoryModalList(allChatSessions);
        return;
    }
    const filtered = allChatSessions.filter(s => (s.title || "").toLowerCase().includes(q));
    renderHistoryModalList(filtered);
}

function renderHistoryModalList(sessions) {
    const container = document.getElementById("history-modal-list-container");
    if (!container) return;
    container.innerHTML = "";

    if (!sessions || sessions.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; color: var(--text-muted); padding: 40px 20px;">
                <div style="font-size: 2.6rem; margin-bottom: 10px;">🗨️</div>
                <h4 style="color: var(--text-primary); margin-bottom: 6px;">هنوز گفتگویی ثبت نشده است</h4>
                <p style="font-size: 0.86rem; margin-bottom: 14px;">با پرسیدن اولین سوال، گفتگوی شما به طور خودکار در تاریخچه ذخیره خواهد شد.</p>
                <button class="btn btn-primary btn-sm" onclick="startNewChat(); closeChatHistoryModal();">➕ شروع گفتگوی نو</button>
            </div>
        `;
        return;
    }

    sessions.forEach(s => {
        const item = document.createElement("div");
        const isActive = s.id === activeSessionId;
        item.style.cssText = `display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; margin-bottom: 8px; border-radius: 12px; border: 1px solid ${isActive ? 'var(--neon-cyan)' : 'var(--card-border)'}; background: ${isActive ? 'rgba(56, 189, 248, 0.08)' : 'rgba(255, 255, 255, 0.02)'}; transition: all 0.2s;`;

        item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px; overflow: hidden; cursor: pointer; flex-grow: 1;" onclick="selectSessionFromModal('${s.id}')">
                <span style="font-size: 1.4rem;">🗨️</span>
                <div style="overflow: hidden;">
                    <div style="font-weight: 700; font-size: 0.94rem; color: var(--text-primary); text-overflow: ellipsis; white-space: nowrap; overflow: hidden;" title="${s.title}">${s.title}</div>
                    <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 3px;">🕒 آخرین بروزرسانی: ${s.updated_at || ''}</div>
                </div>
            </div>
            <div style="display: flex; gap: 6px; align-items: center; flex-shrink: 0; margin-right: 12px;">
                <button class="btn btn-sm btn-secondary" onclick="renameChatSessionPrompt('${s.id}', '${s.title.replace(/'/g, "\\'")}')" title="تغییر عنوان">✏️</button>
                <button class="btn btn-sm btn-danger" onclick="deleteChatSessionFromModal('${s.id}')" title="حذف این گفتگو">🗑️</button>
            </div>
        `;
        container.appendChild(item);
    });
}

async function selectSessionFromModal(sessionId) {
    closeChatHistoryModal();
    switchNav("chat");
    await loadSessionMessages(sessionId);
}

async function deleteChatSessionFromModal(sessionId) {
    if (!confirm("آیا از حذف این گفتگو اطمینان دارید؟")) return;
    await fetch(`/api/chat/sessions/${sessionId}`, { method: "DELETE" });
    if (activeSessionId === sessionId) {
        startNewChat();
    }
    await loadChatSessions(false);
    await fetchAndRenderHistoryModal();
}

async function renameChatSessionPrompt(sessionId, currentTitle) {
    const newTitle = prompt("عنوان جدید گفتگو را وارد فرمایید:", currentTitle);
    if (!newTitle || newTitle.trim() === currentTitle) return;

    try {
        const res = await fetch(`/api/chat/sessions/${sessionId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: newTitle.trim() })
        });
        if (res.ok) {
            await loadChatSessions(false);
            await fetchAndRenderHistoryModal();
        }
    } catch (e) {
        alert("خطا در تغییر نام گفتگو.");
    }
}

function renderChatMessages() {
    const list = document.getElementById("chat-messages-list");
    list.innerHTML = "";

    if (chatMessages.length === 0) {
        list.innerHTML = `
            <div style="text-align: center; margin: 40px auto; color: var(--text-muted); max-width: 480px;">
                <div style="font-size: 2.8rem; margin-bottom: 8px;">✨</div>
                <h3 style="color: var(--text-primary); margin-bottom: 6px;">سلام! چه کمکی از دست من برمی‌آید؟</h3>
                <p style="font-size: 0.9rem;">سوال خود را بپرسید، متنی برای تحلیل بفرستید یا سندی را پیوست نمایید.</p>
            </div>
        `;
        return;
    }

    chatMessages.forEach(m => {
        appendMessageBubble(m.role, m.content);
    });

    scrollChatToBottom();
}

function appendMessageBubble(role, content) {
    const list = document.getElementById("chat-messages-list");
    const bubble = document.createElement("div");
    bubble.className = `message-bubble ${role}`;

    const avatarIcon = role === "user" ? "👤" : "🤖";
    const avatarBg = role === "user" ? "rgba(99, 102, 241, 0.2)" : "rgba(139, 92, 246, 0.2)";

    bubble.innerHTML = `
        <div class="message-avatar" style="background:${avatarBg};">${avatarIcon}</div>
        <div class="message-content">${formatMarkdown(content)}</div>
    `;
    list.appendChild(bubble);
    scrollChatToBottom();
    return bubble.querySelector(".message-content");
}

function formatMarkdown(text) {
    if (!text) return "";
    if (typeof marked !== "undefined" && marked.parse) {
        try {
            marked.setOptions({
                gfm: true,
                breaks: true,
                pedantic: false
            });
            let html = marked.parse(text);
            if (typeof DOMPurify !== "undefined" && DOMPurify.sanitize) {
                html = DOMPurify.sanitize(html, {
                    ADD_TAGS: ["button", "pre", "code", "span", "div"],
                    ADD_ATTR: ["onclick", "class", "style", "title"]
                });
            }
            // افزودن نوار عنوان و دکمه کپی به بلوک‌های کد در صورت لزوم
            html = html.replace(/<pre><code([^>]*)>([\s\S]*?)<\/code><\/pre>/g, (m, attrs, code) => {
                return `<pre><div style="display:flex; justify-content:space-between; align-items:center; color:#94a3b8; font-size:0.75rem; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:4px; margin-bottom:8px;"><span style="font-family:monospace;">کد برنامه</span><button class="btn btn-sm btn-secondary" style="padding:2px 8px; font-size:0.72rem;" onclick="copyCode(this)">📋 کپی</button></div><code${attrs}>${code}</code></pre>`;
            });
            return html;
        } catch (e) {
            console.error("Markdown parse error:", e);
        }
    }

    // راهکار پشتیبان در صورت عدم لود کتابخانه
    let clean = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\n/g, "<br>");
    return clean;
}

function copyCode(btn) {
    const codeBlock = btn.closest("pre")?.querySelector("code");
    if (codeBlock) {
        navigator.clipboard.writeText(codeBlock.innerText).then(() => {
            btn.innerText = "✅ کپی شد";
            setTimeout(() => { btn.innerText = "📋 کپی"; }, 2000);
        });
    }
}

function scrollChatToBottom() {
    const list = document.getElementById("chat-messages-list");
    list.scrollTop = list.scrollHeight;
}

function handleChatKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function applyPresetPrompt(prompt) {
    const input = document.getElementById("chat-user-input");
    input.value = prompt;
    input.focus();
}

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/chat/extract-file", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            attachedFileContext = `\n\n--- [سند پیوست: ${data.filename}] ---\n${data.text}\n--- [پایان سند] ---\n`;
            attachedFileName = data.filename;
            document.getElementById("file-attachment-badge").style.display = "flex";
            document.getElementById("file-attachment-name").innerText = `📎 سند پیوست: ${data.filename} (${data.token_estimate.toLocaleString()} توکن)`;
        } else {
            alert(data.detail || "خطا در خواندن فایل.");
        }
    } catch (err) {
        alert("خطا در آپلود فایل.");
    }
}

function removeAttachment() {
    attachedFileContext = "";
    attachedFileName = "";
    document.getElementById("chat-file-input").value = "";
    document.getElementById("file-attachment-badge").style.display = "none";
}

// ارسال پیام و دریافت استریم پاسخ (SSE) با حفظ کامل حافظه و زمینه مکالمه
async function sendMessage() {
    const input = document.getElementById("chat-user-input");
    const text = input.value.trim();
    if (!text && !attachedFileContext) return;

    // پاکسازی بنر اولیه خوش‌آمدگویی در آغاز اولین پیام
    if (chatMessages.length === 0) {
        const msgList = document.getElementById("chat-messages-list");
        if (msgList) msgList.innerHTML = "";
    }

    // بازیابی سشن فعال از حافظه در صورت عدم مقداردهی
    if (!activeSessionId) {
        activeSessionId = localStorage.getItem("aradgpt_active_session_id") || null;
    }

    const sendBtn = document.getElementById("chat-send-btn");
    sendBtn.disabled = true;
    input.value = "";

    const fullUserText = text + attachedFileContext;
    chatMessages.push({ role: "user", content: fullUserText });

    // رندر پیام کاربر
    appendMessageBubble("user", text + (attachedFileName ? `\n\n📎 *سند ضمیمه شد: ${attachedFileName}*` : ""));
    removeAttachment();

    // ایجاد حباب پیام خالی برای استریم هوش مصنوعی
    const assistantContentEl = appendMessageBubble("assistant", "در حال پردازش پاسخ...");

    const selectedModel = document.getElementById("chat-model-select").value;
    const sysPrompt = document.getElementById("chat-system-prompt").value;
    const temp = parseFloat(document.getElementById("chat-temperature").value);

    try {
        const payload = {
            session_id: activeSessionId,
            model: selectedModel,
            messages: chatMessages,
            system_prompt: sysPrompt,
            temperature: temp
        };
        if (selectedChatKnowledgeId) {
            payload.knowledge_collection_id = selectedChatKnowledgeId;
        }

        const response = await fetch("/api/chat/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            assistantContentEl.innerHTML = `<span style="color:#f87171;">⚠️ خطا: ${errData.detail || 'خطا در ارتباط با سرور'}</span>`;
            sendBtn.disabled = false;
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let accumulatedReply = "";
        let accumulatedReasoning = "";
        assistantContentEl.innerHTML = "";

        const updateBubbleUI = () => {
            let html = "";
            if (accumulatedReasoning) {
                html += `<details open style="margin-bottom:12px; background:rgba(255,255,255,0.03); border:1px solid rgba(139,92,246,0.25); border-radius:10px; padding:10px 14px; font-size:0.84rem; color:var(--text-muted);"><summary style="cursor:pointer; color:#a78bfa; font-weight:600; outline:none; user-select:none;">🧠 فرآیند تفکر و استدلال مدل (Thinking)</summary><div style="margin-top:8px; line-height:1.6; white-space:pre-wrap; opacity:0.9;">${formatMarkdown(accumulatedReasoning)}</div></details>`;
            }
            if (accumulatedReply) {
                html += formatMarkdown(accumulatedReply);
            } else if (!accumulatedReasoning) {
                html = "در حال پردازش پاسخ...";
            }
            assistantContentEl.innerHTML = html;
            scrollChatToBottom();
        };

        let sseBuffer = "";
        let streamDoneHandled = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            sseBuffer += decoder.decode(value, { stream: true });
            const parts = sseBuffer.split("\n\n");
            // قطعه آخر هنوز کامل نشده است و در بافر نگهداری می‌شود
            sseBuffer = parts.pop();

            for (const part of parts) {
                const lines = part.split("\n");
                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (trimmedLine.startsWith("data: ")) {
                        const jsonStr = trimmedLine.substring(6).trim();
                        if (!jsonStr) continue;
                        try {
                            const data = JSON.parse(jsonStr);

                            if (data.reasoning) {
                                accumulatedReasoning += data.reasoning;
                                updateBubbleUI();
                            }

                            if (data.delta) {
                                accumulatedReply += data.delta;
                                updateBubbleUI();
                            }

                            if (data.done) {
                                streamDoneHandled = true;
                                activeSessionId = data.session_id;
                                localStorage.setItem("aradgpt_active_session_id", activeSessionId);
                                chatMessages.push({ role: "assistant", content: accumulatedReply });

                                // بروزرسانی موجودی کاربر
                                if (data.new_balance !== undefined) {
                                    currentUser.balance = data.new_balance;
                                    document.getElementById("sidebar-balance").innerText = `💎 ${Math.floor(currentUser.balance).toLocaleString("fa-IR")} تومان`;
                                }
                                loadChatSessions(false);
                            }

                            if (data.error) {
                                assistantContentEl.innerHTML += `<div style="background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); border-radius:10px; padding:10px; color:#f87171; margin-top:8px;">⚠️ <b>خطا در پردازش مدل:</b><br>${data.error}</div>`;
                            }
                        } catch (pe) {
                            console.error("JSON parse error on SSE:", pe);
                        }
                    }
                }
            }
        }

        // بررسی قطعه باقیمانده در بافر پس از پایان استریم
        if (sseBuffer.trim().startsWith("data: ")) {
            try {
                const jsonStr = sseBuffer.trim().substring(6).trim();
                const data = JSON.parse(jsonStr);
                if (data.done) {
                    streamDoneHandled = true;
                    activeSessionId = data.session_id;
                    localStorage.setItem("aradgpt_active_session_id", activeSessionId);
                    chatMessages.push({ role: "assistant", content: accumulatedReply });
                    if (data.new_balance !== undefined) {
                        currentUser.balance = data.new_balance;
                        document.getElementById("sidebar-balance").innerText = `💎 ${Math.floor(currentUser.balance).toLocaleString("fa-IR")} تومان`;
                    }
                    loadChatSessions(false);
                }
            } catch (e) {}
        }

        // تضمین قطعی حفظ پاسخ در آرایه پیام‌ها برای پایداری ۱۰۰٪ حافظه
        if (!streamDoneHandled && accumulatedReply) {
            const lastMsg = chatMessages[chatMessages.length - 1];
            if (!lastMsg || lastMsg.role !== "assistant" || lastMsg.content !== accumulatedReply) {
                chatMessages.push({ role: "assistant", content: accumulatedReply });
            }
            if (activeSessionId) {
                localStorage.setItem("aradgpt_active_session_id", activeSessionId);
            }
        }
    } catch (e) {
        assistantContentEl.innerHTML = `<span style="color:#f87171;">خطا در ارسال درخواست: ${e.message}</span>`;
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

// ==========================================
// 5. استودیو تصویر
// ==========================================
function switchImageTab(tab) {
    const createTab = document.getElementById("image-create-tab");
    const galleryTab = document.getElementById("image-gallery-tab");
    const createBtn = document.getElementById("img-tab-create-btn");
    const galleryBtn = document.getElementById("img-tab-gallery-btn");

    if (tab === "create") {
        createTab.style.display = "block";
        galleryTab.style.display = "none";
        createBtn.classList.add("active");
        galleryBtn.classList.remove("active");
    } else {
        createTab.style.display = "none";
        galleryTab.style.display = "block";
        createBtn.classList.remove("active");
        galleryBtn.classList.add("active");
        loadImageGallery();
    }
}

async function generateImage() {
    const prompt = document.getElementById("image-prompt-input").value.trim();
    if (!prompt) {
        alert("لطفاً توصیف تصویر مورد نظر را وارد فرمایید.");
        return;
    }

    const model = document.getElementById("image-model-select").value;
    const style = document.getElementById("image-style-select").value;
    const size = document.getElementById("image-size-select").value;

    const fullPrompt = style ? `${prompt}, ${style}` : prompt;
    const btn = document.getElementById("btn-generate-image");
    const outBox = document.getElementById("image-output-container");

    btn.disabled = true;
    outBox.innerHTML = `
        <div style="color:var(--text-secondary); text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:10px;">⏳</div>
            <p>هوش مصنوعی در حال پردازش و تولید تصویر است... (۱۰ الی ۳۰ ثانیه)</p>
        </div>
    `;

    try {
        const res = await fetch("/api/image/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model: model, prompt: fullPrompt, size: size })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            outBox.innerHTML = `
                <img src="${data.image_url}" alt="Generated Image" style="max-width:100%; border-radius:14px; box-shadow:0 8px 24px rgba(0,0,0,0.5); margin-bottom:14px;">
                <div style="display:flex; gap:10px; justify-content:center;">
                    <a href="${data.image_url}" target="_blank" class="btn btn-primary">📥 مشاهده در اندازه اصلی</a>
                </div>
            `;
            if (data.new_balance !== undefined) {
                currentUser.balance = data.new_balance;
                document.getElementById("sidebar-balance").innerText = `💎 ${Math.floor(currentUser.balance).toLocaleString("fa-IR")} تومان`;
            }
        } else {
            outBox.innerHTML = `<span style="color:#f87171;">⚠️ ${data.detail || 'خطا در ایجاد تصویر'}</span>`;
        }
    } catch (err) {
        outBox.innerHTML = `<span style="color:#f87171;">خطا در برقراری ارتباط با سرور.</span>`;
    } finally {
        btn.disabled = false;
    }
}

async function loadImageGallery() {
    try {
        const res = await fetch("/api/image/history");
        const items = await res.json();
        const grid = document.getElementById("image-gallery-grid");
        grid.innerHTML = "";

        if (items.length === 0) {
            grid.innerHTML = `<p style="color:var(--text-muted); grid-column:span 3;">هنوز تصویری تولید نکرده‌اید.</p>`;
            return;
        }

        items.forEach(it => {
            const card = document.createElement("div");
            card.className = "glass-card";
            card.style.padding = "12px";
            card.innerHTML = `
                <img src="${it.image_url}" style="width:100%; height:200px; object-fit:cover; border-radius:10px; margin-bottom:8px;">
                <div style="font-size:0.8rem; color:#94a3b8; margin-bottom:6px;">مدل: ${it.model}</div>
                <div style="font-size:0.82rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; margin-bottom:10px;" title="${it.prompt}">${it.prompt}</div>
                <a href="${it.image_url}" target="_blank" class="btn btn-sm btn-secondary" style="width:100%;">📥 مشاهده عکس</a>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        console.error("Error loading gallery:", e);
    }
}

// ==========================================
// 6. استودیو صدا (TTS و STT)
// ==========================================
function switchAudioTab(tab) {
    const ttsCont = document.getElementById("audio-tts-container");
    const sttCont = document.getElementById("audio-stt-container");
    const ttsBtn = document.getElementById("audio-tab-tts-btn");
    const sttBtn = document.getElementById("audio-tab-stt-btn");

    if (tab === "tts") {
        ttsCont.style.display = "block";
        sttCont.style.display = "none";
        ttsBtn.classList.add("active");
        sttBtn.classList.remove("active");
    } else {
        ttsCont.style.display = "none";
        sttCont.style.display = "block";
        ttsBtn.classList.remove("active");
        sttBtn.classList.add("active");
    }
}

async function generateTTS() {
    const text = document.getElementById("tts-input-text").value.trim();
    if (!text) {
        alert("لطفاً متنی برای تبدیل به گفتار بنویسید.");
        return;
    }

    const model = document.getElementById("tts-model-select").value;
    const voice = document.getElementById("tts-voice-select").value;
    const speed = parseFloat(document.getElementById("tts-speed-range").value);
    const btn = document.getElementById("btn-generate-tts");

    btn.disabled = true;
    btn.innerText = "⏳ در حال ساخت صدا...";

    try {
        const res = await fetch("/api/audio/tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model: model, input_text: text, voice: voice, speed: speed })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            const audioSrc = `data:${data.mime_type};base64,${data.audio_base64}`;
            const player = document.getElementById("tts-audio-player");
            player.src = audioSrc;
            player.play();

            document.getElementById("tts-download-link").href = audioSrc;
            document.getElementById("tts-player-container").style.display = "block";

            if (data.new_balance !== undefined) {
                currentUser.balance = data.new_balance;
                document.getElementById("sidebar-balance").innerText = `💎 ${Math.floor(currentUser.balance).toLocaleString("fa-IR")} تومان`;
            }
        } else {
            alert(data.detail || "خطا در تولید صوت.");
        }
    } catch (err) {
        alert("خطا در ارتباط با سرور.");
    } finally {
        btn.disabled = false;
        btn.innerText = "🎵 تولید فایل صوتی";
    }
}

function onSTTFileSelected(e) {
    const file = e.target.files[0];
    if (file) {
        selectedSTTFile = file;
        recordedAudioBlob = null;
        document.getElementById("stt-selected-file-label").innerText = `فایل انتخاب شد: ${file.name}`;
    }
}

async function toggleMicRecording() {
    const btn = document.getElementById("btn-record-mic");
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
            mediaRecorder.onstop = () => {
                recordedAudioBlob = new Blob(audioChunks, { type: "audio/wav" });
                selectedSTTFile = null;
                document.getElementById("stt-selected-file-label").innerText = "🎙️ صدای شما با موفقیت ضبط شد. آماده پیاده‌سازی متن.";
            };
            mediaRecorder.start();
            btn.innerText = "🛑 توقف ضبط صدا";
            btn.classList.add("btn-danger");
        } catch (err) {
            alert("امکان دسترسی به میکروفون میسر نشد: " + err.message);
        }
    } else {
        mediaRecorder.stop();
        btn.innerText = "🎙️ ضبط زنده با میکروفون";
        btn.classList.remove("btn-danger");
    }
}

async function runSTT() {
    if (!selectedSTTFile && !recordedAudioBlob) {
        alert("لطفاً یک فایل صوتی انتخاب کنید یا صدایی با میکروفون ضبط فرمایید.");
        return;
    }

    const model = document.getElementById("stt-model-select").value;
    const lang = document.getElementById("stt-lang-select").value;
    const btn = document.getElementById("btn-run-stt");

    btn.disabled = true;
    btn.innerText = "⏳ در حال گوش دادن و پیاده‌سازی متن...";

    const formData = new FormData();
    formData.append("model", model);
    formData.append("language", lang);

    if (selectedSTTFile) {
        formData.append("file", selectedSTTFile);
    } else {
        formData.append("file", recordedAudioBlob, "recording.wav");
    }

    try {
        const res = await fetch("/api/audio/stt", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById("stt-result-container").style.display = "block";
            document.getElementById("stt-output-text").value = data.text;
            if (data.new_balance !== undefined) {
                currentUser.balance = data.new_balance;
                document.getElementById("sidebar-balance").innerText = `💎 ${Math.floor(currentUser.balance).toLocaleString("fa-IR")} تومان`;
            }
        } else {
            alert(data.detail || "خطا در پیاده‌سازی متن.");
        }
    } catch (err) {
        alert("خطا در ارتباط با سرور.");
    } finally {
        btn.disabled = false;
        btn.innerText = "📝 استخراج و پیاده‌سازی متن";
    }
}

// ==========================================
// 7. کیف پول و امور مالی
// ==========================================
function switchWalletTab(tab) {
    const chargeTab = document.getElementById("wallet-charge-tab");
    const requestsTab = document.getElementById("wallet-requests-tab");
    const historyTab = document.getElementById("wallet-history-tab");

    const chargeBtn = document.getElementById("w-tab-charge-btn");
    const requestsBtn = document.getElementById("w-tab-requests-btn");
    const historyBtn = document.getElementById("w-tab-history-btn");

    chargeTab.style.display = tab === "charge" ? "block" : "none";
    requestsTab.style.display = tab === "requests" ? "block" : "none";
    historyTab.style.display = tab === "history" ? "block" : "none";

    chargeBtn.classList.toggle("active", tab === "charge");
    requestsBtn.classList.toggle("active", tab === "requests");
    historyBtn.classList.toggle("active", tab === "history");

    if (tab === "requests" || tab === "history") loadWalletData();
}

async function loadWalletData() {
    try {
        const res = await fetch("/api/wallet/info");
        const data = await res.json();

        currentUser.balance = data.balance;
        document.getElementById("sidebar-balance").innerText = `💎 ${Math.floor(currentUser.balance).toLocaleString("fa-IR")} تومان`;

        // حساب‌های بانکی
        const bankContainer = document.getElementById("wallet-bank-cards-list");
        bankContainer.innerHTML = "";
        if (data.bank_accounts.length === 0) {
            bankContainer.innerHTML = `<span style="color:var(--text-muted); font-size:0.85rem;">حساب فعالی ثبت نشده است.</span>`;
        } else {
            data.bank_accounts.forEach(b => {
                bankContainer.innerHTML += `
                    <div style="background:rgba(255,255,255,0.03); border:1px solid var(--card-border); border-radius:12px; padding:12px; margin-bottom:10px;">
                        <b style="color:#fff;">${b.bank_name}</b> — <span>به نام ${b.owner_name}</span>
                        <div style="margin-top:6px; display:flex; align-items:center; justify-content:space-between; background:#050811; padding:6px 10px; border-radius:8px;">
                            <code style="color:#34d399; font-size:1rem;">${b.card_number}</code>
                            <button class="btn btn-sm btn-secondary" onclick="navigator.clipboard.writeText('${b.card_number}'); alert('شماره کارت کپی شد.')">کپی</button>
                        </div>
                    </div>
                `;
            });
        }

        // سوابق فیش‌ها
        const reqContainer = document.getElementById("wallet-my-requests-list");
        reqContainer.innerHTML = "";
        if (data.deposit_requests.length === 0) {
            reqContainer.innerHTML = `<span style="color:var(--text-muted);">هنوز فیش واریزی ارسال نکرده‌اید.</span>`;
        } else {
            data.deposit_requests.forEach(r => {
                let badge = '<span class="badge badge-pending">⏳ در انتظار بررسی</span>';
                if (r.status === "APPROVED") badge = '<span class="badge badge-approved">✅ تایید و شارژ شده</span>';
                if (r.status === "REJECTED") badge = '<span class="badge badge-rejected">❌ رد شده</span>';

                reqContainer.innerHTML += `
                    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); border:1px solid var(--card-border); border-radius:10px; padding:12px; margin-bottom:8px;">
                        <div>
                            <b>مبلغ: ${r.amount.toLocaleString()} تومان</b>
                            <div style="font-size:0.8rem; color:var(--text-muted);">تاریخ: ${r.created_at} ${r.admin_note ? `| نظر ادمین: ${r.admin_note}` : ''}</div>
                        </div>
                        <div>${badge}</div>
                    </div>
                `;
            });
        }

        // تاریخچه مصارف
        const tBody = document.getElementById("wallet-transactions-tbody");
        tBody.innerHTML = "";
        data.transactions.forEach(t => {
            tBody.innerHTML += `
                <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                    <td style="padding:10px;">#${t.id}</td>
                    <td>${t.model}</td>
                    <td>${t.type}</td>
                    <td style="color:#f87171;">-${Math.floor(t.cost_toman).toLocaleString()} ت</td>
                    <td style="color:var(--text-muted); font-size:0.8rem;">${t.timestamp}</td>
                </tr>
            `;
        });
    } catch (e) {
        console.error("Error loading wallet data:", e);
    }
}

async function submitDepositReceipt() {
    const amt = document.getElementById("deposit-amount-input").value;
    const file = document.getElementById("deposit-receipt-file").files[0];
    if (!file) {
        alert("لطفاً تصویر فیش واریزی را انتخاب کنید.");
        return;
    }

    const formData = new FormData();
    formData.append("amount", amt);
    formData.append("receipt", file);

    try {
        const res = await fetch("/api/wallet/deposit", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert(data.message);
            document.getElementById("deposit-receipt-file").value = "";
            switchWalletTab("requests");
        } else {
            alert(data.detail || "خطا در ثبت فیش.");
        }
    } catch (err) {
        alert("خطا در ارتباط با سرور.");
    }
}

// ==========================================
// 8. کنترل‌پنل مدیریت ارشد (Admin)
// ==========================================
function switchAdminTab(tab) {
    const tabs = ["deposits", "banks", "users", "settings", "logs"];
    tabs.forEach(t => {
        document.getElementById(`admin-${t}-tab`).style.display = (t === tab) ? "block" : "none";
        document.getElementById(`adm-tab-${t}-btn`).classList.toggle("active", t === tab);
    });
}

async function loadAdminDashboard() {
    try {
        const sRes = await fetch("/api/admin/stats");
        const stats = await sRes.json();
        document.getElementById("admin-stat-users").innerText = stats.total_users.toLocaleString();
        document.getElementById("admin-stat-revenue").innerText = `${Math.floor(stats.total_revenue).toLocaleString()} ت`;
        document.getElementById("admin-stat-pending").innerText = stats.pending_payments;
        document.getElementById("admin-stat-requests").innerText = stats.total_requests.toLocaleString();

        loadAdminDeposits();
        loadAdminBanks();
        loadAdminUsers();
        loadAdminSettings();
        loadAdminLogs();
    } catch (e) {
        console.error("Error loading admin stats:", e);
    }
}

async function loadAdminDeposits() {
    try {
        const res = await fetch("/api/admin/deposits");
        const data = await res.json();
        const container = document.getElementById("admin-pending-deposits-list");
        container.innerHTML = "";

        if (data.pending.length === 0) {
            container.innerHTML = `<span style="color:var(--text-muted);">در حال حاضر فیش جدیدی در انتظار نیست.</span>`;
            return;
        }

        data.pending.forEach(d => {
            container.innerHTML += `
                <div style="background:rgba(255,255,255,0.02); border:1px solid var(--card-border); border-radius:12px; padding:16px; margin-bottom:12px; display:flex; gap:16px; align-items:center;">
                    ${d.receipt_b64 ? `<img src="data:image/png;base64,${d.receipt_b64}" style="width:120px; height:120px; object-fit:cover; border-radius:10px; cursor:pointer;" onclick="window.open(this.src)">` : ''}
                    <div style="flex-grow:1;">
                        <h4 style="color:#fff;">کاربر: ${d.username} | مبلغ: ${d.amount.toLocaleString()} تومان</h4>
                        <span style="font-size:0.8rem; color:var(--text-muted);">تاریخ ارسال: ${d.created_at}</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-sm btn-primary" onclick="adminProcessDeposit(${d.id}, 'APPROVED')">✅ تایید و شارژ</button>
                        <button class="btn btn-sm btn-danger" onclick="adminProcessDeposit(${d.id}, 'REJECTED')">❌ رد</button>
                    </div>
                </div>
            `;
        });
    } catch (e) {
        console.error("Error loading deposits:", e);
    }
}

async function adminProcessDeposit(reqId, action) {
    const note = prompt(action === "APPROVED" ? "یادداشت تایید (اختیاری):" : "دلیل رد فیش:");
    const formData = new FormData();
    formData.append("action", action);
    formData.append("admin_note", note || "");

    await fetch(`/api/admin/deposits/${reqId}/process`, {
        method: "POST",
        body: formData
    });
    loadAdminDeposits();
    loadAdminDashboard();
}

async function loadAdminBanks() {
    try {
        const res = await fetch("/api/admin/bank-accounts");
        const banks = await res.json();
        const container = document.getElementById("admin-banks-list");
        container.innerHTML = "";

        banks.forEach(b => {
            container.innerHTML += `
                <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); border:1px solid var(--card-border); padding:10px; border-radius:10px; margin-bottom:8px;">
                    <div>
                        <b>${b.bank_name}</b> (${b.owner_name})
                        <div style="font-size:0.85rem; color:#34d399;">${b.card_number}</div>
                    </div>
                    <button class="btn btn-sm btn-danger" onclick="adminDeleteBank(${b.id})">حذف</button>
                </div>
            `;
        });
    } catch (e) {
        console.error("Error loading admin banks:", e);
    }
}

async function adminAddBank() {
    const name = document.getElementById("new-bank-name").value.trim();
    const owner = document.getElementById("new-bank-owner").value.trim();
    const card = document.getElementById("new-bank-card").value.trim();
    const sheba = document.getElementById("new-bank-sheba").value.trim();

    if (!name || !owner || !card) {
        alert("لطفاً نام بانک، صاحب حساب و شماره کارت را وارد کنید.");
        return;
    }

    const formData = new FormData();
    formData.append("bank_name", name);
    formData.append("owner_name", owner);
    formData.append("card_number", card);
    formData.append("sheba_number", sheba);

    await fetch("/api/admin/bank-accounts", { method: "POST", body: formData });
    document.getElementById("new-bank-name").value = "";
    document.getElementById("new-bank-owner").value = "";
    document.getElementById("new-bank-card").value = "";
    document.getElementById("new-bank-sheba").value = "";
    loadAdminBanks();
}

async function adminDeleteBank(id) {
    if (!confirm("آیا از حذف این حساب بانکی اطمینان دارید؟")) return;
    await fetch(`/api/admin/bank-accounts/${id}`, { method: "DELETE" });
    loadAdminBanks();
}

let allAdminUsers = [];
async function loadAdminUsers() {
    try {
        const res = await fetch("/api/admin/users");
        allAdminUsers = await res.json();
        renderAdminUsersTable(allAdminUsers);
    } catch (e) {
        console.error("Error loading users:", e);
    }
}

function adminSearchUsers(q) {
    const filtered = allAdminUsers.filter(u => u.username.includes(q.toLowerCase().trim()));
    renderAdminUsersTable(filtered);
}

function renderAdminUsersTable(users) {
    const tBody = document.getElementById("admin-users-tbody");
    tBody.innerHTML = "";
    users.forEach(u => {
        tBody.innerHTML += `
            <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                <td style="padding:10px;"><b>${u.username}</b></td>
                <td>${Math.floor(u.balance).toLocaleString()} ت</td>
                <td><span class="badge ${u.role === 'admin' ? 'badge-approved' : 'badge-pending'}">${u.role}</span></td>
                <td style="color:var(--text-muted); font-size:0.8rem;">${u.created_at || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="openUserModal('${u.username}', ${u.balance}, '${u.role}')">مدیریت</button>
                </td>
            </tr>
        `;
    });
}

let modalTargetUser = null;
function openUserModal(username, balance, role) {
    modalTargetUser = username;
    document.getElementById("modal-user-title").innerText = `مدیریت کاربر: ${username} (موجودی: ${Math.floor(balance).toLocaleString()} ت)`;
    document.getElementById("modal-balance-change").value = "";
    document.getElementById("modal-new-password").value = "";
    document.getElementById("modal-role-select").value = role;
    document.getElementById("user-modal").style.display = "flex";
}

function closeUserModal() {
    document.getElementById("user-modal").style.display = "none";
}

async function adminSubmitBalanceChange() {
    const amt = document.getElementById("modal-balance-change").value;
    if (!amt) return;
    const formData = new FormData();
    formData.append("amount", amt);
    await fetch(`/api/admin/users/${modalTargetUser}/balance`, { method: "PUT", body: formData });
    alert("موجودی کاربر بروزرسانی شد.");
    closeUserModal();
    loadAdminUsers();
}

async function adminSubmitPasswordChange() {
    const p = document.getElementById("modal-new-password").value;
    if (!p) return;
    const formData = new FormData();
    formData.append("new_password", p);
    await fetch(`/api/admin/users/${modalTargetUser}/password`, { method: "PUT", body: formData });
    alert("رمز عبور کاربر تغییر یافت.");
    closeUserModal();
}

async function adminSubmitRoleChange() {
    const r = document.getElementById("modal-role-select").value;
    const formData = new FormData();
    formData.append("role", r);
    await fetch(`/api/admin/users/${modalTargetUser}/role`, { method: "PUT", body: formData });
    alert("نقش کاربر تغییر یافت.");
    closeUserModal();
    loadAdminUsers();
}

async function adminSubmitDeleteUser() {
    if (!confirm(`آیا از حذف دائمی کاربر ${modalTargetUser} اطمینان دارید؟`)) return;
    const res = await fetch(`/api/admin/users/${modalTargetUser}`, { method: "DELETE" });
    if (res.ok) {
        alert("کاربر حذف گردید.");
        closeUserModal();
        loadAdminUsers();
    } else {
        alert("خطا در حذف کاربر.");
    }
}

// تنظیمات سراسری API
async function loadAdminSettings() {
    try {
        const res = await fetch("/api/admin/settings");
        const s = await res.json();
        document.getElementById("admin-provider-select").value = s.active_provider;
        document.getElementById("admin-base-url-input").value = s.base_url;
        document.getElementById("admin-api-key-input").value = s.api_key;
        document.getElementById("admin-usd-toman-input").value = s.usd_to_toman;
        document.getElementById("admin-welcome-bonus-input").value = s.welcome_bonus;
    } catch (e) {
        console.error("Error loading settings:", e);
    }
}

function onAdminProviderChanged() {
    const p = document.getElementById("admin-provider-select").value;
    const urlMap = {
        openrouter: "https://openrouter.ai/api/v1",
        gapgpt: "https://api.gapgpt.app/v1",
        openai: "https://api.openai.com/v1",
        deepseek: "https://api.deepseek.com/v1",
        groq: "https://api.groq.com/openai/v1",
        custom: "http://localhost:11434/v1"
    };
    if (urlMap[p]) {
        document.getElementById("admin-base-url-input").value = urlMap[p];
    }
}

async function adminSaveSettings() {
    const payload = {
        active_provider: document.getElementById("admin-provider-select").value,
        base_url: document.getElementById("admin-base-url-input").value,
        api_key: document.getElementById("admin-api-key-input").value,
        usd_to_toman: parseInt(document.getElementById("admin-usd-toman-input").value) || 85000,
        welcome_bonus: parseInt(document.getElementById("admin-welcome-bonus-input").value) || 20000
    };

    const res = await fetch("/api/admin/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok && data.success) {
        alert("✅ تنظیمات با موفقیت ذخیره و اعمال گردید!");
        loadProvidersAndModels();
    } else {
        alert("خطا در ذخیره تنظیمات.");
    }
}

async function adminPingAPI() {
    const key = document.getElementById("admin-api-key-input").value;
    const url = document.getElementById("admin-base-url-input").value;
    const box = document.getElementById("admin-test-result-box");

    box.style.display = "block";
    box.style.background = "rgba(255,255,255,0.05)";
    box.style.color = "#fff";
    box.innerText = "⏳ در حال ارسال پینگ تست و بررسی مدل‌ها...";

    try {
        const res = await fetch("/api/admin/test-api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: key, base_url: url })
        });
        const data = await res.json();
        if (data.success) {
            box.style.background = "rgba(16, 185, 129, 0.15)";
            box.style.color = "#34d399";
            box.innerHTML = `✅ ${data.message} ${data.models.length > 0 ? `<br><small>مدل‌های نمونه: ${data.models.slice(0, 5).join(', ')}</small>` : ''}`;
        } else {
            box.style.background = "rgba(239, 68, 68, 0.15)";
            box.style.color = "#f87171";
            box.innerText = `❌ ${data.message}`;
        }
    } catch (err) {
        box.style.background = "rgba(239, 68, 68, 0.15)";
        box.style.color = "#f87171";
        box.innerText = "خطا در تست ارتباط.";
    }
}

async function loadAdminLogs() {
    try {
        const res = await fetch("/api/admin/logs");
        const logs = await res.json();
        const tBody = document.getElementById("admin-logs-tbody");
        tBody.innerHTML = "";

        logs.forEach(l => {
            tBody.innerHTML += `
                <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                    <td style="padding:8px;">#${l.id}</td>
                    <td><b>${l.username}</b></td>
                    <td>${l.model}</td>
                    <td>${l.type}</td>
                    <td style="color:#f87171;">-${Math.floor(l.cost_toman).toLocaleString()} ت</td>
                    <td style="color:var(--text-muted); font-size:0.8rem;">${l.timestamp}</td>
                </tr>
            `;
        });
    } catch (e) {
        console.error("Error loading logs:", e);
    }
}


// ==========================================
// 8. پایگاه دانش سازمانی و شخصی (RAG)
// ==========================================
let knowledgeCollections = [];
let activeCollectionId = null;
let selectedChatKnowledgeId = "";

async function loadKnowledgeCollections() {
    try {
        const res = await fetch("/api/knowledge/collections");
        const data = await res.json();
        knowledgeCollections = data.collections || [];

        // پر کردن گرید مجموعه‌ها در تب پایگاه دانش
        const grid = document.getElementById("kb-collections-grid");
        if (grid) {
            grid.innerHTML = "";
            if (knowledgeCollections.length === 0) {
                grid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
                        <div style="font-size: 3rem; margin-bottom: 12px;">📚</div>
                        <h4 style="color: var(--text-primary); margin-bottom: 6px;">هنوز پایگاه دانشی ایجاد نکرده‌اید</h4>
                        <p style="font-size: 0.88rem; margin-bottom: 16px;">با کلیک روی «ساخت مجموعه جدید»، اولین پایگاه دانش خود را بسازید و اسناد خود را بارگذاری کنید.</p>
                        <button class="btn btn-primary" onclick="openCreateCollectionModal()">➕ ساخت اولین پایگاه دانش</button>
                    </div>
                `;
            } else {
                knowledgeCollections.forEach(col => {
                    const card = document.createElement("div");
                    card.className = "glass-card collection-card";
                    card.style.cursor = "pointer";
                    card.onclick = () => selectKnowledgeCollection(col.id);
                    card.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                            <span style="font-size: 2.2rem;">${col.icon || '📚'}</span>
                            <span class="role-badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399; font-size: 0.75rem;">
                                ${col.document_count || 0} سند | ${col.chunk_count || 0} قطعه
                            </span>
                        </div>
                        <h4 style="margin-bottom: 6px; font-size: 1.05rem; color: var(--text-primary); font-weight: 700;">${col.title}</h4>
                        <p style="font-size: 0.84rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 14px; min-height: 40px;">
                            ${col.description || 'بدون توضیحات اضافی'}
                        </p>
                        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--card-border); padding-top: 10px; font-size: 0.78rem; color: var(--text-muted);">
                            <span>📅 ${col.created_at || ''}</span>
                            <span style="color: var(--neon-cyan); font-weight: 600;">مدیریت اسناد ➔</span>
                        </div>
                    `;
                    grid.appendChild(card);
                });
            }
        }

        // پر کردن دراپ‌داون در چت استودیو و تب جستجو
        populateKnowledgeDropdowns();
    } catch (e) {
        console.error("Error loading knowledge collections:", e);
    }
}

function populateKnowledgeDropdowns() {
    // 1. انتخابگر در چت استودیو
    const chatSelect = document.getElementById("chat-knowledge-select");
    if (chatSelect) {
        const prev = chatSelect.value;
        chatSelect.innerHTML = `<option value="">بدون پایگاه دانش (چت مستقیم عمومی)</option>`;
        knowledgeCollections.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.innerText = `${c.icon || '📚'} ${c.title} (${c.document_count} سند | ${c.chunk_count} قطعه وکتور)`;
            chatSelect.appendChild(opt);
        });
        if (prev && knowledgeCollections.some(c => c.id === prev)) {
            chatSelect.value = prev;
        } else if (selectedChatKnowledgeId) {
            chatSelect.value = selectedChatKnowledgeId;
        }
        onChatKnowledgeChange();
    }

    // 2. دراپ‌داون در تب سرچ معنایی
    const searchSelect = document.getElementById("kb-search-col-select");
    if (searchSelect) {
        searchSelect.innerHTML = "";
        knowledgeCollections.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.innerText = `${c.icon || '📚'} ${c.title}`;
            searchSelect.appendChild(opt);
        });
    }
}

function openCreateCollectionModal() {
    document.getElementById("kb-new-col-title").value = "";
    document.getElementById("kb-new-col-desc").value = "";
    document.getElementById("kb-create-modal").style.display = "flex";
}

function closeCreateCollectionModal() {
    document.getElementById("kb-create-modal").style.display = "none";
}

async function submitCreateCollection() {
    const title = document.getElementById("kb-new-col-title").value.trim();
    const desc = document.getElementById("kb-new-col-desc").value.trim();
    const icon = document.getElementById("kb-new-col-icon").value;

    if (!title) {
        alert("لطفاً عنوان پایگاه دانش را وارد فرمایید.");
        return;
    }

    try {
        const res = await fetch("/api/knowledge/collections", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, description: desc, icon })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            closeCreateCollectionModal();
            await loadKnowledgeCollections();
            selectKnowledgeCollection(data.collection.id);
        } else {
            alert(data.detail || "خطا در ساخت مجموعه.");
        }
    } catch (e) {
        alert("خطا در برقراری ارتباط با سرور.");
    }
}

async function selectKnowledgeCollection(colId) {
    activeCollectionId = colId;
    const col = knowledgeCollections.find(c => c.id === colId);
    if (!col) return;

    const detailBox = document.getElementById("kb-active-collection-details");
    if (detailBox) detailBox.style.display = "block";

    document.getElementById("kb-active-col-icon").innerText = col.icon || "📚";
    document.getElementById("kb-active-col-title").innerText = col.title;
    document.getElementById("kb-active-col-desc").innerText = col.description || "بدون توضیحات";

    detailBox.scrollIntoView({ behavior: "smooth" });
    await loadCollectionDocuments(colId);
}

async function loadCollectionDocuments(colId) {
    const container = document.getElementById("kb-documents-list-container");
    if (!container) return;
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 16px;">⏳ در حال بارگذاری اسناد...</div>`;

    try {
        const res = await fetch(`/api/knowledge/collections/${colId}/documents`);
        const data = await res.json();
        const docs = data.documents || [];

        if (docs.length === 0) {
            container.innerHTML = `
                <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--card-border); border-radius: 10px; padding: 18px; text-align: center; color: var(--text-muted); font-size: 0.88rem;">
                    هیچ سندی در این مجموعه وجود ندارد. لطفاً فایلی بارگذاری کرده یا متنی درج فرمایید.
                </div>
            `;
            return;
        }

        container.innerHTML = "";
        docs.forEach(doc => {
            const row = document.createElement("div");
            row.style.cssText = "display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); border: 1px solid var(--card-border); border-radius: 10px; padding: 12px 16px; margin-bottom: 8px; flex-wrap: wrap; gap: 10px;";
            row.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.3rem;">📄</span>
                    <div>
                        <div style="font-weight: 700; font-size: 0.92rem; color: var(--text-primary);">${doc.title}</div>
                        <div style="font-size: 0.78rem; color: var(--text-muted);">
                            <span>قطعات وکتور: <b>${doc.chunk_count}</b></span> • 
                            <span>کاراکترها: <b>${doc.char_count.toLocaleString()}</b></span> • 
                            <span>تاریخ: ${doc.created_at}</span>
                        </div>
                    </div>
                </div>
                <div>
                    <button class="btn btn-sm btn-danger" onclick="deleteKnowledgeDocument('${doc.id}')">🗑️ حذف</button>
                </div>
            `;
            container.appendChild(row);
        });
    } catch (e) {
        container.innerHTML = `<div style="color: #f87171;">خطا در بارگذاری اسناد.</div>`;
    }
}

async function uploadKnowledgeFile(e) {
    const file = e.target.files[0];
    if (!file || !activeCollectionId) return;

    const spinner = document.getElementById("kb-upload-spinner");
    if (spinner) spinner.style.display = "block";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(`/api/knowledge/collections/${activeCollectionId}/upload`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert(`✅ سند «${file.name}» با موفقیت تقطیع شد و ${data.document.chunk_count} قطعه امبدینگ ساخته شد.`);
            document.getElementById("kb-upload-file-input").value = "";
            await loadCollectionDocuments(activeCollectionId);
            await loadKnowledgeCollections();
        } else {
            alert(data.detail || "خطا در پردازش فایل.");
        }
    } catch (err) {
        alert("خطا در بارگذاری سند.");
    } finally {
        if (spinner) spinner.style.display = "none";
    }
}

async function submitKnowledgeDocText() {
    const titleInput = document.getElementById("kb-new-doc-title");
    const contentInput = document.getElementById("kb-new-doc-content");
    const title = titleInput.value.trim();
    const content = contentInput.value.trim();

    if (!title || !content || !activeCollectionId) {
        alert("لطفاً عنوان و محتوای متن را تکمیل فرمایید.");
        return;
    }

    try {
        const res = await fetch(`/api/knowledge/collections/${activeCollectionId}/documents`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, content })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            titleInput.value = "";
            contentInput.value = "";
            alert(`✅ یادداشت با موفقیت ثبت شد و ${data.document.chunk_count} قطعه وکتور تولید گردید.`);
            await loadCollectionDocuments(activeCollectionId);
            await loadKnowledgeCollections();
        } else {
            alert(data.detail || "خطا در ثبت سند.");
        }
    } catch (e) {
        alert("خطا در ذخیره سند متنی.");
    }
}

async function deleteKnowledgeDocument(docId) {
    if (!confirm("آیا از حذف این سند و وکتورهای مربوطه اطمینان دارید؟")) return;
    try {
        const res = await fetch(`/api/knowledge/documents/${docId}`, { method: "DELETE" });
        if (res.ok) {
            await loadCollectionDocuments(activeCollectionId);
            await loadKnowledgeCollections();
        }
    } catch (e) {
        alert("خطا در حذف سند.");
    }
}

async function deleteActiveCollection() {
    if (!activeCollectionId) return;
    if (!confirm("آیا از حذف کل این پایگاه دانش و تمام اسناد و قطعات آن اطمینان دارید؟")) return;

    try {
        const res = await fetch(`/api/knowledge/collections/${activeCollectionId}`, { method: "DELETE" });
        if (res.ok) {
            document.getElementById("kb-active-collection-details").style.display = "none";
            activeCollectionId = null;
            if (selectedChatKnowledgeId === activeCollectionId) {
                selectedChatKnowledgeId = "";
            }
            await loadKnowledgeCollections();
        }
    } catch (e) {
        alert("خطا در حذف مجموعه.");
    }
}

function chatWithActiveCollection() {
    if (!activeCollectionId) return;
    selectedChatKnowledgeId = activeCollectionId;
    const chatSelect = document.getElementById("chat-knowledge-select");
    if (chatSelect) {
        chatSelect.value = activeCollectionId;
    }
    onChatKnowledgeChange();
    switchNav("chat");
}

function onChatKnowledgeChange() {
    const sel = document.getElementById("chat-knowledge-select");
    const status = document.getElementById("chat-knowledge-status");
    if (!sel || !status) return;

    selectedChatKnowledgeId = sel.value;
    if (selectedChatKnowledgeId) {
        const col = knowledgeCollections.find(c => c.id === selectedChatKnowledgeId);
        const name = col ? col.title : "پایگاه دانش";
        status.innerHTML = `<span style="color:var(--neon-emerald); font-weight:700;">🟢 RAG فعال: استناد به «${name}»</span>`;
    } else {
        status.innerHTML = `<span>حالت چت بدون استناد اسناد</span>`;
    }
}

function switchKnowledgeTab(tab) {
    const colView = document.getElementById("kb-view-collections");
    const searchView = document.getElementById("kb-view-search");
    const colBtn = document.getElementById("kb-tab-collections-btn");
    const searchBtn = document.getElementById("kb-tab-search-btn");

    if (tab === "collections") {
        colView.style.display = "block";
        searchView.style.display = "none";
        colBtn.classList.add("active");
        searchBtn.classList.remove("active");
    } else {
        colView.style.display = "none";
        searchView.style.display = "block";
        colBtn.classList.remove("active");
        searchBtn.classList.add("active");
    }
}

async function executeKnowledgeSearch() {
    const colSelect = document.getElementById("kb-search-col-select");
    const qInput = document.getElementById("kb-search-query-input");
    const container = document.getElementById("kb-search-results-container");

    const colId = colSelect ? colSelect.value : null;
    const q = qInput ? qInput.value.trim() : "";

    if (!colId) {
        alert("لطفاً یک پایگاه دانش انتخاب فرمایید.");
        return;
    }
    if (!q) {
        alert("لطفاً عبارت جستجو را وارد فرمایید.");
        return;
    }

    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 18px;">⏳ در حال محاسبه بردار و جستجوی تشابه کسینوسی...</div>`;

    try {
        const res = await fetch("/api/knowledge/search", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ collection_id: colId, query: q, top_k: 5 })
        });
        const data = await res.json();
        const results = data.results || [];

        if (results.length === 0) {
            container.innerHTML = `<div class="glass-card" style="text-align:center; color:var(--text-muted);">تطابق معنایی مناسبی یافت نشد.</div>`;
            return;
        }

        container.innerHTML = "";
        results.forEach((hit, idx) => {
            const card = document.createElement("div");
            card.className = "glass-card";
            card.style.marginBottom = "14px";
            const percent = Math.round(hit.score * 100);
            const scoreColor = percent > 50 ? "#34d399" : (percent > 25 ? "#60a5fa" : "#fbbf24");

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div style="font-weight:700; color:var(--text-primary); font-size:0.95rem;">
                        📄 [نتیجه ${idx + 1}] سند: ${hit.title}
                    </div>
                    <span style="background:rgba(255,255,255,0.05); color:${scoreColor}; border:1px solid ${scoreColor}; padding:3px 10px; border-radius:12px; font-size:0.8rem; font-weight:700;">
                        تطابق: ${percent}%
                    </span>
                </div>
                <div style="background:rgba(0,0,0,0.2); border-radius:8px; padding:12px; font-size:0.88rem; line-height:1.7; color:var(--text-secondary); white-space:pre-wrap;">${hit.text}</div>
            `;
            container.appendChild(card);
        });
    } catch (e) {
        container.innerHTML = `<div style="color:#f87171;">خطا در جستجوی معنایی.</div>`;
    }
}


// ==========================================
// 9. کاوشگر جامع مدل‌های هوش مصنوعی (۴۵۵ مدل)
// ==========================================
let explorerVendorFilter = "all";

function loadExplorerModels() {
    renderExplorerGrid();
}

function setExplorerVendor(vendor, btn) {
    explorerVendorFilter = vendor;
    document.querySelectorAll("#explorer-vendor-chips .chip-btn").forEach(b => b.classList.remove("active"));
    if (btn) btn.classList.add("active");
    renderExplorerGrid();
}

function filterExplorerModels() {
    renderExplorerGrid();
}

function renderExplorerGrid() {
    const grid = document.getElementById("explorer-models-grid");
    const countLabel = document.getElementById("explorer-count-label");
    const searchVal = (document.getElementById("explorer-search-input")?.value || "").trim().toLowerCase();
    const sortVal = document.getElementById("explorer-sort-select")?.value || "name";

    if (!grid) return;

    let models = [...activeProviderModels];

    // ۱. فیلتر کمپانی و برند
    if (explorerVendorFilter !== "all") {
        if (explorerVendorFilter === "free") {
            models = models.filter(m => m.is_free || m.category === "free" || (m.input_price === 0 && m.output_price === 0));
        } else {
            models = models.filter(m => {
                const vid = (m.id || "").toLowerCase();
                const vname = (m.name || "").toLowerCase();
                const vvendor = (m.vendor || "").toLowerCase();
                return vid.includes(explorerVendorFilter) || vname.includes(explorerVendorFilter) || vvendor.includes(explorerVendorFilter);
            });
        }
    }

    // ۲. فیلتر متن جستجو
    if (searchVal) {
        models = models.filter(m => 
            (m.id && m.id.toLowerCase().includes(searchVal)) ||
            (m.name && m.name.toLowerCase().includes(searchVal)) ||
            (m.description && m.description.toLowerCase().includes(searchVal)) ||
            (m.vendor && m.vendor.toLowerCase().includes(searchVal))
        );
    }

    // ۳. مرتب‌سازی
    if (sortVal === "price_asc") {
        models.sort((a, b) => (a.output_price_toman || 0) - (b.output_price_toman || 0));
    } else if (sortVal === "price_desc") {
        models.sort((a, b) => (b.output_price_toman || 0) - (a.output_price_toman || 0));
    } else if (sortVal === "context_desc") {
        const parseCtx = (c) => {
            if (!c) return 0;
            const str = String(c).toUpperCase();
            if (str.includes("M")) return parseFloat(str) * 1000;
            if (str.includes("K")) return parseFloat(str);
            return parseFloat(str) || 0;
        };
        models.sort((a, b) => parseCtx(b.context) - parseCtx(a.context));
    } else {
        models.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
    }

    if (countLabel) {
        countLabel.innerText = `نمایش ${models.length.toLocaleString("fa-IR")} مدل از کل ${activeProviderModels.length.toLocaleString("fa-IR")} مدل موجود در سامانه`;
    }

    grid.innerHTML = "";

    if (models.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
                <div style="font-size: 2.5rem; margin-bottom: 8px;">🔍</div>
                <h4>مدلی با این مشخصات یافت نشد</h4>
                <p style="font-size: 0.88rem;">عبارت جستجو یا فیلتر برند را تغییر دهید.</p>
            </div>
        `;
        return;
    }

    const frag = document.createDocumentFragment();
    models.forEach(m => {
        const card = document.createElement("div");
        card.className = "glass-card model-card";
        const isFree = m.is_free || (m.input_price === 0 && m.output_price === 0);

        let vendorBadge = `<span style="background:rgba(99,102,241,0.15); color:#a5b4fc; padding:2px 8px; border-radius:6px; font-size:0.75rem;">${m.vendor || 'AI'}</span>`;
        if (isFree) {
            vendorBadge = `<span style="background:rgba(16,185,129,0.15); color:#34d399; padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:700;">🎁 رایگان</span>`;
        }

        const inT = m.input_price_toman ? `${m.input_price_toman.toLocaleString()}ت` : 'رایگان';
        const outT = m.output_price_toman ? `${m.output_price_toman.toLocaleString()}ت` : 'رایگان';

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                <div style="font-weight:800; font-size:1.02rem; color:var(--text-primary); line-height:1.4;">${m.name}</div>
                ${vendorBadge}
            </div>
            <div style="font-family:monospace; font-size:0.76rem; color:var(--text-muted); margin-bottom:10px; word-break:break-all;">${m.id}</div>
            
            <p style="font-size:0.83rem; color:var(--text-secondary); line-height:1.5; margin-bottom:14px; min-height:42px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">
                ${m.description || 'مدل هوشمند برای پردازش، درک متن و تولید محتوا.'}
            </p>

            <div style="background:rgba(0,0,0,0.18); border-radius:8px; padding:8px 12px; margin-bottom:14px; font-size:0.8rem; display:flex; justify-content:space-between;">
                <div>
                    <span style="color:var(--text-muted);">کانتکست:</span>
                    <b style="color:var(--neon-cyan);">${m.context || '128K'}</b>
                </div>
                <div>
                    <span style="color:var(--text-muted);">تعرفه ۱M توکن:</span>
                    <b style="color:#34d399;">${inT} / ${outT}</b>
                </div>
            </div>

            <button class="btn btn-secondary btn-sm" style="width:100%; justify-content:center; font-weight:600;" onclick="selectModelForChat('${m.id}')">
                💬 انتخاب برای گفتگو در چت
            </button>
        `;
        frag.appendChild(card);
    });

    grid.appendChild(frag);
}

function selectModelForChat(modelId) {
    const chatSelect = document.getElementById("chat-model-select");
    if (chatSelect) {
        let exists = false;
        for (let i = 0; i < chatSelect.options.length; i++) {
            if (chatSelect.options[i].value === modelId) {
                exists = true;
                break;
            }
        }
        if (!exists) {
            const m = activeProviderModels.find(item => item.id === modelId);
            const opt = document.createElement("option");
            opt.value = modelId;
            opt.innerText = m ? `${m.name} [انتخاب مستقیم]` : modelId;
            chatSelect.appendChild(opt);
        }
        chatSelect.value = modelId;
        onChatModelChange();
    }
    switchNav("chat");
}
