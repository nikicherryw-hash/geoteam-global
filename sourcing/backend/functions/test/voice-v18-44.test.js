"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const voice=require("../../../../preview-v18-7/voice-search.js");
test("voice transcript parses Russian part, quantity, and delivery",()=>{
 const r=voice.parse("Найди ротокс 916 2 штуки доставка в Стамбул");
 assert.equal(r.query,"ротокс 916");
 assert.equal(r.quantity,2);
 assert.equal(r.destination,"Стамбул");
});
test("voice supports English and Turkish product requests",()=>{
 const en=voice.parse("Find Siemens 6ES7315-2EH14-0AB0 3 pcs delivery to Frankfurt");
 assert.equal(en.query,"Siemens 6ES7315-2EH14-0AB0");
 assert.equal(en.quantity,3);
 assert.equal(en.destination,"Frankfurt");
 const tr=voice.parse("Bul Grundfos CRN32 4 adet teslimat yeri Ankara");
 assert.equal(tr.query,"Grundfos CRN32");
 assert.equal(tr.quantity,4);
 assert.equal(tr.destination,"Ankara");
});
test("voice never invents a destination or part number",()=>{
 assert.deepEqual(voice.parse(""),{query:"",quantity:null,destination:"",condition:"any"});
 assert.equal(voice.parse("найди UNKNOWN-992871").query,"UNKNOWN-992871");
 assert.equal(voice.parse("найди UNKNOWN-992871").destination,"");
});
test("voice recognizes item state conservatively",()=>{
 assert.equal(voice.parse("Найди Wilo Rexa б/у 1 шт").condition,"used");
 assert.equal(voice.parse("найди насос Иртыш новый 4 шт").condition,"new");
});
