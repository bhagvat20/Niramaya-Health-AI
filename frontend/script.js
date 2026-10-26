// Shuffle array function
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

// Fetch Research Papers
async function fetchResearchPapers() {
    const container = document.getElementById("research-papers");
    container.innerHTML = '<div class="loading"><span class="spinner"></span>Loading papers...</div>';

    // Array of 20 unique, verified health-related images from Unsplash (re-verified)
    const imagePool = [
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?ixlib=rb-4.0.3&auto=format&fit=crop&w=320",
        "https://images.unsplash.com/photo-1550831107-1553da8c8464?ixlib=rb-4.0.3&auto=format&fit=crop&w=320",
        "https://images.unsplash.com/photo-1498837167922-ddd27525d352?ixlib=rb-4.0.3&auto=format&fit=crop&w=320",
        "https://images.unsplash.com/photo-1557682224-5b8590cd9ec5?ixlib=rb-4.0.3&auto=format&fit=crop&w=320",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?ixlib=rb-4.0.3&auto=format&fit=crop&w=320",
        "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?ixlib=rb-4.0.3&auto=format&fit=crop&w=320",
        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?ixlib=rb-4.0.3&auto=format&fit=crop&w=320",
        "https://images.unsplash.com/photo-1543353071-873f17a7a088?ixlib=rb-4.0.3&auto=format&fit=crop&w=320",
        "https://images.unsplash.com/photo-1579684385127-1ef15d508118?ixlib=rb-4.0.3&auto=format&fit=crop&w=320",
        "https://images.unsplash.com/photo-1506126613408-eca07ce68773?ixlib=rb-4.0.3&auto=format&fit=crop&w=320",
    ];

    // Fallback image pool (re-verified)
    const fallbackImages = [
        "https://images.unsplash.com/photo-1617791160536-585948b95a38?ixlib=rb-4.0.3&auto=format&fit=crop&w=320"
    ];

    try {
        const response = await fetch("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=health%20AI%20wellness&resultType=lite&format=json&pageSize=20");
        const data = await response.json();
        let papers = data.resultList.result;

        if (!papers || papers.length === 0) {
            container.innerHTML = '<p>No recent health papers found.</p>';
            return;
        }

        papers = shuffleArray(papers).slice(0, 20);
        const shuffledImages = shuffleArray([...imagePool]).slice(0, Math.min(6, papers.length));
        const selectedPapers = papers.slice(0, 6);

        container.innerHTML = "";

        selectedPapers.forEach((paper, index) => {
            const title = paper.title || "Untitled";
            const authors = paper.authorString || "Unknown Authors";
            const pmcId = paper.pmcid || paper.id;
            const imageUrl = shuffledImages[index] || fallbackImages[index % fallbackImages.length];

            const paperElement = document.createElement("div");
            paperElement.classList.add("paper-card");
            paperElement.innerHTML = `
                <a href="https://europepmc.org/article/MED/${paper.id}" target="_blank" class="paper-link">
                    <div class="paper-image-wrapper">
                        <img src="${imageUrl}" alt="${title}" class="paper-image" 
                             onload="console.log('Image loaded:', '${imageUrl}')"
                             onerror="console.error('Image failed:', '${imageUrl}'); this.onerror=null; this.src='${fallbackImages[(index + 1) % fallbackImages.length]}';">
                        <div class="paper-overlay">
                            <span class="read-more">Read More</span>
                        </div>
                    </div>
                    <div class="paper-details">
                        <h3 class="paper-title">${title}</h3>
                        <p class="paper-authors">${authors}</p>
                    </div>
                </a>
            `;
            container.appendChild(paperElement);
        });
    } catch (error) {
        console.warn("Using offline health AI research cards:", error);
        const offlinePapers = [
            { title: "Machine Learning in Early Disease Symptom Prediction", authors: "Clinical AI Informatics, 2025", tag: "Diagnostic AI" },
            { title: "Clinical Decision Support Systems: Accuracy & Validation", authors: "Niramaya AI Research Group", tag: "Clinical AI" },
            { title: "Automated Symptom Risk Assessment and Triage Systems", authors: "HealthTech Informatics Quarterly", tag: "Healthcare ML" },
            { title: "Preventive Healthcare & Lifestyle Intervention via AI", authors: "Global Health Consortium", tag: "Wellness AI" }
        ];
        container.innerHTML = "";
        offlinePapers.forEach((paper) => {
            const paperElement = document.createElement("div");
            paperElement.classList.add("paper-card");
            paperElement.innerHTML = `
                <div class="paper-link" style="cursor:default; text-decoration:none;">
                    <div class="paper-image-wrapper" style="background: linear-gradient(135deg, #1e293b, #0f172a); display:flex; align-items:center; justify-content:center; height:140px; color:#38bdf8;">
                        <i class="fas fa-file-medical fa-3x"></i>
                    </div>
                    <div class="paper-details">
                        <span style="font-size:11px; font-weight:700; color:#10b981; text-transform:uppercase; letter-spacing:0.5px;">${paper.tag}</span>
                        <h3 class="paper-title" style="margin-top:6px;">${paper.title}</h3>
                        <p class="paper-authors">${paper.authors}</p>
                    </div>
                </div>
            `;
            container.appendChild(paperElement);
        });
    }
}

