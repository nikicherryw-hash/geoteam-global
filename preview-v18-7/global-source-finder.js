/* GeoTeam Global — v18.40 worldwide source discovery (NO third-party API or crawling).
 * Registry source URLs are candidates for manual search, not verified stock or prices.
 * Search provider queries are transmitted ONLY when a person clicks the outbound link.
 */
(function(root,factory){
  "use strict";
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  root.GeoTeamSourceFinder=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
"use strict";
const REGIONS=Object.freeze({
  all:[],
  russia_cis:["russia","kazakhstan","belarus","cis"],
  asia:["asia","china","korea","japan","taiwan","hong_kong","indonesia","thailand","singapore","malaysia","india"],
  europe:["europe","dach","ukraine"],
  north_america:["north_america"],
  latin_america:["latin_america"],
  turkey_mena:["turkey","middle_east","africa"],
  oceania:["oceania"]
});
const ENGINES=Object.freeze({
  google:{base:"https://www.google.com/search?q=",parameter:"q"},
  bing:{base:"https://www.bing.com/search?q=",parameter:"q"},
  yandex:{base:"https://yandex.ru/search/?text=",parameter:"text"},
  baidu:{base:"https://www.baidu.com/s?wd=",parameter:"wd"}
});
const SECTORS={
 electronics:{ru:"Электроника и автоматика",en:"Electronics & automation",tr:"Elektronik ve otomasyon"},
 aviation:{ru:"Авиационные компоненты",en:"Aviation components",tr:"Havacılık bileşenleri"},
 industrial:{ru:"Промышленное оборудование",en:"Industrial equipment",tr:"Endüstriyel ekipman"},
 manufacturer:{ru:"Производитель",en:"Manufacturer",tr:"Üretici"},
 general_b2b:{ru:"B2B-каталог",en:"B2B directory",tr:"B2B dizini"},
 marketplace:{ru:"Торговая площадка",en:"Marketplace",tr:"Pazar yeri"}
};
const WORDS={
  ru:{
    title:"Площадки для проверки поставщиков",
    subtitle:"Каталоги подобраны по товарной категории и региону. Это не результаты проверки наличия, цены или срока поставки.",
    count:"источников для проверки",search:"Поиск артикула",view:"Открыть сайт",
    status:"Данные о товаре не получены · проверьте предложение непосредственно у продавца",
    showMore:"Показать ещё источники",shown:"Показано",
    worldwide:"Искать во всём интернете",notice:"Откроется выбранная поисковая система. Запрос передаётся ей только после нажатия.",
    cardNotice:"Площадка указана в реестре кандидатов. Доступность сайта, права использования данных, поставка и контрагент не подтверждены.",
    noResults:"Для этого сочетания категории и региона пока нет подходящих источников. Попробуйте «Весь мир».",
    rfq:"Для цены с доставкой и подтверждения наличия подготовьте RFQ. Возможность поставки зависит от экспортных, таможенных и других применимых ограничений.",
    sector:"Направление",region:"Регион",number:"№",engine:"Поисковая система"
  },
  en:{
    title:"Supplier websites to investigate",
    subtitle:"Sources are selected by product type and region, not by confirmed stock, price or lead time.",
    count:"candidate sources",search:"Search part",view:"Open site",
    status:"Product data not retrieved · confirm any offer with its seller",
    showMore:"Show more sources",shown:"Showing",
    worldwide:"Search the open web",notice:"The selected search engine opens on your click. No background queries are sent.",
    cardNotice:"Candidate registry entry. Site availability, reuse rights, trade eligibility and seller identity are not verified.",
    noResults:"No matching sources registered in this category and region. Try Worldwide.",
    rfq:"For delivery-inclusive pricing and confirmed inventory, prepare an RFQ. Export, customs and other applicable restrictions remain subject to review.",
    sector:"Category",region:"Region",number:"No.",engine:"Search engine"
  },
  tr:{
    title:"Araştırılacak tedarikçi kaynakları",
    subtitle:"Kaynaklar ürün türüne ve bölgeye göre seçilir; stok, fiyat ve teslim süresi doğrulanmış değildir.",
    count:"aday kaynak",search:"Parçayı ara",view:"Siteyi aç",
    status:"Ürün verileri alınmadı · satıcıdan doğrulayın",
    showMore:"Diğer kaynakları göster",shown:"Gösterilen",
    worldwide:"Tüm internette ara",notice:"Seçilen arama motoru yalnızca tıklayınca açılır. Arka planda sorgu gönderilmez.",
    cardNotice:"Aday kaynak kaydı. Site erişimi, veri kullanım hakkı, ticari uygunluk ve satıcı doğrulanmamıştır.",
    noResults:"Bu kategori ve bölgede uygun kaynak bulunamadı. Dünya geneline bakın.",
    rfq:"Teslimat dahil fiyat ve doğrulanmış stok için RFQ hazırlayın. İhracat ve gümrük kısıtları ayrıca değerlendirilmelidir.",
    sector:"Kategori",region:"Bölge",number:"No.",engine:"Arama motoru"
  }
};
const SOURCE_TYPES={
 industrial_distributor:{ru:"Поставщик / каталог",en:"Supplier / catalog",tr:"Tedarikçi / katalog"},
 manufacturer_official:{ru:"Производитель",en:"Manufacturer",tr:"Üretici"},
 b2b_directory:{ru:"B2B-каталог",en:"B2B directory",tr:"B2B dizini"},
 retail_marketplace:{ru:"Маркетплейс",en:"Marketplace",tr:"Pazar yeri"},
 classifieds:{ru:"Частные объявления",en:"Private listings",tr:"Bireysel ilanlar"},
 used_equipment:{ru:"Б/у оборудование",en:"Used equipment",tr:"İkinci el ekipman"},
 auction:{ru:"Аукцион — статус проверить",en:"Auction — check status",tr:"Müzayede — durumu doğrulayın"},
 surplus_stock:{ru:"Складские остатки",en:"Surplus stock",tr:"Stok fazlası"},
 aviation_sources:{ru:"Авиационные источники",en:"Aviation sources",tr:"Havacılık kaynakları"}
};
const EXTRA_WORDS={
 ru:{global:"Весь мир · без географических ограничений поиска",scope:"Поиск по всем зарегистрированным источникам",listing:"Объявление не проверено: возможно продано, снято или торги завершены",priority:"Местоположение поставки влияет только на порядок результатов",breakdown:"Типы источников"},
 en:{global:"Worldwide · no regional source exclusion",scope:"All registered sources are considered",listing:"Listing not verified: it may be sold, withdrawn or the auction may have ended",priority:"Delivery location changes ranking only",breakdown:"Source types"},
 tr:{global:"Tüm dünya · bölgesel kaynak kısıtı yok",scope:"Kayıtlı tüm kaynaklar değerlendirilir",listing:"İlan doğrulanmadı: satılmış, kaldırılmış veya ihale kapanmış olabilir",priority:"Teslimat adresi yalnızca sıralamayı etkiler",breakdown:"Kaynak türleri"}
};
const ALL_SOURCE_TYPES=new Set(Object.keys(SOURCE_TYPES));
const BRAND_HINTS={
 electronics:/\b(siemens|schneider|abb|phoenix\s*contact|eaton|rockwell|allen[ -]?bradley|omron|smc|festo|bosch\s*rexroth|rexroth|mitsubishi\s*electric|danfoss|wago|ifm|beckhoff|pilz|pepperl|balluff|turck|lenze|yaskawa|fanuc|weidmuller|honeywell|texas instruments)\b/i,
 aviation:/\b(airbus|boeing|cessna|embraer|bombardier|aircraft|aviation|airframe|aerospace|helicopter)\b|(?:ми[\s-]?(?:8|17)|вертол|самол[её]т|авиаци)/i,
 industrial:/\b(pump|valve|gearbox|actuator|spindle|compressor|motor|cnc|hermle|dmg\s*mori|grundfos|wilo|sulzer|kessler|misumi|pompa|vana)\b|(?:иртыш|насос|клапан|шпиндел|подшипник|редуктор|станок|электродвигател)/i
};
let cache=null,loading=null;
function canonical(q){return String(q||"").normalize("NFKC").trim().replace(/\s+/g," ").slice(0,160)}
function classify(query,requested){
 if(["electronics","aviation","industrial","general_b2b"].includes(requested))return requested;
 const q=canonical(query),scores={electronics:0,aviation:0,industrial:0,general_b2b:1};
 if(BRAND_HINTS.electronics.test(q))scores.electronics+=8;
 if(BRAND_HINTS.aviation.test(q)||/\b(?:NAS\d{3,}|MS\d{4,}|AN\d{4,}|BAC\d{4,})\b/i.test(q))scores.aviation+=10;
 if(BRAND_HINTS.industrial.test(q))scores.industrial+=8;
 if(/\b(?:6ES7|6SL\d|3LD\d|XPSU|LC1D\d|DI52\d|FL\s*BT|[A-Z]{1,3}\d{4,}-\d{2})\b/i.test(q))scores.electronics+=4;
 if(/drawing|черт[её]ж|по\s+эскизу|manufactur|изготовлен|производств|technical drawing/i.test(q))scores.industrial+=6;
 const sorted=Object.entries(scores).sort((a,b)=>b[1]-a[1]);
 return sorted[0][1]>1?sorted[0][0]:"general_b2b";
}
function domain(url){
 const u=new URL(url);
 if(u.protocol!=="https:"||u.username||u.password||!u.hostname||u.hostname.includes("@"))throw Error("Invalid provider URL");
 return u.hostname.replace(/^www\./,"");
}
function validateRegistry(obj){
 if(!obj||obj.product_id!=="GEOTEAM_GLOBAL"||!Array.isArray(obj.sources))throw Error("Invalid GeoTeam registry");
 const seen=new Set();
 return obj.sources.filter(x=>{
   if(!x||typeof x.id!=="string"||seen.has(x.id)||typeof x.name!=="string"||typeof x.url!=="string")return false;
   if(x.segment==="logistics")return false;
   if(x.enabled!==false||x.integration_status!=="NOT_CONNECTED"||x.rights_status!=="NOT_REVIEWED")return false;
   if(!SECTORS[x.segment]||!ALL_SOURCE_TYPES.has(x.source_type))return false;
   try{domain(x.url)}catch{return false}
   seen.add(x.id);return true;
 });
}
/* We never exclude foreign providers based on IP, VPN or delivery address.
 * A recognized delivery destination may only boost relevant source ordering. */
function preferredRegion(destination,optionalRegion){
 if(optionalRegion&&optionalRegion!=="all"&&REGIONS[optionalRegion])return optionalRegion;
 const d=canonical(destination).toLowerCase();
 const hints=[
  ["russia_cis",/(?:росси|москв|санкт.петербург|казах|беларус|минск|новосибирск|russia|moscow|kazakhstan|belarus|astana|almaty)/i],
  ["turkey_mena",/(?:турц|стамбул|анталь|фетхие|анкара|t[uü]rkiye|istanbul|fethiye|ankara|izmir|dubai|uae|saudi|oman)/i],
  ["asia",/(?:кита|япони|коре|малайзи|индонези|индия|kitay|china|japan|korea|malaysia|indonesia|india|singapore|shanghai|tokyo|beijing|kuala lumpur|seoul|hong kong)/i],
  ["europe",/(?:германи|франци|итал|испан|польш|нидерланд|чехи|берлин|лондон|париж|europe|germany|france|italy|poland|spain|uk|united kingdom|berlin|london|milan|frankfurt)/i],
  ["north_america",/(?:сша|канады|канада|usa|united states|canada|new york|toronto|chicago|texas)/i],
  ["latin_america",/(?:бразили|мексик|аргентин|чили|brazil|brasil|mexico|argentina|chile|colombia|s[aã]o paulo)/i],
  ["oceania",/(?:австрали|новой зеланд|australia|new zealand|sydney|melbourne)/i]
 ];
 return hints.find(pair=>pair[1].test(d))?.[0]||"all";
}
function directRegion(src,region){
 const regions=REGIONS[region];
 return region!=="all"&&Array.isArray(regions)&&Array.isArray(src.scope)&&src.scope.some(x=>regions.includes(x));
}
function usedIntent(query,condition){
 return condition==="used"||/(?:б\/у|бывш|подержан|восстановлен|used|second.hand|pre.owned|refurbished|gebraucht|ikinci el|二手|中古|중고|usado)/i.test(query);
}
function score(src,category,region,isUsed){
 const matrix={
 electronics:{electronics:115,manufacturer:110,industrial:64,general_b2b:63,marketplace:47,aviation:18},
 aviation:{aviation:130,manufacturer:65,industrial:53,electronics:36,general_b2b:71,marketplace:50},
 industrial:{industrial:124,manufacturer:116,electronics:58,general_b2b:78,marketplace:62,aviation:29},
 general_b2b:{general_b2b:112,industrial:91,manufacturer:86,electronics:73,marketplace:80,aviation:44}
 };
 const type=src.source_type;
 let n=matrix[category]?.[src.segment]||20;
 if(isUsed){
  if(["used_equipment","surplus_stock","auction","classifieds"].includes(type))n+=74;
  if(type==="retail_marketplace")n+=29;
 }else{
  if(["industrial_distributor","manufacturer_official"].includes(type))n+=29;
  if(["used_equipment","surplus_stock","classifieds","auction"].includes(type))n+=12;
 }
 if(directRegion(src,region))n+=24;
 if((src.scope||[]).includes("global"))n+=3;
 return n-(Number(src.priority||2)-1)*5;
}
function diverseSort(sorted){
 /* Initial screen shows official/catalog, used, private and auction channels.
    The full ranked inventory remains accessible via Show more; none discarded. */
 const lanes=["industrial_distributor","manufacturer_official","used_equipment","surplus_stock","classifieds","auction","b2b_directory","retail_marketplace","aviation_sources"];
 const picked=[],used=new Set();
 for(const lane of lanes){
  const hit=sorted.find(x=>x.source_type===lane&&!used.has(x.id));
  if(hit){picked.push(hit);used.add(hit.id);}
 }
 return picked.concat(sorted.filter(x=>!used.has(x.id)));
}
function route(sources,input){
 const query=canonical(input?.part||input?.query),quantity=Number(input?.qty??input?.quantity);
 if(query.length<2||query.length>160)throw Error("Part number required");
 if(!Number.isSafeInteger(quantity)||quantity<1||quantity>999999)throw Error("Invalid quantity");
 const category=classify(query,input?.sector);
 const dest=String(input?.dest||input?.destination||"").slice(0,100);
 const priorityRegion=preferredRegion(dest,input?.region);
 const condition=String(input?.condition||"any");
 const isUsed=usedIntent(query,condition);
 const ranked=sources.map(x=>({
   id:x.id,name:x.name,segment:x.segment,scope:x.scope||[],mode:x.mode,source_type:x.source_type,
   provider_url:x.url,score:score(x,category,priorityRegion,isUsed),
   verification_status:x.verification_status||"CANDIDATE_NOT_LIVE_VERIFIED",
   listing_state:"UNKNOWN_NOT_CHECKED",search_access:"USER_CLICK_EXTERNAL_ONLY",
   requires_confirmation:true,verified_inventory:false,verified_price:false
 })).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name));
 const results=diverseSort(ranked);
 return{
   product_id:"GEOTEAM_GLOBAL",request:{query,quantity,destination:dest,condition},
   category,region:"all",preferred_region:priorityRegion,scope:"ALL_REGISTERED_PRODUCT_SOURCES",
   total:results.length,results,mode:"SOURCE_DISCOVERY_ONLY",
   price_confirmed:false,stock_confirmed:false,directory_generated_at:new Date().toISOString()
 };
}
/* Future licensed listing connector gate. It never changes the source registry
 * state, and must not claim an item AVAILABLE based on an old search snippet. */
