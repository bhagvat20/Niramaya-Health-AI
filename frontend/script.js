// ==============================================================================
// Niramaya Home Script - Latest Research Papers & Navigation
// ==============================================================================

const CURATED_RESEARCH_PAPERS = [
    {
        title: "BioGPT: Generative Pre-trained Transformer for Biomedical Text Generation and Mining",
        authors: "Luo R, Sun L, Xia Y, Qin T, Zhang S, Poon H, Liu TY",
        journal: "Briefings in Bioinformatics",
        year: "2022",
        url: "https://pubmed.ncbi.nlm.nih.gov/36156661/",
        image: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=600&q=80",
        tag: "Biomedical AI • 2022"
    },
    {
        title: "Large Language Models Encode Clinical Knowledge",
        authors: "Singhal K, Azizi S, Tu T, Mahdavi SS, Wei J, Chung HW, et al.",
        journal: "Nature",
        year: "2023",
        url: "https://pubmed.ncbi.nlm.nih.gov/37438534/",
        image: "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?auto=format&fit=crop&w=600&q=80",
        tag: "Nature • 2023"
    },
    {
        title: "Evaluation of Symptom Checkers for Self Diagnosis and Triage: Audit Study",
        authors: "Semigran HL, Linder JA, Gidengil C, Mehrotra A",
        journal: "BMJ",
        year: "2015",
        url: "https://pubmed.ncbi.nlm.nih.gov/26157077/",
        image: "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=600&q=80",
        tag: "BMJ • 2015"
    },
    {
        title: "High-Performance Medicine: The Convergence of Human and Artificial Intelligence",
        authors: "Topol EJ",
        journal: "Nature Medicine",
        year: "2019",
        url: "https://pubmed.ncbi.nlm.nih.gov/30617339/",
        image: "https://images.unsplash.com/photo-1550831107-1553da8c8464?auto=format&fit=crop&w=600&q=80",
        tag: "Nature Medicine • 2019"
    },
    {
        title: "A Guide to Deep Learning in Healthcare",
        authors: "Esteva A, Robicquet A, Ramsundar B, Kuleshov V, DePristo M, et al.",
        journal: "Nature Medicine",
        year: "2019",
        url: "https://pubmed.ncbi.nlm.nih.gov/30617335/",
        image: "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=600&q=80",
        tag: "Healthcare ML • 2019"
    },
    {
        title: "Artificial Intelligence in Clinical Decision Support: Challenges and Opportunities",
        authors: "Sutton RT, Pincock D, Baumgart DC, Sadowski DC, Fedorak RN, Kroeker KI",
        journal: "NPJ Digital Medicine",
        year: "2020",
        url: "https://pubmed.ncbi.nlm.nih.gov/32047862/",
        image: "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=600&q=80",
        tag: "NPJ Digital Medicine • 2020"
    }
];

let researchLoaded = false;

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text || "";
    return div.innerHTML;
}

function renderResearchCards(papers) {
    const container = document.getElementById("research-papers");
    if (!container) return;

    const fallbackImg = "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=600&q=80";
    container.innerHTML = "";

    papers.slice(0, 6).forEach((paper) => {
        const title = escapeHtml(paper.title || "Untitled Research Paper");
        const authors = escapeHtml(paper.authors || "Clinical Research Group");
        const tag = escapeHtml(paper.tag || `${paper.journal || "Research"} • ${paper.year || "Latest"}`);
        const url = paper.url || "https://europepmc.org/";
        const imgUrl = paper.image || fallbackImg;

        const card = document.createElement("div");
        card.className = "paper-card";
        card.innerHTML = `
            <a href="${url}" target="_blank" rel="noopener noreferrer" class="paper-link">
                <div class="paper-image-wrapper">
                    <img src="${imgUrl}" alt="${title}" class="paper-image"
                         onerror="this.onerror=null; this.parentElement.innerHTML='<div style=\\'background:linear-gradient(135deg,#1e293b,#0f172a);display:flex;align-items:center;justify-content:center;height:100%;color:#38bdf8;\\'><i class=\\'fas fa-file-medical fa-3x\\'></i></div>';">
                    <div class="paper-overlay">
                        <span class="read-more"><i class="fas fa-external-link-alt"></i> Read Paper</span>
                    </div>
                </div>
                <div class="paper-details">
                    <span class="paper-tag">${tag}</span>
                    <h3 class="paper-title">${title}</h3>
                    <p class="paper-authors">${authors}</p>
                    <span class="paper-read-cta">Open Full Study <i class="fas fa-arrow-right"></i></span>
                </div>
            </a>
        `;
        container.appendChild(card);
    });

    researchLoaded = true;
}

