#!/usr/bin/env bash
# GEOTEAM_GLOBAL only: native Ubuntu 24.04/systemd install with model OFF by default.
set -Eeuo pipefail
umask 077
abort(){ echo "GEOTEAM_INSTALL=BLOCKED:$1"; exit 2; }
[ "$(id -u)" -eq 0 ] || abort ROOT_REQUIRED
[ -n "$GEOTEAM_SOURCE_SHA" ] || abort SHA_REQUIRED
[[ "$GEOTEAM_SOURCE_SHA" =~ ^[a-f0-9]{40}$ ]] || abort INVALID_SHA
SRC="$(pwd -P)"
for cmd in git python3 systemctl useradd curl ss tar df; do
 command -v "$cmd" >/dev/null 2>&1 || abort "MISSING_$cmd"
done
[ "$(git rev-parse HEAD)" = "$GEOTEAM_SOURCE_SHA" ] || abort WRONG_GIT_COMMIT
[ -f sourcing/search_v2/agent_service.py ] || abort NO_AGENT_CODE
[ -f sourcing/search_v2/requirements.txt ] || abort NO_REQUIREMENTS
[ -f sourcing/backend/functions/source_registry.json ] || abort NO_REGISTRY
. /etc/os-release
[ "$ID" = ubuntu ] && [ "$VERSION_ID" = 24.04 ] || abort WRONG_OS
python3 -c 'import sys;assert sys.version_info[:2] in [(3,12),(3,13)]' || abort PYTHON_NOT_TESTED
[ ! -e /opt/geoteam-global-ai ] || abort GEOTEAM_CODE_EXISTS
[ ! -e /etc/geoteam-ai ] || abort GEOTEAM_CONFIG_EXISTS
[ ! -e /var/lib/geoteam-ai ] || abort GEOTEAM_DATA_EXISTS
[ ! -e /etc/systemd/system/geoteam-ai.service ] || abort UNIT_EXISTS
! id geoteamai >/dev/null 2>&1 || abort USER_EXISTS
! ss -H -ltn '( sport = :18088 )' | grep -q . || abort PORT_BUSY
MEM="$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)"
[ "$MEM" -ge 720000 ] || abort MEMORY_PRESSURE
FREE="$(df -Pk /opt | awk 'NR==2{print $4}')"
[ "$FREE" -ge 4194304 ] || abort DISK_PRESSURE
for svc in sks-clean-tika.service nginx.service postgresql.service; do
 systemctl is-active --quiet "$svc" || abort "EXISTING_SERVICE_INACTIVE_$svc"
done
echo "GEOTEAM_PREFLIGHT=PASS SHA=$GEOTEAM_SOURCE_SHA MEM_KiB=$MEM"
install -d -m 0755 /opt/geoteam-global-ai
tar -cf - -C "$SRC" sourcing/search_v2 sourcing/backend/functions/source_registry.json | tar -xf - -C /opt/geoteam-global-ai
python3 -m venv /opt/geoteam-global-ai/.venv
/opt/geoteam-global-ai/.venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir -r /opt/geoteam-global-ai/sourcing/search_v2/requirements.txt
cd /opt/geoteam-global-ai
/opt/geoteam-global-ai/.venv/bin/python -m unittest discover -q -s sourcing/search_v2 -p 'test_*.py' || abort TESTS_FAILED
chown -R root:root /opt/geoteam-global-ai
chmod -R a+rX /opt/geoteam-global-ai
useradd --system --no-create-home --user-group --home-dir /var/lib/geoteam-ai --shell /usr/sbin/nologin geoteamai
install -d -o geoteamai -g geoteamai -m 0700 /var/lib/geoteam-ai
install -d -o root -g root -m 0700 /etc/geoteam-ai
TOKEN="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
{
 echo GEOTEAM_AGENT_ENABLED=0
 echo GEOTEAM_OPENAI_MODEL=gpt-6-luna
 echo GEOTEAM_BUDGET_DB=/var/lib/geoteam-ai/pilot-budget.sqlite
 echo GEOTEAM_INTERNAL_TOKEN="$TOKEN"
 echo OPENAI_API_KEY=
} > /etc/geoteam-ai/agent.env
unset TOKEN
chmod 0600 /etc/geoteam-ai/agent.env
cat > /etc/systemd/system/geoteam-ai.service <<'UNIT'
[Unit]
Description=GeoTeam Global AI Search (isolated, AI disabled until configured)
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=4

[Service]
Type=simple
User=geoteamai
Group=geoteamai
WorkingDirectory=/opt/geoteam-global-ai
EnvironmentFile=/etc/geoteam-ai/agent.env
ExecStart=/opt/geoteam-global-ai/.venv/bin/python -m uvicorn sourcing.search_v2.agent_service:app --host 127.0.0.1 --port 18088 --workers 1 --no-access-log
Restart=on-failure
RestartSec=15
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ProtectKernelTunables=true
ProtectControlGroups=true
ReadWritePaths=/var/lib/geoteam-ai
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
MemoryHigh=200M
MemoryMax=320M
CPUQuota=45%
TasksMax=64
OOMScoreAdjust=700

[Install]
WantedBy=multi-user.target
UNIT
chmod 0644 /etc/systemd/system/geoteam-ai.service
systemctl daemon-reload
systemctl start geoteam-ai.service
for i in 1 2 3 4 5 6 7 8 9 10; do
 curl -fsS --max-time 2 http://127.0.0.1:18088/health >/dev/null && break
 sleep 1
done
systemctl is-active --quiet geoteam-ai.service || abort SERVICE_FAILED
HEALTH="$(curl -fsS --max-time 3 http://127.0.0.1:18088/health)" || abort HEALTH_FAILED
HEALTH="$HEALTH" python3 - <<'PY'
import json,os
x=json.loads(os.environ["HEALTH"])
assert x["product_id"]=="GEOTEAM_GLOBAL"
assert x["enabled"] is False
assert x["supplier_api_connected"] is False
print("HEALTH=PASS PRODUCT=GEOTEAM_GLOBAL AI_CALLS=0")
PY
ss -H -ltn '( sport = :18088 )' | grep -q '127.0.0.1:18088' || abort NOT_LOOPBACK
systemctl enable geoteam-ai.service >/dev/null
echo "GEOTEAM_NATIVE=DEPLOYED_VERIFIED_DISABLED"
echo "SKS=UNCHANGED PORT=127.0.0.1:18088"
echo "CONFIG=/etc/geoteam-ai/agent.env SECRET_DO_NOT_SHARE"
echo "ROLLBACK=systemctl disable --now geoteam-ai.service"