function listingLifecycle(listing,now=new Date().toISOString()){
 const value=listing||{},nowMs=Date.parse(now);
 if(!Number.isFinite(nowMs))throw Error("Invalid evaluation timestamp");
 if(value.sold===true||value.isSold===true||/(?:^SOLD$|SOLD_OUT)/i.test(value.status||""))return "SOLD";
 if(value.ended===true||value.deleted===true||/(?:^ENDED$|^CLOSED$|^REMOVED$)/i.test(value.status||""))return "ENDED";
 const expiry=value.itemEndDate||value.endDate||value.auctionEndsAt;
 if(expiry&&Number.isFinite(Date.parse(expiry))&&Date.parse(expiry)<=nowMs)return "ENDED";
 if(["OUT_OF_STOCK","UNAVAILABLE","TEMPORARILY_UNAVAILABLE"].includes(String(value.estimatedAvailabilityStatus||value.availabilityStatus||"").toUpperCase()))return "UNAVAILABLE";
 const verifiedAt=value.verifiedAt||value.checkedAt;
 const verifiedMs=verifiedAt?Date.parse(verifiedAt):NaN;
 if(!Number.isFinite(verifiedMs)||verifiedMs>nowMs||nowMs-verifiedMs>30*60*1000)return "UNKNOWN_UNVERIFIED";
 if(["IN_STOCK","AVAILABLE"].includes(String(value.estimatedAvailabilityStatus||value.availabilityStatus||"").toUpperCase())&&value.sourceVerified===true)return "ACTIVE_CONFIRMED";
 return "UNKNOWN_UNVERIFIED";
}
async function loadRegistry(url){
 if(cache)return cache;
 if(loading)return loading;
 const path=url||new URL("data/sources.v1.json?v=41-everywhere",typeof location!=="undefined"?location.href:"https://geoteam-global.com/sourcing.html").href;
 loading=(async()=>{
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),9000);
   try{
     const res=await fetch(path,{headers:{Accept:"application/json"},credentials:"same-origin",signal:controller.signal});
     if(!res.ok)throw Error("Registry "+res.status);
     const parsed=validateRegistry(await res.json());
     if(parsed.length<30)throw Error("Incomplete source directory");
     cache=parsed;
     return cache;
   }finally{clearTimeout(timer);loading=null}
 })();
 return loading;
}
async function search(input,options){
 return route(await loadRegistry(options?.indexUrl),input);
}
function searchEngineUrl(provider,query,engine,withoutSite){
 const type=Object.prototype.hasOwnProperty.call(ENGINES,engine)?engine:"google";
 const suffix=withoutSite?"":"site:"+domain(provider.provider_url)+" ";
 return ENGINES[type].base+encodeURIComponent(suffix+canonical(query));
}
/* Native public search links avoid stale search-indexed auction pages.
 * Still not a live listing-state confirmation. Only documented common URL forms. */
