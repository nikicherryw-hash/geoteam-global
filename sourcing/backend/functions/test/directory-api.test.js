"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const finder=require("../source-finder");
const registry=require("../source_registry.json");
const {sourceApi,rateAllowed}=require("../directory-api");
const sources=finder.validateRegistry(registry);
const checks=[
 ["Siemens 6ES7315-2EH14-0AB0","electronics"],
 ["Schneider LC1D32P7","electronics"],
 ["Boeing 737 actuator","aviation"],
 ["Airbus A320 P/N 2042M67P02","aviation"],
 ["Насос Иртыш ПФ2","industrial"],
 ["Клапан обратный Ду150","industrial"],
 ["Manufacturing to drawing","industrial"],
 ["BOM custom equipment","general_b2b"],
 ["Шпиндель HERMLE","industrial"],
 ["Вертолет Ми-17","aviation"],
 ["Phoenix Contact 2866022","electronics"]
];
test("sources are safe, unique and deliberately NOT connected",()=>{
 assert.equal(registry.product_id,"GEOTEAM_GLOBAL");
 assert.equal(registry.sources.length,269);
 assert.equal(sources.length,266);
 assert.equal(new Set(registry.sources.map(x=>x.id)).size,registry.sources.length);
 for(const source of registry.sources){
   assert.equal(source.enabled,false);
   assert.equal(source.integration_status,"NOT_CONNECTED");
   assert.equal(source.rights_status,"NOT_REVIEWED");
 }
});
for(const [part,category] of checks){
 test("routes "+part,()=>{
   const r=finder.route(sources,{part,qty:2,dest:"Istanbul, Türkiye"});
   assert.equal(r.category,category);
   assert.ok(r.results.length>0);
   assert.ok(r.results.every(x=>x.requires_confirmation&&!x.verified_inventory&&!x.verified_price));
   assert.equal(r.mode,"SOURCE_DISCOVERY_ONLY");
 });
}
function mock(path,query={},method="GET",ip="client-"+Math.random()){
 const res={statusCode:0,headers:{},body:null,
    set(k,v){this.headers[k]=v;return this},
    status(n){this.statusCode=n;return this},
    json(value){this.body=value;return this}};
 sourceApi({path,query,method,ip},res);
 return res;
}
test("health reports directory-only and 266 candidates",()=>{
 const r=mock("/api/sourcing/health");
 assert.equal(r.statusCode,200);assert.equal(r.body.source_count,266);
 assert.equal(r.body.mode,"SOURCE_DISCOVERY_ONLY");
});
test("GET search returns honest unverified source results",()=>{
 const r=mock("/api/sourcing/search",{query:"Siemens 6ES7315",quantity:"2",destination:"Istanbul"});
 assert.equal(r.statusCode,200);
 assert.ok(r.body.results.length>0);
 assert.equal(r.body.price_confirmed,false);
 assert.equal(r.body.stock_confirmed,false);
});
test("validation and method gates",()=>{
 assert.equal(mock("/api/sourcing/search",{query:"ABB",quantity:"0",destination:"Istanbul"}).statusCode,422);
 assert.equal(mock("/api/sourcing/search",{query:"ABB",quantity:"1",destination:""}).statusCode,422);
 assert.equal(mock("/api/sourcing/search",{},"POST").statusCode,405);
 assert.equal(mock("/api/sourcing/unknown").statusCode,404);
});
test("suggestions are reference hints only",()=>{
 const r=mock("/api/sourcing/suggest",{q:"siem"});
 assert.equal(r.statusCode,200);
 assert.ok(r.body.suggestions.some(x=>x.value==="Siemens"));
 assert.ok(r.body.suggestions.every(x=>x.type==="maker"));
});
test("rate limit is bounded per client key",()=>{
 const ip="unit-"+Math.random();
 const now=10000;
 for(let n=0;n<35;n++) assert.equal(rateAllowed(ip,now),true);
 assert.equal(rateAllowed(ip,now),false);
 assert.equal(rateAllowed(ip,now+60001),true);
});
test("unsafe source URL is rejected",()=>{
 const copy=JSON.parse(JSON.stringify(registry));copy.sources[0].url="javascript:alert(1)";
 assert.equal(finder.validateRegistry(copy).length,sources.length-1);
});


