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
})();
