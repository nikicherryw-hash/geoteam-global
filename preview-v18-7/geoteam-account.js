(() => {
  'use strict';
  const API = '/api/v1/commerce';
  const $ = id => document.getElementById(id);
  const copy = {
    ru:{title:'Кабинет клиента',intro:'Ваши заявки и позиции в одном месте.',login:'Войти',register:'Зарегистрироваться',password:'Пароль',organization:'Организация',consent:'Согласен с условиями обработки данных',logout:'Выйти',newRequest:'Новая заявка',newHelp:'Укажите один P/N в строке или приложите CSV/XLSX с колонкой P/N. До 100 позиций. Сохранение не запускает платный AI-поиск.',positions:'Артикулы по одному в строке',file:'CSV или XLSX',preview:'Проверить позиции',save:'Сохранить заявку',requests:'Мои заявки',details:'Позиции заявки',more:'Показать ещё',empty:'Заявок пока нет.',noRfq:'RFQ пока нет.',pending:'Ожидает поиска',count:'Позиций: ',saved:'Заявка сохранена в кабинете. Поиск ожидает доступного бюджета.',select:'Выберите файл или укажите P/N по строкам.',invalid:'Проверьте список: от 1 до 100 непустых позиций.',signIn:'Войдите или зарегистрируйтесь, чтобы сохранить заявку.',verify:'Подтвердить email в тестовом режиме',verified:'Email подтверждён. Теперь войдите.',registered:'Регистрация создана. Подтвердите email, затем войдите.',working:'Обработка…',error:'Не удалось выполнить действие.',loaded:'Список позиций проверен. Сохраните заявку.',fileSize:'Файл должен быть не больше 3 МБ.'},
    en:{title:'Customer account',intro:'Your requests and positions in one place.',login:'Sign in',register:'Register',password:'Password',organization:'Organization',consent:'I agree to the data processing terms',logout:'Sign out',newRequest:'New request',newHelp:'Enter one P/N per line or attach a CSV/XLSX file with a P/N column. Up to 100 positions. Saving does not start paid AI search.',positions:'One part number per line',file:'CSV or XLSX',preview:'Review positions',save:'Save request',requests:'My requests',details:'Request positions',more:'Show more',empty:'No requests yet.',noRfq:'No RFQs yet.',pending:'Awaiting search',count:'Positions: ',saved:'Request saved in your account. Search awaits available budget.',select:'Choose a file or enter P/Ns on separate lines.',invalid:'Check the list: 1 to 100 nonempty positions.',signIn:'Sign in or register to save a request.',verify:'Verify email in test mode',verified:'Email verified. You can sign in.',registered:'Registration created. Verify your email, then sign in.',working:'Processing…',error:'Action could not be completed.',loaded:'Positions reviewed. Save the request.',fileSize:'File must be no larger than 3 MB.'},
    tr:{title:'Müşteri hesabı',intro:'Talepleriniz ve kalemleriniz tek yerde.',login:'Giriş yap',register:'Kaydol',password:'Şifre',organization:'Şirket',consent:'Veri işleme koşullarını kabul ediyorum',logout:'Çıkış yap',newRequest:'Yeni talep',newHelp:'Her satıra bir P/N girin veya P/N sütunlu CSV/XLSX ekleyin. En fazla 100 kalem. Kaydetmek ücretli AI aramasını başlatmaz.',positions:'Her satırda bir parça numarası',file:'CSV veya XLSX',preview:'Kalemleri kontrol et',save:'Talebi kaydet',requests:'Taleplerim',details:'Talep kalemleri',more:'Daha fazla göster',empty:'Henüz talep yok.',noRfq:'Henüz RFQ yok.',pending:'Arama bekliyor',count:'Kalem sayısı: ',saved:'Talep hesabınıza kaydedildi. Arama bütçe uygunluğunu bekliyor.',select:'Dosya seçin veya P/N değerlerini ayrı satırlara girin.',invalid:'Listeyi kontrol edin: 1–100 dolu kalem.',signIn:'Talebi kaydetmek için giriş yapın veya kaydolun.',verify:'Test modunda e-postayı doğrula',verified:'E-posta doğrulandı. Giriş yapabilirsiniz.',registered:'Kayıt oluşturuldu. E-postayı doğrulayıp giriş yapın.',working:'İşleniyor…',error:'İşlem tamamlanamadı.',loaded:'Kalemler kontrol edildi. Talebi kaydedin.',fileSize:'Dosya en fazla 3 MB olabilir.'},
    de:{title:'Kundenkonto',intro:'Ihre Anfragen und Positionen an einem Ort.',login:'Anmelden',register:'Registrieren',password:'Passwort',organization:'Unternehmen',consent:'Ich stimme den Bedingungen zur Datenverarbeitung zu',logout:'Abmelden',newRequest:'Neue Anfrage',newHelp:'Ein P/N je Zeile oder CSV/XLSX mit P/N-Spalte. Bis zu 100 Positionen. Das Speichern startet keine kostenpflichtige KI-Suche.',positions:'Eine Teilenummer pro Zeile',file:'CSV oder XLSX',preview:'Positionen prüfen',save:'Anfrage speichern',requests:'Meine Anfragen',details:'Anfragepositionen',more:'Mehr anzeigen',empty:'Noch keine Anfragen.',noRfq:'Noch keine RFQs.',pending:'Suche ausstehend',count:'Positionen: ',saved:'Anfrage gespeichert. Die Suche wartet auf verfügbares Budget.',select:'Datei wählen oder P/N zeilenweise eingeben.',invalid:'Liste prüfen: 1 bis 100 ausgefüllte Positionen.',signIn:'Zum Speichern anmelden oder registrieren.',verify:'E-Mail im Testmodus bestätigen',verified:'E-Mail bestätigt. Bitte anmelden.',registered:'Registrierung erstellt. E-Mail bestätigen und anmelden.',working:'Verarbeitung…',error:'Aktion konnte nicht abgeschlossen werden.',loaded:'Positionen geprüft. Anfrage speichern.',fileSize:'Datei darf höchstens 3 MB groß sein.'},
    fr:{title:'Espace client',intro:'Vos demandes et références au même endroit.',login:'Se connecter',register:"S'inscrire",password:'Mot de passe',organization:'Entreprise',consent:"J'accepte les conditions de traitement des données",logout:'Se déconnecter',newRequest:'Nouvelle demande',newHelp:"Une référence P/N par ligne ou un CSV/XLSX avec colonne P/N. Jusqu'à 100 lignes. L'enregistrement ne lance pas de recherche IA payante.",positions:'Une référence par ligne',file:'CSV ou XLSX',preview:'Vérifier les références',save:'Enregistrer la demande',requests:'Mes demandes',details:'Références demandées',more:'Afficher plus',empty:'Aucune demande.',noRfq:'Aucune RFQ.',pending:'Recherche en attente',count:'Références : ',saved:'Demande enregistrée. La recherche attend un budget disponible.',select:'Choisissez un fichier ou saisissez les P/N par ligne.',invalid:'Vérifiez la liste : de 1 à 100 références non vides.',signIn:'Connectez-vous ou inscrivez-vous pour enregistrer.',verify:"Vérifier l'e-mail en mode test",verified:'E-mail vérifié. Connectez-vous.',registered:"Inscription créée. Vérifiez l'e-mail puis connectez-vous.",working:'Traitement…',error:"L'action a échoué.",loaded:'Références vérifiées. Enregistrez la demande.',fileSize:'Le fichier ne doit pas dépasser 3 Mo.'},
    es:{title:'Área de cliente',intro:'Sus solicitudes y referencias en un solo lugar.',login:'Entrar',register:'Registrarse',password:'Contraseña',organization:'Empresa',consent:'Acepto las condiciones de tratamiento de datos',logout:'Salir',newRequest:'Nueva solicitud',newHelp:'Un P/N por línea o CSV/XLSX con columna P/N. Hasta 100 posiciones. Guardar no inicia una búsqueda de IA de pago.',positions:'Una referencia por línea',file:'CSV o XLSX',preview:'Revisar posiciones',save:'Guardar solicitud',requests:'Mis solicitudes',details:'Posiciones solicitadas',more:'Mostrar más',empty:'Aún no hay solicitudes.',noRfq:'Aún no hay RFQ.',pending:'Búsqueda pendiente',count:'Posiciones: ',saved:'Solicitud guardada. La búsqueda espera presupuesto disponible.',select:'Seleccione un archivo o introduzca los P/N por líneas.',invalid:'Revise la lista: de 1 a 100 posiciones no vacías.',signIn:'Entre o regístrese para guardar.',verify:'Verificar correo en modo de prueba',verified:'Correo verificado. Ya puede entrar.',registered:'Registro creado. Verifique el correo y entre.',working:'Procesando…',error:'No se pudo completar la acción.',loaded:'Posiciones revisadas. Guarde la solicitud.',fileSize:'El archivo no debe superar 3 MB.'},
    it:{title:'Area clienti',intro:'Richieste e articoli in un unico posto.',login:'Accedi',register:'Registrati',password:'Password',organization:'Azienda',consent:'Accetto le condizioni sul trattamento dei dati',logout:'Esci',newRequest:'Nuova richiesta',newHelp:'Un P/N per riga oppure CSV/XLSX con colonna P/N. Fino a 100 articoli. Il salvataggio non avvia una ricerca AI a pagamento.',positions:'Un codice per riga',file:'CSV o XLSX',preview:'Verifica articoli',save:'Salva richiesta',requests:'Le mie richieste',details:'Articoli richiesti',more:'Mostra altri',empty:'Nessuna richiesta.',noRfq:'Nessuna RFQ.',pending:'Ricerca in attesa',count:'Articoli: ',saved:'Richiesta salvata. La ricerca attende budget disponibile.',select:'Seleziona un file o inserisci P/N su righe separate.',invalid:'Controlla l’elenco: da 1 a 100 articoli non vuoti.',signIn:'Accedi o registrati per salvare.',verify:'Verifica email in modalità test',verified:'Email verificata. Puoi accedere.',registered:'Registrazione creata. Verifica email e accedi.',working:'Elaborazione…',error:'Operazione non riuscita.',loaded:'Articoli verificati. Salva la richiesta.',fileSize:'Il file non può superare 3 MB.'},
    pt:{title:'Área do cliente',intro:'Pedidos e itens em um só lugar.',login:'Entrar',register:'Cadastrar',password:'Senha',organization:'Empresa',consent:'Concordo com as condições de tratamento de dados',logout:'Sair',newRequest:'Novo pedido',newHelp:'Um P/N por linha ou CSV/XLSX com coluna P/N. Até 100 itens. Salvar não inicia pesquisa de IA paga.',positions:'Um código por linha',file:'CSV ou XLSX',preview:'Revisar itens',save:'Salvar pedido',requests:'Meus pedidos',details:'Itens do pedido',more:'Mostrar mais',empty:'Ainda não há pedidos.',noRfq:'Ainda não há RFQs.',pending:'Pesquisa pendente',count:'Itens: ',saved:'Pedido salvo. A pesquisa aguarda orçamento disponível.',select:'Escolha um arquivo ou informe os P/N em linhas separadas.',invalid:'Confira a lista: de 1 a 100 itens preenchidos.',signIn:'Entre ou cadastre-se para salvar.',verify:'Verificar email em modo de teste',verified:'Email verificado. Faça login.',registered:'Cadastro criado. Verifique o email e entre.',working:'Processando…',error:'Não foi possível concluir a ação.',loaded:'Itens revisados. Salve o pedido.',fileSize:'O arquivo deve ter no máximo 3 MB.'},
    ar:{title:'حساب العميل',intro:'طلباتك وبنودك في مكان واحد.',login:'تسجيل الدخول',register:'إنشاء حساب',password:'كلمة المرور',organization:'الشركة',consent:'أوافق على شروط معالجة البيانات',logout:'تسجيل الخروج',newRequest:'طلب جديد',newHelp:'أدخل رقم P/N واحدًا في كل سطر أو أرفق CSV/XLSX يحتوي على عمود P/N. حتى 100 بند. الحفظ لا يبدأ بحثًا مدفوعًا بالذكاء الاصطناعي.',positions:'رقم قطعة واحد في كل سطر',file:'CSV أو XLSX',preview:'مراجعة البنود',save:'حفظ الطلب',requests:'طلباتي',details:'بنود الطلب',more:'عرض المزيد',empty:'لا توجد طلبات بعد.',noRfq:'لا توجد طلبات RFQ بعد.',pending:'بانتظار البحث',count:'عدد البنود: ',saved:'حُفظ الطلب في حسابك. البحث ينتظر توفر الميزانية.',select:'اختر ملفًا أو أدخل أرقام P/N في أسطر منفصلة.',invalid:'تحقق من القائمة: من 1 إلى 100 بند غير فارغ.',signIn:'سجّل الدخول أو أنشئ حسابًا لحفظ الطلب.',verify:'تأكيد البريد في وضع الاختبار',verified:'تم تأكيد البريد. يمكنك تسجيل الدخول.',registered:'تم إنشاء الحساب. أكّد البريد ثم سجّل الدخول.',working:'جارٍ المعالجة…',error:'تعذر إكمال الإجراء.',loaded:'تمت مراجعة البنود. احفظ الطلب.',fileSize:'يجب ألا يتجاوز الملف 3 ميغابايت.'},
    zh:{title:'客户账户',intro:'集中查看您的询价与物料。',login:'登录',register:'注册',password:'密码',organization:'企业',consent:'我同意数据处理条款',logout:'退出登录',newRequest:'新询价',newHelp:'每行输入一个 P/N，或上传含 P/N 列的 CSV/XLSX，最多 100 项。保存不会启动付费 AI 搜索。',positions:'每行一个零件号',file:'CSV 或 XLSX',preview:'检查物料',save:'保存询价',requests:'我的询价',details:'询价物料',more:'显示更多',empty:'暂无询价。',noRfq:'暂无 RFQ。',pending:'等待搜索',count:'物料数：',saved:'询价已保存在账户中。搜索等待预算可用。',select:'选择文件或逐行输入 P/N。',invalid:'请检查清单：1 至 100 项非空物料。',signIn:'请登录或注册后保存询价。',verify:'在测试模式验证邮箱',verified:'邮箱已验证，请登录。',registered:'注册成功，请验证邮箱后登录。',working:'处理中…',error:'操作未完成。',loaded:'物料已检查，请保存询价。',fileSize:'文件不得超过 3 MB。'}
  };
  const params = new URLSearchParams(location.search);
  let language = copy[params.get('lang')] ? params.get('lang') : 'ru';
  let csrf = sessionStorage.getItem('geoteam_commerce_csrf') || '';
  let items = [], requestPage = 1, detailPage = 1, selectedRequest = null, requestKey = crypto.randomUUID();
  const selectedOffers = new Map();
  let quoteKey = crypto.randomUUID();
  const quoteCopy = {
    ru:['Запрос на расчёт коммерческого предложения','Выберите предложения в сохранённой заявке. GeoTeam проверит товар, пошлины и доставку до выпуска КП.','Страна получения (код ISO, например TR)','Отправить на расчёт','Выбрано предложений: ','Выбрать','Количество','Заявка на расчёт сохранена','Предварительные расчёты','Нужно выбрать хотя бы одно предложение.'],
    en:['Request a commercial calculation','Select offers from a saved search. GeoTeam will verify the item, duties and delivery before issuing a quote.','Destination country (ISO code, e.g. TR)','Submit for calculation','Offers selected: ','Select','Quantity','Calculation request saved','Preliminary calculations','Select at least one offer.'],
    tr:['Ticari hesaplama talebi','Kayıtlı aramadan teklifleri seçin. GeoTeam teklif vermeden önce ürünü, vergileri ve teslimatı doğrular.','Varış ülkesi (ISO kodu, ör. TR)','Hesaplama talep et','Seçilen teklifler: ','Seç','Miktar','Hesaplama talebi kaydedildi','Ön hesaplamalar','En az bir teklif seçin.'],
    de:['Kalkulation anfragen','Wählen Sie Angebote aus einer gespeicherten Suche. GeoTeam prüft Ware, Abgaben und Lieferung vor einem Angebot.','Zielland (ISO-Code, z. B. TR)','Kalkulation anfragen','Ausgewählte Angebote: ','Auswählen','Menge','Kalkulationsanfrage gespeichert','Vorläufige Kalkulationen','Wählen Sie mindestens ein Angebot.'],
    fr:['Demander un calcul commercial','Sélectionnez des offres enregistrées. GeoTeam vérifiera le produit, les droits et la livraison avant tout devis.','Pays de destination (code ISO, ex. TR)','Demander le calcul','Offres sélectionnées : ','Sélectionner','Quantité','Demande de calcul enregistrée','Calculs préliminaires','Sélectionnez au moins une offre.'],
    es:['Solicitar cálculo comercial','Seleccione ofertas guardadas. GeoTeam verificará el producto, los aranceles y la entrega antes de emitir una oferta.','País de destino (código ISO, p. ej. TR)','Solicitar cálculo','Ofertas seleccionadas: ','Seleccionar','Cantidad','Solicitud de cálculo guardada','Cálculos preliminares','Seleccione al menos una oferta.'],
    it:['Richiedi un calcolo commerciale','Seleziona offerte salvate. GeoTeam verificherà prodotto, dazi e consegna prima di emettere un preventivo.','Paese di destinazione (codice ISO, es. TR)','Richiedi il calcolo','Offerte selezionate: ','Seleziona','Quantità','Richiesta di calcolo salvata','Calcoli preliminari','Seleziona almeno un’offerta.'],
    pt:['Solicitar cálculo comercial','Selecione ofertas salvas. A GeoTeam verificará o produto, os direitos e a entrega antes de emitir uma cotação.','País de destino (código ISO, ex. TR)','Solicitar cálculo','Ofertas selecionadas: ','Selecionar','Quantidade','Pedido de cálculo salvo','Cálculos preliminares','Selecione pelo menos uma oferta.'],
    ar:['طلب حساب عرض تجاري','اختر العروض من بحث محفوظ. ستتحقق GeoTeam من المنتج والرسوم والتسليم قبل إصدار عرض السعر.','بلد الوجهة (رمز ISO مثل TR)','إرسال طلب الحساب','العروض المختارة: ','اختيار','الكمية','تم حفظ طلب الحساب','الحسابات الأولية','اختر عرضًا واحدًا على الأقل.'],
    zh:['申请商业报价计算','从已保存的搜索中选择报价。GeoTeam 将在出具报价前核实产品、关税和交付。','目的地国家（ISO 代码，例如 TR）','提交计算申请','已选报价：','选择','数量','计算申请已保存','初步计算','请至少选择一项报价。']
  };
  const q = index => (quoteCopy[language] || quoteCopy.en)[index];
  const estimateCopy = {
    ru:['Получатель','Юридическое лицо','Физическое лицо','Город доставки','Турция','Россия','Кыргызстан','Казахстан','Детали расчёта','Для расчёта требуются подтверждённые данные: ','Авиа','Авто','Железная дорога','Море / контейнер','Стоимость и срок уточняются','Предварительный итог','Расчёт не является коммерческим предложением.'],
    en:['Importer','Business','Individual','Delivery city','Türkiye','Russia','Kyrgyzstan','Kazakhstan','Calculation details','Verified data required: ','Air','Road','Rail','Sea / container','Cost and transit time pending','Preliminary total','This calculation is not a commercial quotation.'],
    tr:['İthalatçı','Şirket','Birey','Teslimat şehri','Türkiye','Rusya','Kırgızistan','Kazakistan','Hesaplama ayrıntıları','Doğrulanmış veriler gerekli: ','Hava','Karayolu','Demiryolu','Deniz / konteyner','Maliyet ve süre bekleniyor','Ön toplam','Bu hesaplama ticari teklif değildir.'],
    de:['Importeur','Unternehmen','Privatperson','Lieferort','Türkei','Russland','Kirgisistan','Kasachstan','Berechnungsdetails','Verifizierte Daten erforderlich: ','Luft','Straße','Bahn','See / Container','Kosten und Laufzeit offen','Vorläufige Summe','Dies ist kein verbindliches Angebot.'],
    fr:['Importateur','Entreprise','Particulier','Ville de livraison','Turquie','Russie','Kirghizistan','Kazakhstan','Détails du calcul','Données vérifiées requises : ','Air','Route','Rail','Mer / conteneur','Coût et délai à confirmer','Total provisoire','Ce calcul ne constitue pas une offre commerciale.'],
    es:['Importador','Empresa','Particular','Ciudad de entrega','Turquía','Rusia','Kirguistán','Kazajistán','Detalles del cálculo','Datos verificados necesarios: ','Aire','Carretera','Ferrocarril','Mar / contenedor','Costo y plazo pendientes','Total preliminar','Este cálculo no es una oferta comercial.'],
    it:['Importatore','Azienda','Privato','Città di consegna','Turchia','Russia','Kirghizistan','Kazakistan','Dettagli del calcolo','Dati verificati necessari: ','Aereo','Strada','Ferrovia','Mare / container','Costo e tempi da confermare','Totale preliminare','Questo calcolo non è un’offerta commerciale.'],
    pt:['Importador','Empresa','Pessoa física','Cidade de entrega','Turquia','Rússia','Quirguistão','Cazaquistão','Detalhes do cálculo','Dados verificados necessários: ','Aéreo','Rodoviário','Ferroviário','Marítimo / contentor','Custo e prazo pendentes','Total preliminar','Este cálculo não constitui proposta comercial.'],
    ar:['المستورد','شركة','فرد','مدينة التسليم','تركيا','روسيا','قيرغيزستان','كازاخستان','تفاصيل الحساب','البيانات المؤكدة المطلوبة: ','جوي','بري','سكك حديدية','بحري / حاوية','التكلفة والمدة قيد التحقق','الإجمالي الأولي','هذا الحساب ليس عرض سعر تجارياً.'],
    zh:['进口方','企业','个人','交货城市','土耳其','俄罗斯','吉尔吉斯斯坦','哈萨克斯坦','计算详情','需要核实的数据：','空运','公路','铁路','海运 / 集装箱','费用与时效待确认','初步总额','此计算并非正式商业报价。']
  };
  const e = index => (estimateCopy[language] || estimateCopy.en)[index];
  const dateText = seconds => seconds ? new Intl.DateTimeFormat(language, {dateStyle:'medium',timeStyle:'short'}).format(new Date(Number(seconds) * 1000)) : '';
  const updateSelectionCount = () => { $('selection-count').textContent = q(4) + selectedOffers.size; };
  const t = key => copy[language][key] || copy.en[key] || key;
  const startLabels = {ru:'Начать пакетный поиск',en:'Start batch search',tr:'Toplu aramayı başlat',de:'Stapelsuche starten',fr:'Lancer la recherche groupée',es:'Iniciar búsqueda por lotes',it:'Avvia ricerca multipla',pt:'Iniciar pesquisa em lote',ar:'بدء البحث الجماعي',zh:'开始批量搜索'};
  const queuedLabels = {ru:'Позиции поставлены в очередь.',en:'Positions added to the search queue.',tr:'Kalemler arama kuyruğuna eklendi.',de:'Positionen zur Suchwarteschlange hinzugefügt.',fr:'Références ajoutées à la file de recherche.',es:'Artículos añadidos a la cola de búsqueda.',it:'Articoli aggiunti alla coda di ricerca.',pt:'Itens adicionados à fila de pesquisa.',ar:'أُضيفت البنود إلى قائمة انتظار البحث.',zh:'物料已加入搜索队列。'};
  const budgetLabels = {ru:'Пакетный AI-поиск остановлен бюджетным лимитом. Заявка сохранена.',en:'The AI budget limit blocks batch search. Your request remains saved.',tr:'Yapay zekâ bütçe sınırı toplu aramayı durduruyor. Talebiniz kayıtlı.',de:'Das KI-Budgetlimit blockiert die Stapelsuche. Ihre Anfrage bleibt gespeichert.',fr:'Le budget IA bloque la recherche groupée. Votre demande reste enregistrée.',es:'El límite de presupuesto de IA bloquea la búsqueda. Su solicitud sigue guardada.',it:'Il limite del budget AI blocca la ricerca. La richiesta resta salvata.',pt:'O limite do orçamento de IA bloqueia a pesquisa. O pedido continua salvo.',ar:'حد ميزانية الذكاء الاصطناعي يمنع البحث الجماعي. طلبك محفوظ.',zh:'AI 预算限制阻止批量搜索。您的请求仍已保存。'};
  function localize() {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    $('language').value = language;
    $('page-title').textContent = t('title'); $('page-intro').textContent = t('intro');
    document.querySelectorAll('[data-i18n]').forEach(node => { node.textContent = t(node.dataset.i18n); });
    $('search-link').href = 'sourcing.html?lang=' + encodeURIComponent(language);
    document.querySelector('.brand').href = 'index.html?lang=' + encodeURIComponent(language);
    document.title = t('title') + ' · GeoTeam Global';
    $('quote-title').textContent = q(0); $('quote-help').textContent = q(1);
    $('destination-label').firstChild.textContent = q(2);
    $('importer-label').firstChild.textContent = e(0);
    $('city-label').firstChild.textContent = e(3);
    const importerOptions = $('importer-type').options;
    importerOptions[0].textContent=e(1); importerOptions[1].textContent=e(2);
    [...$('destination').options].forEach((option,index)=>{option.textContent=e(4+index);});
    $('quote-submit').textContent = q(3); updateSelectionCount();
  }
  function notice(message, error = false) { $('notice').textContent = message; $('notice').classList.toggle('error', error); }
  async function api(path, method = 'GET', payload) {
    async function refreshCsrf() {
      const response = await fetch(API + '/auth/csrf', {method:'POST',credentials:'same-origin',cache:'no-store'});
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.csrf_token) throw new Error(data.detail || 'CSRF_REFRESH_FAILED');
      csrf = data.csrf_token;
      sessionStorage.setItem('geoteam_commerce_csrf', csrf);
    }
    const protectedWrite = method !== 'GET' && !/^\/auth\/(login|register|verify)$/.test(path);
    if (protectedWrite && !csrf) await refreshCsrf();
    const headers = {};
    if (payload !== undefined) headers['Content-Type'] = 'application/json';
    if (csrf) headers['X-CSRF-Token'] = csrf;
    let response = await fetch(API + path, {method, headers, body: payload === undefined ? undefined : JSON.stringify(payload), credentials:'same-origin', cache:'no-store'});
    if (protectedWrite && response.status === 403) {
      const error = await response.clone().json().catch(() => ({}));
      if (error.detail === 'CSRF_REJECTED') {
        await refreshCsrf();
        headers['X-CSRF-Token'] = csrf;
        response = await fetch(API + path, {method, headers, body: payload === undefined ? undefined : JSON.stringify(payload), credentials:'same-origin', cache:'no-store'});
      }
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || data.message || 'HTTP ' + response.status);
    return data;
  }
  function p(parent, text, className) { const node = document.createElement('p'); node.textContent = text; if (className) node.className = className; parent.append(node); return node; }
  function showItems() {
    $('preview-list').replaceChildren();
    $('preview-count').textContent = items.length ? t('count') + items.length : '';
    items.forEach(item => { const li = document.createElement('li'); li.textContent = [item.part_number || item.requested_text, item.manufacturer].filter(Boolean).join(' · '); $('preview-list').append(li); });
    $('save').hidden = !items.length;
  }
  async function preview() {
    notice(t('working')); $('save').hidden = true;
    const file = $('file').files[0];
    try {
      if (file) {
        if (file.size > 3 * 1024 * 1024) throw new Error(t('fileSize'));
        const mime = file.name.toLowerCase().endsWith('.xlsx') ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'text/csv';
        const base64 = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onerror = () => reject(new Error('FILE_READ')); reader.onload = () => resolve(String(reader.result).split(',')[1]); reader.readAsDataURL(file); });
        const result = await api('/sourcing/preview','POST',{mime,data_base64:base64});
        items = result.items;
      } else {
        const lines = $('positions').value.split(/\r?\n/).map(line => line.trim()).filter(Boolean);
        if (!lines.length || lines.length > 100 || lines.some(line => line.length > 120)) throw new Error(t('invalid'));
        items = lines.map(line => ({requested_text:line,part_number:line}));
      }
      requestKey = crypto.randomUUID();
      showItems(); notice(t('loaded'));
    } catch (error) { items = []; showItems(); notice(error.message || t('error'), true); }
  }
  async function save() {
    if (!items.length) return;
    $('save').disabled = true; notice(t('working'));
    try {
      const result = await api('/sourcing/drafts','POST',{
        idempotency_key:requestKey, query_text:$('file').files[0]?.name || $('positions').value.slice(0,4000) || 'Procurement list',
        locale:language, items
      });
      notice(t('saved')); items = []; $('positions').value = ''; $('file').value = ''; showItems();
      sessionStorage.removeItem('geoteam_pending_positions'); requestPage = 1; await loadRequests(true);
      await openRequest(result.id);
    } catch (error) { notice(error.message || t('error'), true); }
    finally { $('save').disabled = false; }
  }
  async function loadRequests(reset = false) {
    if (reset) { $('requests').replaceChildren(); requestPage = 1; }
    const data = await api('/sourcing/requests?page=' + requestPage + '&page_size=20');
    if (!data.items.length && requestPage === 1) p($('requests'), t('empty'), 'muted');
    data.items.forEach(row => {
      const box = document.createElement('div'); box.className = 'request';
      const button = document.createElement('button'); button.type = 'button';
      button.textContent = row.query_text + ' · ' + t('count') + row.positions_total;
      button.addEventListener('click', () => openRequest(row.id)); box.append(button);
      p(box, [dateText(row.created_at),row.status === 'AWAITING_SEARCH' ? t('pending') : row.status].filter(Boolean).join(' · '), 'status'); $('requests').append(box);
    });
    $('more').hidden = data.items.length < 20; requestPage++;
  }
  async function openRequest(id, append = false) {
    selectedRequest = id;
    if (!append) { detailPage = 1; $('detail').replaceChildren(); }
    try {
      const data = await api('/sourcing/requests/' + encodeURIComponent(id) + '?page=' + detailPage + '&page_size=10');
      $('detail-panel').hidden = false;
      data.items.forEach(item => {
        const box = document.createElement('div'); box.className = 'item';
        const title = document.createElement('strong'); title.textContent = item.ordinal + '. ' + (item.part_number || item.requested_text); box.append(title);
        if (item.image) { const image = document.createElement('img'); image.src = item.image; image.alt = item.product_name || item.part_number || item.requested_text; image.loading = 'lazy'; image.style.cssText = 'display:block;max-width:min(100%,320px);max-height:220px;object-fit:contain;margin:12px auto;border-radius:12px'; image.onerror = () => image.remove(); box.append(image); }
        if (item.product_name) p(box, item.product_name);
        if (item.short_description) p(box, item.short_description);
        if (item.intended_use) p(box, item.intended_use);
        p(box, item.status === 'AWAITING_SEARCH' ? t('pending') : item.status, 'status');
        item.offers.forEach(offer => {
          const row = document.createElement('div'); row.className = 'offer-choice';
          p(row,[offer.public_offer_id,offer.country,offer.condition,offer.public_price,offer.currency].filter(Boolean).join(' · '));
          const key = [id,item.ordinal,offer.public_offer_id].join(':');
          const label = document.createElement('label'); label.className = 'offer-select';
          const check = document.createElement('input'); check.type = 'checkbox'; check.checked = selectedOffers.has(key);
          const caption = document.createElement('span'); caption.textContent = q(5);
          const qty = document.createElement('input'); qty.type = 'number'; qty.min = '1'; qty.max = '1000000'; qty.step = '1';
          qty.value = selectedOffers.get(key)?.quantity || '1'; qty.setAttribute('aria-label',q(6));
          check.addEventListener('change', () => {
            if (check.checked) selectedOffers.set(key,{request_id:id,ordinal:item.ordinal,public_offer_id:offer.public_offer_id,quantity:qty.value});
            else selectedOffers.delete(key);
            updateSelectionCount();
          });
          qty.addEventListener('change', () => { if (selectedOffers.has(key)) selectedOffers.get(key).quantity = qty.value; });
          label.append(check,caption,qty); row.append(label); box.append(row);
        });
        $('detail').append(box);
      });
      $('more-items').hidden = detailPage * 10 >= data.positions_total; detailPage++;
      $('detail-panel').scrollIntoView({behavior:'smooth',block:'start'});
    } catch (error) { notice(error.message || t('error'), true); }
  }
  async function loadRfqs() {
    try { const data = await api('/rfqs'); const rows = data.items || []; $('rfqs').replaceChildren();
      if (!rows.length) p($('rfqs'),t('noRfq'),'muted');
      rows.forEach(row => p($('rfqs'),[row.number,row.status].filter(Boolean).join(' · ')));
    } catch (error) { p($('rfqs'),t('error'),'muted'); }
  }
  async function loadQuoteDrafts() {
    const data = await api('/sourcing/quote-drafts'); $('quote-drafts').replaceChildren();
    const heading = document.createElement('h3'); heading.textContent = q(8); $('quote-drafts').append(heading);
    data.items.forEach(row => {
      const box=document.createElement('div');box.className='status';
      p(box,[dateText(row.created_at),row.destination_country,row.lines_total,row.status,row.id.slice(0,8)].join(' · '));
      const button=document.createElement('button');button.type='button';button.className='secondary';button.textContent=e(8);
      button.addEventListener('click',async()=>{
        try {
          const detail=await api('/sourcing/quote-drafts/'+encodeURIComponent(row.id));
          const target=$('quote-estimate');target.replaceChildren();
          const estimate=detail.estimate;
          if(!estimate){p(target,e(15));return;}
          estimate.lines.forEach(line=>{
            const item=document.createElement('section');item.className='panel';
            const title=document.createElement('h3');title.textContent=[line.product_name,line.part_number].filter(Boolean).join(' · ')||line.public_offer_id;item.append(title);
            const gaps=line.calculation.gaps||[];
            if(gaps.length)p(item,e(9)+gaps.join(', '),'muted');
            line.calculation.routes.forEach((route,index)=>{
              const label=e(10+index);
              p(item,label+' · '+(route.estimated_subtotal ? e(15)+': '+route.estimated_subtotal+' '+route.currency : e(14)));
            });
            target.append(item);
          });
          p(target,e(16),'muted');
        } catch(error){notice(error.message||t('error'),true);}
      });
      box.append(button);$('quote-drafts').append(box);
    });
  }
  async function load() {
    let me;
    try {
      me = await api('/me');
    } catch (error) { $('auth').hidden = false; $('account').hidden = true; notice(t('signIn')); return; }
    $('auth').hidden = true; $('account').hidden = false;
    $('identity').textContent = [me.organization_name,me.email].filter(Boolean).join(' · ');
    const sections = await Promise.allSettled([loadRequests(true),loadRfqs(),loadQuoteDrafts()]);
    if (sections.some(section => section.status === 'rejected')) notice(t('error'),true);
  }
  $('language').addEventListener('change', () => { language = $('language').value; const url = new URL(location.href); url.searchParams.set('lang',language); history.replaceState(null,'',url); localize(); });
  $('login').addEventListener('submit', async event => { event.preventDefault(); const form = new FormData(event.currentTarget); notice(t('working'));
    try { const data = await api('/auth/login','POST',{email:form.get('email'),password:form.get('password')}); csrf = data.csrf_token; sessionStorage.setItem('geoteam_commerce_csrf',csrf); notice(''); await load(); }
    catch (error) { notice(error.message || t('error'),true); }
  });
  $('register').addEventListener('submit', async event => { event.preventDefault(); const form = new FormData(event.currentTarget); notice(t('working'));
    try { const data = await api('/auth/register','POST',{email:form.get('email'),password:form.get('password'),organization_name:form.get('organization'),consent_terms:form.get('consent') === 'on'});
      notice(t('registered'));
      if (data.test_verification_token) { const button = document.createElement('button'); button.type='button'; button.textContent=t('verify');
        button.addEventListener('click', async () => { try { const verified = await api('/auth/verify','POST',{token:data.test_verification_token}); csrf=verified.csrf_token || ''; if (csrf) sessionStorage.setItem('geoteam_commerce_csrf',csrf); notice(t('verified')); if (csrf) await load(); button.remove(); } catch (error) { notice(error.message || t('error'),true); } });
        $('notice').after(button); }
    } catch (error) { notice(error.message || t('error'),true); }
  });
  $('logout').addEventListener('click', async () => { try { await api('/auth/logout','POST',{}); } finally { csrf=''; sessionStorage.removeItem('geoteam_commerce_csrf'); await load(); } });
  $('quote-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (!selectedOffers.size) { notice(q(9),true); return; }
    const button = $('quote-submit'); button.disabled = true;
    try {
      await api('/sourcing/quote-drafts','POST',{idempotency_key:quoteKey,
        destination_country:$('destination').value.trim().toUpperCase(),locale:language,
        importer_type:$('importer-type').value,destination_city:$('destination-city').value.trim(),
        lines:[...selectedOffers.values()]});
      quoteKey = crypto.randomUUID(); selectedOffers.clear(); updateSelectionCount();
      notice(q(7)); await loadQuoteDrafts();
    } catch (error) { notice(error.message || t('error'),true); }
    finally { button.disabled = false; }
  });
  $('more').addEventListener('click',() => loadRequests().catch(error => notice(error.message,true)));
  $('more-items').addEventListener('click',() => openRequest(selectedRequest,true));
  localize(); load();
})();

