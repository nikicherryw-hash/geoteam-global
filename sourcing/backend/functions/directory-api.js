"use strict";
/**
 * GeoTeam public source-directory API.
 * No supplier API calls, stock, vendor price, persistence, or outbound RFQs.
 * Mount behind same-origin /api/sourcing/* only after production preflight.
 */
const finder=require("./source-finder.js");
const registry=require("./source_registry.json");
const sources=finder.validateRegistry(registry);
const MAKERS=[
 "Siemens","Schneider Electric","ABB","Phoenix Contact","Eaton","Rockwell Automation",
 "Omron","SMC","Festo","Bosch Rexroth","Danfoss","WAGO","Beckhoff","Pilz",
 "Pepperl+Fuchs","Balluff","Grundfos","Wilo","Sulzer","Kessler",
 "Boeing","Airbus","Embraer","Bombardier"
];
const minute=new Map();
const WINDOW=60_000,LIMIT=35,MAX_KEYS=5000;
function rateAllowed(key,now=Date.now()){
 const id=String(key||"anonymous").slice(0,180),rec=minute.get(id);
 if(minute.size>MAX_KEYS){for(const [k,v] of minute){if(now>=v.until)minute.delete(k);if(minute.size<=MAX_KEYS/2)break;}if(minute.size>MAX_KEYS)minute.clear();}
 if(!rec||now>=rec.until){minute.set(id,{count:1,until:now+WINDOW});return true}
 rec.count++;return rec.count<=LIMIT;
}
function getParam(req,name){
 const p=req.query?.[name];
 return typeof p==="string"?p:Array.isArray(p)?p[0]:"";
}
function send(res,status,payload){
 res.set("Cache-Control","no-store");
 res.set("X-Content-Type-Options","nosniff");
 res.status(status).json(payload);
}
function sourceApi(req,res){
 const path=String(req.path||"/");
 if(req.method!=="GET"){res.set("Allow","GET");return send(res,405,{ok:false,error:"METHOD_NOT_ALLOWED"})}
 if(!["/api/sourcing/search","/api/sourcing/suggest","/api/sourcing/health"].includes(path))return send(res,404,{ok:false,error:"NOT_FOUND"});
 const key=(req.ip||req.socket?.remoteAddress||"unknown").slice(0,180);
 if(!rateAllowed(key))return send(res,429,{ok:false,error:"RATE_LIMITED"});
 if(path==="/api/sourcing/health")return send(res,200,{ok:true,product_id:"GEOTEAM_GLOBAL",mode:"SOURCE_DISCOVERY_ONLY",source_count:sources.length});
 if(path==="/api/sourcing/suggest"){
   const q=finder.canonical(getParam(req,"q"));
   if(q.length<2)return send(res,200,{suggestions:[]});
   const needle=q.toLowerCase();
   const suggestions=MAKERS.filter(x=>x.toLowerCase().includes(needle)).slice(0,7).map(x=>({label:x,value:x,type:"maker"}));
   return send(res,200,{suggestions});
 }
 try{
   const q=getParam(req,"query"),quantity=Number(getParam(req,"quantity")),destination=getParam(req,"destination"),sector=getParam(req,"sector");
   if(q.length>160||destination.length>100||destination.length<2)return send(res,422,{ok:false,error:"INVALID_QUERY"});
   const result=finder.route(sources,{query:q,quantity,destination,sector});
   return send(res,200,{ok:true,...result});
 }catch(e){return send(res,422,{ok:false,error:"INVALID_QUERY"})}
}
module.exports={sourceApi,rateAllowed};
