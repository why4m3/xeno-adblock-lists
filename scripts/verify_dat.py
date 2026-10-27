#!/usr/bin/env python3
"""Проверяет готовый geosite .dat: теги на месте, размер разумный, критичные
хосты не блокируются. Печатает сводку в Markdown (идёт в описание релиза).

Можно запускать и на сервере против любого geosite-файла:
  python3 verify_dat.py /usr/local/x-ui/bin/xeno-ads.dat --critical critical.txt --tags ads
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geolib  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dat")
    ap.add_argument("--critical", required=True)
    ap.add_argument("--tags", required=True, help="через запятую")
    ap.add_argument("--min-entries", type=int, default=100000)
    ap.add_argument("--stats", help="stats.json от build_lists.py")
    args = ap.parse_args()

    sites = geolib.read_dat(args.dat)
    critical = geolib.read_hosts_file(args.critical)
    errors = []
    lines = ["| тег | записей | domain | full | regexp | keyword |", "|---|---|---|---|---|---|"]
    for tag in args.tags.split(","):
        entries = sites.get(tag.upper())
        if entries is None:
            errors.append(f"tag {tag} missing in {args.dat}")
            continue
        if len(entries) < args.min_entries:
            errors.append(f"tag {tag}: only {len(entries)} entries")
        counts = {t: 0 for t in ("domain", "full", "regexp", "keyword")}
        for t, _ in entries:
            counts[t] = counts.get(t, 0) + 1
        lines.append(f"| {tag} | {len(entries)} | {counts['domain']} | {counts['full']} | "
                     f"{counts['regexp']} | {counts['keyword']} |")
        m = geolib.Matcher(entries)
        for h in critical:
            rule = m.match(h)
            if rule:
                errors.append(f"tag {tag} blocks critical host {h} via {rule}")

    print(f"Файл: `{os.path.basename(args.dat)}`, {os.path.getsize(args.dat)} байт\n")
    print("\n".join(lines))
    if args.stats:
        with open(args.stats, encoding="utf-8") as f:
            stats = json.load(f)
        print("\n| источник | записей | пропущено при разборе |\n|---|---|---|")
        for name, s in stats["sources"].items():
            print(f"| [{name}]({s['url']}) | {s['entries']} | {s['skipped']} |")
    print(f"\nКритичных хостов проверено: {len(critical)}")
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
