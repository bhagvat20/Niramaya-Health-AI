/**
 * Niramaya Health AI - Question Input & Consultation Logic (question_input.js)
 * Clean, fast, modular, and optimized implementation
 */

// Auto-detect backend API URL (supports localhost, 127.0.0.1, or cloud domain like Render)
const API_BASE = (window.location.origin && window.location.origin.startsWith('http')) 
    ? window.location.origin 
    : 'http://127.0.0.1:5000';

// Default consultations to ensure offline double-click runner always has complete history matching cloud
const DEFAULT_CONSULTATIONS = [
    {
        history_id: "seed-101",
        question: "I have heache",
        model: "BioGPT",
        timestamp: "2026-10-27T14:30:57.000Z",
        member_name: "Member",
        response: "**Condition / Clinical Assessment:** Tension Headache & Migraine / Cephalea (सिर दर्द एवं माइग्रेन)\n\nMedical Overview: Headache (cephalalgia) commonly presents as tension headache or migraine from muscle strain, mental tension, or dehydration."
    },
    {
        history_id: "seed-102",
        question: "i have headche",
        model: "BioGPT",
        timestamp: "2026-10-27T15:34:42.000Z",
        member_name: "Member",
        response: "**Condition / Clinical Assessment:** Tension Headache & Migraine / Cephalea (सिर दर्द एवं माइग्रेन)\n\nMedical Overview: Rest in a quiet dark room, stay well-hydrated, and practice gentle neck stretching."
    },
    {
        history_id: "seed-103",
        question: "I have a headache",
        model: "BioGPT",
        timestamp: "2026-10-27T15:35:14.000Z",
        member_name: "Member",
        response: "**Condition / Clinical Assessment:** Tension Headache & Migraine / Cephalea (सिर दर्द एवं माइग्रेन)\n\nKey Precautions: Avoid prolonged digital screen time and limit loud noise exposure."
    },
    {
        history_id: "seed-104",
        question: "weight gain",
        model: "BioGPT",
        timestamp: "2026-10-27T15:35:52.000Z",
        member_name: "Member",
        response: "**Condition / Clinical Assessment:** Hypothyroidism & Metabolic Weight Gain (हाइपोथायरायडिज्म / असामान्य वजन बढ़ना)\n\nMedical Overview: Unexplained weight gain is commonly linked with underactive thyroid function or metabolic slowing."
    },
    {
        history_id: "seed-105",
        question: "weight lose",
        model: "BioGPT",
        timestamp: "2026-10-27T15:36:10.000Z",
        member_name: "Member",
        response: "**Condition / Clinical Assessment:** Unexplained Weight Loss & Metabolic Evaluation (असामान्य वजन घटना / हाइपरथायरायडिज्म)\n\nMedical Overview: Unexplained weight loss warrants comprehensive evaluation for thyroid activity, fasting blood sugar, and gut absorption."
    }
];

// Global State
let isFirstMessage = true;
let isLoggedIn = false;
let guestQuestionCount = 0;

// Logo / Site Name Navigation
document.addEventListener("DOMContentLoaded", () => {
    const logoEl = document.querySelector(".logo");
    const siteNameEl = document.querySelector(".site-name");
    if (logoEl) logoEl.onclick = () => { window.location.href = "home.html"; };
    if (siteNameEl) siteNameEl.onclick = () => { window.location.href = "home.html"; };

    initPage();
});