test("all 266 sources are considered worldwide regardless of chosen region",()=>{
 const sample={part:"Насос Иртыш ПФ2",qty:1,dest:"Istanbul",condition:"any"};
 const world=finder.route(sources,{...sample,region:"all"});
 const ru=finder.route(sources,{...sample,region:"russia_cis"});
 const asia=finder.route(sources,{...sample,region:"asia"});
 assert.equal(world.total,266);
 assert.equal(ru.total,266);
 assert.equal(asia.total,266);
 assert.ok(world.results.some(x=>x.id==="avito_ru"));
 assert.ok(world.results.some(x=>x.id==="trendyol_tr"));
 assert.ok(world.results.some(x=>x.id==="olx_br"));
 assert.ok(world.results.some(x=>x.id==="machinio"));
 assert.ok(world.results.some(x=>x.id==="kitmondo"));
 assert.ok(ru.results.some(x=>x.id==="etm_ru"));
 assert.ok(asia.results.some(x=>x.id==="china_1688"));
 assert.ok(world.results.every(x=>x.listing_state==="UNKNOWN_NOT_CHECKED"&&!x.verified_inventory&&!x.verified_price));
});
test("customer destination influences rank, not available coverage",()=>{
 const ru=finder.route(sources,{part:"Siemens 6ES7",qty:1,dest:"Москва",region:"all"});
 const tr=finder.route(sources,{part:"Siemens 6ES7",qty:1,dest:"Istanbul",region:"all"});
 assert.equal(ru.preferred_region,"russia_cis");
 assert.equal(tr.preferred_region,"turkey_mena");
 assert.equal(ru.region,"all");
 assert.equal(tr.region,"all");
 assert.equal(ru.total,tr.total);
 assert.equal(finder.preferredRegion("Kuala Lumpur"),"asia");
 assert.equal(finder.preferredRegion("São Paulo"),"latin_america");
});
test("used machinery and auctions appear near top and are NOT confirmed listings",()=>{
 const r=finder.route(sources,{part:"used Siemens 6ES7",qty:1,dest:"Berlin",condition:"used"});
 assert.equal(r.total,266);
 assert.ok(r.results.slice(0,12).some(x=>x.source_type==="used_equipment"));
 assert.ok(r.results.slice(0,12).some(x=>x.source_type==="classifieds"));
 assert.ok(r.results.slice(0,12).some(x=>x.source_type==="auction"));
 assert.ok(r.results.slice(0,12).some(x=>x.source_type==="surplus_stock"));
 assert.ok(r.results.every(x=>x.search_access==="USER_CLICK_EXTERNAL_ONLY"));
});
test("listing status rejects ended, sold, stale and unsupported offers",()=>{
 const now="2026-10-29T12:00:00Z";
 assert.equal(finder.listingLifecycle({itemEndDate:"2026-10-28T23:00:00Z",sourceVerified:true,estimatedAvailabilityStatus:"AVAILABLE",verifiedAt:now},now),"ENDED");
 assert.equal(finder.listingLifecycle({sold:true},now),"SOLD");
 assert.equal(finder.listingLifecycle({availabilityStatus:"OUT_OF_STOCK"},now),"UNAVAILABLE");
 assert.equal(finder.listingLifecycle({availabilityStatus:"AVAILABLE",sourceVerified:true,verifiedAt:"2026-10-29T10:00:00Z"},now),"UNKNOWN_UNVERIFIED");
 assert.equal(finder.listingLifecycle({availabilityStatus:"AVAILABLE",sourceVerified:false,verifiedAt:now},now),"UNKNOWN_UNVERIFIED");
 assert.equal(finder.listingLifecycle({availabilityStatus:"AVAILABLE",sourceVerified:true,verifiedAt:now},now),"ACTIVE_CONFIRMED");
 assert.equal(finder.listingLifecycle({},now),"UNKNOWN_UNVERIFIED");
});
test("country-specific catalogs require explicit click; engine URLs use HTTPS",()=>{
 const p={provider_url:"https://www.elec.ru/"};const q="Siemens 6ES7315";
 const outputs=["google","bing","yandex","baidu"].map(engine=>finder.searchEngineUrl(p,q,engine,false));
 assert.ok(outputs.every(x=>x.startsWith("https://")));
 assert.ok(outputs[2].includes("yandex.ru/search/?text="));
 assert.ok(outputs[3].includes("baidu.com/s?wd="));
 assert.ok(outputs.every(x=>decodeURIComponent(x).includes("site:elec.ru")));
 const globalSearch=finder.searchEngineUrl(null,q,"google",true);
 assert.ok(decodeURIComponent(globalSearch).endsWith(q));
});
test("future API honors market-region routing",()=>{
 const req={query:"Насос Иртыш ПФ2",quantity:"2",destination:"Istanbul",region:"russia_cis"};
 const rr=mock("/api/sourcing/search",req);
 assert.equal(rr.statusCode,200);
 assert.equal(rr.body.region,"all");
 assert.equal(rr.body.preferred_region,"russia_cis");
 assert.equal(rr.body.total,266);
 assert.ok(rr.body.results.some(x=>x.id==="pulscen"));
 assert.equal(mock("/api/sourcing/search",{...req,region:"mars"}).statusCode,422);
});

