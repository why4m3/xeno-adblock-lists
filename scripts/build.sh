#!/usr/bin/env bash
# Полная сборка xeno-ads.dat:
#   1. build_lists.py качает источники и пишет build/data/{ads,ads-strict}
#   2. domain-list-community (зафиксированный коммит) собирает из них .dat
#   3. verify_dat.py читает готовый .dat и ещё раз проверяет critical.txt
# Требуется: python3, go, git. Результат в build/publish/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${OUT:-$ROOT/build}"
# Коммит v2fly/domain-list-community, которым собирается .dat (меняется вручную).
DLC_REPO="https://github.com/v2fly/domain-list-community"
DLC_COMMIT="${DLC_COMMIT:-3119c9698e93ecf05b388a69b031beb2d2364a53}"
DAT_NAME="xeno-ads.dat"

rm -rf "$OUT/data" "$OUT/publish"
mkdir -p "$OUT/publish"

python3 "$ROOT/scripts/build_lists.py" --config "$ROOT/config" --out "$OUT"

if [ ! -d "$OUT/dlc/.git" ] || [ "$(git -C "$OUT/dlc" rev-parse HEAD)" != "$DLC_COMMIT" ]; then
  rm -rf "$OUT/dlc"
  git init -q "$OUT/dlc"
  git -C "$OUT/dlc" fetch -q --depth 1 "$DLC_REPO" "$DLC_COMMIT"
  git -C "$OUT/dlc" checkout -q FETCH_HEAD
fi

TAGS="$(cd "$OUT/data" && ls | paste -sd, -)"
(cd "$OUT/dlc" && go run ./ \
  --datapath="$OUT/data" \
  --outputdir="$OUT/publish" \
  --outputname="$DAT_NAME" \
  --exportlists="$TAGS")

python3 "$ROOT/scripts/verify_dat.py" "$OUT/publish/$DAT_NAME" \
  --critical "$ROOT/config/critical.txt" --tags "$TAGS" --stats "$OUT/stats.json" \
  > "$OUT/publish/stats.md"

cp "$OUT/stats.json" "$OUT/publish/stats.json"
(cd "$OUT/publish" && sha256sum "$DAT_NAME" > "$DAT_NAME.sha256sum")
cat "$OUT/publish/stats.md"
ls -la "$OUT/publish"
