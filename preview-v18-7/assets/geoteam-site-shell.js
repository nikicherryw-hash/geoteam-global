(() => {
  'use strict';

  const locales = ['en', 'tr', 'ru', 'de', 'fr', 'es', 'it', 'pt', 'ar', 'zh'];
  const query = new URLSearchParams(window.location.search);
  const language = locales.includes(query.get('lang')) ? query.get('lang') : 'en';
  const year = new Date().getFullYear();
  const copy = {
    en: { home: 'Home', signIn: 'Sign in', sourcing: 'Global Sourcing', sectors: 'Sectors', company: 'Company', legal: 'Legal', about: 'About us', supplied: 'What we source', process: 'How we work', privacy: 'Privacy', rfq: 'RFQ', tagline: 'Intelligent solution platform', description: 'International sourcing for technical equipment, specifications and documented supply options.', fallback: 'Technical reference content is currently available in English.' },
    ru: { home: 'На главную', signIn: 'Войти', sourcing: 'Глобальный поиск', sectors: 'Направления', company: 'Компания', legal: 'Документы', about: 'О нас', supplied: 'Что поставляем', process: 'Как мы работаем', privacy: 'Конфиденциальность', rfq: 'RFQ', tagline: 'Интеллектуальная платформа решений', description: 'Международный поиск технической продукции, работа со спецификациями и вариантами поставки.', fallback: 'Технические справочные материалы пока доступны на английском языке.' },
    tr: { home: 'Ana sayfa', signIn: 'Giriş', sourcing: 'Küresel arama', sectors: 'Sektörler', company: 'Şirket', legal: 'Yasal', about: 'Hakkımızda', supplied: 'Ne tedarik ediyoruz', process: 'Nasıl çalışıyoruz', privacy: 'Gizlilik', rfq: 'RFQ', tagline: 'Akıllı çözüm platformu', description: 'Teknik ekipman, spesifikasyon ve belgeli tedarik seçenekleri için uluslararası kaynak araştırması.', fallback: 'Teknik referans içeriği şu anda İngilizce olarak sunulmaktadır.' }
  };
  const text = copy[language] || copy.en;
  const isSector = /\/(aviation|industrial|electronics|marine)(?:\.html|\/)/.test(window.location.pathname);
  const pathWithLanguage = (path) => {
    const url = new URL(path, window.location.origin);
    url.searchParams.set('lang', language);
    return `${url.pathname}${url.search}${url.hash}`;
  };
  const localizedPath = (nextLanguage) => {
    const url = new URL(window.location.href);
    const localized = url.pathname.match(/^\/(en|tr|ru)\/what-we-source\.html$/);
    if (localized) url.pathname = `/${['en', 'tr', 'ru'].includes(nextLanguage) ? nextLanguage : 'en'}/what-we-source.html`;
    url.searchParams.set('lang', nextLanguage);
    return url.toString();
  };
  const sectorLinks = [
    ['/aviation.html', { en: 'Aviation', ru: 'Авиация', tr: 'Havacılık' }],
    ['/industrial.html', { en: 'Industrial', ru: 'Промышленность', tr: 'Endüstri' }],
    ['/electronics.html', { en: 'Electronics', ru: 'Электроника', tr: 'Elektronik' }],
    ['/marine.html', { en: 'Shipbuilding & Shipping', ru: 'Судостроение и судоходство', tr: 'Gemi İnşa ve Deniz Taşımacılığı' }]
  ];

  // The approved home header remains the visual reference.  Its footer still
  // uses this shared component, while every other public page receives the
  // full shared shell.
  const shellMode = document.querySelector('meta[name="gt-site-shell"]')?.content || 'full';
  const footerOnly = shellMode === 'footer';
  const body = document.body;
  if (!body || body.dataset.gtSiteShell === 'ready') return;
  body.dataset.gtSiteShell = 'ready';
  if (!footerOnly) body.classList.add('gt-site-shell');
  document.documentElement.lang = language;

  if (!footerOnly) {
    document.querySelectorAll('body > header, .site-header, .av-header, .in-header, .ec-header, .mr-header').forEach((element) => {
      if (!element.classList.contains('gt-site-header')) element.hidden = true;
    });
  }
  document.querySelectorAll('body > footer, .av-footer, .in-footer, .ec-footer, .mr-footer, .gt-legal-single').forEach((element) => {
    if (!element.classList.contains('gt-site-footer')) element.hidden = true;
  });

  const header = document.createElement('header');
  header.className = 'gt-site-header';
  if (language === 'ar') header.dir = 'rtl';
  header.innerHTML = `
    <div class="gt-site-header__inner">
      <a class="gt-site-brand" href="${pathWithLanguage('/index.html')}" aria-label="GeoTeam Global ${text.home}">
        <img src="/data/geoteam-mark.svg" width="36" height="36" alt="" aria-hidden="true">
        <span><b>GeoTeam</b><small>GLOBAL</small></span>
      </a>
      <nav class="gt-site-nav" aria-label="${text.sectors}">
        ${sectorLinks.map(([href, labels]) => `<a href="${pathWithLanguage(href)}">${labels[language] || labels.en}</a>`).join('')}
      </nav>
      <div class="gt-site-actions">
        <a class="gt-site-home" href="${pathWithLanguage('/index.html')}"><span aria-hidden="true">←</span><span>${text.home}</span></a>
        <a class="gt-site-signin" href="${pathWithLanguage('/sourcing.html')}">${text.signIn}</a>
        <label class="gt-site-locale"><span class="sr-only">Website language</span><select aria-label="Website language">${locales.map((code) => `<option value="${code}"${code === language ? ' selected' : ''}>${code.toUpperCase()}</option>`).join('')}</select></label>
      </div>
    </div>`;
  if (!footerOnly) {
    body.insertBefore(header, body.firstChild);
    header.querySelector('select').addEventListener('change', (event) => window.location.assign(localizedPath(event.target.value)));
  }

  if (!footerOnly && language !== 'en' && language !== 'ru' && language !== 'tr') {
    const note = document.createElement('p');
    note.className = 'gt-site-locale-note';
    note.textContent = 'This page is currently available in English.';
    header.insertAdjacentElement('afterend', note);
  } else if (!footerOnly && isSector && language !== 'en') {
    const note = document.createElement('p');
    note.className = 'gt-site-locale-note';
    note.textContent = text.fallback;
    header.insertAdjacentElement('afterend', note);
  }

  const footer = document.createElement('footer');
  footer.className = 'gt-site-footer';
  if (language === 'ar') footer.dir = 'rtl';
  footer.innerHTML = `
    <div class="gt-site-footer__inner">
      <section class="gt-site-footer__brand">
        <a class="gt-site-brand" href="${pathWithLanguage('/index.html')}"><img src="/data/geoteam-mark.svg" width="34" height="34" alt="" aria-hidden="true"><span><b>GeoTeam</b><small>GLOBAL</small></span></a>
        <p><strong>${text.tagline}</strong><br>${text.description}</p>
      </section>
      <section><h2>${text.sectors}</h2>${sectorLinks.map(([href, labels]) => `<a href="${pathWithLanguage(href)}">${labels[language] || labels.en}</a>`).join('')}</section>
      <section><h2>${text.company}</h2><a href="${pathWithLanguage('/about.html')}">${text.about}</a><a href="${pathWithLanguage(language === 'ru' ? '/ru/what-we-source.html' : language === 'tr' ? '/tr/what-we-source.html' : '/en/what-we-source.html')}">${text.supplied}</a><a href="${pathWithLanguage('/about.html#workflow')}">${text.process}</a><a href="${pathWithLanguage('/sourcing.html')}">${text.sourcing}</a></section>
      <section><h2>${text.legal}</h2><a href="${pathWithLanguage('/privacy.html')}">${text.privacy}</a><a href="${pathWithLanguage('/rfq-privacy.html')}">${text.rfq}</a></section>
    </div>
    <div class="gt-site-footer__bottom"><span>© ${year} GeoTeam Global</span><span>${text.tagline}</span></div>`;
  body.appendChild(footer);
  if (window.location.pathname.endsWith('/about.html')) {
    const workflow = [...document.querySelectorAll('section')].find((section) => /how we work|как устроена работа|nasıl/.test(section.textContent || ''));
    if (workflow && !workflow.id) workflow.id = 'workflow';
  }
})();
