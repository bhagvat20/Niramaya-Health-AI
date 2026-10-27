/**
 * Niramaya Health AI - Question Input & Consultation Logic (question_input.js)
 * Clean, fast, modular, and optimized implementation
 */

// Auto-detect backend API URL (supports localhost, 127.0.0.1, or cloud domain like Render)
const API_BASE = (window.location.origin && window.location.origin.startsWith('http')) 
    ? window.location.origin 
    : 'http://127.0.0.1:5000';

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
    const inputField = isFirstMessage
        ? document.getElementById("user-input")
        : document.getElementById("user-input-footer");

    const modelField = isFirstMessage
        ? document.getElementById("model-select")
        : document.getElementById("model-select-footer");

    const userInput = (inputField ? inputField.value : "").trim();
    const model = modelField ? modelField.value : "BioGPT";
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

    if (inputField) inputField.value = "";

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

        if (!isLoggedIn) {
            guestQuestionCount++;
            localStorage.setItem("guestQuestionCount", guestQuestionCount);
        } else {
            // Save consultation history
            const accountId = localStorage.getItem("accountId");
            const memberId = localStorage.getItem("selectedMemberId");
            if (accountId && memberId) {
                let botSavedResponse = (model === "LRv1" || model === "LRv2")
                    ? JSON.stringify(data)
                    : (data.answer || JSON.stringify(data));

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
function openLoginModal() { openModal("login-modal"); }
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
function openRegisterModal() { openModal("register-modal"); }
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
function openAddMemberModal() { openModal("add-member-modal"); }
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
    const accountId = localStorage.getItem("accountId");
    const memberId = localStorage.getItem("selectedMemberId");
    const historyList = document.getElementById("history-list");

    if (!accountId) {
        historyList.innerHTML = `
            <div style="text-align:center; padding:30px 10px;">
                <i class="fas fa-lock" style="font-size:36px; color:#f59e0b; margin-bottom:12px;"></i>
                <p style="font-size:16px; font-weight:600; margin-bottom:6px;">Please Log In</p>
                <p style="font-size:13px; color:#a1a1aa; margin-bottom:16px;">Log in to access and manage your consultation history.</p>
                <button onclick="closeHistoryModal(); openLoginModal();" class="modal-btn" style="width:auto; padding:8px 24px;">Log In Now</button>
            </div>
        `;
        return;
    }

    historyList.innerHTML = `
        <div style="text-align:center; padding:30px; color:#a1a1aa;">
            <i class="fas fa-spinner fa-spin fa-2x" style="color:#6366f1;"></i>
            <p style="margin-top:12px; font-size:14px;">Loading consultation history...</p>
        </div>
    `;

    const reqBody = { account_id: accountId };
    if (memberId && String(memberId).toLowerCase() !== 'all') {
        reqBody.member_id = memberId;
    }

    fetch(API_BASE + "/getchat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reqBody)
    })
        .then(async res => {
            const data = await res.json().catch(() => null);
            if (!res.ok || !data) throw new Error((data && data.message) || "Failed to fetch");
            return data;
        })
        .then(data => {
            historyList.innerHTML = "";
            if (!data.history || data.history.length === 0) {
                historyList.innerHTML = `
                    <div style="text-align:center; padding:30px 10px; color:#a1a1aa;">
                        <i class="fas fa-comment-medical fa-2x" style="margin-bottom:10px; color:#6366f1;"></i>
                        <p style="font-size:15px; font-weight:600; color:#e4e4e7;">No history yet</p>
                        <p style="font-size:13px;">Ask any health question to save your consultation here.</p>
                    </div>
                `;
                return;
            }

            data.history.forEach(item => {
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
                        else if (parsed.Description) snippet = parsed.Description.slice(0, 90) + "...";
                        else if (parsed.answer) snippet = parsed.answer.slice(0, 90) + "...";
                        else snippet = String(item.response).slice(0, 90) + "...";
                    } catch (_) {
                        snippet = String(item.response).replace(/[#*`_]/g, '').slice(0, 90) + "...";
                    }
                }

                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
                        <h4 style="margin:0 0 6px 0; font-size:15px; font-weight:600; color:#f4f4f5; flex:1;">${item.question}</h4>
                        <i class="fas fa-trash" title="Delete" style="color:#ef4444; cursor:pointer; padding:4px;" onclick="deleteHistory(event, ${item.history_id})"></i>
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 8px 0; align-items:center;">
                        <span style="font-size:11px; padding:2px 8px; border-radius:12px; background:rgba(99,102,241,0.15); color:#818cf8; font-weight:600;">
                            <i class="fas fa-user-circle"></i> ${item.member_name || 'Member'}
                        </span>
                        <span style="font-size:11px; padding:2px 8px; border-radius:12px; background:rgba(16,185,129,0.15); color:#34d399; font-weight:600;">
                            <i class="fas fa-brain"></i> ${item.model}
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
        })
        .catch(err => {
            historyList.innerHTML = `<p style="text-align:center; color:#ef4444; padding:20px;">Error: ${err.message}</p>`;
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

    fetch(API_BASE + "/deletechat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            history_id: historyId,
            account_id: localStorage.getItem("accountId")
        })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                loadHistory();
            } else {
                alert(data.message || "Failed to delete.");
            }
        })
        .catch(() => alert("Network error deleting history."));
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