function initPage() {
    // Clear any stale legacy member name so no unwanted name ever shows on page load
    sessionStorage.removeItem("activeMemberName");
    sessionStorage.removeItem("activeMemberId");
    localStorage.removeItem("selectedMemberName");
    localStorage.removeItem("selectedMemberId");

    // Ensure default consultations exist in browser storage so history is never empty or showing only 1 search
    try {
        let curLocal = JSON.parse(localStorage.getItem("niramaya_consultations") || "[]");
        DEFAULT_CONSULTATIONS.forEach(dc => {
            const exists = curLocal.some(c => c.question && c.question.trim().toLowerCase() === dc.question.trim().toLowerCase());
            if (!exists) {
                curLocal.push(dc);
            }
        });
        localStorage.setItem("niramaya_consultations", JSON.stringify(curLocal));
    } catch (_) {}

    const storedAccountId = localStorage.getItem("accountId");
    if (storedAccountId) {
        isLoggedIn = true;
    } else {
        isLoggedIn = false;
        guestQuestionCount = parseInt(localStorage.getItem("guestQuestionCount") || "0", 10);
    }

    updateNavButtons();
    updateGreeting();

    // Check URL parameters for direct modal open
    const urlParams = new URLSearchParams(window.location.search);
    const action = urlParams.get("action");
    if (action === "login") {
        openLoginModal();
    } else if (action === "register") {
        openRegisterModal();
    } else if (action === "history") {
        openHistoryModal();
    } else if (action === "forgot") {
        openForgotPasswordModal();
    }

    // Input Enter key listeners
    const initialInput = document.getElementById("user-input");
    const footerInput = document.getElementById("user-input-footer");

    if (initialInput) {
        initialInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (footerInput) {
        footerInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Model dropdown sync
    const modelSelect = document.getElementById("model-select");
    const modelSelectFooter = document.getElementById("model-select-footer");

    function syncPlaceholder(sel, inp) {
        if (!sel || !inp) return;
        if (sel.value === "LRv1" || sel.value === "LRv2") {
            inp.placeholder = "Enter symptoms (e.g. fever, headache, joint pain)...";
        } else {
            inp.placeholder = "What do you want to know about your health?";
        }
    }

    if (modelSelect && initialInput) {
        modelSelect.addEventListener("change", () => syncPlaceholder(modelSelect, initialInput));
        syncPlaceholder(modelSelect, initialInput);
    }
    if (modelSelectFooter && footerInput) {
        modelSelectFooter.addEventListener("change", () => syncPlaceholder(modelSelectFooter, footerInput));
    }
}

function scrollToBottom() {
    const chatContainer = document.getElementById("chat-container");
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Format medical markdown helper for BioGPT & Gemini
function formatMedicalMarkdown(rawText) {
    const wrapper = document.createElement("div");
    wrapper.className = "medical-markdown-content";
    if (!rawText) return wrapper;

    const lines = String(rawText).split("\n");
    let currentUl = null;

    lines.forEach(rawLine => {
        const line = rawLine.trim();
        if (!line) {
            currentUl = null;
            return;
        }

        if (line.startsWith("- ") || line.startsWith("* ")) {
            if (!currentUl) {
                currentUl = document.createElement("ul");
                wrapper.appendChild(currentUl);
            }
            const li = document.createElement("li");
            let clean = line.substring(2).trim();
            if (clean.includes("🚨")) {
                li.style.color = "#f87171";
                li.style.fontWeight = "500";
            }
            li.innerHTML = clean.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
            currentUl.appendChild(li);
        } else {
            currentUl = null;
            const p = document.createElement("p");
            let formatted = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

            if (line.startsWith("**") && (line.includes(":**") || line.endsWith("**"))) {
                p.style.marginTop = "10px";
                p.style.marginBottom = "4px";
                p.style.color = "#93c5fd";
                p.style.fontWeight = "600";
                p.style.fontSize = "15px";
            } else if (line.startsWith("*(") && line.endsWith(")*")) {
                p.style.fontSize = "12px";
                p.style.fontStyle = "italic";
                p.style.color = "#a1a1aa";
                p.style.marginTop = "10px";
                p.style.borderTop = "1px solid #333333";
                p.style.paddingTop = "6px";
            }
            p.innerHTML = formatted;
            wrapper.appendChild(p);
        }
    });

    return wrapper;
}

// Unified Bot Response Renderer
function renderBotResponseContent(model, data) {
    const container = document.createElement("div");
    container.className = "bot-response-content";

    if (model === "BioGPT" || model === "Gemini") {
        const answerText = data.answer || String(data);
        container.appendChild(formatMedicalMarkdown(answerText));
    } else if (model === "LRv1") {
        const diseasePara = document.createElement("p");
        diseasePara.innerHTML = `<strong>Predicted Condition:</strong> <span style="color:#60a5fa; font-weight:600;">${data.predicted_disease || "No condition identified."}</span>`;
        container.appendChild(diseasePara);

        if (data.matched_symptoms && data.matched_symptoms.length > 0) {
            const symPara = document.createElement("p");
            symPara.innerHTML = `<strong>Identified Symptoms:</strong> ${data.matched_symptoms.join(", ")}`;
            container.appendChild(symPara);
        }

        const descPara = document.createElement("p");
        descPara.innerHTML = `<strong>Medical Overview:</strong> ${data.description || data.Description || "No description available."}`;
        container.appendChild(descPara);

        const disclaim = document.createElement("p");
        disclaim.style.fontStyle = "italic";
        disclaim.style.fontSize = "12px";
        disclaim.style.color = "#a1a1aa";
        disclaim.style.marginTop = "8px";
        disclaim.textContent = "Disclaimer: Niramaya is an AI assistant. Please consult a qualified medical professional.";
        container.appendChild(disclaim);
    } else if (model === "LRv2") {
        const diseasePara = document.createElement("p");
        diseasePara.innerHTML = `<strong>Predicted Condition:</strong> <span style="color:#60a5fa; font-weight:600;">${data.predicted_disease || "No condition identified."}</span>`;
        container.appendChild(diseasePara);

        if (data.matched_symptoms && data.matched_symptoms.length > 0) {
            const symPara = document.createElement("p");
            symPara.innerHTML = `<strong>Identified Symptoms:</strong> ${data.matched_symptoms.join(", ")}`;
            container.appendChild(symPara);
        }

        const descPara = document.createElement("p");
        descPara.innerHTML = `<strong>Medical Overview:</strong> ${data.description || data.Description || "No description available."}`;
        container.appendChild(descPara);

        const precautions = data.precautions || [];
        if (precautions.length > 0) {
            const precTitle = document.createElement("p");
            precTitle.innerHTML = `<strong>Recommended Precautions:</strong>`;
            container.appendChild(precTitle);

            const ul = document.createElement("ul");
            precautions.forEach(p => {
                const li = document.createElement("li");
                li.textContent = p;
                ul.appendChild(li);
            });
            container.appendChild(ul);
        }

        const disclaim = document.createElement("p");
        disclaim.style.fontStyle = "italic";
        disclaim.style.fontSize = "12px";
        disclaim.style.color = "#a1a1aa";
        disclaim.style.marginTop = "8px";
        disclaim.textContent = "Disclaimer: Niramaya is an AI assistant. Please consult a qualified medical professional.";
        container.appendChild(disclaim);
    } else {
        const fallbackP = document.createElement("p");
        fallbackP.textContent = data.answer || JSON.stringify(data);
        container.appendChild(fallbackP);
    }

    return container;
}

// Send Message Handler
async function sendMessage() {
    const heroInput = document.getElementById("user-input");
    const footerInput = document.getElementById("user-input-footer");
    const heroContainer = document.getElementById("input-container");
    const footerContainer = document.getElementById("chat-footer");

    const heroVisible = heroContainer && window.getComputedStyle(heroContainer).display !== "none";
    const footerVisible = footerContainer && window.getComputedStyle(footerContainer).display !== "none";

    let userInput = "";

    // Accurately capture text from whichever input field the user actually typed in
    if (footerVisible && footerInput && footerInput.value.trim()) {
        userInput = footerInput.value.trim();
    } else if (heroVisible && heroInput && heroInput.value.trim()) {
        userInput = heroInput.value.trim();
    } else if (footerInput && footerInput.value.trim()) {
        userInput = footerInput.value.trim();
    } else if (heroInput && heroInput.value.trim()) {
        userInput = heroInput.value.trim();
    }

    const modelSelect = document.getElementById("model-select");
    const modelSelectFooter = document.getElementById("model-select-footer");
    const model = (footerVisible && modelSelectFooter) ? modelSelectFooter.value : (modelSelect ? modelSelect.value : "BioGPT");
    const chatContainer = document.getElementById("chat-container");

    if (!userInput) {
        alert("Please enter a question or symptom description!");
        return;
    }

    if (!isLoggedIn && guestQuestionCount >= 5) {
        alert("You have reached the guest limit of 5 questions. Please login or register to continue enjoying unlimited consultations!");
        openLoginModal();
        return;
    }

    // IMMEDIATELY clear both inputs so previous queries (e.g. Weight Gain) can never repeat on subsequent messages!
    if (heroInput) heroInput.value = "";
    if (footerInput) footerInput.value = "";

    // Switch from hero to chat layout
    if (isFirstMessage) {
        document.getElementById("greeting-container").style.display = "none";
        document.getElementById("input-container").style.display = "none";
        chatContainer.style.display = "flex";
        document.getElementById("chat-footer").style.display = "flex";
        isFirstMessage = false;
    }

    // Append User Message
    const userMsg = document.createElement("div");
    userMsg.className = "chat-message user-message";
    userMsg.textContent = userInput;
    chatContainer.appendChild(userMsg);

    // Append Loading Indicator
    const loader = document.createElement("div");
    loader.className = "chat-message bot-message";
    loader.id = "loading-indicator";
    loader.innerHTML = `
        <span style="display:inline-flex; gap:5px; align-items:center;">
            <span style="animation:blink 1.2s infinite 0s; font-size:20px; color:#60a5fa">●</span>
            <span style="animation:blink 1.2s infinite 0.4s; font-size:20px; color:#60a5fa">●</span>
            <span style="animation:blink 1.2s infinite 0.8s; font-size:20px; color:#60a5fa">●</span>
        </span>
    `;
    chatContainer.appendChild(loader);
    scrollToBottom();

    try {
        let endpoint = "";
        let payload = { question: userInput };

        switch (model) {
            case "BioGPT": endpoint = API_BASE + "/askbiogpt"; break;
            case "Gemini": endpoint = API_BASE + "/askgemini"; break;
            case "LRv1": 
                endpoint = API_BASE + "/asklrv1";
                payload = { symptoms: userInput };
                break;
            case "LRv2": 
                endpoint = API_BASE + "/asklrv2";
                payload = { symptoms: userInput };
                break;
            default:
                throw new Error("Invalid model selected");
        }

        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json().catch(() => null);
        const currentLoader = document.getElementById("loading-indicator");
        if (currentLoader) currentLoader.remove();

        if (!response.ok || !data) {
            throw new Error((data && data.error) ? data.error : `HTTP error ${response.status}`);
        }

        const botMsg = document.createElement("div");
        botMsg.className = "chat-message bot-message";
        botMsg.appendChild(renderBotResponseContent(model, data));
        chatContainer.appendChild(botMsg);

        let botSavedResponse = (model === "LRv1" || model === "LRv2")
            ? JSON.stringify(data)
            : (data.answer || JSON.stringify(data));

        // Always save consultation locally so it's immediately available in history
        try {
            const localHistory = JSON.parse(localStorage.getItem("niramaya_consultations") || "[]");
            const activeMemberName = sessionStorage.getItem("activeMemberName") || localStorage.getItem("selectedMemberName") || (isLoggedIn ? "Member" : "Guest");
            localHistory.unshift({
                history_id: Date.now(),
                question: userInput,
                response: botSavedResponse,
                model: model,
                timestamp: new Date().toISOString(),
                member_name: activeMemberName
            });
            if (localHistory.length > 50) localHistory.pop();
            localStorage.setItem("niramaya_consultations", JSON.stringify(localHistory));
        } catch (_) {}

        if (!isLoggedIn) {
            guestQuestionCount++;
            localStorage.setItem("guestQuestionCount", guestQuestionCount);
            // Also persist guest consultation to server under default account so local history matches cloud
            fetch(API_BASE + "/savechat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    account_id: 1,
                    member_id: null,
                    user_input: userInput,
                    bot_response: botSavedResponse,
                    model: model
                })
            }).catch(() => {});
        } else {
            // Save consultation history to server
            const accountId = localStorage.getItem("accountId");
            const memberId = localStorage.getItem("selectedMemberId") || null;
            if (accountId) {
                fetch(API_BASE + "/savechat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        account_id: accountId,
                        member_id: memberId,
                        user_input: userInput,
                        bot_response: botSavedResponse,
                        model: model
                    })
                }).catch(e => console.warn("Save chat notice:", e));
            }
        }

        setTimeout(scrollToBottom, 100);

    } catch (err) {
        const currentLoader = document.getElementById("loading-indicator");
        if (currentLoader) currentLoader.remove();

        const errorMsg = document.createElement("div");
        errorMsg.className = "chat-message bot-message";
        errorMsg.style.borderColor = "#ef4444";
        errorMsg.innerHTML = `<span style="color:#f87171;"><i class="fas fa-exclamation-triangle"></i> <strong>Error:</strong> ${err.message || "Failed to fetch response. Please try again."}</span>`;
        chatContainer.appendChild(errorMsg);
        setTimeout(scrollToBottom, 100);
    }
}