test("native marketplace search links use current platform search, not old snippets",()=>{
 const link=finder.nativeSearchUrl({provider_url:"https://www.ebay.com/"},"Siemens 6ES7315");
 assert.ok(link.startsWith("https://ebay.com/sch/i.html?_nkw="));
 assert.ok(link.includes("Siemens%206ES7315"));
 const amazon=finder.nativeSearchUrl({provider_url:"https://www.amazon.com.tr/"},"ABB DI524");
 assert.ok(amazon.includes("/s?k="));
 assert.equal(finder.nativeSearchUrl({provider_url:"https://www.machinio.com/"},"ABB DI524"),null);
});

test("multilingual discovery preserves requested OEM identifiers and requires user click",()=>{
 const pump=finder.multilingualVariants("Насос Иртыш ПФ2");
 assert.ok(pump.length>=6);
 assert.ok(pump.some(x=>x.locale==="ZH"&&x.query.includes("泵")));
 assert.ok(pump.some(x=>x.locale==="EN"&&x.query.includes("pump")));
 assert.ok(pump.every(x=>x.query.includes("Иртыш ПФ2")));
 const valve=finder.multilingualVariants("Клапан Ду150 Ру10");
 assert.ok(valve.some(x=>x.locale==="DE"&&x.query.includes("Ventil")));
 assert.ok(valve.some(x=>x.locale==="ZH"&&x.query.includes("阀门")));
 assert.deepEqual(finder.multilingualVariants("6ES7315-2EH14-0AB0"),[]);
});
test("static registry candidates are never treated as active supplier offers",()=>{
 const sources=finder.validateRegistry(registry);
 assert.equal(sources.length,266);
 const r=finder.route(sources,{part:"Siemens 6ES7",qty:2,dest:"Frankfurt",condition:"any"});
 assert.equal(r.total,266);
 assert.ok(r.results.every(x=>x.listing_state==="UNKNOWN_NOT_CHECKED"));
 assert.ok(r.results.every(x=>x.verified_inventory===false&&x.verified_price===false));
 assert.equal(r.scope,"ALL_REGISTERED_PRODUCT_SOURCES");
 assert.equal(r.directory_generated_at?.length>0,true);
});
