#!/usr/bin/env bash
# GEOTEAM_GLOBAL: strictly READ-ONLY Timeweb VPS capacity audit.
# No installs, restarts, networking or filesystem writes.
set -u
echo '=== GEOTEAM TIMEWEB READ-ONLY PREFLIGHT ==='
date -u '+UTC=%Y-%m-%dT%H:%M:%SZ'
printf 'HOST='; hostname 2>/dev/null || true
printf 'OS='; (. /etc/os-release && echo "$PRETTY_NAME") 2>/dev/null || uname -s
printf 'ARCH='; uname -m
printf 'KERNEL='; uname -r
printf 'USER='; id -un
echo '--- CPU AND LOAD ---'
nproc 2>/dev/null || true
uptime 2>/dev/null || true
echo '--- MEMORY AND SWAP ---'
free -m 2>/dev/null || true
swapon --show --noheadings 2>/dev/null || true
echo '--- DISK USAGE (NO FILE READS) ---'
df -hT / /opt /var/lib/docker 2>/dev/null || true
echo '--- DOCKER HEALTH ---'
if command -v docker >/dev/null 2>&1; then
  docker --version 2>&1
  docker compose version 2>&1
  timeout 8 docker info --format 'DOCKER_ROOT={{.DockerRootDir}} DOCKER_CPUS={{.NCPU}} DOCKER_MEM={{.MemTotal}}' 2>&1 || true
  timeout 8 docker ps --format 'CONTAINER={{.Names}} STATUS={{.Status}} PORTS={{.Ports}}' 2>&1 || true
  timeout 10 docker stats --no-stream --format 'CONTAINER={{.Name}} RAM={{.MemUsage}} CPU={{.CPUPerc}}' 2>/dev/null | head -n 35 || true
else
  echo 'DOCKER=NOT_INSTALLED'
fi
echo '--- CURRENT LISTENING PORTS, NO ENV/SECRETS ---'
if command -v ss >/dev/null 2>&1; then
  ss -H -lnt 2>/dev/null | awk '{print "LISTEN="$4}' | sort -u | head -n 75
fi
echo '--- SERVICES (STATE ONLY) ---'
for unit in docker nginx postgresql redis-server; do
  if command -v systemctl >/dev/null 2>&1; then
    printf '%s=' "$unit"; systemctl is-active "$unit" 2>/dev/null || true
  fi
done
echo '--- DECISION GATES ---'
python3 - <<'PY'
import os
values={}
with open('/proc/meminfo', encoding='ascii') as f:
 for l in f:
  if ':' in l:
   key,v=l.split(':',1)
   if key in ('MemTotal','MemAvailable','SwapTotal'):
    values[key]=int(v.split()[0])//1024
for key in ('MemTotal','MemAvailable','SwapTotal'):
 print(f'{key}_MiB={values.get(key,"UNKNOWN")}')
print('GEOTEAM_CAN_DEPLOY=UNVERIFIED_UNTIL_HUMAN_REVIEW')
PY
echo 'NO_CHANGES_MADE=YES'