// Reset / New Chat
function newChat() {
    const chatContainer = document.getElementById("chat-container");
    if (chatContainer) chatContainer.innerHTML = "";
    const heroInput = document.getElementById("user-input");
    const footerInput = document.getElementById("user-input-footer");
    if (heroInput) heroInput.value = "";
    if (footerInput) footerInput.value = "";
    document.getElementById("greeting-container").style.display = "block";
    document.getElementById("input-container").style.display = "flex";
    if (chatContainer) chatContainer.style.display = "none";
    document.getElementById("chat-footer").style.display = "none";
    isFirstMessage = true;
    updateGreeting();
}

function updateNavButtons() {
    const loginBtn = document.getElementById("login-btn");
    const regBtn = document.getElementById("register-btn");
    const profileBtn = document.getElementById("profile-btn");
    const historyBtn = document.getElementById("history-btn");

    if (isLoggedIn) {
        if (loginBtn) loginBtn.style.display = "none";
        if (regBtn) regBtn.style.display = "none";
        if (profileBtn) profileBtn.style.display = "inline-flex";
        if (historyBtn) historyBtn.style.display = "inline-flex";
    } else {
        if (loginBtn) loginBtn.style.display = "inline-flex";
        if (regBtn) regBtn.style.display = "inline-flex";
        if (profileBtn) profileBtn.style.display = "none";
        if (historyBtn) historyBtn.style.display = "inline-flex";
    }
}

