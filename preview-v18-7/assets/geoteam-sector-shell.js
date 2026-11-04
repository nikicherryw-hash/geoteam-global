(() => {
  const supportedLanguages = new Set(['en', 'tr', 'ru', 'de', 'fr', 'es', 'it', 'pt', 'ar', 'zh']);
  const requestedLanguage = new URLSearchParams(window.location.search).get('lang') || 'en';
  const language = supportedLanguages.has(requestedLanguage) ? requestedLanguage : 'en';
  const withLanguage = (path) => `${path}?lang=${encodeURIComponent(language)}`;
  const sectorLinks = [
    ['/aviation.html', 'Aviation'],
    ['/industrial.html', 'Industrial'],
    ['/electronics.html', 'Electronics'],
    ['/marine.html', 'Shipbuilding & Shipping']
  ];
  const sourcing = withLanguage('/sourcing.html');
  const shell = document.createElement('header');
  shell.className = 'gt-sector-shell';
  shell.innerHTML = `<div class="gt-sector-shell__inner">
    <a class="gt-sector-shell__brand brand gt-brand-refined gt-wordmark" href="${withLanguage('/index.html')}" aria-label="GeoTeam Global home"><span class="gt-brand-mark" aria-hidden="true"><img src="/data/geoteam-mark.svg" alt=""></span><span class="gt-brand-text"><span class="top">GeoTeam</span><span class="bottom">GLOBAL</span></span></a>
    <nav class="gt-sector-shell__nav" aria-label="Sector navigation">${sectorLinks.map(([href,label]) => `<a href="${withLanguage(href)}">${label}</a>`).join('')}</nav>
    <div class="gt-sector-shell__actions"><a class="gt-sector-shell__account" href="${sourcing}">Sign in</a><label class="gt-sector-shell__locale" aria-label="Website language"><span class="sr-only">Website language</span><select>${[['en','EN'],['tr','TR'],['ru','RU'],['de','DE'],['fr','FR'],['es','ES'],['it','IT'],['pt','PT'],['ar','AR'],['zh','ZH']].map(([value,label]) => `<option value="${value}"${value === language ? ' selected' : ''}>${label}</option>`).join('')}</select></label></div>
  </div>`;
  document.body.insertBefore(shell, document.body.firstChild);
  document.body.classList.add('mr-has-geoteam-shell');
  const languageSelect = shell.querySelector('select');
  languageSelect.addEventListener('change', () => {
    const nextUrl = new URL(window.location.href);
    nextUrl.searchParams.set('lang', languageSelect.value);
    window.location.assign(nextUrl.toString());
  });
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
