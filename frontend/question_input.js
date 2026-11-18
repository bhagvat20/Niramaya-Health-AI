/**
 * Niramaya Health AI - Question Input & Consultation Logic (question_input.js)
 * Clean, fast, modular, and optimized implementation
 */

// Auto-detect backend API URL (supports localhost, 127.0.0.1, or cloud domain like Render)
const LOCAL_API = 'http://127.0.0.1:5000';
const CLOUD_API = 'https://niramaya-health-ai.onrender.com';
let API_BASE = (window.location.protocol.startsWith('http') && window.location.origin) 
    ? window.location.origin 
    : LOCAL_API;

// Helper: Reliable fetch with configurable timeout (generous on Render cold starts)
async function fastFetch(url, options = {}, timeoutMs = 30000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const response = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(timeoutId);
        return response;
    } catch (err) {
        clearTimeout(timeoutId);
        throw err;
    }
}

function getApiTimeoutMs() {
    const isLocal = API_BASE.includes("127.0.0.1") || API_BASE.includes("localhost");
    return isLocal ? 10000 : 35000;
}

function toTitleCase(str) {
    return String(str || "").replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.slice(1).toLowerCase());
}

// If opening locally via file://, probe local python server on 5000
if (window.location.protocol === 'file:') {
    API_BASE = LOCAL_API;
    fastFetch(LOCAL_API + '/api/status', {}, 400)
        .then(() => { API_BASE = LOCAL_API; })
        .catch(() => {});
}

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
    // Always clear legacy shared consultation cache so one user NEVER sees another user's or guest's history
    try {
        localStorage.removeItem("niramaya_consultations");
    } catch (_) {}

    // Persistent login: stays logged in across Home, refreshes, and tabs until explicit Logout
    const persistentLoggedIn = localStorage.getItem("userLoggedIn") === "true" && !!localStorage.getItem("accountId");
    const sessionLoggedIn = sessionStorage.getItem("userLoggedIn") === "true" && !!sessionStorage.getItem("accountId");

    if (persistentLoggedIn || sessionLoggedIn) {
        isLoggedIn = true;
        const accId = localStorage.getItem("accountId") || sessionStorage.getItem("accountId");
        const famName = localStorage.getItem("familyName") || sessionStorage.getItem("familyName") || "";
        const uEmail = localStorage.getItem("userEmail") || sessionStorage.getItem("userEmail") || "";
        const memName = localStorage.getItem("selectedMemberName") || sessionStorage.getItem("activeMemberName") || famName;
        const memId = localStorage.getItem("selectedMemberId") || sessionStorage.getItem("activeMemberId") || "";

        localStorage.setItem("userLoggedIn", "true");
        localStorage.setItem("accountId", accId);
        if (famName) localStorage.setItem("familyName", famName);
        if (uEmail) localStorage.setItem("userEmail", uEmail);
        if (memName) localStorage.setItem("selectedMemberName", memName);
        if (memId) localStorage.setItem("selectedMemberId", memId);

        sessionStorage.setItem("userLoggedIn", "true");
        sessionStorage.setItem("accountId", accId);
        if (famName) sessionStorage.setItem("familyName", famName);
        if (uEmail) sessionStorage.setItem("userEmail", uEmail);
        if (memName) sessionStorage.setItem("activeMemberName", memName);
        if (memId) sessionStorage.setItem("activeMemberId", memId);
    } else {
        isLoggedIn = false;
        guestQuestionCount = parseInt(localStorage.getItem("guestQuestionCount") || "0", 10);
        // Clean out any incomplete/stale keys for guests
        localStorage.removeItem("userLoggedIn");
        localStorage.removeItem("accountId");
        localStorage.removeItem("familyName");
        localStorage.removeItem("userEmail");
        localStorage.removeItem("selectedMemberName");
        localStorage.removeItem("selectedMemberId");
        sessionStorage.removeItem("activeMemberName");
        sessionStorage.removeItem("activeMemberId");
        sessionStorage.removeItem("accountId");
        sessionStorage.removeItem("userLoggedIn");
        sessionStorage.removeItem("familyName");
        sessionStorage.removeItem("userEmail");
    }

    updateNavButtons();
    updateGreeting();

    // Check URL parameters for direct modal open (skip login/register modal if already logged in)
    const urlParams = new URLSearchParams(window.location.search);
    const action = urlParams.get("action");
    if (action === "login" && !isLoggedIn) {
        openLoginModal();
    } else if (action === "register" && !isLoggedIn) {
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

    // Model dropdown sync (keeps hero & footer dropdowns aligned)
    const modelSelect = document.getElementById("model-select");
    const modelSelectFooter = document.getElementById("model-select-footer");

    function syncPlaceholder(sel, inp) {
        if (!sel || !inp) return;
        if (sel.value === "LRv1" || sel.value === "LRv2") {
            inp.placeholder = "Enter health symptoms (e.g. fever, headache, cough, skin rash)...";
        } else if (sel.value === "All") {
            inp.placeholder = "Enter symptoms to compare all 4 models (e.g. fever, headache, cough)...";
        } else {
            inp.placeholder = "Describe your health symptoms (e.g. fever, cough, stomach pain)...";
        }
    }

    if (modelSelect && initialInput) {
        modelSelect.addEventListener("change", () => {
            if (modelSelectFooter) modelSelectFooter.value = modelSelect.value;
            syncPlaceholder(modelSelect, initialInput);
            syncPlaceholder(modelSelectFooter, footerInput);
        });
        syncPlaceholder(modelSelect, initialInput);
    }
    if (modelSelectFooter && footerInput) {
        modelSelectFooter.addEventListener("change", () => {
            if (modelSelect) modelSelect.value = modelSelectFooter.value;
            syncPlaceholder(modelSelectFooter, footerInput);
            syncPlaceholder(modelSelect, initialInput);
        });
        syncPlaceholder(modelSelectFooter, footerInput);
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
                p.style.color = "var(--headline-color, #60a5fa)";
                p.style.fontWeight = "600";
                p.style.fontSize = "15px";
            } else if (line.startsWith("*(") && line.endsWith(")*")) {
                p.style.fontSize = "12px";
                p.style.fontStyle = "italic";
                p.style.color = "var(--secondary-text, #a1a1aa)";
                p.style.marginTop = "10px";
                p.style.borderTop = "1px solid var(--border-color, #333333)";
                p.style.paddingTop = "6px";
            }
            p.innerHTML = formatted;
            wrapper.appendChild(p);
        }
    });

    return wrapper;
}