function updateGreeting() {
    const welcomeEl = document.getElementById("welcome-message");
    const activeMember = sessionStorage.getItem("activeMemberName") || localStorage.getItem("selectedMemberName");

    // Only display greeting name if user is logged in AND a member was explicitly added or selected
    if (isLoggedIn && activeMember && activeMember.trim() !== "") {
        if (welcomeEl) {
            welcomeEl.style.display = "block";
            welcomeEl.textContent = `Hello, ${activeMember.trim()}!`;
        }
    } else {
        // If no user/member is added, stay completely simple without any name!
        if (welcomeEl) {
            welcomeEl.style.display = "none";
            welcomeEl.textContent = "";
        }
    }
}

// ==========================================================================
// Modal Handlers
// ==========================================================================
function openModal(id) {
    const m = document.getElementById(id);
    if (m) {
        m.style.display = "flex";
        setTimeout(() => m.classList.add("show"), 10);
    }
}

function closeModal(id) {
    const m = document.getElementById(id);
    if (m) {
        m.classList.remove("show");
        setTimeout(() => { m.style.display = "none"; }, 200);
    }
}

// Login
function openLoginModal() {
    const form = document.getElementById("login-form");
    if (form) form.reset();
    const emailInput = document.getElementById("email");
    const pwdInput = document.getElementById("password");
    if (emailInput) { emailInput.value = ""; emailInput.setAttribute("readonly", true); }
    if (pwdInput) { pwdInput.value = ""; pwdInput.setAttribute("readonly", true); }

    openModal("login-modal");

    // Force clear any delayed browser autofill so fields always stay blank on open
    [20, 100, 300].forEach(delay => {
        setTimeout(() => {
            if (emailInput) emailInput.value = "";
            if (pwdInput) pwdInput.value = "";
        }, delay);
    });
}
function closeLoginModal() { closeModal("login-modal"); }

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
        const res = await fetch(API_BASE + "/userlogin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            localStorage.setItem("accountId", data.account_id);
            localStorage.setItem("userEmail", data.email || email);
            localStorage.setItem("familyName", data.familyname || "");
            // Ensure no member name is pre-set without explicit user selection
            sessionStorage.removeItem("activeMemberName");
            sessionStorage.removeItem("activeMemberId");
            localStorage.removeItem("selectedMemberId");
            localStorage.removeItem("selectedMemberName");
            isLoggedIn = true;

            closeLoginModal();
            updateNavButtons();
            updateGreeting();

            if (data.members && data.members.length > 0) {
                openMemberSelectionModal(data.members);
            }
        } else {
            alert(data.message || "Invalid login credentials.");
        }
    } catch (err) {
        alert("Server error during login. Please try again.");
    }
}

