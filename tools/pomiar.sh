#!/bin/bash
# Rejestrator przebiegu testu: co INTERWAL sekund dopisuje wiersz do CSV.
# Uzycie (z katalogu infra/): bash ../tools/pomiar.sh <plik.csv> [interwal_s]
set -u
OUT="$1"; INTERWAL="${2:-30}"
U=$(grep ^POSTGRES_USER= .env | cut -d= -f2); D=$(grep ^POSTGRES_DB= .env | cut -d= -f2)
KOLEJKI="q:ingest q:ingest:fb q:render q:render:fb q:render:yt q:fetch:www q:render:tt q:gpu"
if [ ! -f "$OUT" ]; then
  echo "czas,facebook,youtube,www,www_live,tiktok,materialy_razem,wyniki,wysokie,srednie,niskie,poza_zakresem,$(echo $KOLEJKI | tr ' ' ','),kontenery_analizy,gpu_proc,gpu_mb" > "$OUT"
fi
while true; do
  t=$(date +%H:%M:%S)
  src=$(docker compose exec -T postgres psql -U "$U" -d "$D" -tAF, -c \
    "select coalesce(sum((source='facebook')::int),0), coalesce(sum((source='youtube')::int),0), coalesce(sum((source='www')::int),0), coalesce(sum((source='www_live')::int),0), coalesce(sum((source like 'tiktok%')::int),0), count(*) from cases" 2>/dev/null | tr -d '\r')
  fnd=$(docker compose exec -T postgres psql -U "$U" -d "$D" -tAF, -c \
    "select count(*), coalesce(sum((risk_level='high')::int),0), coalesce(sum((risk_level='medium')::int),0), coalesce(sum((risk_level='low')::int),0), coalesce(sum((routing::text like '%out_of_scope%')::int),0) from findings" 2>/dev/null | tr -d '\r')
  q=""
  for k in $KOLEJKI; do q="$q,$(docker compose exec -T valkey valkey-cli llen rq:queue:$k 2>/dev/null | tr -d '\r')"; done
  an=$(docker ps --filter name=investwatch-analyzer --format x | wc -l)
  gpu=$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null | tr -d ' ')
  echo "$t,${src:-,,,,,},${fnd:-,,,,}$q,$an,${gpu:-,}" >> "$OUT"
  sleep "$INTERWAL"
done
