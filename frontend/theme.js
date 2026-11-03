// ==============================================================================
// Niramaya Theme Manager (Unified Dark/Light Mode Across All Pages)
// ==============================================================================

(function () {
    // 1. Immediately apply saved theme to prevent FOUC (flash of unstyled content)
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.classList.remove('dark', 'light');
    document.documentElement.classList.add(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);

    function updateThemeUI(theme) {
        // Update all toggle buttons
        const toggleButtons = document.querySelectorAll('#theme-toggle, .theme-toggle-btn');
        toggleButtons.forEach(btn => {
            btn.innerHTML = (theme === 'dark')
                ? '<i class="fas fa-sun"></i>'
                : '<i class="fas fa-moon"></i>';
            btn.setAttribute('aria-label', `Current theme: ${theme}. Click to switch.`);
            btn.setAttribute('title', (theme === 'dark') ? 'Switch to Light Mode' : 'Switch to Dark Mode');
        });

        // Update all logo images
        const logoImgs = document.querySelectorAll('#logo-img, .logo img');
        logoImgs.forEach(img => {
            img.src = (theme === 'dark') ? 'N-dark.png' : 'N-light.png';
        });
    }

    function toggleTheme() {
        const currentTheme = localStorage.getItem('theme') || 'dark';
        const newTheme = (currentTheme === 'dark') ? 'light' : 'dark';

        localStorage.setItem('theme', newTheme);
        document.documentElement.classList.remove('dark', 'light');
        document.documentElement.classList.add(newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);

        updateThemeUI(newTheme);
    }

    // Attach listeners and sync UI when DOM is ready
    function initTheme() {
        const currentTheme = localStorage.getItem('theme') || 'dark';
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

    // Expose helper globally
    window.NiramayaTheme = {
        getTheme: () => localStorage.getItem('theme') || 'dark',
        setTheme: (t) => {
            localStorage.setItem('theme', t);
            document.documentElement.classList.remove('dark', 'light');
            document.documentElement.classList.add(t);
            document.documentElement.setAttribute('data-theme', t);
            updateThemeUI(t);
        },
        toggleTheme: toggleTheme
    };
})();
