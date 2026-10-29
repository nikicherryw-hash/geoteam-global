# GeoTeam AI Search Pilot — Installation and Security

ProductID: **GEOTEAM_GLOBAL**. API pilot allocation: **$20 approved** (USD).  
Release: **PREPARED / NOT DEPLOYED**. Current Firebase separate search site remains v18.42. No SKS/Archivist/Timeweb resources are used.

## What is actually implemented
- OpenAI Responses API with the documented `web_search` built-in tool, one bounded request with structured candidate output; model default `gpt-6.1-sol` requires actual API entitlement and live validation.
- A seller URL is accepted only when it is present among OpenAI's structured web-search sources or URL citation annotations.
- Exact code/model gating for ROTAX and common industrial P/N, including avoiding 918→916 substitution.
- Prices are **web-cited references only**, not seller-verified quotes or confirmed inventory. No model output is silently upgraded to `IN_STOCK`.
- Existing 310 GeoTeam website candidates inform the prompt via a bounded top-12 shortlist. They are never labeled as found suppliers.
- Private FastAPI `POST /internal/ai/research` requiring a server-side shared token; OFF unless explicitly enabled.
- SQLite single-instance conservative allocations: one $1 reservation per attempted OpenAI call, maximum 20 attempts, no automatic reset. **Not an OpenAI spending hard-stop**. The actual platform costs can vary and must be tracked in the OpenAI project's billing/usage page.
- Docker/Compose for a **dedicated, isolated GeoTeam-only** Linux server: unprivileged, local-only port 8088, persistent volume, one worker.

## The two remaining external prerequisites
1. In OpenAI Platform, create a *dedicated GeoTeam API project* and its restricted server key. Configure an initial $20 project budget/alerts, check whether the budget threshold is a notification rather than a hard cap, check model availability, and monitor real usage. Do not paste the key in ChatGPT, Firebase Hosting, GitHub or any client-side code.
2. Select a *dedicated GeoTeam-controlled server or isolated service* with Docker and persistent disk. Owner has authorized preparing this server but has not confirmed any actual host/provider, billing association, IP or SSH access. **Do not use the SKS Timeweb VPS or another tenant's resources**. Cloud Shell is temporary and is not a durable server.

## Preparation on the dedicated new server (after host confirmed)
Use only a repo checkout tied to a reviewed commit; leave main GeoTeam Firebase unchanged.

```bash
git clone --single-branch --branch geoteam-v18-47-openai-agent https://github.com/nikicherryw-hash/geoteam-global.git
cd geoteam-global/sourcing/search_v2
cp .env.example .env
chmod 600 .env
```

Edit `.env` privately on the server only. Set `OPENAI_API_KEY`, a cryptographically random `GEOTEAM_INTERNAL_TOKEN` (at least 32 characters), and the correct entitled model. Confirm `GEOTEAM_BUDGET_DB=/data/pilot-budget.sqlite`. Keep `GEOTEAM_AGENT_ENABLED=0` until the private acceptance test is authorized. Never commit `.env`.

```bash
docker compose -f compose.yaml config --quiet
docker compose -f compose.yaml up --build -d
curl --fail --silent http://127.0.0.1:8088/health
```

The service remains localhost-only. To test it from the host, set `GEOTEAM_AGENT_ENABLED=1` privately and restart the container. Issue an authenticated internal POST with the secret header, not from a browser:

```bash
curl --fail-with-body -sS http://127.0.0.1:8088/internal/ai/research \
  -H "Content-Type: application/json" \
  -H "X-GeoTeam-Internal-Token: ${GEOTEAM_INTERNAL_TOKEN}" \
  -d '{"query":"ROTAX 916 iS","quantity":1,"destination":"Istanbul","locale":"ru"}'
```

Do not add the internal token to a web frontend, GitHub workflow or Firebase Hosting. Before allowing public users, build and verify a separate authenticated session gateway, abuse protection, cache/limits, and final browser-side contract. The direct private API intentionally cannot be called from anonymous web clients.

## Gate checklist before any paid request
- [ ] Dedicated project/server is confirmed for GEOTEAM_GLOBAL only.
- [ ] OpenAI API account and model access tested without exposing key.
- [ ] Real billing budget/alerts and $20 allocation are confirmed.
- [ ] Persistent budget database volume is mounted and backed up.
- [ ] User authorization/rate limiting exists before public traffic.
- [ ] Host HTTPS/TLS, outbound network restrictions and logs are configured.
- [ ] No supplier scraping without source-specific permission.
- [ ] Verified official OEM model and article reference handling.
- [ ] Manual price reference vs seller-confirmed price always separated.
- [ ] Source URLs clickable, source text not treated as instructions.
- [ ] No RFQ sending, purchases, accounts, or outbound supplier contact.

## Tests and rollout
```bash
python3 -m pip install -r sourcing/search_v2/requirements.txt
python3 -m unittest discover -v -s sourcing/search_v2 -p "test_*.py"
```
CI runs deterministic mocked Responses tests with **zero** real OpenAI requests. Production URL requires a real host and successful test search from that host, then a separate staged Firebase front-end integration and HTTP/browser readback. Existing Firebase v18.42 and primary GeoTeam Hosting are unchanged by this branch.

## Rollback
On the independent server `docker compose -f compose.yaml down` stops the worker. Do not remove volumes or the budget ledger (no `down -v`). Disabling `GEOTEAM_AGENT_ENABLED` and restarting also stops model calls. No Firebase, DNS, main-site functions or current databases are modified by backend preparation.

## Critical limitations
This pilot is **not yet a complete verified-offer engine**. Built-in web search provides cited candidate price references; it does not guarantee that model saw the latest seller inventory. Seller-page verification through approved provider APIs or isolated read-only browser with egress policy must be implemented and actually verified before claiming confirmed prices/stock. Do not silently swap product models or display a historical auction as available.
