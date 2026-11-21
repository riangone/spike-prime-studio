// Page glue: no template strings are interpolated into inline JS; everything reads data-* attributes.
(() => {
  const THEME_KEY = 'spike_theme';

  // Theme (the <head> snippet applies the stored theme before first paint)
  const themeSelect = document.querySelector('[data-theme-select]');
  if (themeSelect) {
    themeSelect.value = document.documentElement.getAttribute('data-theme') || 'night';
    themeSelect.addEventListener('change', () => {
      document.documentElement.setAttribute('data-theme', themeSelect.value);
      try {
        localStorage.setItem(THEME_KEY, themeSelect.value);
      } catch (_) {}
    });
  }

  // Tab state must exist before the language-link handler below reads `activeTab`.
  const TAB_NAMES = ['build', 'blocks', 'code', 'deploy'];
  const urlTab = new URLSearchParams(window.location.search).get('tab');
  let activeTab = TAB_NAMES.includes(urlTab) ? urlTab : 'build';

  // Language links keep the current lesson + step (the URL is kept in sync by hx-replace-url).
  document.addEventListener('click', (ev) => {
    const link = ev.target.closest('[data-lang-link]');
    if (!link) return;
    ev.preventDefault();
    const url = new URL(window.location.href);
    url.searchParams.set('lang', link.dataset.langLink);
    if (activeTab !== 'build') url.searchParams.set('tab', activeTab);
    else url.searchParams.delete('tab');
    const base = window.SPIKE_BASE_PATH || '';
    url.pathname = `${base}/`;
    window.location.href = url.toString();
  });

  // Workspace tabs. Plain buttons + panels instead of DaisyUI radio tabs: the radio variant lays tabs
  // and panels out in one CSS grid, so a wide panel (the code listing) squeezed the tab labels.
  // The chosen tab survives lesson swaps and page reloads (?tab=), and is reflected in the URL
  // (hx-replace-url) so language links keep it. Other modules listen for `spike:tab` (e.g. lazy Blockly).
  function writeTabToUrl(name) {
    const url = new URL(window.location.href);
    if (name === 'build') url.searchParams.delete('tab');
    else url.searchParams.set('tab', name);
    const mode = currentMode();
    if (mode) url.searchParams.set('mode', mode);
    else url.searchParams.delete('mode');
    const ver = currentVersion();
    if (ver) url.searchParams.set('ver', ver);
    else url.searchParams.delete('ver');
    window.history.replaceState(window.history.state, '', url);
  }

  function currentMode() {
    const m = document.querySelector('[data-lesson-root]')?.dataset.programMode || 'blockly';
    return m === 'blockly' ? '' : m;
  }

  function currentVersion() {
    const v = document.querySelector('[data-lesson-root]')?.dataset.programVersion || 'v2';
    return v === 'v2' ? '' : v;
  }

  function showTab(name, opts = {}) {
    const root = document.querySelector('[data-tabs]');
    if (!root || !root.querySelector(`[data-tab-panel="${name}"]`)) return;
    activeTab = name;
    root.querySelectorAll('[data-tab]').forEach((t) => {
      const on = t.dataset.tab === name;
      t.classList.toggle('tab-active', on);
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
    });
    root.querySelectorAll('[data-tab-panel]').forEach((p) => {
      p.hidden = p.dataset.tabPanel !== name;
    });
    if (opts.syncUrl !== false) writeTabToUrl(name);
    document.dispatchEvent(new CustomEvent('spike:tab', { detail: { name } }));
  }
  window.SpikeTabs = { show: showTab, get active() { return activeTab; } };

  document.addEventListener('click', (ev) => {
    const tab = ev.target.closest('[data-tab]');
    if (tab) showTab(tab.dataset.tab);
  });

  // Keyboard: ←/→ move between tabs (ARIA tab pattern).
  document.addEventListener('keydown', (ev) => {
    const tab = ev.target.closest?.('[data-tab]');
    if (!tab || !['ArrowLeft', 'ArrowRight'].includes(ev.key)) return;
    ev.preventDefault();
    const i = TAB_NAMES.indexOf(tab.dataset.tab);
    const next = TAB_NAMES[(i + (ev.key === 'ArrowRight' ? 1 : TAB_NAMES.length - 1)) % TAB_NAMES.length];
    showTab(next);
    document.querySelector(`[data-tab="${next}"]`)?.focus();
  });

  // Event order: blocks.js and viewer3d.js register their listeners first (they are earlier
  // <script> tags), so this runs after them and the tab state they react to is final.
  document.addEventListener('htmx:afterSettle', (ev) => {
    // Step 1: the HTMX swap already put ?lesson=<id> in the URL; only the tab can be stale.
    if (ev.target?.id !== 'lesson-workspace') {
      if (document.getElementById('step-detail-panel')?.contains(ev.target)) showTab(activeTab, { syncUrl: false });
      return;
    }
    showTab(activeTab, { syncUrl: false });
    const root = document.querySelector('[data-lesson-root]');
    const lessonId = root?.dataset.lessonId;
    document.querySelectorAll('[data-lesson-nav]').forEach((a) => {
      a.classList.toggle('active', a.dataset.lessonNav === lessonId);
    });
    // A new lesson always starts from step 1 unless the server-rendered DOM says otherwise.
    const step = document.querySelector('[data-step-root]')?.dataset.step || '1';
    const url = new URL(window.location.href);
    if (lessonId) url.searchParams.set('lesson', lessonId);
    if (step === '1') url.searchParams.delete('step');
    else url.searchParams.set('step', step);
    const ver = currentVersion();
    if (ver) url.searchParams.set('ver', ver);
    else url.searchParams.delete('ver');
    window.history.replaceState(window.history.state, '', url);
    // Lessons can be short or long, so frame a different element each time: the 3D model on a
    // first step, the step navigation when jumping to a later step.
    if (step === '1') document.querySelector('#viewer3d-canvas')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    else document.querySelector('[data-step-root]')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  // Copy code
  document.addEventListener('click', async (ev) => {
    const btn = ev.target.closest('[data-copy-code]');
    if (!btn) return;
    const codeEl = document.getElementById('spike-python-code');
    if (!codeEl) return;
    try {
      await navigator.clipboard.writeText(codeEl.textContent);
    } catch (_) {
      return;
    }
    const orig = btn.dataset.origLabel || btn.textContent;
    btn.dataset.origLabel = orig;
    btn.textContent = btn.dataset.copiedLabel;
    setTimeout(() => {
      btn.textContent = orig;
    }, 1800);
  });

  // PWA Service Worker registration & Install Prompt
  const base = window.SPIKE_BASE_PATH || '';
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register(`${base}/sw.js`, { scope: `${base}/` }).catch(() => {});
    });
  }

  let deferredInstallPrompt = null;
  const installBtn = document.querySelector('[data-pwa-install]');
  window.addEventListener('beforeinstallprompt', (ev) => {
    ev.preventDefault();
    deferredInstallPrompt = ev;
    if (installBtn) installBtn.hidden = false;
  });

  if (installBtn) {
    installBtn.addEventListener('click', async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      try {
        await deferredInstallPrompt.userChoice;
      } catch (_) {}
      deferredInstallPrompt = null;
      installBtn.hidden = true;
    });
  }

  window.addEventListener('appinstalled', () => {
    deferredInstallPrompt = null;
    if (installBtn) installBtn.hidden = true;
  });
})();
