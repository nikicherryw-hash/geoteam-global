/* GeoTeam Global Source Finder v1: real, authorized supplier DIRECTORY routing.
 * This module DOES NOT query external inventory or claim verified stock/prices.
 * No credentials, scraping, third-party background requests, or RFQ sends.
 */
(function(root,factory){
  "use strict";
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  root.GeoTeamSourceFinder=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const SEGMENT_LABELS={
    electronics:{ru:"Электроника и автоматика",en:"Electronics & automation",tr:"Elektronik ve otomasyon"},
    aviation:{ru:"Авиационные компоненты",en:"Aviation components",tr:"Havacılık bileşenleri"},
    industrial:{ru:"Промышленное оборудование",en:"Industrial equipment",tr:"Endüstriyel ekipman"},
    manufacturer:{ru:"Каталоги производителей",en:"Manufacturer catalogs",tr:"Üretici katalogları"},
    general_b2b:{ru:"Международные B2B-площадки",en:"Global B2B directories",tr:"Küresel B2B platformları"},
    marketplace:{ru:"Торговые площадки",en:"Marketplaces",tr:"Pazar yerleri"}
  };
  const TXT={
    ru:{title:"Подобраны мировые источники",subtitle:"Поиск площадок по артикулу и категории. Остатки, цены и сроки поставки ещё не проверены.",results:"источников",view:"Открыть площадку",lookup:"Искать артикул",meta:"Доступ к каталогу · данные поставщика не подтверждены",none:"Для этой категории источники пока не зарегистрированы.",fallback:"Не удалось загрузить реестр источников. Повторите запрос позже.",mode:"Тип доступа",manual:"Информация поступает с сайтов поставщиков. Для подтверждённого КП добавьте позицию в RFQ.",route:"Релевантность подбора",score:"приоритет",info:"Для точного поиска откроется Google с ограничением на сайт выбранного поставщика. Запрос передаётся только после вашего нажатия."},
    en:{title:"Worldwide sourcing channels",subtitle:"Supplier directories matched to your part number and category. Stock, prices and lead times are not verified.",results:"sources",view:"Open source",lookup:"Search this part",meta:"Catalog discovery · supplier data not confirmed",none:"No matching sources are registered for this category yet.",fallback:"Source directory could not be loaded. Please try again.",mode:"Access type",manual:"Supplier data lives at each provider. Add the item to your RFQ to request a confirmed quotation.",route:"Source routing relevance",score:"priority",info:"The part search opens Google restricted to the selected provider domain. Your query is sent only when you click."},
    tr:{title:"Küresel tedarik kaynakları",subtitle:"Parça numaranız ve kategoriye göre uygun kaynaklar. Stok, fiyat ve teslim süresi henüz doğrulanmadı.",results:"kaynak",view:"Kaynağı aç",lookup:"Parçayı ara",meta:"Katalog araştırması · tedarikçi bilgileri doğrulanmadı",none:"Bu kategori için henüz kayıtlı kaynak bulunamadı.",fallback:"Kaynak dizini yüklenemedi. Lütfen tekrar deneyin.",mode:"Erişim türü",manual:"Tedarikçi verileri kendi sitelerindedir. Onaylı teklif için ürünü RFQ'ya ekleyin.",route:"Kaynak uygunluğu",score:"öncelik",info:"Parça araması, seçilen sağlayıcı alanıyla sınırlı Google araması açar. Sorgunuz yalnızca tıklamanızla iletilir."}
  };
  const STRONG_BRANDS={
    electronics:/\b(siemens|schneider|abb|phoenix\s*contact|eaton|rockwell|allen[ -]?bradley|omron|smc|festo|bosch\s*rexroth|rexroth|mitsubishi\s*electric|danfoss|wago|ifm|beckhoff|pilz|pepperl|balluff|turck|lenze|yaskawa|fanuc|sew[ -]?eurodrive|weidmuller)\b/i,
    aviation:/\b(airbus|boeing|cessna|embraer|bombardier|aircraft|aviation|airframe|turbine|jet engine|aerospace|helicopter|ми[\s-]?8|ми[\s-]?17|вертол|самол[её]т|авиаци|uçak|havacılık|uçak yedek)\b/i,
    industrial:/\b(pump|valve|gearbox|actuator|spindle|compressor|motor|cnc|hermle|dmg\s*mori|grundfos|wilo|sulzer|kessler|irt[yı]sh|иртыш|насос|клапан|шпиндел|подшипник|редуктор|станок|электродвигател|pompa|vana)\b/i
  };
  const AVIATION_NUMBERS=/\b(?:NAS\d{3,}|MS\d{4,}|AN\d{4,}|BAC\d{4,})\b/i;
  let cached=null, loading=null;
  function classify(query,requested){
    if(["electronics","aviation","industrial","general_b2b"].includes(requested))return requested;
    const q=String(query||"");
    const weights={electronics:0,aviation:0,industrial:0,general_b2b:1};
    if(STRONG_BRANDS.electronics.test(q))weights.electronics+=7;
    if(STRONG_BRANDS.aviation.test(q)||AVIATION_NUMBERS.test(q))weights.aviation+=9;
    if(STRONG_BRANDS.industrial.test(q))weights.industrial+=6;
    if(/\b(?:6ES7|6SL\d|3LD\d|XPSU|LC1D\d|DI52\d|FL\s*BT|[A-Z]{1,3}\d{4,}-\d{2})\b/i.test(q))weights.electronics+=4;
    if(/drawing|черт[её]ж|по\s+эскизу|manufactur|изготовлен|производств|technical drawing/i.test(q))weights.industrial+=6;
    const sorted=Object.entries(weights).sort((a,b)=>b[1]-a[1]);
    return sorted[0][1]>1?sorted[0][0]:"general_b2b";
  }
  function canonical(q){
    return String(q||"").normalize("NFKC").trim().replace(/\s+/g," ").slice(0,160);
  }
  function domain(url){
    const v=new URL(url);
    if(v.protocol!=="https:"||v.username||v.password||!v.hostname||v.hostname.includes("@"))throw Error("Invalid provider URL");
    return v.hostname.replace(/^www\./,"");
  }
  function validateRegistry(obj){
    if(!obj||obj.product_id!=="GEOTEAM_GLOBAL"||!Array.isArray(obj.sources))throw Error("Invalid GeoTeam registry");
    const seen=new Set();
    return obj.sources.filter(src=>{
      if(!src||typeof src.id!=="string"||seen.has(src.id)||typeof src.name!=="string"||typeof src.url!=="string")return false;
      if(src.segment==="logistics")return false;
      try{domain(src.url)}catch{return false}
      if(src.enabled!==false||src.integration_status!=="NOT_CONNECTED")return false;
      seen.add(src.id);return true;
    });
  }
  async function loadRegistry(url){
    if(cached)return cached;
    if(loading)return loading;
    const path=url||new URL("data/sources.v1.json",typeof location!=="undefined"?location.href:"https://geoteam-global.com/sourcing.html").href;
    loading=(async()=>{
      const ctrl=new AbortController();
      const timer=setTimeout(()=>ctrl.abort(),9000);
      try{
        const res=await fetch(path,{headers:{"Accept":"application/json"},signal:ctrl.signal,credentials:"same-origin"});
        if(!res.ok)throw Error("Registry HTTP "+res.status);
        const obj=await res.json();
        cached=validateRegistry(obj);
        if(!cached.length)throw Error("Empty directory");
        return cached;
      }finally{clearTimeout(timer);loading=null}
    })();
    return loading;
  }
  function scoring(source,category){
    const base={electronics:0,aviation:0,industrial:0,general_b2b:0};
    if(category==="electronics"){base.electronics=90;base.manufacturer=62;base.industrial=21;base.general_b2b=18;base.marketplace=7}
    if(category==="aviation"){base.aviation=95;base.general_b2b=25;base.industrial=12;base.marketplace=7}
    if(category==="industrial"){base.industrial=96;base.manufacturer=67;base.electronics=42;base.general_b2b=37;base.marketplace=9}
    if(category==="general_b2b"){base.general_b2b=75;base.industrial=54;base.manufacturer=45;base.electronics=44;base.aviation=27;base.marketplace=20}
    const number=base[source.segment]||0;
    return number-(source.priority-1)*5;
  }
  function route(sources,input){
    const query=canonical(input?.part||input?.query);
    const qty=Number(input?.qty??input?.quantity);
    if(query.length<2||query.length>160)throw Error("Part number is required");
    if(!Number.isSafeInteger(qty)||qty<1||qty>999999)throw Error("Invalid quantity");
    const category=classify(query,input?.sector);
    const results=sources.map(src=>({id:src.id,name:src.name,segment:src.segment,scope:src.scope||[],mode:src.mode,provider_url:src.url,score:scoring(src,category),requires_confirmation:true,verified_inventory:false,verified_price:false}))
      .filter(x=>x.score>=18).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name)).slice(0,13);
    return {product_id:"GEOTEAM_GLOBAL",request:{query,quantity:qty,destination:String(input?.dest||input?.destination||"").slice(0,100)},category,total:results.length,results,mode:"SOURCE_DISCOVERY_ONLY",price_confirmed:false,stock_confirmed:false,checked_at:new Date().toISOString()};
  }
  async function search(input,options){
    const registry=await loadRegistry(options?.indexUrl);
    return route(registry,input);
  }
  function productSearchUrl(provider,query){
    const host=domain(provider.provider_url);
    // A public search engine site: query is NOT sent until the user opens the link.
    return "https://www.google.com/search?q="+encodeURIComponent("site:"+host+" "+canonical(query));
  }
  function render(target,data,options){
    const lang=["ru","en","tr"].includes(options?.lang)?options.lang:"en",t=TXT[lang];
    target.replaceChildren();
    target.classList.add("is-visible","gt-source-results");
    const h=document.createElement("h3");
    h.className="gt-source-headline";h.textContent=t.title+" · "+data.results.length+" "+t.results;
    const description=document.createElement("p");description.className="gt-source-descr";description.textContent=t.subtitle;
    target.append(h,description);
    const meta=document.createElement("p");meta.className="gt-source-info";meta.textContent=t.info;
    target.append(meta);
    if(!data.results.length){const p=document.createElement("p");p.textContent=t.none;target.append(p);return}
    const list=document.createElement("div");list.className="gt-source-grid";
    for(const entry of data.results){
      const card=document.createElement("article");card.className="gt-source-card";
      const brand=document.createElement("strong");brand.textContent=entry.name;
      const badge=document.createElement("span");badge.className="gt-source-sector";badge.textContent=SEGMENT_LABELS[entry.segment]?.[lang]||entry.segment;
      const buttons=document.createElement("div");buttons.className="gt-source-links";
      const a=document.createElement("a");a.className="gt-source-find";a.target="_blank";a.rel="noopener noreferrer";a.href=productSearchUrl(entry,data.request.query);a.textContent=t.lookup+" ↗";
      const direct=document.createElement("a");direct.className="gt-source-direct";direct.target="_blank";direct.rel="noopener noreferrer";direct.href=entry.provider_url;direct.textContent=t.view+" ↗";
      const foot=document.createElement("small");foot.textContent=t.meta;
      buttons.append(a,direct);card.append(brand,badge,buttons,foot);list.append(card);
    }
    target.append(list);
    const notice=document.createElement("p");notice.className="gt-source-bottom";notice.textContent=t.manual;
    target.append(notice);
  }
  return Object.freeze({classify,canonical,domain,validateRegistry,route,search,loadRegistry,productSearchUrl,render});
});