// Helper: Render Real ML Probability Bars (from actual model predict_proba output)
function renderProbabilityBars(topPredictions, accentColor) {
    const list = document.createElement("div");
    list.className = "prob-bar-list";

    if (!Array.isArray(topPredictions) || topPredictions.length === 0) {
        const empty = document.createElement("p");
        empty.style.fontSize = "13px";
        empty.style.color = "var(--secondary-text)";
        empty.textContent = "No ML probability distribution available (insufficient matched symptom features).";
        list.appendChild(empty);
        return list;
    }

    topPredictions.forEach((pred, idx) => {
        const pct = Number(pred.probability || 0);
        const widthPct = Math.max(pct, 1.5);
        const item = document.createElement("div");
        item.className = "prob-bar-item";
        item.innerHTML = `
            <div class="prob-bar-header">
                <span>${idx + 1}. <strong>${pred.disease}</strong></span>
                <span class="prob-bar-pct" style="color:${accentColor};">${pct.toFixed(2)}%</span>
            </div>
            <div class="prob-bar-track">
                <div class="prob-bar-fill" style="width:${Math.min(widthPct, 100)}%; background:${accentColor};"></div>
            </div>
        `;
        list.appendChild(item);
    });

    return list;
}

// Helper: Render Matched Symptom Chips
function renderMatchedChips(symptoms) {
    const row = document.createElement("div");
    row.className = "symptom-chip-row";
    (symptoms || []).forEach(sym => {
        const chip = document.createElement("span");
        chip.className = "symptom-chip";
        chip.textContent = sym;
        row.appendChild(chip);
    });
    return row;
}

// Helper: Render Individual Model Card (BioGPT, Gemini, LRv1, or LRv2)
function renderModelPanel(modelKey, data, sectionNumber) {
    const card = document.createElement("div");
    const numPrefix = sectionNumber ? `${sectionNumber}. ` : "";

    if (modelKey === "BioGPT") {
        card.className = "model-panel-card biogpt-panel";
        card.innerHTML = `
            <div class="model-panel-header">
                <span class="model-panel-title"><i class="fas fa-dna" style="color:#06b6d4;"></i> ${numPrefix}BioGPT</span>
                <span class="model-role-pill">Biomedical Knowledge &amp; Medical Explanations</span>
            </div>
        `;
        if (data.source) {
            const meta = document.createElement("div");
            meta.className = "model-source-meta";
            meta.textContent = `Source: ${data.source}`;
            card.appendChild(meta);
        }
        card.appendChild(formatMedicalMarkdown(data.answer || String(data)));
        return card;
    }

    if (modelKey === "Gemini") {
        card.className = "model-panel-card gemini-panel";
        card.innerHTML = `
            <div class="model-panel-header">
                <span class="model-panel-title"><i class="fas fa-sparkles" style="color:#8b5cf6;"></i> ${numPrefix}Gemini</span>
                <span class="model-role-pill">AI Health Assistant — Guidance &amp; Follow-Up Questions</span>
            </div>
        `;
        if (data.source) {
            const meta = document.createElement("div");
            meta.className = "model-source-meta";
            meta.textContent = `Source: ${data.source}`;
            card.appendChild(meta);
        }
        card.appendChild(formatMedicalMarkdown(data.answer || String(data)));
        return card;
    }

    if (modelKey === "LRv1") {
        card.className = "model-panel-card lrv1-panel";
        card.innerHTML = `
            <div class="model-panel-header">
                <span class="model-panel-title"><i class="fas fa-chart-bar" style="color:#3b82f6;"></i> ${numPrefix}LRv1 — Logistic Regression Classifier</span>
                <span class="model-role-pill">Independent ML Disease Prediction</span>
            </div>
        `;
        if (data.algorithm) {
            const meta = document.createElement("div");
            meta.className = "model-source-meta";
            meta.textContent = `Model: ${data.algorithm}`;
            card.appendChild(meta);
        }

        const topProbStr = (data.top_probability !== undefined && data.top_predictions && data.top_predictions.length > 0)
            ? ` <span style="font-size:13px; color:#3b82f6; font-weight:700;">(${Number(data.top_probability).toFixed(2)}%)</span>`
            : "";
        const diseasePara = document.createElement("p");
        diseasePara.innerHTML = `<strong>Top Predicted Disease:</strong> <span style="color:#3b82f6; font-weight:700;">${data.predicted_disease || "No condition identified."}</span>${topProbStr}`;
        card.appendChild(diseasePara);

        if (data.matched_symptoms && data.matched_symptoms.length > 0) {
            const symLbl = document.createElement("p");
            symLbl.style.marginTop = "8px";
            symLbl.innerHTML = `<strong>Matched LRv1 Features (${data.matched_symptoms.length}):</strong>`;
            card.appendChild(symLbl);
            card.appendChild(renderMatchedChips(data.matched_symptoms));
        }

        if (data.top_predictions && data.top_predictions.length > 0) {
            const probTitle = document.createElement("p");
            probTitle.style.marginTop = "10px";
            probTitle.innerHTML = `<strong>Top Possible Diseases (Actual predict_proba Distribution):</strong>`;
            card.appendChild(probTitle);
            card.appendChild(renderProbabilityBars(data.top_predictions, "#3b82f6"));
        }

        const descPara = document.createElement("p");
        descPara.style.marginTop = "8px";
        descPara.innerHTML = `<strong>Disease Description:</strong> ${data.description || data.Description || "No description available."}`;
        card.appendChild(descPara);

        if (!sectionNumber && data.inference_status === "success" && data._query) {
            const cmpBtn = document.createElement("button");
            cmpBtn.type = "button";
            cmpBtn.style.cssText = "margin-top:12px; padding:7px 14px; border:1px solid #f59e0b; border-radius:8px; background:rgba(245,158,11,0.12); color:#f59e0b; font-size:12.5px; font-weight:600; cursor:pointer;";
            cmpBtn.innerHTML = '<i class="fas fa-balance-scale-right"></i> Compare LRv1 vs LRv2';
            cmpBtn.onclick = () => runOnDemandComparison(data._query, cmpBtn, card);
            card.appendChild(cmpBtn);
        }
        return card;
    }

    if (modelKey === "LRv2") {
        card.className = "model-panel-card lrv2-panel";
        card.innerHTML = `
            <div class="model-panel-header">
                <span class="model-panel-title"><i class="fas fa-project-diagram" style="color:#10b981;"></i> ${numPrefix}LRv2 — Enhanced Random Forest Classifier</span>
                <span class="model-role-pill">Independent Enhanced Prediction &amp; Precautions</span>
            </div>
        `;
        if (data.algorithm) {
            const meta = document.createElement("div");
            meta.className = "model-source-meta";
            meta.textContent = `Model: ${data.algorithm}`;
            card.appendChild(meta);
        }

        const topProbStr = (data.top_probability !== undefined && data.top_predictions && data.top_predictions.length > 0)
            ? ` <span style="font-size:13px; color:#10b981; font-weight:700;">(${Number(data.top_probability).toFixed(2)}%)</span>`
            : "";
        const diseasePara = document.createElement("p");
        diseasePara.innerHTML = `<strong>Top Predicted Disease:</strong> <span style="color:#10b981; font-weight:700;">${data.predicted_disease || "No condition identified."}</span>${topProbStr}`;
        card.appendChild(diseasePara);

        if (data.matched_symptoms && data.matched_symptoms.length > 0) {
            const symLbl = document.createElement("p");
            symLbl.style.marginTop = "8px";
            symLbl.innerHTML = `<strong>Matched LRv2 MLB Features (${data.matched_symptoms.length}):</strong>`;
            card.appendChild(symLbl);
            card.appendChild(renderMatchedChips(data.matched_symptoms));
        }

        if (data.top_predictions && data.top_predictions.length > 0) {
            const probTitle = document.createElement("p");
            probTitle.style.marginTop = "10px";
            probTitle.innerHTML = `<strong>Top Possible Diseases (Actual predict_proba Distribution):</strong>`;
            card.appendChild(probTitle);
            card.appendChild(renderProbabilityBars(data.top_predictions, "#10b981"));
        }

        const descPara = document.createElement("p");
        descPara.style.marginTop = "8px";
        descPara.innerHTML = `<strong>Disease Description:</strong> ${data.description || data.Description || "No description available."}`;
        card.appendChild(descPara);

        const precautions = data.precautions || [];
        if (precautions.length > 0) {
            const precTitle = document.createElement("p");
            precTitle.style.marginTop = "10px";
            precTitle.innerHTML = `<strong>Recommended Clinical Precautions:</strong>`;
            card.appendChild(precTitle);

            const ul = document.createElement("ul");
            precautions.forEach(p => {
                const li = document.createElement("li");
                li.textContent = p;
                ul.appendChild(li);
            });
            card.appendChild(ul);
        }

        if (!sectionNumber && data.inference_status === "success" && data._query) {
            const cmpBtn = document.createElement("button");
            cmpBtn.type = "button";
            cmpBtn.style.cssText = "margin-top:12px; padding:7px 14px; border:1px solid #f59e0b; border-radius:8px; background:rgba(245,158,11,0.12); color:#f59e0b; font-size:12.5px; font-weight:600; cursor:pointer;";
            cmpBtn.innerHTML = '<i class="fas fa-balance-scale-right"></i> Compare LRv1 vs LRv2';
            cmpBtn.onclick = () => runOnDemandComparison(data._query, cmpBtn, card);
            card.appendChild(cmpBtn);
        }
        return card;
    }

    card.className = "model-panel-card";
    card.textContent = data.answer || JSON.stringify(data);
    return card;
}

