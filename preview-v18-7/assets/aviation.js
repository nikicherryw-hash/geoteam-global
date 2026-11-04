/* First-party progressive enhancement; no external network or tracking library. */
(function () {
  'use strict';
  const box = document.getElementById('av-brand-search');
  const directory = document.getElementById('av-brand-directory');
  const status = document.getElementById('av-filter-status');
  if (box && directory && status) {
    const items = Array.from(directory.querySelectorAll('[data-av-brand]'));
    box.addEventListener('input', () => {
      const term = box.value.trim().toLocaleLowerCase('en');
      let count = 0;
      items.forEach((item) => {
        const show = item.getAttribute('data-av-brand').includes(term);
        item.hidden = !show;
        if (show) count++;
      });
      status.textContent = count + (count === 1 ? ' manufacturer profile' : ' manufacturer profiles');
    });
  }
  // Local first-party intent event only. No GTM, cookies, network or PII.
  // Integrate with the existing CMP and analytics only after explicit configuration.
  document.addEventListener('click', (event) => {
    const target = event.target.closest('[data-av-event]');
    if (!target) return;
    const pageType = location.pathname.includes('/manufacturers/') ? 'manufacturer' :
      location.pathname.includes('/categories/') ? 'category' :
      location.pathname.includes('/guides/') ? 'guide' : 'hub';
    document.dispatchEvent(new CustomEvent('geoteam:aviation-interaction', {
      detail: { event: 'aviation_' + target.dataset.avEvent, section:'aviation', page_type:pageType }
    }));
  });
})();
