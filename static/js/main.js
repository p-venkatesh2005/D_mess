/**
 * Dwaraka Mess Management System
 * Main JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {

    // ─── SIDEBAR TOGGLE ───────────────────────────────────────────────
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', (e) => {
            e.preventDefault();
            sidebar.classList.toggle('toggled');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && 
                !sidebar.contains(e.target) && 
                !sidebarToggle.contains(e.target) && 
                sidebar.classList.contains('toggled')) {
                sidebar.classList.remove('toggled');
            }
        });
    }

    // ─── LIVE CLOCK ───────────────────────────────────────────────────
    const liveTimeEl = document.getElementById('live-time');
    if (liveTimeEl) {
        const updateTime = () => {
            const now = new Date();
            liveTimeEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        };
        updateTime();
        setInterval(updateTime, 1000);
    }

    // ─── AUTO-DISMISS FLASH MESSAGES ──────────────────────────────────
    const flashMessages = document.querySelectorAll('.flash-msg');
    flashMessages.forEach((msg) => {
        // Auto-close success and info messages after 4 seconds
        if (msg.classList.contains('alert-success') || msg.classList.contains('alert-info')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(msg);
                bsAlert.close();
            }, 4000);
        }
    });

    // ─── ACTIVE NAV LINK HIGHLIGHT INTUITION ──────────────────────────
    // Scroll sidebar into view if active item is hidden
    const activeNav = document.querySelector('.sidebar-nav li a.active');
    if (activeNav) {
        activeNav.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

});