// Helper: On-demand LRv1 vs LRv2 Comparison (only runs when user clicks "Compare LRv1 vs LRv2")
async function runOnDemandComparison(queryText, btnEl, parentCard) {
    if (!queryText) return;
    btnEl.disabled = true;
    btnEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Comparing LRv1 vs LRv2...';
    try {
        const res = await fastFetch(API_BASE + "/askall", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: queryText, symptoms: queryText })
        }, getApiTimeoutMs());
        const d = await res.json().catch(() => null);
        if (res.ok && d && d.comparison) {
            btnEl.remove();
            const cmpPanel = renderComparisonPanel(d.comparison);
            cmpPanel.style.marginTop = "12px";
            parentCard.parentElement.appendChild(cmpPanel);
            setTimeout(scrollToBottom, 100);
        } else {
            btnEl.disabled = false;
            btnEl.innerHTML = '<i class="fas fa-balance-scale-right"></i> Compare LRv1 vs LRv2';
        }
    } catch (_) {
        btnEl.disabled = false;
        btnEl.innerHTML = '<i class="fas fa-balance-scale-right"></i> Compare LRv1 vs LRv2';
    }
}

// Helper: Render LRv1 vs LRv2 Comparison Section
function renderComparisonPanel(comp) {
    const card = document.createElement("div");
    card.className = "model-panel-card comparison-panel";

    const code = comp.agreement_code || "insufficient";
    const statusIcon = (code === "agree")
        ? "fa-check-circle"
        : (code === "partial")
            ? "fa-balance-scale"
            : (code === "disagree")
                ? "fa-exchange-alt"
                : "fa-info-circle";

    const v1 = comp.lrv1_summary || {};
    const v2 = comp.lrv2_summary || {};

    let overlapHtml = "";
    if (Array.isArray(comp.overlapping_diseases) && comp.overlapping_diseases.length > 0) {
        const rows = comp.overlapping_diseases.map(o => `
            <tr>
                <td><strong>${o.disease}</strong></td>
                <td style="color:#3b82f6; font-weight:600;">${Number(o.lrv1_probability).toFixed(2)}%</td>
                <td style="color:#10b981; font-weight:600;">${Number(o.lrv2_probability).toFixed(2)}%</td>
            </tr>
        `).join("");
        overlapHtml = `
            <p style="margin-top:10px; font-weight:600;">Overlapping Candidates in Top-5 Predictions:</p>
            <table class="overlap-table">
                <thead>
                    <tr>
                        <th>Disease</th>
                        <th>LRv1 Probability</th>
                        <th>LRv2 Probability</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    }

    card.innerHTML = `
        <div class="model-panel-header">
            <span class="model-panel-title"><i class="fas fa-balance-scale-right" style="color:#f59e0b;"></i> LRv1 vs LRv2 — Model Comparison &amp; Agreement</span>
            <span class="agreement-badge ${code}"><i class="fas ${statusIcon}"></i> ${comp.agreement_status || "Comparison"}</span>
        </div>
        <div class="comparison-grid">
            <div class="comparison-col">
                <h5 style="color:#3b82f6;"><i class="fas fa-chart-bar"></i> LRv1 (Logistic Regression)</h5>
                <p><strong>Top-1 Prediction:</strong> ${v1.predicted_disease || "N/A"}</p>
                <p><strong>Top-1 Probability:</strong> ${Number(v1.top_probability || 0).toFixed(2)}%</p>
                <p><strong>Top-5 Cumulative Prob:</strong> ${Number(v1.top5_cumulative_probability || 0).toFixed(2)}%</p>
                <p><strong>Matched Features:</strong> ${v1.matched_feature_count || 0} (across ${v1.total_classes || 261} classes)</p>
            </div>
            <div class="comparison-col">
                <h5 style="color:#10b981;"><i class="fas fa-project-diagram"></i> LRv2 (Random Forest)</h5>
                <p><strong>Top-1 Prediction:</strong> ${v2.predicted_disease || "N/A"}</p>
                <p><strong>Top-1 Probability:</strong> ${Number(v2.top_probability || 0).toFixed(2)}%</p>
                <p><strong>Top-5 Cumulative Prob:</strong> ${Number(v2.top5_cumulative_probability || 0).toFixed(2)}%</p>
                <p><strong>Matched Features:</strong> ${v2.matched_feature_count || 0} (across ${v2.total_classes || 41} classes)</p>
            </div>
        </div>
        ${overlapHtml}
        <p style="font-size:13px; color:var(--secondary-text); margin-top:8px; line-height:1.55;">
            <strong style="color:var(--text-color);">Comparison Analysis:</strong> ${comp.comparison_notes || ""}
        </p>
    `;
    return card;
}

// Unified Bot Response Renderer (Supports All 4 Differentiated Models + Individual Models)
function renderBotResponseContent(model, data) {
    const container = document.createElement("div");
    container.className = "bot-response-content";

    // Multi-model 4-output + LRv1 vs LRv2 Comparison payload
    if (model === "All" || (data && data.biogpt && data.gemini && data.lrv1 && data.lrv2)) {
        if (data.is_greeting || data.is_health_related === false) {
            container.appendChild(formatMedicalMarkdown(data.answer || data.message || "Please enter health symptoms."));
            return container;
        }
        const stack = document.createElement("div");
        stack.className = "multi-model-stack";
        stack.appendChild(renderModelPanel("BioGPT", data.biogpt, 1));
        stack.appendChild(renderModelPanel("Gemini", data.gemini, 2));
        stack.appendChild(renderModelPanel("LRv1", data.lrv1, 3));
        stack.appendChild(renderModelPanel("LRv2", data.lrv2, 4));
        if (data.comparison) {
            stack.appendChild(renderComparisonPanel(data.comparison));
        }
        container.appendChild(stack);
        return container;
    }

    if (model === "BioGPT" || model === "Gemini" || model === "LRv1" || model === "LRv2") {
        container.appendChild(renderModelPanel(model, data));
        return container;
    }

    const fallbackP = document.createElement("p");
    fallbackP.textContent = (data && data.answer) ? data.answer : JSON.stringify(data);
    container.appendChild(fallbackP);
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
            case "All":
                endpoint = API_BASE + "/askall";
                payload = { question: userInput, symptoms: userInput };
                break;
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

        let response = null;
        let data = null;

        // Direct fetch to active API endpoint (generous timeout for Render cold-start & Gemini AI)
        try {
            response = await fastFetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            }, getApiTimeoutMs());
            data = await response.json().catch(() => null);
        } catch (_) {}

        // Fallback: If local API failed or unreachable, try Render live cloud directly
        if ((!response || !response.ok || !data) && !endpoint.includes("niramaya-health-ai.onrender.com")) {
            try {
                const cloudPath = (model === "All")
                    ? "/askall"
                    : (model === "LRv1") ? "/asklrv1"
                    : (model === "LRv2") ? "/asklrv2"
                    : (model === "Gemini") ? "/askgemini"
                    : "/askbiogpt";
                const cloudRes = await fastFetch(CLOUD_API + cloudPath, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                }, 30000);
                const cloudData = await cloudRes.json().catch(() => null);
                if (cloudRes.ok && cloudData) {
                    response = cloudRes;
                    data = cloudData;
                    API_BASE = CLOUD_API;
                }
            } catch (_) {}
        }

        const currentLoader = document.getElementById("loading-indicator");
        if (currentLoader) currentLoader.remove();

        if (!data) {
            // Offline clinical engine fallback guarantee: matches backend strict symptom-only guardrail
            const cleanSym = userInput.trim();
            const cleanLower = cleanSym.toLowerCase().replace(/[?!.,]+$/g, '').trim();

            // 1. Check pure short greetings ONLY
            const greetings = ['hi', 'hello', 'hey', 'namaste', 'good morning', 'good afternoon', 'good evening', 'help', 'hi there', 'hello there'];
            const isGreeting = greetings.includes(cleanLower);

            if (isGreeting) {
                if (model === "LRv1" || model === "LRv2") {
                    data = {
                        predicted_disease: "Niramaya AI Health Assistant",
                        matched_symptoms: [],
                        description: "Hello! I am your Niramaya AI Health Assistant. I am specialized strictly in symptom checking, health assessment, and clinical precautions (not general chat). Please enter any health symptoms you are experiencing (e.g., fever, headache, cough, stomach pain, dizziness) to receive clinical insights.",
                        precautions: [
                            "List your specific symptoms in detail",
                            "Track symptom onset and severity",
                            "Stay well-hydrated with clean water and rest",
                            "Seek immediate medical care for severe symptoms"
                        ]
                    };
                } else {
                    data = {
                        question: userInput,
                        answer: "Hello! I am your **Niramaya AI Health Assistant** (Symptom Checker Only — not a general chatbot).\n\nPlease describe the **health symptoms** you are experiencing (e.g., *fever, headache, cough, stomach pain, rash*) to receive instant clinical guidance."
                    };
                }
            } else {
                // 2. Strict whole-word symptom & health domain check (blocks general ChatGPT queries)
                const outOfDomain = /\b(python|javascript|java|coding|programming|cricket|football|movie|song|capital of|weather|joke|poem|story|recipe|cook|chatgpt|openai|politics|prime minister|laptop|phone|galaxy|spain|france|teacher|homework|essay|email)\b/i;
                const strictHealthRegex = /\b(pain|ache|fever|fevr|cough|caugh|flu|sneeze|vomit|vomiting|nausea|diarrhea|diarrhoea|headache|headche|migraine|dizzy|dizziness|fatigue|weakness|swelling|bleeding|rash|itching|cramp|cramps|sore throat|breathless|shortness of breath|chills|sweating|weight loss|weight gain|insomnia|acidity|indigestion|bloating|constipation|infection|viral|allergy|asthma|diabetes|hypertension|thyroid|dengue|malaria|typhoid|jaundice|stomach pain|chest pain|back pain|neck pain|joint pain|knee pain|earache|toothache|digestive|gastritis|piles|ulcer|dard|bukhar|khansi|sardi|jukam|ulti|dast|pet dard|sir dard|sar dard|chakkar|kamzori|sujan|khujli|gale me dard|gale me kharash)\b/i;
                const isHealth = !outOfDomain.test(cleanLower) && strictHealthRegex.test(cleanLower);

                if (!isHealth) {
                    if (model === "LRv1" || model === "LRv2") {
                        data = {
                            predicted_disease: "Non-Health Query",
                            matched_symptoms: [],
                            description: "⚠️ Medical Domain Restriction: Niramaya AI only processes medical and health symptoms (not general chat). Please enter specific health symptoms (e.g. fever, headache, stomach ache, body pain) to predict conditions.",
                            precautions: ["Please ask questions strictly related to human health, symptoms, and medical wellness."]
                        };
                    } else {
                        data = {
                            question: userInput,
                            answer: "⚠️ **Medical & Symptom Checker Domain Restriction:**\n\nI am your **Niramaya AI Health Assistant**. I am specialized **exclusively in health symptoms, medical conditions, and clinical precautions** — I do **not** act as a general chatbot like ChatGPT.\n\nI cannot answer non-medical questions (such as general knowledge, coding, essays, politics, sports, weather, recipes, or casual conversation).\n\n👉 **Please describe your health symptoms** (e.g., *fever, headache, cough, body pain, dizziness, stomach ache, rash*) to receive clinical assessment, home care, and precautions."
                        };
                    }
                } else if (model === "LRv1" || model === "LRv2") {
                    let predDis = toTitleCase(cleanSym) + " (Symptom Assessment)";
                    let precs = [
                        "Stay well-hydrated with clean water and herbal broths",
                        "Ensure 7 to 8 hours of uninterrupted physical rest",
                        "Avoid unprescribed frequent pain medications",
                        "Seek immediate medical attention if symptoms escalate"
                    ];
                    if (cleanLower.includes("throat") || cleanLower.includes("gala") || cleanLower.includes("gale")) {
                        predDis = "Acute Pharyngitis & Throat Irritation (गले में खराश)";
                        precs = ["Warm saline water gargles 3-4 times daily", "Sip warm ginger-honey water", "Avoid refrigerated cold beverages", "Consult a doctor if swallowing is difficult"];
                    } else if (cleanLower.includes("digest") || cleanLower.includes("stomach") || cleanLower.includes("pet dard") || cleanLower.includes("gut")) {
                        predDis = "Functional Dyspepsia & Gut Disturbance (पाचन संबंधी समस्या)";
                        precs = ["Consume fresh curd / probiotic buttermilk", "Sip warm fennel-cumin water after meals", "Adopt a light khichdi / BRAT diet", "Avoid deep-fried and spicy curries"];
                    } else if (cleanLower.includes("cough") || cleanLower.includes("khansi") || cleanLower.includes("cold")) {
                        predDis = "Bronchial Congestion & Upper Respiratory Irritation (खांसी व जुकाम)";
                        precs = ["Steam inhalation twice daily", "Drink warm turmeric milk before sleeping", "Keep head elevated at night", "Avoid direct cold air drafts"];
                    } else if (cleanLower.includes("fever") || cleanLower.includes("bukhar")) {
                        predDis = "Acute Pyrexia & Immune Response (वायरल बुखार)";
                        precs = ["Total physical bed rest in cool room", "ORS and tender coconut water hydration", "Tepid sponging with lukewarm water", "Seek doctor if fever exceeds 102°F"];
                    } else if (cleanLower.includes("headache") || cleanLower.includes("headche") || cleanLower.includes("sir dard")) {
                        predDis = "Cephalea & Tension / Migraine (सिर दर्द)";
                        precs = ["Rest in a quiet, dark room away from screens", "Drink 500ml water immediately", "Apply a cold compress on forehead", "Avoid loud sounds and skipping meals"];
                    }
                    data = {
                        predicted_disease: predDis,
                        matched_symptoms: [cleanSym],
                        description: `Clinical assessment for '${cleanSym}': Monitor symptom duration, avoid physical strain, and practice targeted home care.`,
                        precautions: precs
                    };
                } else {
                    let clinicalOverview = `Health inquiries regarding '${userInput}' involve evaluating physiological balance and organ stress.`;
                    let causesText = "- Dehydration, irregular sleep, or situational physical/mental fatigue\n- Underlying viral, bacterial, or seasonal reactivity\n- Dietary sensitivities or irregular meal intervals";
                    let homeCareText = "- Hydration: Drink 2.5 to 3 liters of warm water and electrolyte broths\n- Rest: Ensure 7 to 8 hours of uninterrupted rest in a quiet space\n- Nutrition: Eat freshly prepared light, nutrient-rich meals";
                    let redFlagsText = "- 🚨 High persistent fever (>102°F)\n- 🚨 Severe unremitting pain or difficulty breathing\n- 🚨 Extreme weakness or inability to keep liquids down";

                    if (cleanLower.includes("throat") || cleanLower.includes("gala") || cleanLower.includes("gale")) {
                        clinicalOverview = "Pharyngeal irritation and acute pharyngitis involve inflammation of mucous membranes in the throat or tonsils.";
                        causesText = "- Viral pharyngitis (rhinovirus, adenovirus, or flu)\n- Bacterial tonsillopharyngitis (strep throat)\n- Acid reflux (LPR) or vocal cord strain";
                        homeCareText = "- Warm Saline Gargles: Gargle with 1/2 tsp salt in warm water 3-4 times daily\n- Soothing Warm Sips: Warm water with pure honey, ginger, and tulsi\n- Steam Inhalation: Inhale warm vapor for 5-7 minutes\n- Avoid: Cold refrigerated drinks, ice cream, and spicy peppers";
                        redFlagsText = "- 🚨 Inability to swallow liquids or saliva\n- 🚨 Difficulty breathing or whistling breath sounds\n- 🚨 Asymmetric swelling of tonsils or fever > 102°F";
                    } else if (cleanLower.includes("digest") || cleanLower.includes("stomach") || cleanLower.includes("pet dard") || cleanLower.includes("gut")) {
                        clinicalOverview = "Gastrointestinal disturbances involve altered gut motility, acid imbalance, or gut flora (dysbiosis) irritation.";
                        causesText = "- Gastric hyperacidity or GERD acid reflux\n- Irritable bowel syndrome (IBS) or food intolerance\n- Sluggish motility or stress-mediated gut spasms";
                        homeCareText = "- Probiotics: Fresh homemade curd, yogurt, or buttermilk with roasted cumin\n- Digestive Tea: Lukewarm water with fennel seeds (saunf) and ginger\n- Bland Diet: Light moong dal khichdi, steamed rice, and ripe bananas\n- Avoid: Deep-fried oily snacks, carbonated drinks, and late heavy dinners";
                        redFlagsText = "- 🚨 Severe, acute abdominal rigidity or localized sharp colic\n- 🚨 Blood in vomit or black tarry stools\n- 🚨 Inability to keep liquids down for 24 hours or yellowing of eyes (jaundice)";
                    } else if (cleanLower.includes("cough") || cleanLower.includes("khansi") || cleanLower.includes("cold")) {
                        clinicalOverview = "Respiratory cough reflects tracheobronchial hyperreactivity and mucosal clearing mechanisms.";
                        causesText = "- Viral respiratory infection or seasonal bronchitis\n- Post-nasal drip pooling in posterior airway\n- Allergic airway sensitivity to dust, smoke, or cold drafts";
                        homeCareText = "- Steam Inhalation: Warm water steam for 5-10 minutes twice daily\n- Warm Turmeric Milk: Drink warm milk with turmeric and black pepper before bed\n- Head Elevation: Sleep with an extra pillow to reduce nocturnal cough\n- Avoid: Chilled water, smoking, and air conditioning drafts";
                        redFlagsText = "- 🚨 Shortness of breath or rapid labored breathing\n- 🚨 Coughing up blood or rust-colored phlegm\n- 🚨 Persistent high fever lasting beyond 3 days";
                    } else if (cleanLower.includes("fever") || cleanLower.includes("bukhar")) {
                        clinicalOverview = "Pyrexia is an active immune-mediated defense orchestrated by the hypothalamus against pathogens.";
                        causesText = "- Systemic viral flu, dengue, or seasonal infectious agents\n- Bacterial focal infection (urinary, respiratory, or enteric)\n- Localized inflammatory immune response";
                        homeCareText = "- Complete Bed Rest: Conserve metabolic energy for immune defense\n- Electrolytes: Drink generous amounts of ORS, coconut water, and clear soups\n- Tepid Sponging: Wipe forehead and neck with lukewarm water (never cold ice)\n- Diet: Thin dal soup, barley water, and light rice porridge";
                        redFlagsText = "- 🚨 Temperature rising above 103°F or unresponsive to antipyretics\n- 🚨 Fever with stiff neck, confusion, or convulsions\n- 🚨 Tiny red/purple pinpoint spots on skin (petechiae)";
                    } else if (cleanLower.includes("headache") || cleanLower.includes("headche") || cleanLower.includes("sir dard")) {
                        clinicalOverview = "Cephalea arises from pericranial muscle tension, vascular spasms, or cranial nerve sensitivity.";
                        causesText = "- Tension headache from mental stress, prolonged screen time, or neck stiffness\n- Vascular migraine from sleep disruption or skipped meals\n- Dehydration or sudden caffeine withdrawal";
                        homeCareText = "- Quiet Rest: Lie down in a dark, quiet room away from screens\n- Rapid Hydration: Drink 500ml of cool water immediately\n- Cold Compress: Place an ice pack wrapped in a cloth over forehead or temples\n- Gentle Relief: Slow neck rolls and shoulder stretches";
                        redFlagsText = "- 🚨 Sudden explosive 'thunderclap' headache\n- 🚨 Headache with stiff neck, high fever, or confusion\n- 🚨 Facial drooping, slurred speech, or vision loss";
                    }

                    data = {
                        question: userInput,
                        answer: `**Condition / Clinical Assessment:** ${toTitleCase(cleanSym)} (Clinical Evaluation)\n\n**Medical Overview:**\n${clinicalOverview}\n\n**Probable Causes & Contributing Factors:**\n${causesText}\n\n**Dietary Recommendations & Home Care:**\n${homeCareText}\n\n**When to Seek Immediate Medical Attention (Red Flags):**\n${redFlagsText}\n\n*(Disclaimer: Niramaya provides AI-guided informational health insights. This does not replace formal examination, laboratory diagnosis, or prescription by a licensed medical practitioner.)*`
                    };
                }
            }
        }

        if (data && typeof data === "object") {
            data._query = userInput;
        }
        const botMsg = document.createElement("div");
        botMsg.className = "chat-message bot-message";
        botMsg.appendChild(renderBotResponseContent(model, data));
        chatContainer.appendChild(botMsg);

        let botSavedResponse = (model === "All" || model === "LRv1" || model === "LRv2")
            ? JSON.stringify(data)
            : (data.answer || JSON.stringify(data));

        if (!isLoggedIn) {
            // Guest users: track question limit only — NEVER save guest chats to DB or shared localStorage
            guestQuestionCount++;
            localStorage.setItem("guestQuestionCount", guestQuestionCount);
        } else {
            // Logged-in family user: save consultation history strictly under their own account & member profile
            const accountId = localStorage.getItem("accountId") || sessionStorage.getItem("accountId");
            const memberId = localStorage.getItem("selectedMemberId") || sessionStorage.getItem("activeMemberId") || null;
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
                })
                    .then(async (saveRes) => {
                        if (saveRes.status === 404) {
                            // Account was deleted by admin or server ephemeral SQLite restarted — clear stale session
                            console.warn("Saved account_id no longer exists on server. Prompting re-login.");
                        }
                    })
                    .catch(e => console.warn("Save chat notice:", e));
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
        if (historyBtn) historyBtn.style.display = "none";
    }
}

function getLoggedInDisplayName() {
    if (!isLoggedIn) return "";

    // 1. Explicitly selected member profile
    const activeMember = sessionStorage.getItem("activeMemberName") || localStorage.getItem("selectedMemberName");
    if (activeMember && activeMember.trim() && activeMember.trim().toLowerCase() !== "null") {
        return activeMember.trim();
    }

    // 2. Family / registered user name from session or storage
    const familyName = sessionStorage.getItem("familyName") || localStorage.getItem("familyName");
    if (familyName && familyName.trim() && familyName.trim().toLowerCase() !== "null") {
        return familyName.trim();
    }

    // 3. User email prefix
    const email = sessionStorage.getItem("userEmail") || localStorage.getItem("userEmail");
    if (email && email.trim()) {
        const raw = email.split("@")[0].replace(/[^a-zA-Z0-9]/g, ' ').trim();
        if (raw) {
            return raw.charAt(0).toUpperCase() + raw.slice(1);
        }
    }

    return "User";
}

function updateGreeting() {
    const welcomeEl = document.getElementById("welcome-message");
    const subHeaderEl = document.querySelector(".sub-header");

    // Only display greeting name if user is logged in
    if (isLoggedIn) {
        const displayName = getLoggedInDisplayName();
        if (welcomeEl) {
            welcomeEl.style.display = "block";
            welcomeEl.textContent = `Hello, ${displayName}!`;
        }
        if (subHeaderEl) {
            subHeaderEl.textContent = "What is your goal today? How can I help you?";
        }
    } else {
        // Guest / Not logged in: completely simple without any name!
        if (welcomeEl) {
            welcomeEl.style.display = "none";
            welcomeEl.textContent = "";
        }
        if (subHeaderEl) {
            subHeaderEl.textContent = "How can I help you today?";
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
    
    const wipeInputs = () => {
        const emailInput = document.getElementById("email");
        const pwdInput = document.getElementById("password");
        if (emailInput) {
            emailInput.value = "";
            emailInput.defaultValue = "";
            emailInput.setAttribute("autocomplete", "new-password");
        }
        if (pwdInput) {
            pwdInput.value = "";
            pwdInput.defaultValue = "";
            pwdInput.setAttribute("autocomplete", "new-password");
        }
    };

    wipeInputs();
    openModal("login-modal");

    // Multi-pass clear to defeat aggressive browser autofill injection
    setTimeout(wipeInputs, 30);
    setTimeout(wipeInputs, 150);
    setTimeout(wipeInputs, 300);
}
function closeLoginModal() { closeModal("login-modal"); }

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const loginBtn = document.getElementById("user-login-btn") || e.target.querySelector("button[type='submit']");
    const origText = loginBtn ? loginBtn.innerHTML : "Login";

    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Authenticating...';
    }

    try {
        let res = null;
        let data = null;

        // Try primary API
        try {
            res = await fetch(API_BASE + "/userlogin", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });
            data = await res.json().catch(() => null);
        } catch (_) {}

        // Fallback: If primary local server was completely unreachable, try Render cloud
        if (!res && API_BASE !== CLOUD_API) {
            try {
                const cloudRes = await fetch(CLOUD_API + "/userlogin", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });
                const cloudData = await cloudRes.json().catch(() => null);
                if (cloudRes.ok && cloudData && cloudData.success) {
                    res = cloudRes;
                    data = cloudData;
                    API_BASE = CLOUD_API;
                }
            } catch (_) {}
        }

        if (res && res.ok && data && data.success) {
            const resolvedName = (data.familyname && data.familyname.trim()) 
                ? data.familyname.trim() 
                : (data.members && data.members.length > 0 && data.members[0].name ? data.members[0].name : (email ? email.split("@")[0] : "User"));

            sessionStorage.setItem("userLoggedIn", "true");
            sessionStorage.setItem("accountId", data.account_id);
            sessionStorage.setItem("familyName", resolvedName);
            sessionStorage.setItem("userEmail", data.email || email);
            sessionStorage.setItem("activeMemberName", resolvedName);

            localStorage.setItem("userLoggedIn", "true");
            localStorage.setItem("accountId", data.account_id);
            localStorage.setItem("userEmail", data.email || email);
            localStorage.setItem("familyName", resolvedName);
            localStorage.setItem("selectedMemberName", resolvedName);

            if (data.members && data.members.length > 0) {
                sessionStorage.setItem("activeMemberId", data.members[0].member_id);
                localStorage.setItem("selectedMemberId", data.members[0].member_id);
            }
            isLoggedIn = true;

            closeLoginModal();
            updateNavButtons();
            updateGreeting();

            if (data.members && data.members.length > 1) {
                openMemberSelectionModal(data.members);
            }
        } else {
            alert((data && data.message) || "Invalid email or password. Please try again.");
        }
    } catch (err) {
        alert("Server connection error during login. Ensure backend server is running.");
    } finally {
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.innerHTML = origText;
        }
    }
}

// Register
function openRegisterModal() {
    const form = document.getElementById("register-form");
    if (form) form.reset();

    const wipeInputs = () => {
        ['familyname', 'register-email', 'register-password'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.value = "";
                el.defaultValue = "";
                el.setAttribute("autocomplete", "new-password");
            }
        });
    };

    wipeInputs();
    openModal("register-modal");

    setTimeout(wipeInputs, 30);
    setTimeout(wipeInputs, 150);
}
function closeRegisterModal() { closeModal("register-modal"); }

async function handleRegister(e) {
    e.preventDefault();
    const fname = document.getElementById("familyname").value.trim();
    const email = document.getElementById("register-email").value.trim();
    const password = document.getElementById("register-password").value;
    const regBtn = document.getElementById("user-register-btn") || e.target.querySelector("button[type='submit']");
    const origText = regBtn ? regBtn.innerHTML : "Register";

    if (!fname || !email || !password) {
        alert("Please fill in your name, email address, and password.");
        return;
    }

    if (regBtn) {
        regBtn.disabled = true;
        regBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
    }

    try {
        let res = null;
        let data = null;

        try {
            res = await fastFetch(API_BASE + "/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ fname, email, password })
            }, getApiTimeoutMs());
            data = await res.json().catch(() => null);
        } catch (_) {}

        // Fallback to cloud Render deployment ONLY when running locally and local server is unreachable
        if (!res && API_BASE !== CLOUD_API) {
            try {
                const cloudRes = await fastFetch(CLOUD_API + "/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ fname, email, password })
                }, 35000);
                const cloudData = await cloudRes.json().catch(() => null);
                res = cloudRes;
                data = cloudData;
                if (cloudRes.ok) API_BASE = CLOUD_API;
            } catch (_) {}
        }

        if (res && res.ok && data && data.success) {
            sessionStorage.setItem("userLoggedIn", "true");
            sessionStorage.setItem("accountId", data.account_id);
            sessionStorage.setItem("familyName", fname);
            sessionStorage.setItem("userEmail", data.email || email);
            sessionStorage.setItem("activeMemberName", fname);

            localStorage.setItem("userLoggedIn", "true");
            localStorage.setItem("accountId", data.account_id);
            localStorage.setItem("userEmail", data.email || email);
            localStorage.setItem("familyName", fname);
            localStorage.setItem("selectedMemberName", fname);
            if (data.member_id) {
                localStorage.setItem("selectedMemberId", data.member_id);
                sessionStorage.setItem("activeMemberId", data.member_id);
            }
            isLoggedIn = true;

            alert("Registration successful! Welcome to Niramaya.");
            closeRegisterModal();
            updateNavButtons();
            updateGreeting();
            // Open member selection / setup
            openAddMemberModal();
        } else if (data && data.message) {
            alert(data.message);
        } else {
            alert("Unable to complete registration right now. The server may be waking up — please try again in a few seconds.");
        }
    } catch (err) {
        alert("Unable to connect to the registration server. Please check your internet connection and try again.");
    } finally {
        if (regBtn) {
            regBtn.disabled = false;
            regBtn.innerHTML = origText;
        }
    }
}

// Logout
function logout() {
    sessionStorage.clear();
    localStorage.removeItem("userLoggedIn");
    localStorage.removeItem("accountId");
    localStorage.removeItem("userEmail");
    localStorage.removeItem("familyName");
    localStorage.removeItem("selectedMemberId");
    localStorage.removeItem("selectedMemberName");
    localStorage.removeItem("niramaya_consultations");
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

// Consultation History Modal (Strictly for Logged-In Family Users Only)
function openHistoryModal() {
    if (!isLoggedIn || !(localStorage.getItem("accountId") || sessionStorage.getItem("accountId"))) {
        alert("Please login to view your personal consultation history.");
        openLoginModal();
        return;
    }
    openModal("history-modal");
    loadHistory();
}

function closeHistoryModal() { closeModal("history-modal"); }

function loadHistory() {
    const historyList = document.getElementById("history-list");
    if (!historyList) return;

    const storedAccountId = localStorage.getItem("accountId") || sessionStorage.getItem("accountId");
    const activeMemberId = localStorage.getItem("selectedMemberId") || sessionStorage.getItem("activeMemberId") || null;

    // Strictly block unauthenticated/guest users from seeing any chat history
    if (!isLoggedIn || !storedAccountId) {
        historyList.innerHTML = `
            <div style="text-align:center; padding:35px; color:var(--secondary-text);">
                <i class="fas fa-lock fa-2x" style="color:#6366f1; margin-bottom:12px;"></i>
                <p style="font-size:15px; font-weight:600; color:var(--text-color);">Login Required</p>
                <p style="font-size:13px; color:var(--secondary-text); margin:6px 0 16px;">Only logged-in family members can save and view their own private consultation history.</p>
                <button class="modal-btn" style="max-width:220px; margin:0 auto;" onclick="closeHistoryModal(); openLoginModal();"><i class="fas fa-sign-in-alt"></i> Login Now</button>
            </div>
        `;
        return;
    }

    historyList.innerHTML = `
        <div style="text-align:center; padding:30px; color:var(--secondary-text);">
            <i class="fas fa-spinner fa-spin fa-2x" style="color:#6366f1;"></i>
            <p style="margin-top:12px; font-size:14px;">Loading your consultation history...</p>
        </div>
    `;

    // Strictly fetch ALL consultations belonging ONLY to this logged-in family account
    // (never leaks other accounts' or guest chats, and shows all family member chats with member badges)
    const reqBody = { account_id: storedAccountId };

    const renderOwnHistory = (serverHistory) => {
        const items = Array.isArray(serverHistory) ? serverHistory : [];
        if (items.length === 0) {
            historyList.innerHTML = `
                <div style="text-align:center; padding:35px; color:var(--secondary-text);">
                    <i class="fas fa-comment-medical fa-2x" style="color:#6366f1; margin-bottom:12px;"></i>
                    <p style="font-size:14px; font-weight:600; color:var(--text-color);">No consultation history yet</p>
                    <p style="font-size:12.5px; color:var(--secondary-text); margin-top:4px;">Your own symptom checks will appear privately here.</p>
                </div>
            `;
        } else {
            renderHistoryCards(items);
        }
    };

    fastFetch(API_BASE + "/getchat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reqBody)
    }, getApiTimeoutMs())
        .then(async res => {
            const data = await res.json().catch(() => null);
            if (!res.ok || !data || !data.success) throw new Error("History fetch failed");
            return data;
        })
        .then(data => {
            renderOwnHistory(data.history || []);
        })
        .catch(() => {
            historyList.innerHTML = `
                <div style="text-align:center; padding:30px; color:#ef4444;">
                    <i class="fas fa-exclamation-triangle fa-2x" style="margin-bottom:10px;"></i>
                    <p style="font-size:14px;">Unable to load your consultation history right now. Please try again.</p>
                </div>
            `;
        });
}

function renderHistoryCards(items) {
    const historyList = document.getElementById("history-list");
    if (!historyList) return;
    historyList.innerHTML = "";

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
                if (parsed.lrv1 && parsed.lrv2) {
                    const compStatus = parsed.comparison ? parsed.comparison.agreement_status : "";
                    snippet = `LRv1: ${parsed.lrv1.predicted_disease} | LRv2: ${parsed.lrv2.predicted_disease}${compStatus ? " (" + compStatus + ")" : ""}`;
                } else if (parsed.predicted_disease) snippet = "Predicted: " + parsed.predicted_disease;
                else if (parsed.Description) snippet = parsed.Description.slice(0, 95) + "...";
                else if (parsed.answer) snippet = parsed.answer.slice(0, 95) + "...";
                else snippet = String(item.response).slice(0, 95) + "...";
            } catch (_) {
                snippet = String(item.response).replace(/[#*`_]/g, '').slice(0, 95) + "...";
            }
        }

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
                <h4 style="margin:0 0 6px 0; font-size:15px; font-weight:600; color:var(--text-color); flex:1;">${item.question}</h4>
                <i class="fas fa-trash" title="Delete" style="color:#ef4444; cursor:pointer; padding:4px;" onclick="deleteHistory(event, '${item.history_id}')"></i>
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 8px 0; align-items:center;">
                <span style="font-size:11px; padding:2px 8px; border-radius:12px; background:rgba(99,102,241,0.15); color:#6366f1; font-weight:600;">
                    <i class="fas fa-user-circle"></i> ${item.member_name || 'Member'}
                </span>
                <span style="font-size:11px; padding:2px 8px; border-radius:12px; background:rgba(16,185,129,0.15); color:#10b981; font-weight:600;">
                    <i class="fas fa-brain"></i> ${item.model || 'AI Model'}
                </span>
                <span style="font-size:11px; color:var(--secondary-text); margin-left:auto;">
                    <i class="far fa-clock"></i> ${formattedDate}
                </span>
            </div>
            ${snippet ? `<p style="font-size:13px; color:var(--secondary-text); margin:0; line-height:1.4;">${snippet}</p>` : ''}
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
    const accountId = localStorage.getItem("accountId") || sessionStorage.getItem("accountId");
    if (!isLoggedIn || !accountId) return;
    if (!confirm("Are you sure you want to delete this consultation?")) return;

    fetch(API_BASE + "/deletechat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            history_id: historyId,
            account_id: accountId
        })
    })
        .then(r => r.json())
        .then(() => {
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
    const btn = document.getElementById("send-otp-btn") || e.target.querySelector("button[type='submit']");
    const origText = btn ? btn.innerHTML : "Send OTP Code";

    if (!email) {
        alert("Please enter your registered email address.");
        return;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending OTP...';
    }

    try {
        let res = null;
        let data = null;

        try {
            res = await fastFetch(API_BASE + "/forgotpassword", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            }, getApiTimeoutMs());
            data = await res.json().catch(() => null);
        } catch (_) {}

        if (!res && API_BASE !== CLOUD_API) {
            try {
                const cloudRes = await fastFetch(CLOUD_API + "/forgotpassword", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email })
                }, 35000);
                data = await cloudRes.json().catch(() => null);
                res = cloudRes;
                if (cloudRes.ok) API_BASE = CLOUD_API;
            } catch (_) {}
        }

        if (res && res.ok && data && data.success && data.email_sent) {
            sessionStorage.removeItem("storedOtp");
            sessionStorage.setItem("storedAccountId", data.account_id);
            closeSendOtpModal();
            openResetPasswordModal();

            const banner = document.getElementById("otp-delivery-banner");
            const otpInput = document.getElementById("otp");
            if (otpInput) otpInput.value = "";

            if (banner) {
                banner.style.display = "block";
                banner.style.background = "rgba(16, 185, 129, 0.14)";
                banner.style.border = "1px solid #10b981";
                banner.style.color = "#10b981";
                banner.innerHTML = `<i class="fas fa-envelope-open-text"></i> <strong>OTP Sent!</strong> ${data.message}`;
            }
        } else {
            alert((data && data.message) || "Failed to send OTP email. Please check email SMTP configuration and try again.");
        }
    } catch (_) {
        alert("Error connecting to server. Please try again.");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origText;
        }
    }
}

