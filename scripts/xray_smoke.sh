#!/usr/bin/env bash
# Проверка готового .dat настоящим Xray: конфиг загружается, рекламный домен
# уходит в blocked, критичный остаётся на default route.
# Использование: scripts/xray_smoke.sh <каталог с xeno-ads.dat> <путь к xray>
set -euo pipefail

ASSETS="$(cd "$1" && pwd)"
XRAY="$2"
WORK="$(mktemp -d)"
trap 'kill "${PID:-0}" 2>/dev/null || true; rm -rf "$WORK"' EXIT

cat > "$WORK/config.json" <<'EOF'
{
  "log": {"loglevel": "info"},
  "inbounds": [{"listen": "127.0.0.1", "port": 10808, "protocol": "socks", "settings": {"udp": false}}],
  "outbounds": [{"tag": "direct", "protocol": "freedom"}, {"tag": "blocked", "protocol": "blackhole"}],
  "routing": {"rules": [
    {"domain": ["ext:xeno-ads.dat:ads"], "outboundTag": "blocked"},
    {"domain": ["ext:xeno-ads.dat:ads-strict", "domain:example.invalid"], "outboundTag": "blocked"}
  ]}
}
EOF

XRAY_LOCATION_ASSET="$ASSETS" "$XRAY" run -test -c "$WORK/config.json"

XRAY_LOCATION_ASSET="$ASSETS" "$XRAY" run -c "$WORK/config.json" > "$WORK/xray.log" 2>&1 &
PID=$!
sleep 3

probe() {
  curl -s -m 3 -o /dev/null --socks5-hostname 127.0.0.1:10808 "https://$1/" || true
}
BLOCK="an.yandex.ru mc.yandex.ru ad.mail.ru adfox.ru googleads.g.doubleclick.net d.applovin.com"
PASS="gosuslugi.ru yastatic.net www.youtube.com clck.yandex.ru"
for h in $BLOCK $PASS; do probe "$h"; done
sleep 1

fail=0
for h in $BLOCK; do
  grep -q "taking detour \[blocked\] for \[tcp:$h:443\]" "$WORK/xray.log" || { echo "NOT BLOCKED: $h"; fail=1; }
done
for h in $PASS; do
  grep -q "taking detour \[blocked\] for \[tcp:$h:443\]" "$WORK/xray.log" && { echo "WRONGLY BLOCKED: $h"; fail=1; }
done
if [ "$fail" -ne 0 ]; then
  cat "$WORK/xray.log"
  exit 1
fi
echo "xray smoke test passed"
