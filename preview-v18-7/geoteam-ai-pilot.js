(() => {
  'use strict';

  const api = String((window.GeoTeamAIPilotConfig || {}).apiBase || '/api/v1').replace(/\/$/, '');
  const supported = ['en', 'tr', 'ru', 'de', 'fr', 'es', 'it', 'pt', 'ar', 'zh'];
  const copy = {
    en:{ph:'Part number, P/N, serial number, manufacturer or product name',hint:'Enter a part number, P/N, serial number, manufacturer or product name. You may attach a photo or document.',attach:'Attach a file or photo',go:'Start search',ready:'Ready for global search.',checking:'Checking search access…',searching:'Searching global markets…',invalid:'Enter at least two characters.',budget:'AI search is temporarily unavailable because the approved budget limit was reached. Please try later.',error:'Search could not be completed. Please try later.',files:'Attached: ',product:'Identified product',offers:'Commercial offers',quote:'Request a quote',none:'No public offers found yet for this request.',manufacturer:'Manufacturer',part:'Part Number',name:'Product name',category:'Category',description:'Description',use:'Intended use',specs:'Verified specifications',condition:'Condition',availability:'Availability',lead:'Lead time',unknown:'Not confirmed'},
    ru:{ph:'Артикул, P/N, серийный номер, производитель или наименование',hint:'Введите артикул, P/N, серийный номер, производителя или наименование. Можно приложить фото или документ.',attach:'Прикрепить файл или фотографию',go:'Начать поиск',ready:'Готово к глобальному поиску.',checking:'Проверяем доступ к поиску…',searching:'Ищем предложения по мировому рынку…',invalid:'Введите не менее двух символов.',budget:'AI-поиск временно недоступен: достигнут лимит бюджета. Повторите позже.',error:'Не удалось выполнить поиск. Повторите позже.',files:'Прикреплено: ',product:'Найденное изделие',offers:'Коммерческие предложения',quote:'Запросить цену',none:'По вашему запросу публичных предложений пока не найдено.',manufacturer:'Производитель',part:'Part Number',name:'Наименование',category:'Категория',description:'Описание',use:'Назначение',specs:'Подтверждённые характеристики',condition:'Состояние',availability:'Наличие',lead:'Срок',unknown:'Не подтверждено'},
    tr:{ph:'Parça numarası, P/N, seri numarası, üretici veya ürün adı',hint:'Parça numarası, P/N, seri numarası, üretici veya ürün adını girin. Fotoğraf veya belge ekleyebilirsiniz.',attach:'Dosya veya fotoğraf ekle',go:'Aramayı başlat',ready:'Küresel arama için hazır.',checking:'Arama erişimi kontrol ediliyor…',searching:'Küresel pazarlarda aranıyor…',invalid:'En az iki karakter girin.',budget:'Onaylı bütçe limiti aşıldığı için AI araması geçici olarak kullanılamıyor. Lütfen sonra tekrar deneyin.',error:'Arama tamamlanamadı. Lütfen tekrar deneyin.',files:'Eklenen: ',product:'Tanımlanan ürün',offers:'Ticari teklifler',quote:'Fiyat iste',none:'Bu istek için henüz herkese açık teklif bulunamadı.',manufacturer:'Üretici',part:'Parça numarası',name:'Ürün adı',category:'Kategori',description:'Açıklama',use:'Kullanım amacı',specs:'Doğrulanmış özellikler',condition:'Durum',availability:'Stok durumu',lead:'Termin',unknown:'Doğrulanmadı'},
    de:{ph:'Teilenummer, P/N, Seriennummer, Hersteller oder Produktname',hint:'Geben Sie Teilenummer, P/N, Seriennummer, Hersteller oder Produktname ein. Foto oder Dokument kann angehängt werden.',attach:'Datei oder Foto anhängen',go:'Suche starten',ready:'Bereit für die globale Suche.',checking:'Suchzugang wird geprüft…',searching:'Weltweite Märkte werden durchsucht…',invalid:'Geben Sie mindestens zwei Zeichen ein.',budget:'Die KI-Suche ist vorübergehend wegen des freigegebenen Budgetlimits nicht verfügbar. Bitte später erneut versuchen.',error:'Suche konnte nicht abgeschlossen werden. Bitte erneut versuchen.',files:'Angehängt: ',product:'Identifiziertes Produkt',offers:'Kommerzielle Angebote',quote:'Preis anfragen',none:'Für diese Anfrage wurden noch keine öffentlichen Angebote gefunden.',manufacturer:'Hersteller',part:'Teilenummer',name:'Produktname',category:'Kategorie',description:'Beschreibung',use:'Verwendungszweck',specs:'Bestätigte Spezifikationen',condition:'Zustand',availability:'Verfügbarkeit',lead:'Lieferzeit',unknown:'Nicht bestätigt'},
    fr:{ph:'Référence, P/N, numéro de série, fabricant ou nom du produit',hint:'Saisissez une référence, P/N, numéro de série, fabricant ou nom du produit. Vous pouvez joindre une photo ou un document.',attach:'Joindre un fichier ou une photo',go:'Lancer la recherche',ready:'Prêt pour la recherche mondiale.',checking:'Vérification de l’accès à la recherche…',searching:'Recherche sur les marchés mondiaux…',invalid:'Saisissez au moins deux caractères.',budget:'La recherche IA est temporairement indisponible car la limite de budget approuvée est atteinte. Réessayez plus tard.',error:'La recherche n’a pas pu être terminée. Réessayez plus tard.',files:'Joint : ',product:'Produit identifié',offers:'Offres commerciales',quote:'Demander un prix',none:'Aucune offre publique trouvée pour le moment.',manufacturer:'Fabricant',part:'Référence',name:'Nom du produit',category:'Catégorie',description:'Description',use:'Usage prévu',specs:'Caractéristiques confirmées',condition:'État',availability:'Disponibilité',lead:'Délai',unknown:'Non confirmé'},
    es:{ph:'Número de pieza, P/N, número de serie, fabricante o nombre del producto',hint:'Introduzca número de pieza, P/N, número de serie, fabricante o nombre. Puede adjuntar una foto o documento.',attach:'Adjuntar archivo o foto',go:'Iniciar búsqueda',ready:'Listo para la búsqueda global.',checking:'Comprobando acceso de búsqueda…',searching:'Buscando en mercados mundiales…',invalid:'Introduzca al menos dos caracteres.',budget:'La búsqueda con IA no está disponible temporalmente porque se alcanzó el límite de presupuesto aprobado. Inténtelo más tarde.',error:'No se pudo completar la búsqueda. Inténtelo de nuevo.',files:'Adjunto: ',product:'Producto identificado',offers:'Ofertas comerciales',quote:'Solicitar precio',none:'Aún no se encontraron ofertas públicas para esta solicitud.',manufacturer:'Fabricante',part:'Número de pieza',name:'Nombre del producto',category:'Categoría',description:'Descripción',use:'Uso previsto',specs:'Especificaciones confirmadas',condition:'Estado',availability:'Disponibilidad',lead:'Plazo',unknown:'Sin confirmar'},
    it:{ph:'Codice articolo, P/N, numero di serie, produttore o nome prodotto',hint:'Inserisci codice articolo, P/N, numero di serie, produttore o nome prodotto. Puoi allegare una foto o un documento.',attach:'Allega file o foto',go:'Avvia ricerca',ready:'Pronto per la ricerca globale.',checking:'Verifica accesso alla ricerca…',searching:'Ricerca nei mercati globali…',invalid:'Inserisci almeno due caratteri.',budget:'La ricerca AI è temporaneamente non disponibile perché è stato raggiunto il limite di budget approvato. Riprova più tardi.',error:'Impossibile completare la ricerca. Riprova.',files:'Allegato: ',product:'Prodotto identificato',offers:'Offerte commerciali',quote:'Richiedi prezzo',none:'Nessuna offerta pubblica trovata per ora.',manufacturer:'Produttore',part:'Codice articolo',name:'Nome prodotto',category:'Categoria',description:'Descrizione',use:'Uso previsto',specs:'Specifiche confermate',condition:'Condizione',availability:'Disponibilità',lead:'Tempi',unknown:'Non confermato'},
    pt:{ph:'Número da peça, P/N, número de série, fabricante ou nome do produto',hint:'Informe número da peça, P/N, número de série, fabricante ou nome do produto. Você pode anexar foto ou documento.',attach:'Anexar arquivo ou foto',go:'Iniciar busca',ready:'Pronto para busca global.',checking:'Verificando acesso à busca…',searching:'Buscando nos mercados globais…',invalid:'Informe pelo menos dois caracteres.',budget:'A busca por IA está temporariamente indisponível porque o limite de orçamento aprovado foi atingido. Tente mais tarde.',error:'Não foi possível concluir a busca. Tente novamente.',files:'Anexado: ',product:'Produto identificado',offers:'Ofertas comerciais',quote:'Solicitar preço',none:'Ainda não foram encontradas ofertas públicas.',manufacturer:'Fabricante',part:'Número da peça',name:'Nome do produto',category:'Categoria',description:'Descrição',use:'Uso previsto',specs:'Especificações confirmadas',condition:'Condição',availability:'Disponibilidade',lead:'Prazo',unknown:'Não confirmado'},
    ar:{ph:'رقم القطعة أو P/N أو الرقم التسلسلي أو الشركة المصنعة أو اسم المنتج',hint:'أدخل رقم القطعة أو P/N أو الرقم التسلسلي أو الشركة المصنعة أو اسم المنتج. يمكنك إرفاق صورة أو مستند.',attach:'إرفاق ملف أو صورة',go:'بدء البحث',ready:'جاهز للبحث العالمي.',checking:'جارٍ التحقق من الوصول إلى البحث…',searching:'جارٍ البحث في الأسواق العالمية…',invalid:'أدخل حرفين على الأقل.',budget:'البحث بالذكاء الاصطناعي غير متاح مؤقتًا بسبب بلوغ حد الميزانية المعتمد. حاول لاحقًا.',error:'تعذر إكمال البحث. حاول لاحقًا.',files:'المرفق: ',product:'المنتج المحدد',offers:'العروض التجارية',quote:'طلب السعر',none:'لم يتم العثور على عروض عامة لهذا الطلب بعد.',manufacturer:'الشركة المصنعة',part:'رقم القطعة',name:'اسم المنتج',category:'الفئة',description:'الوصف',use:'الغرض من الاستخدام',specs:'مواصفات مؤكدة',condition:'الحالة',availability:'التوفر',lead:'المهلة',unknown:'غير مؤكد'},
    zh:{ph:'零件号、P/N、序列号、制造商或产品名称',hint:'请输入零件号、P/N、序列号、制造商或产品名称。您可以附加照片或文件。',attach:'附加文件或照片',go:'开始搜索',ready:'已准备好全球搜索。',checking:'正在检查搜索访问权限…',searching:'正在搜索全球市场…',invalid:'请至少输入两个字符。',budget:'由于达到批准的预算上限，AI 搜索暂时不可用。请稍后再试。',error:'无法完成搜索，请重试。',files:'已附加：',product:'已识别产品',offers:'商业报价',quote:'询价',none:'尚未找到该请求的公开报价。',manufacturer:'制造商',part:'零件号',name:'产品名称',category:'类别',description:'说明',use:'用途',specs:'已确认规格',condition:'状态',availability:'库存',lead:'交期',unknown:'未确认'}
  };

  const queryLanguage = new URLSearchParams(location.search).get('lang');
  let lang = supported.includes(queryLanguage) ? queryLanguage : (supported.includes(localStorage.getItem('geoteam_sourcing_lang')) ? localStorage.getItem('geoteam_sourcing_lang') : 'ru');
  const $ = id => document.getElementById(id);
  const query = $('query'), form = $('research'), submit = $('submit'), status = $('status'), results = $('results');
  const legacyLanguage = $('lang'), hint = $('hint'), attach = $('attach'), files = $('files'), back = $('back');
  let busy = false;
  attach.accept = 'image/jpeg,image/png,image/webp,.pdf,.txt,.csv,.docx,.xlsx';
  const t = key => (copy[lang] || copy.en)[key] || copy.en[key] || '';
  const text = (node, value) => { if (node) node.textContent = value == null ? '' : String(value); };
  const make = (tag, className) => { const node = document.createElement(tag); if (className) node.className = className; return node; };
  const hasValue = value => value !== null && value !== undefined && String(value).trim() !== '';
  const offerWords = {
    ru:['Страна не установлена','Новое','Б/у','Восстановленное','Состояние не установлено','Наличие не подтверждено','Цена по запросу','Цена из публичного источника; комплектация и единица продажи требуют уточнения.'],
    en:['Country not established','New','Used','Refurbished','Condition not established','Availability not confirmed','Price on request','Public price reference; configuration and sales unit require confirmation.'],
    tr:['Ülke belirlenmedi','Yeni','Kullanılmış','Yenilenmiş','Durum belirlenmedi','Stok doğrulanmadı','Fiyat talep üzerine','Herkese açık fiyat referansı; yapılandırma ve satış birimi teyit edilmelidir.']
  };

  function setStatus(message, state = 'global') {
    status.dataset.state = ['global', 'local', 'offline'].includes(state) ? state : 'offline';
    status.className = `status${state === 'offline' ? ' bad' : ''}`;
    text(status, message);
  }
  function applyLanguage() {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    if (legacyLanguage) legacyLanguage.value = lang;
    query.placeholder = t('ph');
    attach.parentElement.title = t('attach');
    attach.parentElement.setAttribute('aria-label', t('attach'));
    text(hint, t('hint')); text(submit, t('go'));
    if (back) back.textContent = lang === 'ar' ? 'الرئيسية ←' : `← ${lang === 'ru' ? 'На главную' : lang === 'tr' ? 'Ana sayfa' : lang === 'de' ? 'Startseite' : lang === 'fr' ? 'Accueil' : lang === 'es' ? 'Inicio' : lang === 'pt' ? 'Início' : lang === 'zh' ? '首页' : 'Home'}`;
    if (!busy) setStatus(t('ready'));
    localStorage.setItem('geoteam_sourcing_lang', lang);
  }
  function appendFact(box, label, value) {
    if (!hasValue(value)) return;
    const fact = make('div', 'fact'), caption = make('b'); text(caption, label); fact.append(caption, document.createTextNode(String(value))); box.append(fact);
  }
  function safeImage(value) { try { const url = new URL(String(value), location.origin); return url.protocol === 'https:' && (url.origin === location.origin || /^https:/.test(String(value))) ? url.href : ''; } catch (_) { return ''; } }
  function render(report) {
    results.replaceChildren();
    const product = report && typeof report.product === 'object' && report.product ? report.product : {};
    const offers = Array.isArray(report && report.offers) ? report.offers : [];
    if (Object.keys(product).length) {
      const card = make('section', 'product');
      const heading = make('h2'); text(heading, t('product')); card.append(heading);
      const name = product.product_name || product.part_number || report.query || '';
      const imageUrl = safeImage(report.image || product.image);
      if (imageUrl) { const image = make('img'); image.src = imageUrl; image.alt = name || t('product'); image.loading = 'lazy'; image.referrerPolicy = 'no-referrer'; image.onerror = () => image.remove(); card.append(image); }
      if (name) { const title = make('h3'); text(title, name); card.append(title); }
      const facts = make('div', 'facts');
      appendFact(facts, t('manufacturer'), product.manufacturer);
      appendFact(facts, t('part'), product.part_number);
      appendFact(facts, t('category'), product.product_category);
      appendFact(facts, t('description'), product.short_description);
      appendFact(facts, t('use'), product.intended_use);
      if (facts.childNodes.length) card.append(facts);
      const specifications = Array.isArray(product.technical_specifications) ? product.technical_specifications.filter(hasValue).slice(0, 12) : [];
      if (specifications.length) { const specTitle = make('h3'); text(specTitle, t('specs')); const list = make('ul', 'product-specifications'); specifications.forEach(item => { const row = make('li'); text(row, item); list.append(row); }); card.append(specTitle, list); }
      results.append(card);
    }
    const section = make('section', 'offers'), heading = make('h2'); text(heading, t('offers')); section.append(heading);
    if (!offers.length) { const none = make('p'); text(none, t('none')); section.append(none); results.append(section); return; }
    const grid = make('div', 'offersgrid');
    offers.slice(0, 12).forEach(offer => {
      const card = make('article', 'offer'), title = make('strong'); text(title, offer.public_offer_id || 'GeoTeam offer'); card.append(title);
      const words = offerWords[lang] || offerWords.en;
      const meta = make('p', 'meta'); text(meta, [offer.country || words[0], words[({NEW:1,USED:2,REFURBISHED:3})[offer.condition] || 4], words[5]].join(' · ')); card.append(meta);
      const price = make('p', 'price');
      const numericPrice = Number(offer.price);
      text(price, hasValue(offer.price) && Number.isFinite(numericPrice) && numericPrice > 0 && /^[A-Z]{3}$/.test(offer.currency || '') ? new Intl.NumberFormat(lang, {style:'currency',currency:offer.currency}).format(numericPrice) : words[6]); card.append(price);
      const qualification = make('p', 'meta'); text(qualification, words[7]); card.append(qualification);
      if (hasValue(offer.lead_time)) { const lead = make('p', 'meta'); text(lead, `${t('lead')}: ${offer.lead_time}`); card.append(lead); }
      const action = make('button', 'rfq'); action.type = 'button'; text(action, t('quote')); action.addEventListener('click', () => document.dispatchEvent(new CustomEvent('geoteam:rfq-select', {detail: offer}))); card.append(action); grid.append(card);
    });
    section.append(grid); results.append(section);
  }
  async function poll(jobId) {
    for (let attempt = 0; attempt < 90; attempt += 1) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      const response = await fetch(`${api}/guest/research/${encodeURIComponent(jobId)}`, {credentials:'same-origin', cache:'no-store'});
      if (!response.ok) throw Error(`POLL_${response.status}`);
      const data = await response.json();
      if (['SUCCEEDED', 'FAILED', 'INTERRUPTED'].includes(data.status)) {
        if (data.status !== 'SUCCEEDED' || !data.result) throw Error(data.status);
        return data.result;
      }
    }
    throw Error('TIMEOUT');
  }
  form.addEventListener('submit', async event => {
    event.preventDefault(); if (busy) return;
    const value = query.value.trim(), file = attach.files[0]; if ((!file && value.length < 2) || value.length > 160) { setStatus(t('invalid'), 'offline'); query.focus(); return; }
    busy = true; submit.disabled = true; results.replaceChildren(); setStatus(t('checking'));
    try {
      let payload = {query:value, locale:lang};
      if (file) {
        if (file.size > 3 * 1024 * 1024) throw Error('FILE_MAX_3_MB');
        const mime = file.type || ({pdf:'application/pdf',txt:'text/plain',csv:'text/csv',jpg:'image/jpeg',jpeg:'image/jpeg',png:'image/png',webp:'image/webp'})[file.name.split('.').pop().toLowerCase()];
        if (!['application/pdf','text/plain','text/csv','image/jpeg','image/png','image/webp','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(mime)) throw Error('UNSUPPORTED_FILE_FORMAT');
        const data = await new Promise((resolve,reject) => { const reader = new FileReader(); reader.onerror = () => reject(Error('FILE_READ')); reader.onload = () => resolve(String(reader.result).split(',')[1]); reader.readAsDataURL(file); });
        payload = {...payload,mime,filename:file.name,data};
      }
      const response = await fetch(`${api}/guest/${file ? 'research-attachment' : 'research'}`, {method:'POST', credentials:'same-origin', cache:'no-store', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
      if (response.status === 429) { setStatus(t('budget'), 'offline'); return; }
      if (!response.ok) throw Error(`START_${response.status}`);
      const job = await response.json(); if (!/^[a-f0-9]{32}$/i.test(String(job.job_id || ''))) throw Error('JOB');
      setStatus(t('searching'), 'local'); render(await poll(job.job_id)); setStatus(t('ready'));
    } catch (error) { setStatus(`${t('error')} [${String(error.message || 'ERR')}]`, 'offline'); }
    finally { busy = false; submit.disabled = false; }
  });
  legacyLanguage?.addEventListener('change', () => { lang = supported.includes(legacyLanguage.value) ? legacyLanguage.value : 'en'; const next = new URL(location.href); next.searchParams.set('lang', lang); location.assign(next); });
  attach.addEventListener('change', () => { const names = [...attach.files].map(file => file.name).join(', '); text(files, names ? t('files') + names : ''); });
  applyLanguage();
})();
