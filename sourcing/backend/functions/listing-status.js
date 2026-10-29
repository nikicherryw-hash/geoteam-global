"use strict";
/* GeoTeam listing freshness gate. Designed for REAL provider evidence in later adapters.
 * Candidate directory links never pass this gate as purchasable inventory.
 * No scraping, external requests or assumed stock.
 */
const SOLD=new Set(["sold","completed","ended","expired","withdrawn","removed","cancelled","out_of_stock","unavailable"]);
const ACTIVE=new Set(["active","available","in_stock","open","buy_now"]);
function inspectListing(record,now=new Date()){
 if(!record||typeof record!=="object")return {status:"UNVERIFIED",purchasable:false,reason:"MISSING_EVIDENCE"};
 const state=String(record.provider_status||"").trim().toLowerCase();
 const evidence=record.provider_evidence;
 if(!evidence||!evidence.source_url||!evidence.observed_at)
   return {status:"UNVERIFIED",purchasable:false,reason:"NO_PROVIDER_EVIDENCE"};
 const observation=new Date(evidence.observed_at);
 if(Number.isNaN(observation.getTime())||observation.getTime()>now.getTime())
   return {status:"UNVERIFIED",purchasable:false,reason:"INVALID_OBSERVATION"};
 if(SOLD.has(state))return {status:"INACTIVE",purchasable:false,reason:"SOLD_OR_ENDED"};
 if(record.auction_ends_at){
   const expiry=new Date(record.auction_ends_at);
   if(Number.isNaN(expiry.getTime()))return {status:"UNVERIFIED",purchasable:false,reason:"BAD_AUCTION_DATE"};
   if(expiry.getTime()<=now.getTime())return {status:"INACTIVE",purchasable:false,reason:"AUCTION_ENDED"};
 }
 if(!ACTIVE.has(state))return {status:"UNVERIFIED",purchasable:false,reason:"UNKNOWN_PROVIDER_STATE"};
 const age=now.getTime()-observation.getTime();
 const ttl=Math.max(0,Math.min(Number(record.freshness_seconds)||0,86400))*1000;
 if(ttl<=0||age>ttl)return {status:"STALE",purchasable:false,reason:"RECHECK_REQUIRED"};
 // A fresh listing is still NOT a supplier-confirmed offer or binding quote.
 return {status:"OBSERVED_ACTIVE",purchasable:false,reason:"SUPPLIER_CONFIRMATION_REQUIRED"};
}
module.exports={inspectListing};
