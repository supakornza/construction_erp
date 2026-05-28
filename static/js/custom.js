// ── Universal formset delete-row button ──────────────────────────────────────
function _formsetGetPrefix(row) {
    const el = row.querySelector('[name*="-"]');
    if (!el) return null;
    const parts = el.name.split('-');
    return parts.length >= 3 ? parts.slice(0, -2).join('-') : null;
}

function _formsetRenumber(tbody, prefix) {
    const re = new RegExp('(' + prefix.replace(/-/g, '\\-') + '-)\\d+(-)');
    tbody.querySelectorAll('tr.formset-row').forEach(function(row, idx) {
        row.querySelectorAll('[id],[name]').forEach(function(el) {
            if (el.id)   el.id   = el.id.replace(re,   '$1' + idx + '$2');
            if (el.name) el.name = el.name.replace(re, '$1' + idx + '$2');
        });
    });
    const totalEl = document.getElementById('id_' + prefix + '-TOTAL_FORMS');
    if (totalEl) totalEl.value = tbody.querySelectorAll('tr.formset-row').length;
}

document.addEventListener('click', function(e) {
    const btn = e.target.closest('.formset-delete-btn');
    if (!btn) return;
    const row = btn.closest('tr.formset-row');
    if (!row) return;
    const checkbox = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
    const idInput  = row.querySelector('input[name$="-id"]');
    const isMarked = btn.dataset.deleted === '1';

    if (isMarked) {
        if (checkbox) checkbox.checked = false;
        row.classList.remove('formset-row-deleted');
        btn.innerHTML = '<i class="fas fa-trash-alt"></i>';
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-outline-danger');
        delete btn.dataset.deleted;
    } else if (idInput && idInput.value) {
        if (checkbox) checkbox.checked = true;
        row.classList.add('formset-row-deleted');
        btn.innerHTML = '<i class="fas fa-undo fa-sm"></i>';
        btn.classList.remove('btn-outline-danger');
        btn.classList.add('btn-secondary');
        btn.dataset.deleted = '1';
        btn.title = 'Undo';
    } else {
        const tbody = row.closest('tbody');
        const prefix = _formsetGetPrefix(row);
        row.remove();
        if (tbody && prefix) _formsetRenumber(tbody, prefix);
    }
});
// ─────────────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert-dismissible').forEach(function (el) {
        setTimeout(function () {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(el);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ── Sidebar mobile toggle + backdrop ─────────────────────
    var toggler  = document.getElementById('sidebar-toggler');
    var sidebar  = document.getElementById('sidebar');
    var backdrop = document.getElementById('sidebar-backdrop');

    function openMobileSidebar() {
        if (sidebar)  sidebar.classList.add('show');
        if (backdrop) backdrop.classList.add('show');
        document.body.style.overflow = 'hidden';   // prevent background scroll
    }
    function closeMobileSidebar() {
        if (sidebar)  sidebar.classList.remove('show');
        if (backdrop) backdrop.classList.remove('show');
        document.body.style.overflow = '';
    }

    if (toggler) {
        toggler.addEventListener('click', function () {
            if (sidebar && sidebar.classList.contains('show')) {
                closeMobileSidebar();
            } else {
                openMobileSidebar();
            }
        });
    }
    if (backdrop) {
        backdrop.addEventListener('click', closeMobileSidebar);
    }
    // Close on Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('show')) {
            closeMobileSidebar();
        }
    });
    // Close sidebar when navigating on mobile (link click inside sidebar)
    if (sidebar) {
        sidebar.querySelectorAll('.nav-link').forEach(function (link) {
            link.addEventListener('click', function () {
                if (window.innerWidth < 768) closeMobileSidebar();
            });
        });
    }

    // Sidebar collapse to icon-only mode (desktop)
    var collapseBtn = document.getElementById('sidebar-collapse-btn');
    if (collapseBtn) {
        var icon = collapseBtn.querySelector('i');

        function sidebarSetCollapsed(collapsed) {
            document.body.classList.toggle('sidebar-collapsed', collapsed);
            if (icon) {
                icon.className = collapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
            }
            localStorage.setItem('sidebar-collapsed', collapsed ? '1' : '0');
            if (collapsed) {
                _sidebarInitTooltips();
            } else {
                _sidebarDestroyTooltips();
            }
        }

        // Restore saved state on page load
        if (localStorage.getItem('sidebar-collapsed') === '1') {
            sidebarSetCollapsed(true);
        }

        collapseBtn.addEventListener('click', function () {
            sidebarSetCollapsed(!document.body.classList.contains('sidebar-collapsed'));
        });
    }

    function _sidebarInitTooltips() {
        document.querySelectorAll('#sidebar [data-bs-toggle="tooltip"]').forEach(function (el) {
            if (!bootstrap.Tooltip.getInstance(el)) {
                new bootstrap.Tooltip(el, { trigger: 'hover' });
            }
        });
    }

    function _sidebarDestroyTooltips() {
        document.querySelectorAll('#sidebar [data-bs-toggle="tooltip"]').forEach(function (el) {
            var t = bootstrap.Tooltip.getInstance(el);
            if (t) t.dispose();
        });
    }

    // Universal Back button in the top bar.
    var backButton = document.getElementById('page-back-btn');
    if (backButton) {
        backButton.addEventListener('click', function () {
            var fallbackUrl = backButton.dataset.fallbackUrl || '/';
            var referrer = document.referrer;

            if (referrer) {
                try {
                    var previous = new URL(referrer);
                    var current = new URL(window.location.href);
                    if (previous.origin === current.origin && previous.href !== current.href) {
                        window.location.href = previous.href;
                        return;
                    }
                } catch (e) {
                    // Fall through to the dashboard fallback when referrer is not parseable.
                }
            }

            if (window.history.length > 1) {
                window.history.back();
                setTimeout(function () {
                    if (document.visibilityState !== 'hidden') {
                        window.location.href = fallbackUrl;
                    }
                }, 250);
                return;
            }

            window.location.href = fallbackUrl;
        });
    }

    // Confirm delete dialogs
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(el.dataset.confirm || 'Are you sure?')) {
                e.preventDefault();
            }
        });
    });

    // Dashboard chart loader
    var chartContainer = document.getElementById('dashboard-charts');
    if (chartContainer) {
        var projectId = document.getElementById('project-selector')?.value || '';
        fetchChartData(projectId);
        document.getElementById('project-selector')?.addEventListener('change', function () {
            fetchChartData(this.value);
        });
    }
});

