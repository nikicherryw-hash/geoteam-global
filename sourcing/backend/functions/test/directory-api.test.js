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
 assert.equal(registry.sources.length,44);
 assert.equal(sources.length,41);
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
test("health reports directory-only and 41 candidates",()=>{
 const r=mock("/api/sourcing/health");
 assert.equal(r.statusCode,200);assert.equal(r.body.source_count,41);
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
