// ==============================================================================
// Niramaya Theme Manager (Unified Dark/Light Mode Across All Pages)
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
        // Update all toggle buttons
        const toggleButtons = document.querySelectorAll('#theme-toggle, .theme-toggle-btn');
        toggleButtons.forEach(btn => {
            btn.innerHTML = (resolved === 'dark')
                ? '<i class="fas fa-sun"></i>'
                : '<i class="fas fa-moon"></i>';
            btn.setAttribute('aria-label', `Current theme: ${resolved}. Click to switch.`);
            btn.setAttribute('title', (resolved === 'dark') ? 'Switch to Light Mode' : 'Switch to Dark Mode');
        });

        // Update all logo images
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

    // Attach listeners and sync UI when DOM is ready
    function initTheme() {
        const currentTheme = applyThemeClass(localStorage.getItem('theme') || savedTheme);
        updateThemeUI(currentTheme);

        const toggleButtons = document.querySelectorAll('#theme-toggle, .theme-toggle-btn');
        toggleButtons.forEach(btn => {
            btn.onclick = function (e) {
                e.preventDefault();
                toggleTheme();
            };
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }

    // Sync theme across tabs/windows and browser back/forward cache (bfcache)
    window.addEventListener('storage', (e) => {
        if (e.key === 'theme' && e.newValue) {
            const resolved = applyThemeClass(e.newValue);
            updateThemeUI(resolved);
        }
    });

    window.addEventListener('pageshow', () => {
        const resolved = applyThemeClass(localStorage.getItem('theme') || 'dark');
        updateThemeUI(resolved);
    });

    // Expose helper globally
    window.NiramayaTheme = {
        getTheme: () => localStorage.getItem('theme') || 'dark',
        setTheme: setTheme,
        toggleTheme: toggleTheme
    };
})();