function openResetPasswordModal() { openModal("reset-password-modal"); }
function closeResetPasswordModal() { closeModal("reset-password-modal"); }

async function handleResetPassword(e) {
    e.preventDefault();
    const otp = document.getElementById("otp").value.trim();
    const newPassword = document.getElementById("new-password").value.trim();
    const confirmPassword = document.getElementById("confirm-password").value.trim();
    const btn = document.getElementById("reset-password-btn") || e.target.querySelector("button[type='submit']");
    const origText = btn ? btn.innerHTML : "Reset Password";

    if (!otp || otp.length !== 6) {
        alert("Please enter the 6-digit OTP.");
        return;
    }

    if (newPassword.length < 6) {
        alert("New password must be at least 6 characters long.");
        return;
    }

    if (newPassword !== confirmPassword) {
        alert("Passwords do not match!");
        return;
    }

    const storedOtp = sessionStorage.getItem("storedOtp");
    if (storedOtp && otp !== storedOtp) {
        alert("Incorrect OTP. Please check and try again.");
        return;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';
    }

    try {
        const res = await fastFetch(API_BASE + "/resetpassword", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                account_id: sessionStorage.getItem("storedAccountId"),
                otp: otp,
                new_password: newPassword
            })
        }, getApiTimeoutMs());
        const data = await res.json().catch(() => null);
        if (res.ok && data && data.success) {
            alert("Password reset successfully! Please login with your new password.");
            sessionStorage.removeItem("storedOtp");
            sessionStorage.removeItem("storedAccountId");
            const form = document.getElementById("reset-password-form");
            if (form) form.reset();
            const banner = document.getElementById("otp-delivery-banner");
            if (banner) banner.style.display = "none";
            closeResetPasswordModal();
            openLoginModal();
        } else {
            alert((data && data.message) || "Failed to reset password.");
        }
    } catch (_) {
        alert("Server error resetting password. Please try again.");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origText;
        }
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
