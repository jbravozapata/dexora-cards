const toggle = document.querySelector('.nav-toggle');
const nav = document.querySelector('.main-nav');
toggle?.addEventListener('click', () => {
  const open = toggle.getAttribute('aria-expanded') === 'true';
  toggle.setAttribute('aria-expanded', String(!open));
  nav?.classList.toggle('is-open', !open);
});

document.body.addEventListener('htmx:beforeRequest', (event) => {
  event.detail.elt.closest('form')?.classList.add('is-loading');
});
document.body.addEventListener('htmx:afterRequest', (event) => {
  event.detail.elt.closest('form')?.classList.remove('is-loading');
});

const reveal = () => document.querySelectorAll('.reveal:not(.is-visible)').forEach((el, i) => {
  window.setTimeout(() => el.classList.add('is-visible'), Math.min(i * 35, 280));
});
reveal();
document.body.addEventListener('htmx:afterSwap', reveal);

const initializeImageFallbacks = (root = document) => {
  root.querySelectorAll?.('img[data-image-fallback]').forEach((image) => {
    const showFallback = () => image.parentElement?.classList.add('image-failed');
    image.addEventListener('error', showFallback, { once: true });
    if (image.complete && image.naturalWidth === 0) showFallback();
  });
};
initializeImageFallbacks();
document.body.addEventListener('htmx:afterSwap', (event) => initializeImageFallbacks(event.detail.target));

document.querySelectorAll('[data-image-picker]').forEach((picker) => {
  const input = picker.querySelector('input[type="file"]');
  const fileName = picker.querySelector('[data-file-name]');
  input?.addEventListener('change', () => {
    if (!fileName) return;
    fileName.textContent = input.files?.[0]?.name || 'Ningún archivo seleccionado';
  });
});

const quickAddDialog = document.querySelector('#quick-add-dialog');
let quickAddTrigger = null;

document.body.addEventListener('click', (event) => {
  const trigger = event.target.closest?.('.species-quick-add[hx-get]');
  if (trigger) quickAddTrigger = trigger;
});

document.body.addEventListener('htmx:afterSwap', (event) => {
  if (event.detail.target?.id !== 'quick-add-content' || !quickAddDialog) return;
  event.detail.target.scrollTop = 0;
  if (!quickAddDialog.open) quickAddDialog.showModal();
});

quickAddDialog?.addEventListener('click', (event) => {
  const bounds = quickAddDialog.getBoundingClientRect();
  const outside = event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom;
  if (outside) quickAddDialog.close();
});

quickAddDialog?.addEventListener('close', () => quickAddTrigger?.focus());

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const dismissToast = (toast) => {
  if (!toast || toast.classList.contains('is-leaving')) return;
  toast.classList.add('is-leaving');
  window.setTimeout(() => toast.remove(), reduceMotion ? 0 : 240);
};

const initializeToast = (toast) => {
  const timeout = Number(toast.dataset.timeout || 3400);
  toast.style.setProperty('--toast-duration', `${timeout}ms`);
  toast.querySelector('[data-toast-close]')?.addEventListener('click', () => dismissToast(toast));
  window.setTimeout(() => dismissToast(toast), timeout);
};

document.querySelectorAll('[data-toast]').forEach(initializeToast);

document.body.addEventListener('wishlist:updated', (event) => {
  const detail = event.detail || {};
  if (detail.stats) {
    Object.entries(detail.stats).forEach(([key, value]) => {
      const stat = document.querySelector(`[data-wishlist-stat="${key}"]`);
      if (stat) stat.textContent = String(value ?? 0);
    });
  }
  if (detail.placement === 'wishlist' && !detail.active) {
    window.setTimeout(() => {
      const grid = document.querySelector('.wishlist-grid');
      if (!grid) return;
      const remaining = grid.querySelectorAll('.tcg-card').length;
      const resultCount = document.querySelector('[data-wishlist-result-count]');
      if (resultCount) resultCount.textContent = String(Math.max(Number(resultCount.textContent || 0) - 1, 0));
      if (remaining === 0 && !grid.querySelector('.empty-state')) {
        const template = document.querySelector('#wishlist-empty-state');
        if (template) grid.append(template.content.cloneNode(true));
      }
    }, 30);
  }
});

const bulkWorkspace = document.querySelector('[data-bulk-workspace]');
if (bulkWorkspace) {
  const bulkToggle = bulkWorkspace.querySelector('[data-bulk-toggle]');
  const bulkCancel = bulkWorkspace.querySelector('[data-bulk-cancel]');
  const bulkForm = bulkWorkspace.querySelector('[data-bulk-form]');
  const selectAll = bulkWorkspace.querySelector('[data-select-all]');
  const selectedCount = bulkWorkspace.querySelector('[data-selected-count]');
  const submitButton = bulkWorkspace.querySelector('[data-bulk-submit]');
  const itemChecks = [...bulkWorkspace.querySelectorAll('[data-bulk-item]')];

  const updateBulkSelection = () => {
    const checked = itemChecks.filter((item) => item.checked).length;
    if (selectedCount) selectedCount.textContent = String(checked);
    if (submitButton) submitButton.disabled = checked === 0;
    if (selectAll) {
      selectAll.checked = itemChecks.length > 0 && checked === itemChecks.length;
      selectAll.indeterminate = checked > 0 && checked < itemChecks.length;
    }
  };

  const setBulkMode = (active) => {
    bulkWorkspace.classList.toggle('bulk-mode', active);
    bulkToggle?.setAttribute('aria-pressed', String(active));
    const copy = bulkToggle?.querySelector('[data-bulk-toggle-copy]');
    if (copy) copy.textContent = active ? 'Selección activa' : 'Gestionar colección';
    if (!active) itemChecks.forEach((item) => { item.checked = false; });
    updateBulkSelection();
  };

  bulkToggle?.addEventListener('click', () => setBulkMode(!bulkWorkspace.classList.contains('bulk-mode')));
  bulkCancel?.addEventListener('click', () => setBulkMode(false));
  selectAll?.addEventListener('change', () => {
    itemChecks.forEach((item) => { item.checked = selectAll.checked; });
    updateBulkSelection();
  });
  itemChecks.forEach((item) => item.addEventListener('change', updateBulkSelection));
  bulkForm?.addEventListener('submit', (event) => {
    if (!itemChecks.some((item) => item.checked)) event.preventDefault();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && bulkWorkspace.classList.contains('bulk-mode')) setBulkMode(false);
  });
}

const counters = document.querySelectorAll('[data-count]');

const animateCounter = (element) => {
  const target = Number(element.dataset.count || 0);
  if (reduceMotion || target === 0) {
    element.textContent = String(target);
    return;
  }
  const duration = 800;
  const start = performance.now();
  const tick = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = String(Math.round(target * eased));
    if (progress < 1) window.requestAnimationFrame(tick);
  };
  window.requestAnimationFrame(tick);
};

if ('IntersectionObserver' in window && !reduceMotion) {
  const counterObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      animateCounter(entry.target);
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.5 });
  counters.forEach((counter) => counterObserver.observe(counter));
} else {
  counters.forEach(animateCounter);
}
