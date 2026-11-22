#!/bin/bash
# Zapis i odtworzenie stanu demonstracyjnego (baza + pliki z magazynu S3).
#
#   bash tools/demo_snapshot.sh export <katalog>   # zapisuje <katalog>/baza.dump i <katalog>/media.tar
#   bash tools/demo_snapshot.sh import <katalog>   # wgrywa je do dzialajacego stosu (nadpisuje dane)
#
# Uruchamiaj z katalogu glownego repozytorium, przy dzialajacym stosie (docker compose up -d).
# media.tar jest duze, dlatego trzymamy je w wydaniu na GitHubie, nie w repozytorium
# (patrz demo/README.md).
set -euo pipefail
export MSYS_NO_PATHCONV=1
CMD="${1:?export|import}"; DIR="${2:?katalog}"
cd "$(dirname "$0")/../infra"
U=$(grep ^POSTGRES_USER= .env | cut -d= -f2); D=$(grep ^POSTGRES_DB= .env | cut -d= -f2)
case "$DIR" in /*|?:*) ;; *) DIR="../$DIR" ;; esac

S3_PY='
import io, os, sys, tarfile, boto3
s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"], aws_access_key_id=os.environ["S3_ACCESS_KEY"],
                  aws_secret_access_key=os.environ["S3_SECRET_KEY"], region_name="us-east-1")
if sys.argv[1] == "export":
    out = tarfile.open(fileobj=sys.stdout.buffer, mode="w|")
    for b in s3.list_buckets()["Buckets"]:
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=b["Name"]):
            for o in page.get("Contents", []):
                body = s3.get_object(Bucket=b["Name"], Key=o["Key"])["Body"].read()
                ti = tarfile.TarInfo(b["Name"] + "/" + o["Key"]); ti.size = len(body)
                out.addfile(ti, io.BytesIO(body))
    out.close()
else:
    tin = tarfile.open(fileobj=sys.stdin.buffer, mode="r|")
    have = {b["Name"] for b in s3.list_buckets()["Buckets"]}
    n = 0
    for m in tin:
        if not m.isfile():
            continue
        bucket, key = m.name.split("/", 1)
        if bucket not in have:
            s3.create_bucket(Bucket=bucket); have.add(bucket)
        s3.put_object(Bucket=bucket, Key=key, Body=tin.extractfile(m).read()); n += 1
    print("wgrano", n, "plikow", file=sys.stderr)
'

case "$CMD" in
  export)
    mkdir -p "$DIR"
    docker compose exec -T postgres pg_dump -U "$U" -d "$D" -Fc -Z 9 > "$DIR/baza.dump"
    docker compose exec -T api python -c "$S3_PY" export > "$DIR/media.tar"
    ls -la "$DIR"
    ;;
  import)
    docker compose stop scheduler scraper-worker scraper-worker-render analyzer autoscaler
    docker compose cp "$DIR/baza.dump" postgres:/tmp/baza.dump
    docker compose exec -T postgres pg_restore -U "$U" -d "$D" --clean --if-exists --no-owner /tmp/baza.dump
    if [ -f "$DIR/media.tar" ]; then
      docker compose exec -T api python -c "$S3_PY" import < "$DIR/media.tar"
    else
      echo "Brak $DIR/media.tar - zrzuty reklam nie beda widoczne (pobierz z wydania na GitHubie)."
    fi
    docker compose up -d api web
    echo "Gotowe. Panel: http://localhost:7090 (zbieranie i analiza zatrzymane)."
    ;;
  *) echo "uzycie: $0 export|import <katalog>"; exit 1 ;;
esac