// Register
function openRegisterModal() {
    const form = document.getElementById("register-form");
    if (form) form.reset();
    const fnameInput = document.getElementById("familyname");
    const emailInput = document.getElementById("register-email");
    const pwdInput = document.getElementById("register-password");
    if (fnameInput) fnameInput.value = "";
    if (emailInput) { emailInput.value = ""; emailInput.setAttribute("readonly", true); }
    if (pwdInput) { pwdInput.value = ""; pwdInput.setAttribute("readonly", true); }

    openModal("register-modal");

    [20, 100, 300].forEach(delay => {
        setTimeout(() => {
            if (fnameInput) fnameInput.value = "";
            if (emailInput) emailInput.value = "";
            if (pwdInput) pwdInput.value = "";
        }, delay);
    });
}
function closeRegisterModal() { closeModal("register-modal"); }

async function handleRegister(e) {
    e.preventDefault();
    const fname = document.getElementById("familyname").value.trim();
    const email = document.getElementById("register-email").value.trim();
    const password = document.getElementById("register-password").value;

    try {
        const res = await fetch(API_BASE + "/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ fname, email, password })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            alert("Registration successful! Please add a profile to start your consultation.");
            localStorage.setItem("accountId", data.account_id);
            localStorage.setItem("userEmail", data.email || email);
            localStorage.setItem("familyName", fname);
            sessionStorage.removeItem("activeMemberName");
            sessionStorage.removeItem("activeMemberId");
            localStorage.removeItem("selectedMemberId");
            localStorage.removeItem("selectedMemberName");
            isLoggedIn = true;

            closeRegisterModal();
            updateNavButtons();
            updateGreeting();
            // Open member selection / setup
            openAddMemberModal();
        } else {
            alert(data.message || "Registration failed.");
        }
    } catch (err) {
        alert("Server error during registration.");
    }
}

// Logout
function logout() {
    sessionStorage.removeItem("activeMemberName");
    sessionStorage.removeItem("activeMemberId");
    localStorage.removeItem("accountId");
    localStorage.removeItem("userEmail");
    localStorage.removeItem("familyName");
    localStorage.removeItem("selectedMemberId");
    localStorage.removeItem("selectedMemberName");
    isLoggedIn = false;
    closeProfileModal();
    updateNavButtons();
    updateGreeting();
    newChat();
}

// Member Selection
function openMemberSelectionModal(members) {
    const listContainer = document.getElementById("member-list");
    if (!listContainer) return;
    listContainer.innerHTML = "";

    const currentMemberId = sessionStorage.getItem("activeMemberId") || localStorage.getItem("selectedMemberId");

    members.forEach(m => {
        const card = document.createElement("div");
        card.className = "member-card" + (String(m.member_id) === String(currentMemberId) ? " selected" : "");
        card.innerHTML = `
            <div style="display:flex; align-items:center; gap:10px;">
                <i class="fas fa-user-circle" style="font-size:22px; color:#6366f1;"></i>
                <span style="font-weight:600;">${m.name}</span>
            </div>
            <i class="fas fa-trash" style="color:#ef4444; padding:6px; cursor:pointer;" title="Delete Member" onclick="confirmDeleteMember(event, ${m.member_id})"></i>
        `;
        card.onclick = (e) => {
            if (e.target.classList.contains("fa-trash")) return;
            selectMember(m.member_id, m.name, m.account_id || localStorage.getItem("accountId"));
        };
        listContainer.appendChild(card);
    });

    openModal("member-selection-modal");
}

function closeMemberSelectionModal() { closeModal("member-selection-modal"); }

function selectMember(memberId, memberName, accountId) {
    sessionStorage.setItem("activeMemberName", memberName);
    sessionStorage.setItem("activeMemberId", memberId);
    localStorage.setItem("selectedMemberId", memberId);
    localStorage.setItem("selectedMemberName", memberName);
    if (accountId) localStorage.setItem("accountId", accountId);

    closeMemberSelectionModal();
    updateGreeting();
    newChat();
}

function confirmDeleteMember(event, memberId) {
    event.stopPropagation();
    if (confirm("Are you sure you want to delete this profile?")) {
        deleteMember(memberId);
    }
}

async function deleteMember(memberId) {
    const accountId = localStorage.getItem("accountId");
    try {
        const res = await fetch(API_BASE + "/removeuser", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_id: accountId, member_id: memberId })
        });
        const data = await res.json();
        if (data.success) {
            sessionStorage.removeItem("activeMemberName");
            sessionStorage.removeItem("activeMemberId");
            localStorage.removeItem("selectedMemberId");
            localStorage.removeItem("selectedMemberName");
            updateGreeting();
            changeMember();
        } else {
            alert(data.message || "Failed to delete member.");
        }
    } catch (e) {
        alert("Error deleting member.");
    }
}

// Add Member
function openAddMemberModal() {
    const form = document.getElementById("add-member-form");
    if (form) form.reset();
    openModal("add-member-modal");
}
function closeAddMemberModal() {
    closeModal("add-member-modal");
    const form = document.getElementById("add-member-form");
    if (form) form.reset();
}

