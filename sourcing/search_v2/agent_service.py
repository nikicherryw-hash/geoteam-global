"""Private-only GeoTeam AI research gateway. No browser-side API key. OFF BY DEFAULT."""
import asyncio
import hmac
import os

import httpx
from fastapi import FastAPI, Header, HTTPException
from .ai_search import search_once
from .budget import BudgetExhausted, PilotBudget
from .registry_hints import pick
from .service import SearchRequest

app=FastAPI(title="GeoTeam Global Internal AI Search",version="0.1.0",docs_url=None,redoc_url=None)
gate=asyncio.Semaphore(1)

def config_check(token):
    if os.getenv("GEOTEAM_AGENT_ENABLED")!="1":
        raise HTTPException(503,detail="AGENT_NOT_ENABLED")
    key=os.getenv("GEOTEAM_INTERNAL_TOKEN","")
    if len(key)<32:
        raise HTTPException(503,detail="INTERNAL_AUTH_NOT_CONFIGURED")
    if not isinstance(token,str) or not hmac.compare_digest(token,key):
        raise HTTPException(401,detail="Unauthorized")
    ai_key=os.getenv("OPENAI_API_KEY","")
    budget_path=os.getenv("GEOTEAM_BUDGET_DB","")
    if not ai_key or not budget_path:
        raise HTTPException(503,detail="API_KEY_OR_PERSISTENT_BUDGET_MISSING")
    model=os.getenv("GEOTEAM_OPENAI_MODEL","gpt-6.1-sol")
    if model not in {"gpt-6.1-sol","gpt-6-astra"}:
        raise HTTPException(503,detail="MODEL_NOT_APPROVED")
    return ai_key,budget_path,model

@app.get("/health")
async def health():
    return {"product_id":"GEOTEAM_GLOBAL","service":"private_ai_search",
            "enabled":os.getenv("GEOTEAM_AGENT_ENABLED")=="1",
            "seller_price_verified":False,
            "supplier_api_connected":False}

@app.post("/internal/ai/research")
async def research(req:SearchRequest,x_geoteam_internal_token: str|None=Header(default=None)):
    api_key,budget_path,model=config_check(x_geoteam_internal_token)
    async with gate:
        try:
            pilot=PilotBudget(budget_path)
            async with httpx.AsyncClient(trust_env=False,follow_redirects=False) as client:
                result=await search_once(req.query,req.locale,pick(req.query),api_key,model,client)
            # Reserve before any outbound request, not after. Keep a reservation on errors.
            result["pilot"]=pilot.status()
            return result
        except BudgetExhausted:
            raise HTTPException(429,detail="PILOT_BUDGET_EXHAUSTED")
        except (httpx.HTTPError, ValueError, RuntimeError):
            raise HTTPException(502,detail="AI_RESEARCH_FAILED_NO_UNVERIFIED_OFFERS")