function fetchChartData(projectId) {
    var url = '/chart-data/?project_id=' + projectId;
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            renderManpowerChart(data.labels, data.manpower_histogram);
            renderMaterialChart(data.labels, data.material_delivery_chart);
            if (data.progress_curve && data.progress_curve.length) {
                renderProgressChart(data.labels, data.progress_curve);
            }
        })
        .catch(function (e) { console.error('Chart data error:', e); });
}

function renderManpowerChart(labels, data) {
    var ctx = document.getElementById('manpowerChart');
    if (!ctx) return;
    if (window._manpowerChart) window._manpowerChart.destroy();
    window._manpowerChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Manpower',
                data: data,
                backgroundColor: 'rgba(41, 128, 185, 0.7)',
                borderColor: 'rgba(41, 128, 185, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderMaterialChart(labels, data) {
    var ctx = document.getElementById('materialChart');
    if (!ctx) return;
    if (window._materialChart) window._materialChart.destroy();
    window._materialChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Material Delivery (qty)',
                data: data,
                fill: true,
                backgroundColor: 'rgba(39, 174, 96, 0.15)',
                borderColor: 'rgba(39, 174, 96, 1)',
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderProgressChart(labels, data) {
    var ctx = document.getElementById('progressChart');
    if (!ctx) return;
    if (window._progressChart) window._progressChart.destroy();
    window._progressChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '% Complete',
                data: data,
                fill: false,
                borderColor: 'rgba(231, 76, 60, 1)',
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            scales: { y: { beginAtZero: true, max: 100 } }
        }
    });
}
