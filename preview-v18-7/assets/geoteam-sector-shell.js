(() => {
  const sectorLinks = [
    ['/aviation.html', 'Aviation'],
    ['/industrial.html', 'Industrial'],
    ['/electronics.html', 'Electronics'],
    ['/marine.html', 'Shipbuilding & Shipping']
  ];
  const sourcing = '/sourcing.html?lang=en';
  const shell = document.createElement('header');
  shell.className = 'gt-sector-shell';
  shell.innerHTML = `<div class="gt-sector-shell__inner">
    <a class="gt-sector-shell__brand" href="/index.html?lang=en" aria-label="GeoTeam Global home"><img src="/data/geoteam-mark.svg" alt="" aria-hidden="true"><span>GeoTeam<small>GLOBAL</small></span></a>
    <nav class="gt-sector-shell__nav" aria-label="Sector navigation">${sectorLinks.map(([href,label]) => `<a href="${href}">${label}</a>`).join('')}<a class="gt-sector-shell__search" href="${sourcing}">Global Sourcing <span aria-hidden="true">→</span></a></nav>
    <span class="gt-sector-shell__locale" aria-label="Page language: English">EN</span>
  </div>`;
  document.body.insertBefore(shell, document.body.firstChild);
  document.body.classList.add('mr-has-geoteam-shell');
  document.querySelectorAll('a[href^="mailto:"]').forEach(link => {
    link.href = sourcing;
    link.setAttribute('aria-label', 'Open Global Sourcing');
    if (link.classList.contains('mr-btn-primary')) link.innerHTML = 'Open Global Sourcing <span aria-hidden="true">→</span>';
  });
  const footer = document.createElement('footer');
  footer.className = 'gt-sector-footer';
  footer.innerHTML = `<div class="gt-sector-footer__inner"><span>© 2026 GeoTeam Global · Technical reference content in English</span><span><a href="/about.html?lang=en">About us</a> · <a href="/privacy.html">Privacy policy</a> · <a href="${sourcing}">Global Sourcing</a></span></div>`;
  document.body.appendChild(footer);
})();