// Fetch Live Research Papers (via backend proxy -> direct EuropePMC -> verified PubMed fallback)
async function fetchResearchPapers() {
    const container = document.getElementById("research-papers");
    if (!container) return;

    container.innerHTML = '<div class="loading" style="grid-column:1/-1; text-align:center; padding:24px;"><i class="fas fa-spinner fa-spin"></i> Loading latest peer-reviewed health AI papers...</div>';

    const apiOrigin = (window.location.origin && window.location.origin.startsWith("http"))
        ? window.location.origin
        : "http://127.0.0.1:5000";

    // 1. Try Niramaya backend proxy (/api/research-papers)
    try {
        const controller = new AbortController();
        const tid = setTimeout(() => controller.abort(), 10000);
        const res = await fetch(`${apiOrigin}/api/research-papers`, { signal: controller.signal });
        clearTimeout(tid);
        if (res.ok) {
            const data = await res.json();
            if (data && data.success && Array.isArray(data.papers) && data.papers.length > 0) {
                renderResearchCards(data.papers);
                return;
            }
        }
    } catch (_) {}

    // 2. Fallback: Direct EuropePMC REST API from browser (generous 8s timeout)
    try {
        const controller = new AbortController();
        const tid = setTimeout(() => controller.abort(), 8000);
        const res = await fetch(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=(%22artificial+intelligence%22+AND+healthcare)&resultType=lite&format=json&pageSize=8&sort=P_PDATE_D+desc",
            { signal: controller.signal }
        );
        clearTimeout(tid);
        if (res.ok) {
            const data = await res.json();
            const results = (data.resultList && data.resultList.result) || [];
            const mapped = results.slice(0, 6).map((p, i) => ({
                title: String(p.title || "Untitled").replace(/<[^>]+>/g, ""),
                authors: p.authorString || "Clinical Research Team",
                journal: p.journalTitle || "Europe PMC",
                year: p.pubYear || "Latest",
                url: p.pmcid
                    ? `https://europepmc.org/article/PMC/${p.pmcid}`
                    : `https://europepmc.org/article/${p.source || "MED"}/${p.id}`,
                image: CURATED_RESEARCH_PAPERS[i % CURATED_RESEARCH_PAPERS.length].image,
                tag: `${p.journalTitle || "Europe PMC"} • ${p.pubYear || "Latest"}`
            }));
            if (mapped.length > 0) {
                renderResearchCards(mapped);
                return;
            }
        }
    } catch (_) {}

    // 3. Verified Clickable PubMed Fallback Papers (always works even offline)
    renderResearchCards(CURATED_RESEARCH_PAPERS);
}

// Expand / collapse Latest Research Papers without clipping bottom cards
function toggleResearch() {
    const content = document.getElementById("research-content");
    const toggle = document.querySelector(".research-toggle");
    if (!content || !toggle) return;

    const icon = toggle.querySelector(".toggle-icon");
    const isExpanded = content.classList.contains("expanded");

    if (!isExpanded) {
        content.classList.add("expanded");
        content.style.maxHeight = "none";
        if (icon) icon.textContent = "▼";
        if (!researchLoaded) {
            fetchResearchPapers();
        }
    } else {
        content.classList.remove("expanded");
        content.style.maxHeight = "0px";
        if (icon) icon.textContent = "▶";
    }
}

// Load papers on page load (theme toggle is managed centrally by theme.js)
document.addEventListener("DOMContentLoaded", function () {
    const papersContainer = document.getElementById("research-papers");
    const researchContent = document.getElementById("research-content");
    if (papersContainer) {
        fetchResearchPapers();
    }
    if (researchContent) {
        researchContent.style.maxHeight = "0px";
        researchContent.classList.remove("expanded");
    }

    const logoEl = document.querySelector(".logo");
    if (logoEl) {
        logoEl.onclick = function (e) {
            e.preventDefault();
            window.location.href = "home.html";
        };
    }

    const siteNameEl = document.querySelector(".site-name");
    if (siteNameEl) {
        siteNameEl.onclick = function (e) {
            e.preventDefault();
            window.location.href = "home.html";
        };
    }
});