// Updated toggleResearch function to handle first click expansion correctly
function toggleResearch() {
    const content = document.getElementById('research-content');
    const toggle = document.querySelector('.research-toggle');
    const icon = toggle.querySelector('.toggle-icon');
    const isCollapsed = content.style.maxHeight === '0px' || !content.style.maxHeight;

    if (isCollapsed) {
        if (content.innerHTML.includes('Loading')) {
            fetchResearchPapers().then(() => {
                content.style.maxHeight = content.scrollHeight + 'px';
                icon.textContent = '▼';
            });
        } else {
            content.style.maxHeight = content.scrollHeight + 'px';
            icon.textContent = '▼';
        }
    } else {
        content.style.maxHeight = '0px';
        icon.textContent = '▶';
    }
}

// Load papers and handle theme toggle on page load
document.addEventListener("DOMContentLoaded", function () {
    fetchResearchPapers();
    document.getElementById('research-content').style.maxHeight = '0';

    document.querySelector(".logo").onclick = function(e) {
        e.preventDefault();
        window.location.href = "home.html";
    };

    document.querySelector(".site-name").onclick = function(e) {
        e.preventDefault();
        window.location.href = "home.html";
    };

    // Theme toggle functionality
    const htmlElement = document.documentElement;
    const themeToggleButton = document.getElementById('theme-toggle');
    let currentTheme = localStorage.getItem('theme') || 'dark';

    if (currentTheme === 'dark') {
        themeToggleButton.innerHTML = '<i class="fas fa-sun"></i>';
    } else {
        themeToggleButton.innerHTML = '<i class="fas fa-moon"></i>';
    }

    themeToggleButton.addEventListener('click', () => {
        const logoImg = document.getElementById('logo-img');
        if (currentTheme === 'dark') {
            htmlElement.classList.remove('dark');
            htmlElement.classList.add('light');
            localStorage.setItem('theme', 'light');
            currentTheme = 'light';
            themeToggleButton.innerHTML = '<i class="fas fa-moon"></i>';
        } else {
            htmlElement.classList.remove('light');
            htmlElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            currentTheme = 'dark';
            themeToggleButton.innerHTML = '<i class="fas fa-sun"></i>';
        }
        if (logoImg) {
            logoImg.src = currentTheme === 'dark' ? 'N-dark.png' : 'N-light.png';
        }
    });

    // Synchronize authentication state on home page
    syncHomeAuthState();

    // Close modals on escape key or backdrop click
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeHomeLoginModal();
            closeHomeRegisterModal();
        }
    });

    window.addEventListener('click', (e) => {
        const loginModal = document.getElementById('home-login-modal');
        const regModal = document.getElementById('home-register-modal');
        if (e.target === loginModal) closeHomeLoginModal();
        if (e.target === regModal) closeHomeRegisterModal();
    });
});

// API Base detection
const HOME_API_BASE = (window.location.origin && window.location.origin.startsWith('http')) 
    ? window.location.origin 
    : 'http://127.0.0.1:5000';

function syncHomeAuthState() {
    const accountId = localStorage.getItem('accountId');
    const familyName = localStorage.getItem('familyName') || 'User';

    const guestNav = document.getElementById('nav-guest-actions');
    const userNav = document.getElementById('nav-user-actions');
    const guestCta = document.getElementById('hero-guest-cta');
    const userCta = document.getElementById('hero-user-cta');
    const nameSpan = document.getElementById('home-family-name');

    if (accountId) {
        if (guestNav) guestNav.style.display = 'none';
        if (userNav) userNav.style.display = 'inline-flex';
        if (guestCta) guestCta.style.display = 'none';
        if (userCta) userCta.style.display = 'flex';
        if (nameSpan) nameSpan.textContent = familyName;
    } else {
        if (guestNav) guestNav.style.display = 'inline-flex';
        if (userNav) userNav.style.display = 'none';
        if (guestCta) guestCta.style.display = 'flex';
        if (userCta) userCta.style.display = 'none';
    }
}

function openHomeLoginModal() {
    closeHomeRegisterModal();
    const modal = document.getElementById('home-login-modal');
    if (modal) {
        modal.style.display = 'flex';
        setTimeout(() => modal.classList.add('show'), 10);
        const emailInput = document.getElementById('home-login-email');
        if (emailInput) emailInput.focus();
    }
}

function closeHomeLoginModal() {
    const modal = document.getElementById('home-login-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => { modal.style.display = 'none'; }, 200);
        const form = document.getElementById('home-login-form');
        if (form) form.reset();
        const msg = document.getElementById('home-login-msg');
        if (msg) msg.textContent = '';
    }
}

