/**
 * SKYsense AI - Global Application JavaScript
 * Master's Degree Final Project Demonstration Grade
 */

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 1. Theme Controller (Dark / Light Theme Toggle)
    // -------------------------------------------------------------
    const htmlElement = document.documentElement;
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const mobileThemeToggleBtn = document.getElementById('mobile-theme-toggle-btn');
    const themeIconDark = document.getElementById('theme-icon-dark');
    const themeIconLight = document.getElementById('theme-icon-light');
    const mobileThemeIconDark = document.getElementById('mobile-theme-icon-dark');
    const mobileThemeIconLight = document.getElementById('mobile-theme-icon-light');

    function applyTheme(theme) {
        const isLight = theme === 'light';
        if (isLight) {
            htmlElement.classList.remove('dark');
            htmlElement.classList.add('light');
            if (themeIconDark) themeIconDark.classList.remove('hidden');
            if (themeIconLight) themeIconLight.classList.add('hidden');
            if (mobileThemeIconDark) mobileThemeIconDark.classList.remove('hidden');
            if (mobileThemeIconLight) mobileThemeIconLight.classList.add('hidden');
            localStorage.setItem('skysense_theme', 'light');
        } else {
            htmlElement.classList.remove('light');
            htmlElement.classList.add('dark');
            if (themeIconDark) themeIconDark.classList.add('hidden');
            if (themeIconLight) themeIconLight.classList.remove('hidden');
            if (mobileThemeIconDark) mobileThemeIconDark.classList.add('hidden');
            if (mobileThemeIconLight) mobileThemeIconLight.classList.remove('hidden');
            localStorage.setItem('skysense_theme', 'dark');
        }

        const labelText = isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode';
        if (themeToggleBtn) {
            themeToggleBtn.setAttribute('title', labelText);
            themeToggleBtn.setAttribute('aria-label', labelText);
        }
        if (mobileThemeToggleBtn) {
            mobileThemeToggleBtn.setAttribute('title', labelText);
            mobileThemeToggleBtn.setAttribute('aria-label', labelText);
        }

        // Update Chart.js defaults if Chart is loaded
        if (window.Chart) {
            Chart.defaults.color = isLight ? '#475569' : '#94A3B8';
        }

        // Dispatch a custom event for any page-specific charts to refresh
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: isLight ? 'light' : 'dark' } }));
    }

    // Initialize from storage or default to dark
    const savedTheme = localStorage.getItem('skysense_theme') || 'dark';
    applyTheme(savedTheme);

    let lastToggleTime = 0;
    function toggleTheme() {
        const now = Date.now();
        if (now - lastToggleTime < 150) return; // Prevent double-trigger debounce
        lastToggleTime = now;

        const currentTheme = htmlElement.classList.contains('light') ? 'light' : 'dark';
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(nextTheme);
    }

    // Expose globally for inline button handlers or external calls
    window.toggleSkySenseTheme = toggleTheme;

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }
    if (mobileThemeToggleBtn) {
        mobileThemeToggleBtn.addEventListener('click', toggleTheme);
    }

    // -------------------------------------------------------------
    // 2. Mobile Navigation Menu Toggle with ARIA Attributes
    // -------------------------------------------------------------
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            const isExpanded = mobileMenuBtn.getAttribute('aria-expanded') === 'true';
            mobileMenuBtn.setAttribute('aria-expanded', !isExpanded);
            mobileMenu.classList.toggle('hidden');
        });

        // Close on ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !mobileMenu.classList.contains('hidden')) {
                mobileMenu.classList.add('hidden');
                mobileMenuBtn.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // -------------------------------------------------------------
    // 3. Auto-Dismiss Alert Toasts with Smooth Fade-Out
    // -------------------------------------------------------------
    const alerts = document.querySelectorAll('.alert-auto-dismiss');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1), transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-12px)';
            setTimeout(() => alert.remove(), 400);
        }, 5500);
    });
});