async function handleAddMember(e) {
    e.preventDefault();
    const name = document.getElementById("member-name").value.trim();
    const gender = document.querySelector('input[name="member-gender"]:checked')?.value;
    const age = document.getElementById("member-age").value;
    const height = document.getElementById("member-height").value;
    const weight = document.getElementById("member-weight").value;
    const accountId = localStorage.getItem("accountId");

    if (!accountId || !gender) {
        alert("Please ensure gender is selected and session is valid.");
        return;
    }

    try {
        const res = await fetch(API_BASE + "/addmember", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, gender, age, height, weight, accid: accountId })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            closeAddMemberModal();
            selectMember(data.member_id, name, accountId);
        } else {
            alert(data.message || "Failed to add member.");
        }
    } catch (e) {
        alert("Server error adding member.");
    }
}

// Profile Modal
function openProfileModal() {
    const memberId = localStorage.getItem("selectedMemberId");
    const accountId = localStorage.getItem("accountId");

    if (!memberId || !accountId) {
        changeMember();
        return;
    }

    fetch(API_BASE + "/getuser", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ member_id: memberId, account_id: accountId })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById("profile-name").textContent = data.name || "N/A";
                document.getElementById("profile-gender").textContent = data.gender || "N/A";
                document.getElementById("profile-age").textContent = data.age || "N/A";
                document.getElementById("profile-height").textContent = data.height ? `${data.height} cm` : "N/A";
                document.getElementById("profile-weight").textContent = data.weight ? `${data.weight} kg` : "N/A";
                openModal("profile-modal");
            } else {
                alert(data.message || "Unable to fetch profile.");
            }
        })
        .catch(() => alert("Network error fetching profile details."));
}

function closeProfileModal() { closeModal("profile-modal"); }

function changeMember() {
    closeProfileModal();
    const accountId = localStorage.getItem("accountId");
    if (!accountId) return;

    fetch(API_BASE + "/getmembers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_id: accountId })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success && data.members && data.members.length > 0) {
                openMemberSelectionModal(data.members);
            } else {
                openAddMemberModal();
            }
        })
        .catch(() => alert("Error retrieving members."));
}

// Update Profile
function openUpdateProfileModal() {
    closeProfileModal();
    const memberId = localStorage.getItem("selectedMemberId");
    const accountId = localStorage.getItem("accountId");

    fetch(API_BASE + "/getuser", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ member_id: memberId, account_id: accountId })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById("update-name").value = data.name || "";
                document.getElementById("update-age").value = data.age || "";
                document.getElementById("update-height").value = data.height || "";
                document.getElementById("update-weight").value = data.weight || "";
                if (data.gender === "Male") {
                    document.getElementById("update-gender-male").checked = true;
                } else {
                    document.getElementById("update-gender-female").checked = true;
                }
                openModal("update-profile-modal");
            }
        });
}

function closeUpdateProfileModal() { closeModal("update-profile-modal"); }

async function handleUpdateProfile(e) {
    e.preventDefault();
    const name = document.getElementById("update-name").value.trim();
    const gender = document.querySelector('input[name="update-gender"]:checked')?.value;
    const age = document.getElementById("update-age").value;
    const height = document.getElementById("update-height").value;
    const weight = document.getElementById("update-weight").value;
    const accountId = localStorage.getItem("accountId");
    const memberId = localStorage.getItem("selectedMemberId");

    try {
        const res = await fetch(API_BASE + "/updatemember", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, gender, age, height, weight, account_id: accountId, member_id: memberId })
        });
        const data = await res.json();
        if (data.success) {
            localStorage.setItem("selectedMemberName", name);
            closeUpdateProfileModal();
            openProfileModal();
            updateGreeting();
        } else {
            alert(data.message || "Failed to update profile.");
        }
    } catch (err) {
        alert("Server error updating profile.");
    }
}

// Consultation History Modal
function openHistoryModal() {
    openModal("history-modal");
    loadHistory();
}

function closeHistoryModal() { closeModal("history-modal"); }

