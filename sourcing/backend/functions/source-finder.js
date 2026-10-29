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
    subtitle:"Глобальный охват: производители, магазины, частные объявления, б/у техника и аукционы. Наличие, цена и актуальность лотов не подтверждены.",
    count:"источников для проверки",search:"Поиск артикула",view:"Открыть сайт",
    status:"Объявление не проверено: может быть продано, снято или завершено. Уточните у продавца.",
    showMore:"Показать ещё источники",shown:"Показано",
    worldwide:"Искать во всём интернете",notice:"Откроется выбранная поисковая система. Запрос передаётся ей только после нажатия.",
    cardNotice:"Площадка указана в реестре кандидатов. Доступность сайта, права использования данных, поставка и контрагент не подтверждены.",
    noResults:"Для этого сочетания категории и региона пока нет подходящих источников. Попробуйте «Весь мир».",
    rfq:"Для цены с доставкой и подтверждения наличия подготовьте RFQ. Возможность поставки зависит от экспортных, таможенных и других применимых ограничений.",
    sector:"Направление",region:"Регион",number:"№",engine:"Поисковая система"
  },
  en:{
    title:"Supplier websites to investigate",
    subtitle:"Worldwide search channels include manufacturers, retailers, private listings, used equipment and auctions. Live availability, prices and listing status are unverified.",
    count:"candidate sources",search:"Search part",view:"Open site",
    status:"Listing not verified: may be sold, withdrawn or expired. Confirm with seller.",
    showMore:"Show more sources",shown:"Showing",
    worldwide:"Search the open web",notice:"The selected search engine opens on your click. No background queries are sent.",
    cardNotice:"Candidate registry entry. Site availability, reuse rights, trade eligibility and seller identity are not verified.",
    noResults:"No matching sources registered in this category and region. Try Worldwide.",
    rfq:"For delivery-inclusive pricing and confirmed inventory, prepare an RFQ. Export, customs and other applicable restrictions remain subject to review.",
    sector:"Category",region:"Region",number:"No.",engine:"Search engine"
  },
  tr:{
    title:"Araştırılacak tedarikçi kaynakları",
    subtitle:"Küresel kapsam: üreticiler, mağazalar, özel ilanlar, ikinci el ekipman ve açık artırmalar. Stok, fiyat ve ilan durumu doğrulanmadı.",
    count:"aday kaynak",search:"Parçayı ara",view:"Siteyi aç",
    status:"İlan doğrulanmadı: satılmış veya süresi dolmuş olabilir. Satıcıdan teyit edin.",
    showMore:"Diğer kaynakları göster",shown:"Gösterilen",
    worldwide:"Tüm internette ara",notice:"Seçilen arama motoru yalnızca tıklayınca açılır. Arka planda sorgu gönderilmez.",
    cardNotice:"Aday kaynak kaydı. Site erişimi, veri kullanım hakkı, ticari uygunluk ve satıcı doğrulanmamıştır.",
    noResults:"Bu kategori ve bölgede uygun kaynak bulunamadı. Dünya geneline bakın.",
    rfq:"Teslimat dahil fiyat ve doğrulanmış stok için RFQ hazırlayın. İhracat ve gümrük kısıtları ayrıca değerlendirilmelidir.",
    sector:"Kategori",region:"Bölge",number:"No.",engine:"Arama motoru"
  }
};
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
   if(!SECTORS[x.segment])return false;
   try{domain(x.url)}catch{return false}
   seen.add(x.id);return true;
 });
}
function allowedRegion(src,region){
 if(region==="all")return true;
 const targets=REGIONS[region];
 if(!targets)return false;
 return (src.scope||[]).includes("global")||(src.scope||[]).some(v=>targets.includes(v));
}
function directRegion(src,region){
 const targets=REGIONS[region];
 return region!=="all"&&Array.isArray(targets)&&Array.isArray(src.scope)&&src.scope.some(v=>targets.includes(v));
}
function score(src,category,region){
 const scores={
 electronics:{electronics:110,manufacturer:88,industrial:39,general_b2b:36,marketplace:27},
 aviation:{aviation:125,manufacturer:51,industrial:45,electronics:37,general_b2b:48,marketplace:27},
 industrial:{industrial:116,manufacturer:102,electronics:59,general_b2b:69,marketplace:32,aviation:12},
 general_b2b:{general_b2b:110,industrial:83,manufacturer:83,electronics:67,aviation:45,marketplace:50}
 };
 const base=scores[category]?.[src.segment]||0;
 return base+(directRegion(src,region)?38:0)-(Number(src.priority||2)-1)*5;
}
function route(sources,input){
 const query=canonical(input?.part||input?.query);
 const quantity=Number(input?.qty??input?.quantity);
 const region="all"; // Universal search: never narrow scope by IP, VPN or selected geography.
 if(query.length<2||query.length>160)throw Error("Part number required");
 if(!Number.isSafeInteger(quantity)||quantity<1||quantity>999999)throw Error("Invalid quantity");
 const category=classify(query,input?.sector);
 const results=sources.filter(x=>allowedRegion(x,region)).map(x=>({
   id:x.id,name:x.name,segment:x.segment,scope:x.scope||[],mode:x.mode,
   provider_url:x.url,score:score(x,category,region),
   verification_status:x.verification_status||"CANDIDATE_NOT_LIVE_VERIFIED",
   market_channel:x.market_channel||"directory",listing_status:"NOT_CHECKED",
   requires_confirmation:true,verified_inventory:false,verified_price:false
 })).filter(x=>x.score>=25)
 .sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name));
 return{
   product_id:"GEOTEAM_GLOBAL",request:{query,quantity,destination:String(input?.dest||input?.destination||"").slice(0,100)},
   category,region,total:results.length,results,mode:"SOURCE_DISCOVERY_ONLY",
   price_confirmed:false,stock_confirmed:false,checked_at:new Date().toISOString()
 };
}
async function loadRegistry(url){
 if(cache)return cache;
 if(loading)return loading;
 const path=url||new URL("data/sources.v1.json?v=41-universal",typeof location!=="undefined"?location.href:"https://geoteam-global.com/sourcing.html").href;
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
function productSearchUrl(provider,query){return searchEngineUrl(provider,query,"google",false)}
function render(target,data,options){
 const lang=["ru","en","tr"].includes(options?.lang)?options.lang:"en";
 const words=WORDS[lang];
 const engine=Object.prototype.hasOwnProperty.call(ENGINES,options?.engine)?options.engine:"google";
 const PAGE_SIZE=12;
 target.replaceChildren();target.classList.add("is-visible","gt-source-results");
 const title=document.createElement("h3");title.className="gt-source-headline";title.textContent=words.title+" · "+data.results.length+" "+words.count;
 const description=document.createElement("p");description.className="gt-source-descr";description.textContent=words.subtitle;
 target.append(title,description);
 const globalBox=document.createElement("div");globalBox.className="gt-worldwide-search";
 const head=document.createElement("strong");head.textContent=words.worldwide;
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
     const kinds={classifieds:{ru:"Частные объявления",en:"Private listings",tr:"Özel ilanlar"},retail:{ru:"Магазин / маркетплейс",en:"Retail / marketplace",tr:"Mağaza / pazar yeri"},used_equipment:{ru:"Б/у оборудование",en:"Used machinery",tr:"İkinci el makina"},auction:{ru:"Аукцион — проверить статус",en:"Auction — check status",tr:"Açık artırma — durumu kontrol edin"}};
     sector.textContent=kinds[item.market_channel]?.[lang]||SECTORS[item.segment]?.[lang]||item.segment;
     const scope=document.createElement("span");scope.className="gt-source-scope";
     scope.textContent=(item.scope||[]).join(" · ");
     const links=document.createElement("div");links.className="gt-source-links";
     const exact=document.createElement("a");exact.href=searchEngineUrl(item,data.request.query,engine,false);
     exact.target="_blank";exact.rel="noopener noreferrer";exact.className="gt-source-find";
     exact.textContent=words.search+" · "+engine+" ↗";
     const direct=document.createElement("a");direct.href=item.provider_url;direct.target="_blank";
     direct.rel="noopener noreferrer";direct.className="gt-source-direct";direct.textContent=words.view+" ↗";
     links.append(exact,direct);
     const caption=document.createElement("small");caption.textContent=words.status;
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
 productSearchUrl,searchEngineUrl,render,REGIONS,ENGINES
});
});
