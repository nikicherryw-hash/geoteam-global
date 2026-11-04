/* First-party progressive enhancement. No network, cookies, external tracking or PII. */
(() => {
  'use strict';
  const field = document.getElementById('mr-brand-search');
  const panel = document.getElementById('mr-brand-directory');
  const status = document.getElementById('mr-filter-status');
  if (field && panel && status) {
    const nodes = [...panel.querySelectorAll('[data-mr-brand]')];
    field.addEventListener('input', () => {
      const query = field.value.trim().toLocaleLowerCase('en');
      let total = 0;
      for (const node of nodes) {
        const visible = node.dataset.mrBrand.includes(query);
        node.hidden = !visible;
        if (visible) total++;
      }
      status.textContent = `${total} manufacturer reference ${total === 1 ? 'profile' : 'profiles'}`;
    });
  }
  document.addEventListener('click', (event) => {
    if (!(event.target instanceof Element)) return;
    const node = event.target.closest('[data-mr-event]');
    if (!node) return;
    const path = location.pathname;
    const pageType = path.includes('/manufacturers/') ? 'manufacturer' : path.includes('/categories/') ? 'category' : path.includes('/guides/') ? 'guide' : 'hub';
    const type = node.dataset.mrEvent;
    if (!['catalog_click', 'rfq_intent'].includes(type)) return;
    // Intent-only event for a separately authorized analytics adapter. Never log P/N or buyer details.
    document.dispatchEvent(new CustomEvent('geoteam:marine-interaction', {
      detail: { event: `marine_${type}`, area: 'marine', page_type: pageType }
    }));
  });
})();