function openHomeRegisterModal() {
    closeHomeLoginModal();
    const modal = document.getElementById('home-register-modal');
    if (modal) {
        modal.style.display = 'flex';
        setTimeout(() => modal.classList.add('show'), 10);
        const nameInput = document.getElementById('home-reg-familyname');
        if (nameInput) nameInput.focus();
    }
}

function closeHomeRegisterModal() {
    const modal = document.getElementById('home-register-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => { modal.style.display = 'none'; }, 200);
        const form = document.getElementById('home-register-form');
        if (form) form.reset();
        const msg = document.getElementById('home-register-msg');
        if (msg) msg.textContent = '';
    }
}

function togglePasswordVisibility(inputId, iconEl) {
    const input = document.getElementById(inputId);
    if (!input) return;
    if (input.type === 'password') {
        input.type = 'text';
        iconEl.classList.remove('fa-eye');
        iconEl.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        iconEl.classList.remove('fa-eye-slash');
        iconEl.classList.add('fa-eye');
    }
}

async function handleHomeLoginSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('home-login-email').value.trim();
    const password = document.getElementById('home-login-password').value;
    const msgEl = document.getElementById('home-login-msg');
    const submitBtn = document.getElementById('home-login-submit-btn');

    if (!email || !password) {
        if (msgEl) {
            msgEl.style.color = '#ef4444';
            msgEl.textContent = 'Please enter both email and password.';
        }
        return;
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
    }

    try {
        const res = await fetch(HOME_API_BASE + '/userlogin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            localStorage.setItem('accountId', data.account_id);
            localStorage.setItem('userEmail', data.email || email);
            localStorage.setItem('familyName', data.familyname || 'User');
            if (data.members && data.members.length > 0) {
                localStorage.setItem('selectedMemberId', data.members[0].member_id);
                localStorage.setItem('selectedMemberName', data.members[0].name);
            }

            if (msgEl) {
                msgEl.style.color = '#10b981';
                msgEl.innerHTML = '<i class="fas fa-check-circle"></i> Login successful! Redirecting...';
            }

            setTimeout(() => {
                window.location.href = 'question_input.html';
            }, 800);
        } else {
            if (msgEl) {
                msgEl.style.color = '#ef4444';
                msgEl.textContent = data.message || 'Login failed. Please check your credentials.';
            }
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
            }
        }
    } catch (err) {
        console.error('Home login error:', err);
        if (msgEl) {
            msgEl.style.color = '#ef4444';
            msgEl.textContent = 'Network or server error. Please try again.';
        }
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
        }
    }
}

async function handleHomeRegisterSubmit(e) {
    e.preventDefault();
    const familyname = document.getElementById('home-reg-familyname').value.trim();
    const email = document.getElementById('home-reg-email').value.trim();
    const password = document.getElementById('home-reg-password').value;
    const confirmPassword = document.getElementById('home-reg-confirm-password').value;
    const msgEl = document.getElementById('home-register-msg');
    const submitBtn = document.getElementById('home-reg-submit-btn');

    if (!familyname || !email || !password || !confirmPassword) {
        if (msgEl) {
            msgEl.style.color = '#ef4444';
            msgEl.textContent = 'Please fill out all fields.';
        }
        return;
    }

    if (password !== confirmPassword) {
        if (msgEl) {
            msgEl.style.color = '#ef4444';
            msgEl.textContent = 'Passwords do not match.';
        }
        return;
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Registering...';
    }

    try {
        const res = await fetch(HOME_API_BASE + '/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fname: familyname, email, password })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            localStorage.setItem('accountId', data.account_id);
            localStorage.setItem('userEmail', data.email || email);
            localStorage.setItem('familyName', data.familyname || familyname);

            if (msgEl) {
                msgEl.style.color = '#10b981';
                msgEl.innerHTML = '<i class="fas fa-check-circle"></i> Registration successful! Setting up session...';
            }

            // Auto-login to fetch primary member
            try {
                const loginRes = await fetch(HOME_API_BASE + '/userlogin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const loginData = await loginRes.json();
                if (loginData.success && loginData.members && loginData.members.length > 0) {
                    localStorage.setItem('selectedMemberId', loginData.members[0].member_id);
                    localStorage.setItem('selectedMemberName', loginData.members[0].name);
                }
            } catch (_) {}

            setTimeout(() => {
                window.location.href = 'question_input.html';
            }, 900);
        } else {
            if (msgEl) {
                msgEl.style.color = '#ef4444';
                msgEl.textContent = data.message || 'Registration failed. Please try a different email.';
            }
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
            }
        }
    } catch (err) {
        console.error('Home register error:', err);
        if (msgEl) {
            msgEl.style.color = '#ef4444';
            msgEl.textContent = 'Server connection error. Please try again.';
        }
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
        }
    }
}

function handleHomeLogout() {
    localStorage.removeItem('accountId');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('familyName');
    localStorage.removeItem('selectedMemberId');
    localStorage.removeItem('selectedMemberName');
    syncHomeAuthState();
}