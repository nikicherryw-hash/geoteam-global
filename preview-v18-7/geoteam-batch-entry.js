(() => {
  'use strict';
  const form = document.getElementById('research');
  const query = document.getElementById('query');
  const attach = document.getElementById('attach');
  if (!form || !query || !attach) return;
  query.maxLength = 12000;
  const language = new URLSearchParams(location.search).get('lang') || document.documentElement.lang || 'ru';
  const account = document.getElementById('account-link');
  if (account) {
    const labels = {ru:'Кабинет',en:'Account',tr:'Hesap',de:'Konto',fr:'Compte',es:'Cuenta',it:'Account',pt:'Conta',ar:'الحساب',zh:'账户'};
    account.textContent = labels[language] || labels.en;
    account.href = 'account.html?lang=' + encodeURIComponent(language);
  }
  const shellSignIn = document.querySelector('.gt-site-signin');
  if (shellSignIn) shellSignIn.href = 'account.html?lang=' + encodeURIComponent(language);
  form.addEventListener('submit', event => {
    const listFile = [...attach.files].some(file => /\.(csv|xlsx)$/i.test(file.name));
    const lines = query.value.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
    if (!listFile && lines.length < 2) return;
    event.preventDefault(); event.stopImmediatePropagation();
    if (!listFile) sessionStorage.setItem('geoteam_pending_positions',lines.join('\n'));
    const url = new URL('account.html',location.href);
    url.searchParams.set('lang',language);
    if (listFile) url.searchParams.set('upload','1');
    location.assign(url.href);
  },true);
})();

