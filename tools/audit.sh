#!/usr/bin/env sh
# Skan podatnosci zaleznosci Pythona (pip-audit, baza PyPA/OSV) dla wszystkich serwisow.
# Kazdy requirements.txt jest rozwiazywany w czystym kontenerze, razem z zaleznosciami tranzytywnymi.
# Uzycie (z katalogu glownego repo): sh tools/audit.sh   -> kod wyjscia != 0 przy znalezionej podatnosci
set -eu
status=0
for req in services/*/requirements.txt; do
  echo "== $req"
  docker run --rm -v "$(pwd)/services:/services:ro" python:3.12.7-slim-bookworm sh -c \
    "pip install -q --disable-pip-version-check pip-audit==2.10.1 >/dev/null && pip-audit -r /$req --progress-spinner off" \
    || status=1
done
exit $status
