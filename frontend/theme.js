// ==============================================================================
// Niramaya Unified Theme & Persistent Auth Manager (All Pages)
// ==============================================================================

(function () {
    function applyThemeClass(theme) {
        const resolved = (theme === 'light') ? 'light' : 'dark';
        document.documentElement.classList.remove('dark', 'light');
        document.documentElement.classList.add(resolved);
        document.documentElement.setAttribute('data-theme', resolved);
        return resolved;
    }

    // 1. Immediately apply saved theme to prevent FOUC (flash of unstyled content)
    const savedTheme = applyThemeClass(localStorage.getItem('theme') || 'dark');

    function updateThemeUI(theme) {
        const resolved = (theme === 'light') ? 'light' : 'dark';
        const toggleButtons = document.querySelectorAll('#theme-toggle, .theme-toggle-btn');
        toggleButtons.forEach(btn => {
            btn.innerHTML = (resolved === 'dark')
                ? '<i class="fas fa-sun"></i>'
                : '<i class="fas fa-moon"></i>';
            btn.setAttribute('aria-label', `Current theme: ${resolved}. Click to switch.`);
            btn.setAttribute('title', (resolved === 'dark') ? 'Switch to Light Mode' : 'Switch to Dark Mode');
        });

        const logoImgs = document.querySelectorAll('#logo-img, .logo img');
        logoImgs.forEach(img => {
            img.src = (resolved === 'dark') ? 'N-dark.png' : 'N-light.png';
        });
    }

    function setTheme(theme) {
        const resolved = applyThemeClass(theme);
        localStorage.setItem('theme', resolved);
        updateThemeUI(resolved);
    }

    function toggleTheme() {
        const currentTheme = localStorage.getItem('theme') || 'dark';
        const newTheme = (currentTheme === 'dark') ? 'light' : 'dark';
        setTheme(newTheme);
    }

    // ==========================================================================
    // Persistent User Auth Helpers (Stays logged in until user clicks Logout)
    // ==========================================================================
    function isUserLoggedIn() {
        return localStorage.getItem('userLoggedIn') === 'true' && !!localStorage.getItem('accountId');
    }

    function getUserDisplayName() {
        const name =
            localStorage.getItem('selectedMemberName') ||
            localStorage.getItem('familyName') ||
            (localStorage.getItem('userEmail') ? localStorage.getItem('userEmail').split('@')[0] : '') ||
            'User';
        return name.trim() || 'User';
    }

    function logoutUserGlobal() {
        localStorage.removeItem('userLoggedIn');
        localStorage.removeItem('accountId');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('familyName');
        localStorage.removeItem('selectedMemberId');
        localStorage.removeItem('selectedMemberName');

        sessionStorage.removeItem('userLoggedIn');
        sessionStorage.removeItem('accountId');
        sessionStorage.removeItem('userEmail');
        sessionStorage.removeItem('familyName');
        sessionStorage.removeItem('activeMemberId');
        sessionStorage.removeItem('activeMemberName');

        // Refresh UI on current page
        syncAuthNavbar();
        if (window.location.pathname.endsWith('question_input.html')) {
            window.location.reload();
        }
    }

    function syncAuthNavbar() {
        // question_input.html manages its own modal buttons via question_input.js
        const isQuestionPage = window.location.pathname.endsWith('question_input.html');
        const isAdminPage = window.location.pathname.includes('admin_');
        if (isQuestionPage || isAdminPage) return;

        const loggedIn = isUserLoggedIn();
        const nav = document.querySelector('.nav');
        if (!nav) return;

        // Find Login & Register links on Home / About / Our Models / Wellness Tips
        const loginLinks = nav.querySelectorAll('a[href*="action=login"], #login-link');
        const regLinks = nav.querySelectorAll('a[href*="action=register"], #register-link');

        // Remove any previously injected auth nav items before re-syncing
        nav.querySelectorAll('.niramaya-auth-nav-item').forEach(el => el.remove());

        if (loggedIn) {
            loginLinks.forEach(a => { a.style.display = 'none'; });
            regLinks.forEach(a => { a.style.display = 'none'; });

            const displayName = getUserDisplayName();
            const adminLink = nav.querySelector('a[href*="admin_login.html"], #adminportal');

            // Create Symptom Checker / Profile link
            const chatLink = document.createElement('a');
            chatLink.href = 'question_input.html';
            chatLink.className = 'niramaya-auth-nav-item';
            chatLink.style.fontWeight = '600';
            chatLink.style.color = '#10b981';
            chatLink.innerHTML = `<i class="fas fa-user-check"></i> ${displayName}`;

            // Create Logout link
            const logoutLink = document.createElement('a');
            logoutLink.href = 'javascript:void(0)';
            logoutLink.className = 'niramaya-auth-nav-item';
            logoutLink.style.fontWeight = '600';
            logoutLink.style.color = '#ef4444';
            logoutLink.innerHTML = '<i class="fas fa-sign-out-alt"></i> Logout';
            logoutLink.onclick = function (e) {
                e.preventDefault();
                logoutUserGlobal();
            };

            if (adminLink) {
                nav.insertBefore(chatLink, adminLink);
                nav.insertBefore(logoutLink, adminLink);
            } else {
                nav.appendChild(chatLink);
                nav.appendChild(logoutLink);
            }

            // On home.html, logged-in users clicking "Try Niramaya Now" go straight to Symptom Checker
            const tryBtn = document.querySelector('.cta-buttons a[href="verify_human.html"]');
            if (tryBtn) {
                tryBtn.setAttribute('href', 'question_input.html');
            }
        } else {
            loginLinks.forEach(a => { a.style.display = ''; });
            regLinks.forEach(a => { a.style.display = ''; });

            const tryBtn = document.querySelector('.cta-buttons a[href="question_input.html"]');
            if (tryBtn) {
                tryBtn.setAttribute('href', 'verify_human.html');
            }
        }
    }

    // Attach listeners and sync UI when DOM is ready
    function initThemeAndAuth() {
        const currentTheme = applyThemeClass(localStorage.getItem('theme') || savedTheme);
        updateThemeUI(currentTheme);
        syncAuthNavbar();

        const toggleButtons = document.querySelectorAll('#theme-toggle, .theme-toggle-btn');
        toggleButtons.forEach(btn => {
            btn.onclick = function (e) {
                e.preventDefault();
                toggleTheme();
            };
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initThemeAndAuth);
    } else {
        initThemeAndAuth();
    }

    // Sync theme and login/logout state across tabs/windows and browser back/forward cache
    window.addEventListener('storage', (e) => {
        if (e.key === 'theme' && e.newValue) {
            const resolved = applyThemeClass(e.newValue);
            updateThemeUI(resolved);
        }
        if (e.key === 'userLoggedIn' || e.key === 'accountId' || e.key === 'familyName' || e.key === 'selectedMemberName') {
            syncAuthNavbar();
        }
    });

    window.addEventListener('pageshow', () => {
        const resolved = applyThemeClass(localStorage.getItem('theme') || 'dark');
        updateThemeUI(resolved);
        syncAuthNavbar();
    });

    // Expose helpers globally
    window.NiramayaTheme = {
        getTheme: () => localStorage.getItem('theme') || 'dark',
        setTheme: setTheme,
        toggleTheme: toggleTheme
    };
    window.NiramayaAuth = {
        isLoggedIn: isUserLoggedIn,
        getDisplayName: getUserDisplayName,
        logout: logoutUserGlobal,
        syncNavbar: syncAuthNavbar
    };
})();
