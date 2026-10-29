"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const finder = require("../source-finder");
const registry = require("../source_registry.json");
const sources = finder.validateRegistry(registry);
const queries = [
  "Siemens 6ES7315-2EH14-0AB0",
  "Schneider XPSUAF13AP",
  "ABB DI524",
  "Phoenix Contact FL BT EPA 2692788",
  "Eaton DIL M170",
  "Rockwell Allen-Bradley 1769-IQ16",
  "Omron E2E-X5ME1",
  "SMC SY3120-5LZD",
  "Festo VUVG-L10",
  "Bosch Rexroth hydraulic valve",
  "Grundfos CRN32-6",
  "Wilo Rexa pump",
  "Насос Иртыш ПФ2",
  "Клапан обратный Ду150 Ру10",
  "Franz Kessler 695.922-17",
  "Boeing 737 actuator",
  "Airbus A320 spare part",
  "NAS6204-24",
  "Used CNC machining center",
  "Second hand industrial spindle",
  "Aufzug Ersatzteil 42-B4",
  "pompa ikinci el 220V",
  "工业泵 50Hz",
  "中고 산업용 모터 220V",
  "bomba industrial usada",
  "custom part drawing 501-99",
  "UNKNOWN-OEM-9999",
  "hydraulic bearing 6205"
];
test("v18.42 source coverage is 310 products and three logistics candidates", () => {
  assert.equal(registry.sources.length,313);
  assert.equal(sources.length,310);
  assert.equal(new Set(sources.map(x=>x.id)).size,310);
  assert.equal(new Set(sources.map(x=>x.url)).size,310);
  for(const x of registry.sources){
    assert.equal(x.integration_status,"NOT_CONNECTED");
    assert.equal(x.enabled,false);
    assert.equal(x.rights_status,"NOT_REVIEWED");
  }
});
for(const query of queries){
  test("worldwide, evidence-safe search "+query,()=>{
    const result=finder.route(sources,{query,qty:2,dest:"Istanbul, Türkiye",condition:"any"});
    assert.equal(result.scope,"ALL_REGISTERED_PRODUCT_SOURCES");
    assert.equal(result.region,"all");
    assert.equal(result.total,310);
    assert.equal(result.results.length,310);
    assert.equal(result.mode,"SOURCE_DISCOVERY_ONLY");
    assert.ok(result.results.every(x=>x.listing_state==="UNKNOWN_NOT_CHECKED"));
    assert.ok(result.results.every(x=>x.verified_price===false && x.verified_inventory===false));
    assert.ok(result.results.every(x=>x.requires_confirmation===true));
    assert.equal(new Set(result.results.map(x=>x.id)).size,310);
  });
}
test("delivery location and VPN-like hints do not exclude sourcing markets",()=>{
  const variants=["Frankfurt, Germany","Fethiye, Türkiye","São Paulo, Brasil","Cape Town, South Africa","Sydney, Australia","Tokyo, Japan","Moscow, Russia"];
  for(const dest of variants){
    const result=finder.route(sources,{query:"6ES7315-2EH14-0AB0",qty:1,dest,region:"asia"});
    assert.equal(result.total,310, dest);
    assert.equal(result.region,"all",dest);
  }
});
test("four search engines only construct explicit user-click links",()=>{
  for(const engine of ["google","bing","yandex","baidu"]){
    const url=finder.searchEngineUrl(null,"Siemens 6ES7315-2EH14-0AB0",engine,true);
    const parsed=new URL(url);
    assert.equal(parsed.protocol,"https:");
    assert.ok(parsed.search.includes("Siemens") || parsed.search.includes("6ES7"));
  }
  const site=finder.searchEngineUrl({provider_url:"https://www.mouser.com/"}, "ABB DI524","google",false);
  assert.ok(decodeURIComponent(site).includes("site:mouser.com"));
});
test("expired auctions and sold items cannot be called current offers",()=>{
  const now="2026-10-29T12:00:00Z";
  assert.equal(finder.listingLifecycle({sold:true},now),"SOLD");
  assert.equal(finder.listingLifecycle({endDate:"2026-10-20T10:00:00Z"},now),"ENDED");
  assert.equal(finder.listingLifecycle({estimatedAvailabilityStatus:"IN_STOCK",sourceVerified:true,verifiedAt:"2026-10-28T10:00:00Z"},now),"UNKNOWN_UNVERIFIED");
  assert.equal(finder.listingLifecycle({estimatedAvailabilityStatus:"IN_STOCK",sourceVerified:true,verifiedAt:"2026-10-29T11:59:00Z"},now),"ACTIVE_CONFIRMED");
  assert.equal(finder.listingLifecycle({estimatedAvailabilityStatus:"IN_STOCK"},now),"UNKNOWN_UNVERIFIED");
});
