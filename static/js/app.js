/* ============================================================
   QR Cracker — Application JavaScript
   ============================================================ */

'use strict';

/* ---------- Utility ---------- */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

/* ============================================================
   TAB SWITCHING (QR type selector)
   ============================================================ */
function initTypeTabs() {
  const tabBtns = $$('.tab-btn[data-type]');
  const typeInput = $('#qr-type-input');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const type = btn.dataset.type;

      // Update button state
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Update hidden input
      if (typeInput) typeInput.value = type;

      // Show correct panel
      $$('.tab-panel').forEach(p => p.classList.remove('active'));
      const panel = $(`#panel-${type}`);
      if (panel) panel.classList.add('active');
    });
  });
}

/* ============================================================
   STATIC / DYNAMIC TOGGLE
   ============================================================ */
function initModeToggle() {
  const toggleBtns = $$('.toggle-btn[data-mode]');
  const modeInput = $('#mode-input');
  const dynamicNote = $('#dynamic-note');

  toggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      toggleBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      if (modeInput) modeInput.value = btn.dataset.mode;

      if (dynamicNote) {
        dynamicNote.style.display = btn.dataset.mode === 'dynamic' ? 'block' : 'none';
      }
    });
  });
}

/* ============================================================
   COLOR PICKER SYNC (hex input ↔ color picker)
   ============================================================ */
function initColorPickers() {
  $$('.color-pair').forEach(pair => {
    const picker = pair.querySelector('input[type="color"]');
    const hex    = pair.querySelector('input[type="text"]');
    if (!picker || !hex) return;

    picker.addEventListener('input', () => { hex.value = picker.value; });
    hex.addEventListener('input', () => {
      if (/^#[0-9a-fA-F]{6}$/.test(hex.value)) {
        picker.value = hex.value;
      }
    });
  });
}

/* ============================================================
   COPY TO CLIPBOARD
   ============================================================ */
function initCopyButtons() {
  $$('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = $(btn.dataset.copy);
      if (!target) return;

      const text = target.value || target.innerText || target.textContent;
      navigator.clipboard.writeText(text).then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '✅ Copied!';
        btn.disabled = true;
        setTimeout(() => {
          btn.innerHTML = orig;
          btn.disabled = false;
        }, 2000);
      });
    });
  });
}

/* ============================================================
   SCAN ANALYTICS CHART (Chart.js)
   ============================================================ */
function initScanChart() {
  const canvas = $('#scan-chart');
  if (!canvas || typeof Chart === 'undefined') return;

  const mobile  = parseInt(canvas.dataset.mobile  || '0', 10);
  const desktop = parseInt(canvas.dataset.desktop || '0', 10);

  if (mobile + desktop === 0) return;

  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Mobile', 'Desktop'],
      datasets: [{
        data: [mobile, desktop],
        backgroundColor: ['#7c3aed', '#06b6d4'],
        borderColor: ['#5b21b6', '#0891b2'],
        borderWidth: 2,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 13 },
            padding: 20,
            usePointStyle: true,
            pointStyleWidth: 10,
          }
        },
        tooltip: {
          backgroundColor: '#0f1120',
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          cornerRadius: 8,
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.parsed} scans`
          }
        }
      }
    }
  });
}

/* ============================================================
   SCANNER — Drag & Drop Upload
   ============================================================ */
function initScanner() {
  const dropZone  = $('#drop-zone');
  const fileInput = $('#file-input');
  const form      = $('#scan-form');

  if (!dropZone || !fileInput) return;

  // Click to open file dialog
  dropZone.addEventListener('click', () => fileInput.click());

  // File chosen via dialog
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      showSelectedFile(fileInput.files[0]);
      if (form) form.submit();
    }
  });

  // Drag events
  ['dragenter', 'dragover'].forEach(ev => {
    dropZone.addEventListener(ev, e => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });
  });

  ['dragleave', 'dragend', 'drop'].forEach(ev => {
    dropZone.addEventListener(ev, e => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
    });
  });

  dropZone.addEventListener('drop', e => {
    const file = e.dataTransfer.files[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      alert('Please drop an image file (PNG, JPG, etc.)');
      return;
    }
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
    showSelectedFile(file);
    if (form) form.submit();
  });

  function showSelectedFile(file) {
    const hint = dropZone.querySelector('.drop-zone-hint');
    if (hint) hint.textContent = `📎 ${file.name}`;
  }
}

/* ============================================================
   FLASH MESSAGE AUTO-DISMISS
   ============================================================ */
function initFlashMessages() {
  $$('.flash').forEach(el => {
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-8px)';
      el.style.transition = 'all 0.4s ease';
      setTimeout(() => el.remove(), 400);
    }, 4500);
  });
}

/* ============================================================
   CONFIRM DELETE
   ============================================================ */
function initDeleteConfirm() {
  $$('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm(btn.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });
}

/* ============================================================
   ANIMATED COUNTERS (stats cards)
   ============================================================ */
function initCounters() {
  $$('[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count, 10);
    if (isNaN(target) || target === 0) return;

    let start = 0;
    const duration = 900;
    const step = (timestamp) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      el.textContent = Math.floor(progress * target);
      if (progress < 1) requestAnimationFrame(step);
      else el.textContent = target;
    };
    requestAnimationFrame(step);
  });
}

/* ============================================================
   GENERATE FORM LOADING STATE
   ============================================================ */
function initFormSubmit() {
  const form = $('#generate-form');
  if (!form) return;

  form.addEventListener('submit', () => {
    const btn = form.querySelector('[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Generating…';
    }
  });
}

/* ============================================================
   MOBILE SIDEBAR TOGGLE
   ============================================================ */
function initMobileSidebar() {
  const toggle = $('#sidebar-toggle');
  const sidebar = $('.sidebar');
  const overlay = $('#sidebar-overlay');

  if (!toggle || !sidebar) return;

  toggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('active');
  });

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('active');
    });
  }
}

/* ============================================================
   THEME SWITCHER
   ============================================================ */
function initThemeSwitcher() {
  const themeSelect = $('#theme-select');
  if (!themeSelect) return;

  const currentTheme = localStorage.getItem('qr-cracker-theme') || 'dark';
  themeSelect.value = currentTheme;

  themeSelect.addEventListener('change', (e) => {
    const selected = e.target.value;
    document.documentElement.setAttribute('data-theme', selected);
    localStorage.setItem('qr-cracker-theme', selected);
  });
}

/* ============================================================
   INIT
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  initTypeTabs();
  initModeToggle();
  initColorPickers();
  initCopyButtons();
  initScanChart();
  initScanner();
  initFlashMessages();
  initDeleteConfirm();
  initCounters();
  initFormSubmit();
  initMobileSidebar();
  initThemeSwitcher();
});
