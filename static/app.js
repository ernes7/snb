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
        var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (!reduced) {
            var cards = document.querySelectorAll('.card, .game-card, .analyst-chip, .sched-row');
            cards.forEach(function (card, i) {
                card.style.animationDelay = (i * 30) + 'ms';
            });
        }
        animateCounters(reduced);
    });

    /* ── Animated stat counters ──
       Parses data-animate target, counts up from 0 over ~600ms with ease-out.
       Preserves decimal count and leading-dot formatting (e.g. ".333" stays ".333"). */
    function animateCounters(reduced) {
        var nodes = document.querySelectorAll('[data-animate]');
        nodes.forEach(function (el) {
            var raw = el.getAttribute('data-animate').trim();
            if (!/^-?\.?\d+(\.\d+)?$/.test(raw)) { el.textContent = raw; return; }
            var target = parseFloat(raw);
            if (isNaN(target)) { el.textContent = raw; return; }
            var dotIdx = raw.indexOf('.');
            var decimals = dotIdx === -1 ? 0 : raw.length - dotIdx - 1;
            var leadingDot = raw.charAt(0) === '.' || raw.substring(0, 2) === '-.';
            function fmt(v) {
                var s = v.toFixed(decimals);
                if (leadingDot) {
                    if (s.charAt(0) === '0') s = s.substring(1);
                    else if (s.substring(0, 2) === '-0') s = '-' + s.substring(2);
                }
                return s;
            }
            if (reduced || target === 0) { el.textContent = fmt(target); return; }
            var duration = 600;
            var start = null;
            el.textContent = fmt(0);
            function step(ts) {
                if (start === null) start = ts;
                var t = Math.min(1, (ts - start) / duration);
                var eased = 1 - Math.pow(1 - t, 3);
                el.textContent = fmt(target * eased);
                if (t < 1) requestAnimationFrame(step);
                else el.textContent = fmt(target);
            }
            requestAnimationFrame(step);
        });
    }

    /* ── Reusable tabs ──
       Driven by the `tab_group` Jinja macro in templates/components/tabs.html.
       Any `[data-tabs]` container with `.toggle-btn[data-tab-target]` buttons
       + matching `.tab-pane[id]` panes is picked up automatically.
    */
    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('[data-tabs]').forEach(function (root) {
            var btns = root.querySelectorAll('.toggle-btn[data-tab-target]');
            btns.forEach(function (btn) {
                if (btn.disabled) return;
                btn.addEventListener('click', function () {
                    var targetId = btn.getAttribute('data-tab-target');
                    btns.forEach(function (b) {
                        var active = b === btn;
                        b.setAttribute('aria-selected', active ? 'true' : 'false');
                        b.classList.toggle('active', active);
                    });
                    root.querySelectorAll('.tab-pane').forEach(function (pane) {
                        pane.hidden = pane.id !== targetId;
                    });
                });
            });
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
