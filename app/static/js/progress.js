// Lesson progress: which lessons the student has opened (stored in this browser only, no account).
// A lesson counts as "started" the first time it is shown; the sidebar ladder and the progress bar
// light up accordingly. Number-only buttons are updated after each HTMX swap.
(() => {
  const KEY = 'spike_lessons_done_v1';
  const LABEL = document.querySelector('[data-progress-label]');

  function load() {
    try {
      return new Set(JSON.parse(localStorage.getItem(KEY) || '[]'));
    } catch (_) {
      return new Set();
    }
  }

  function save(done) {
    try {
      localStorage.setItem(KEY, JSON.stringify([...done]));
    } catch (_) {}
  }

  function paint() {
    const done = load();
    const current = document.querySelector('[data-lesson-root]')?.dataset.lessonId;
    document.querySelectorAll('[data-lesson-nav]').forEach((el) => {
      const id = el.dataset.lessonNav;
      el.classList.toggle('btn-success', done.has(id) && id !== current);
      el.classList.toggle('btn-warning', id === current);
      el.classList.toggle('btn-ghost', !done.has(id) && id !== current);
    });
    const bar = document.querySelector('[data-progress-bar]');
    const total = bar ? Number(bar.max) : 0;
    const n = [...done].filter((id) => document.querySelector(`[data-lesson-nav="${CSS.escape(id)}"]`)).length;
    if (bar) bar.value = n;
    if (LABEL) LABEL.textContent = total ? `${n}/${total}` : '';
  }

  function visit() {
    const id = document.querySelector('[data-lesson-root]')?.dataset.lessonId;
    if (!id) return;
    const done = load();
    if (!done.has(id)) {
      done.add(id);
      save(done);
    }
    paint();
  }

  document.addEventListener('htmx:afterSettle', () => requestAnimationFrame(paint));
  paint();
  visit();
  window.SpikeProgress = { paint, visit };
})();
