"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const price=require("../../../../preview-v18-7/market-offers.js");
const sample=require("../../../../preview-v18-7/data/offer-references.v1.json");
const finder=require("../source-finder");
test("ROTAX 916 alias is recognized but other ROTOX machinery is not conflated",()=>{
 assert.equal(price.match("ротокс 916")?.uncertain,true);
 assert.equal(price.match("Rotax 916 iS")?.uncertain,false);
 assert.equal(price.match("ROTOX KF 457"),null);
 assert.equal(price.match("ротокс 915"),null);
 assert.equal(finder.classify("ротокс 916"),"aviation");
 assert.equal(finder.classify("rotax 916iS"),"aviation");
});
test("Prices are source-cited unconfirmed references, never live stock",()=>{
 const quotes=price.validate(sample);
 assert.equal(quotes.length,5);
 assert.ok(quotes.every(q=>q.amount>0&&q.source_url.startsWith("https://")));
 assert.ok(quotes.every(q=>q.checked_at==="2026-10-29"));
 assert.ok(quotes.every(q=>q.status!=="ACTIVE_CONFIRMED"));
 assert.ok(quotes.some(q=>q.status==="BACKORDERED"));
 assert.match(sample.disclaimer,/not live inventory/);
});
test("Invalid price amounts and stock claims are rejected",()=>{
 const bad=structuredClone(sample);
 const q=bad.products[0].quotes[0];
 bad.products[0].quotes=[{...q,amount:0},{...q,status:"ACTIVE_CONFIRMED"}];
 assert.equal(price.validate(bad).length,0);
});
