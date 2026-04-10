/* Serie Nacional — Shared UI logic */

(function () {
    'use strict';

    /* ── Sidebar toggle ── */
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebar-overlay');
    var toggle = document.getElementById('sidebar-toggle');

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add('open');
        if (overlay) overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (toggle) toggle.addEventListener('click', openSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeSidebar();
    });

    /* ── Card stagger-in animation ── */
    document.addEventListener('DOMContentLoaded', function () {
        var cards = document.querySelectorAll('.card, .game-card, .analyst-chip, .sched-row');
        cards.forEach(function (card, i) {
            card.style.animationDelay = (i * 30) + 'ms';
        });
    });

    /* ── Reusable sortable table ── */
    window.initSortableTable = function (table) {
        if (!table) return;
        var sortState = {};

        table.querySelectorAll('th[data-sort]').forEach(function (th) {
            th.style.cursor = 'pointer';
            th.addEventListener('click', function () {
                var tbody = table.querySelector('tbody');
                var rows = Array.from(tbody.querySelectorAll('tr'));
                var idx = Array.from(th.parentNode.children).indexOf(th);
                var key = (table.id || 'tbl') + '-' + idx;
                var asc = sortState[key] = !sortState[key];

                // Update visual indicators
                table.querySelectorAll('th').forEach(function (h) {
                    h.classList.remove('sort-asc', 'sort-desc');
                    h.removeAttribute('aria-sort');
                });
                th.classList.add(asc ? 'sort-asc' : 'sort-desc');
                th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');

                var type = th.dataset.sort;
                rows.sort(function (a, b) {
                    var va = a.cells[idx].textContent.trim();
                    var vb = b.cells[idx].textContent.trim();
                    if (type === 'num') {
                        va = va === '' ? -999 : parseFloat(va);
                        vb = vb === '' ? -999 : parseFloat(vb);
                        return asc ? va - vb : vb - va;
                    }
                    return asc ? va.localeCompare(vb) : vb.localeCompare(va);
                });
                rows.forEach(function (r) { tbody.appendChild(r); });
            });
        });
    };
})();