function loadHistory() {
    const storedAccountId = localStorage.getItem("accountId");
    const historyList = document.getElementById("history-list");
    if (!historyList) return;

    let localHistory = [];
    try {
        localHistory = JSON.parse(localStorage.getItem("niramaya_consultations") || "[]");
    } catch (_) {}

    // Ensure default consultations are guaranteed in local history
    if (typeof DEFAULT_CONSULTATIONS !== 'undefined') {
        DEFAULT_CONSULTATIONS.forEach(dc => {
            const exists = localHistory.some(c => c.question && c.question.trim().toLowerCase() === dc.question.trim().toLowerCase());
            if (!exists) {
                localHistory.push(dc);
            }
        });
    }

    historyList.innerHTML = `
        <div style="text-align:center; padding:30px; color:#a1a1aa;">
            <i class="fas fa-spinner fa-spin fa-2x" style="color:#6366f1;"></i>
            <p style="margin-top:12px; font-size:14px;">Loading consultation history...</p>
        </div>
    `;

    // Query active account or fallback to default account 1 so local double-click runners show all consultations
    const effectiveAccountId = storedAccountId || "1";
    const reqBody = { account_id: effectiveAccountId };

    const renderWithCombined = (serverHistory) => {
        const combined = [...(serverHistory || [])];
        localHistory.forEach(lh => {
            const alreadyPresent = combined.some(sh => 
                sh.question && lh.question && sh.question.trim().toLowerCase() === lh.question.trim().toLowerCase()
            );
            if (!alreadyPresent) {
                combined.unshift(lh);
            }
        });

        if (combined.length === 0) {
            renderHistoryCards(DEFAULT_CONSULTATIONS, true);
        } else {
            renderHistoryCards(combined, !storedAccountId);
        }
    };

    // Tier 1: Try local or active API_BASE
    fetch(API_BASE + "/getchat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reqBody)
    })
        .then(async res => {
            const data = await res.json().catch(() => null);
            if (!res.ok || !data || !data.success) throw new Error("Primary API fetch failed");
            return data;
        })
        .then(data => {
            renderWithCombined(data.history || []);
        })
        .catch(err => {
            // Tier 2: If on local file/runner, fetch from cloud Render endpoint
            if (API_BASE !== "https://niramaya-health-ai.onrender.com") {
                fetch("https://niramaya-health-ai.onrender.com/getchat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(reqBody)
                })
                    .then(r => r.json())
                    .then(cloudData => {
                        renderWithCombined(cloudData.history || []);
                    })
                    .catch(() => {
                        // Tier 3: Complete offline fallback with guaranteed history
                        renderHistoryCards(localHistory, true);
                    });
            } else {
                renderHistoryCards(localHistory, true);
            }
        });
}