function nativeSearchUrl(provider,query){
 const host=domain(provider.provider_url),q=encodeURIComponent(canonical(query));
 if(/(^|\.)ebay\.(com|de|co\.uk|com\.au|ca)$/.test(host))return "https://"+host+"/sch/i.html?_nkw="+q;
 if(/(^|\.)amazon\.(com|de|co\.uk|com\.tr|com\.au|in|ae|ca)$/.test(host))return "https://"+host+"/s?k="+q;
 if(host==="avito.ru")return "https://www.avito.ru/all?q="+q;
 if(host==="trendyol.com")return "https://www.trendyol.com/sr?q="+q;
 return null;
}
function productSearchUrl(provider,query){return searchEngineUrl(provider,query,"google",false)}
function render(target,data,options){
 const lang=["ru","en","tr"].includes(options?.lang)?options.lang:"en";
 const words=WORDS[lang],extra=EXTRA_WORDS[lang];
 const engine=Object.prototype.hasOwnProperty.call(ENGINES,options?.engine)?options.engine:"google";
 const PAGE_SIZE=12;
 target.replaceChildren();target.classList.add("is-visible","gt-source-results");
 const title=document.createElement("h3");title.className="gt-source-headline";title.textContent=words.title+" · "+data.results.length+" "+words.count;
 const description=document.createElement("p");description.className="gt-source-descr";description.textContent=extra.scope+". "+words.subtitle;
 target.append(title,description);
 const globalBox=document.createElement("div");globalBox.className="gt-worldwide-search";
 const head=document.createElement("strong");head.textContent=extra.global;
 const group=document.createElement("div");group.className="gt-worldwide-engines";
 for(const key of ["google","bing","yandex","baidu"]){
   const link=document.createElement("a");
   link.href=searchEngineUrl(null,data.request.query,key,true);
   link.target="_blank";link.rel="noopener noreferrer";
   link.textContent=key[0].toUpperCase()+key.slice(1)+" ↗";
   group.append(link);
 }
 const notice=document.createElement("small");notice.textContent=words.notice;
 globalBox.append(head,group,notice);target.append(globalBox);
 const sourceStats={classifieds:0,used_equipment:0,auction:0,retail_marketplace:0,surplus_stock:0};
 for(const r of data.results)if(Object.prototype.hasOwnProperty.call(sourceStats,r.source_type))sourceStats[r.source_type]++;
 const mix=document.createElement("p");mix.className="gt-market-mix";
 mix.textContent=extra.breakdown+": "+Object.entries(sourceStats)
 .filter(pair=>pair[1]>0).map(pair=>(SOURCE_TYPES[pair[0]]?.[lang]||pair[0])+" "+pair[1]).join(" · ");
 const geo=document.createElement("p");geo.className="gt-worldwide-geo";
 geo.textContent=extra.priority;
 target.append(mix,geo);
 if(!data.results.length){
   const empty=document.createElement("p");empty.textContent=words.noResults;target.append(empty);return;
 }
 const list=document.createElement("div");list.className="gt-source-grid";
 target.append(list);
 const more=document.createElement("button");more.type="button";more.className="gt-source-more";
 const progress=document.createElement("p");progress.className="gt-source-progress";
 let shown=0;
 function addBatch(){
   const last=Math.min(shown+PAGE_SIZE,data.results.length);
   for(;shown<last;shown++){
     const item=data.results[shown];
     const card=document.createElement("article");card.className="gt-source-card";
     const brand=document.createElement("strong");brand.textContent=item.name;
     const sector=document.createElement("span");sector.className="gt-source-sector";
     sector.textContent=SOURCE_TYPES[item.source_type]?.[lang]||SECTORS[item.segment]?.[lang]||item.segment;
     const scope=document.createElement("span");scope.className="gt-source-scope";
     scope.textContent=(item.scope||[]).join(" · ");
     const links=document.createElement("div");links.className="gt-source-links";
     const exact=document.createElement("a");exact.href=searchEngineUrl(item,data.request.query,engine,false);
     exact.target="_blank";exact.rel="noopener noreferrer";exact.className="gt-source-find";
     exact.textContent=words.search+" · "+engine+" ↗";
     const direct=document.createElement("a");direct.href=item.provider_url;direct.target="_blank";
     direct.rel="noopener noreferrer";direct.className="gt-source-direct";direct.textContent=words.view+" ↗";
     const native=nativeSearchUrl(item,data.request.query);
     links.append(exact,direct);
     if(native){
       const nativeLink=document.createElement("a");nativeLink.href=native;nativeLink.target="_blank";
       nativeLink.rel="noopener noreferrer";nativeLink.className="gt-source-direct";
       nativeLink.textContent=lang==="ru"?"Поиск внутри площадки ↗":lang==="tr"?"Platform içi arama ↗":"Search on marketplace ↗";
       links.prepend(nativeLink);
     }
     const caption=document.createElement("small");
     caption.textContent=["auction","classifieds","used_equipment","surplus_stock","retail_marketplace"].includes(item.source_type)?extra.listing:words.status;
     card.append(brand,sector,scope,links,caption);list.append(card);
   }
   progress.textContent=words.shown+" "+shown+" / "+data.results.length;
   more.hidden=shown>=data.results.length;
 }
 more.textContent=words.showMore;
 more.addEventListener("click",addBatch);
 target.append(progress,more);
 const foot=document.createElement("p");foot.className="gt-source-bottom";foot.textContent=words.rfq+" "+words.cardNotice;target.append(foot);
 addBatch();
}
return Object.freeze({
 classify,canonical,domain,validateRegistry,route,search,loadRegistry,
 productSearchUrl,nativeSearchUrl,searchEngineUrl,render,listingLifecycle,preferredRegion,usedIntent,REGIONS,ENGINES,SOURCE_TYPES
});
});