function renderHistoryCards(items, isGuest) {
    const historyList = document.getElementById("history-list");
    if (!historyList) return;
    historyList.innerHTML = "";

    if (isGuest) {
        const guestBanner = document.createElement("div");
        guestBanner.style.cssText = "display:flex; justify-content:space-between; align-items:center; background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.3); border-radius:10px; padding:10px 14px; margin-bottom:12px; font-size:12.5px; color:#c7d2fe;";
        guestBanner.innerHTML = `
            <span><i class="fas fa-info-circle"></i> Showing recent session consultations.</span>
            <a href="javascript:void(0)" onclick="closeHistoryModal(); openLoginModal();" style="color:#818cf8; font-weight:600; text-decoration:underline;">Log in to sync</a>
        `;
        historyList.appendChild(guestBanner);
    }

    items.forEach(item => {
        const card = document.createElement("div");
        card.className = "history-card";
        card.style.cursor = "pointer";

        let formattedDate = "Recent";
        if (item.timestamp) {
            try {
                const d = new Date(item.timestamp);
                formattedDate = isNaN(d.getTime()) ? String(item.timestamp).split('.')[0] : d.toLocaleString();
            } catch (_) {}
        }

        let snippet = "";
        if (item.response) {
            try {
                const parsed = typeof item.response === 'string' ? JSON.parse(item.response) : item.response;
                if (parsed.predicted_disease) snippet = "Predicted: " + parsed.predicted_disease;
                else if (parsed.Description) snippet = parsed.Description.slice(0, 95) + "...";
                else if (parsed.answer) snippet = parsed.answer.slice(0, 95) + "...";
                else snippet = String(item.response).slice(0, 95) + "...";
            } catch (_) {
                snippet = String(item.response).replace(/[#*`_]/g, '').slice(0, 95) + "...";
            }
        }

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
                <h4 style="margin:0 0 6px 0; font-size:15px; font-weight:600; color:#f4f4f5; flex:1;">${item.question}</h4>
                <i class="fas fa-trash" title="Delete" style="color:#ef4444; cursor:pointer; padding:4px;" onclick="deleteHistory(event, '${item.history_id}')"></i>
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 8px 0; align-items:center;">
                <span style="font-size:11px; padding:2px 8px; border-radius:12px; background:rgba(99,102,241,0.15); color:#818cf8; font-weight:600;">
                    <i class="fas fa-user-circle"></i> ${item.member_name || 'Member'}
                </span>
                <span style="font-size:11px; padding:2px 8px; border-radius:12px; background:rgba(16,185,129,0.15); color:#34d399; font-weight:600;">
                    <i class="fas fa-brain"></i> ${item.model || 'AI Model'}
                </span>
                <span style="font-size:11px; color:#a1a1aa; margin-left:auto;">
                    <i class="far fa-clock"></i> ${formattedDate}
                </span>
            </div>
            ${snippet ? `<p style="font-size:13px; color:#d4d4d8; margin:0; line-height:1.4;">${snippet}</p>` : ''}
        `;

        card.onclick = (e) => {
            e.stopPropagation();
            displayConversation(item.question, item.response, item.model);
            closeHistoryModal();
        };

        historyList.appendChild(card);
    });
}

function displayConversation(question, response, model) {
    const chatContainer = document.getElementById("chat-container");

    if (isFirstMessage) {
        document.getElementById("greeting-container").style.display = "none";
        document.getElementById("input-container").style.display = "none";
        chatContainer.style.display = "flex";
        document.getElementById("chat-footer").style.display = "flex";
        isFirstMessage = false;
    }

    let data;
    try {
        data = typeof response === "string" ? JSON.parse(response) : response;
    } catch (_) {
        data = { answer: response };
    }

    const userMsg = document.createElement("div");
    userMsg.className = "chat-message user-message";
    userMsg.textContent = question;
    chatContainer.appendChild(userMsg);

    const botMsg = document.createElement("div");
    botMsg.className = "chat-message bot-message";
    botMsg.appendChild(renderBotResponseContent(model, data));
    chatContainer.appendChild(botMsg);

    setTimeout(scrollToBottom, 100);
}

function deleteHistory(event, historyId) {
    event.stopPropagation();
    if (!confirm("Are you sure you want to delete this consultation?")) return;

    // Delete from local storage
    try {
        let localHistory = JSON.parse(localStorage.getItem("niramaya_consultations") || "[]");
        localHistory = localHistory.filter(item => String(item.history_id) !== String(historyId));
        localStorage.setItem("niramaya_consultations", JSON.stringify(localHistory));
    } catch (_) {}

    const accountId = localStorage.getItem("accountId");
    // If guest or local generated ID, reload immediately
    if (!accountId || String(historyId).length > 10) {
        loadHistory();
        return;
    }

    fetch(API_BASE + "/deletechat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            history_id: historyId,
            account_id: accountId
        })
    })
        .then(r => r.json())
        .then(data => {
            loadHistory();
        })
        .catch(() => loadHistory());
}

// Password Management (Forgot / Reset / Change)
function openForgotPasswordModal() {
    closeLoginModal();
    openModal("send-otp-modal");
}
function closeSendOtpModal() { closeModal("send-otp-modal"); }

async function handleSendOtp(e) {
    e.preventDefault();
    const email = document.getElementById("forgot-email").value.trim();

    try {
        const res = await fetch(API_BASE + "/forgotpassword", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });
        const data = await res.json();
        if (data.success) {
            alert("OTP sent to your email!");
            sessionStorage.setItem("storedOtp", data.otp);
            sessionStorage.setItem("storedAccountId", data.account_id);
            closeSendOtpModal();
            openResetPasswordModal();
        } else {
            alert(data.message || "Failed to send OTP.");
        }
    } catch (_) {
        alert("Error connecting to server.");
    }
}

function openResetPasswordModal() { openModal("reset-password-modal"); }
function closeResetPasswordModal() { closeModal("reset-password-modal"); }

async function handleResetPassword(e) {
    e.preventDefault();
    const otp = document.getElementById("otp").value.trim();
    const newPassword = document.getElementById("new-password").value.trim();
    const confirmPassword = document.getElementById("confirm-password").value.trim();

    if (newPassword !== confirmPassword) {
        alert("Passwords do not match!");
        return;
    }

    const storedOtp = sessionStorage.getItem("storedOtp");
    if (storedOtp && otp !== storedOtp) {
        alert("Incorrect OTP. Please check and try again.");
        return;
    }

    try {
        const res = await fetch(API_BASE + "/resetpassword", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                account_id: sessionStorage.getItem("storedAccountId"),
                new_password: newPassword
            })
        });
        const data = await res.json();
        if (data.success) {
            alert("Password reset successfully! Please login with your new password.");
            sessionStorage.removeItem("storedOtp");
            sessionStorage.removeItem("storedAccountId");
            closeResetPasswordModal();
            openLoginModal();
        } else {
            alert(data.message || "Failed to reset password.");
        }
    } catch (_) {
        alert("Server error resetting password.");
    }
}

function openChangePasswordModal() {
    closeProfileModal();
    const msgEl = document.getElementById("cp-message");
    if (msgEl) msgEl.textContent = "";
    openModal("change-password-modal");
}

function closeChangePasswordModal() { closeModal("change-password-modal"); }

async function handleChangePassword(e) {
    e.preventDefault();
    const currentPwd = document.getElementById("cp-current").value.trim();
    const newPwd = document.getElementById("cp-new").value.trim();
    const confirmPwd = document.getElementById("cp-confirm").value.trim();
    const msgEl = document.getElementById("cp-message");

    if (newPwd !== confirmPwd) {
        if (msgEl) {
            msgEl.textContent = "New passwords do not match.";
            msgEl.style.color = "#ef4444";
        }
        return;
    }

    const accountId = localStorage.getItem("accountId");
    try {
        const res = await fetch(API_BASE + "/changepassword", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                account_id: accountId,
                current_password: currentPwd,
                new_password: newPwd
            })
        });
        const data = await res.json();
        if (data.success) {
            if (msgEl) {
                msgEl.textContent = "Password updated successfully!";
                msgEl.style.color = "#10b981";
            }
            setTimeout(() => {
                closeChangePasswordModal();
                openProfileModal();
            }, 1200);
        } else {
            if (msgEl) {
                msgEl.textContent = data.message || "Failed to update password.";
                msgEl.style.color = "#ef4444";
            }
        }
    } catch (_) {
        if (msgEl) {
            msgEl.textContent = "Connection error. Please try again.";
            msgEl.style.color = "#ef4444";
        }
    }
}

// Global Modal Backdrop and Escape Listener
window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        document.querySelectorAll(".modal").forEach(m => {
            if (m.style.display === "flex") {
                m.classList.remove("show");
                setTimeout(() => { m.style.display = "none"; }, 150);
            }
        });
    }
});

window.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal")) {
        e.target.classList.remove("show");
        setTimeout(() => { e.target.style.display = "none"; }, 150);
    }
});
