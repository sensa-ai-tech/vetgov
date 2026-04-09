"""命令列介面。

使用：
    python -m src.cli init --with-seed
    python -m src.cli ingest
    python -m src.cli analyze --limit 15
    python -m src.cli build-site
    python -m src.cli stats
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import analyzer, classifier, scraper, storage, timeline

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "events.db"
CONFIG_PATH = ROOT / "config" / "sources.yaml"
SEED_PATH = ROOT / "data" / "seed_events.json"
SITE_DATA = ROOT / "site" / "data.json"


# ---------- helpers ----------

def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"[ERR] config not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


# ---------- commands ----------

def cmd_init(args) -> None:
    conn = storage.connect(DB_PATH)
    print(f"[OK] DB ready: {DB_PATH}")

    if args.with_seed and SEED_PATH.exists():
        seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
        added = 0
        for e in seed.get("events", []):
            if storage.insert_event(
                conn,
                event_date=e["date"],
                title=e["title"],
                summary=e["summary"],
                stance=e.get("stance", "neutral"),
                stakeholders=e.get("stakeholders", []),
                source_urls=e.get("sources", []),
                importance=int(e.get("importance", 1)),
                origin=e.get("origin", "seed"),
            ):
                added += 1
        print(f"[OK] Loaded {added} seed events (duplicates skipped).")


def cmd_ingest(args) -> None:
    cfg = _load_config()
    conn = storage.connect(DB_PATH)

    total = 0
    kept = 0
    errors = 0
    for source in cfg.get("sources", []):
        if source.get("disabled"):
            continue
        name = source["name"]
        url = source["url"]
        stype = source.get("type", "rss")
        if stype != "rss":
            print(f"[SKIP] {name}: type={stype} not yet supported")
            continue
        try:
            for item in scraper.fetch_rss(name, url):
                if not item.url:
                    continue
                total += 1
                text = f"{item.title} {item.summary}"
                score = classifier.score_text(text)
                if storage.insert_raw(conn, item, score):
                    if score.category in ("core", "on_topic"):
                        kept += 1
        except Exception as e:
            errors += 1
            print(f"[WARN] {name}: {e}", file=sys.stderr)

    c = storage.counts(conn)
    print(
        f"[OK] Fetched {total} items, {kept} relevant, {errors} source errors. "
        f"DB totals: raw={c['raw_total']} core={c['raw_core']} events={c['events']}"
    )


def cmd_analyze(args) -> None:
    if not analyzer.is_available():
        print("[INFO] ANTHROPIC_API_KEY not set; skipping LLM analysis.")
        return
    conn = storage.connect(DB_PATH)
    candidates = storage.top_raw_items(
        conn, limit=args.limit, min_category="core", only_unanalyzed=True
    )
    if not candidates:
        print("[INFO] no unanalyzed core items.")
        return

    added = 0
    for c in candidates:
        result = analyzer.analyze(
            title=c["title"], source=c["source"], text=c.get("summary", "")
        )
        storage.mark_analyzed(conn, c["id"])
        if not result:
            continue
        if storage.insert_event(
            conn,
            event_date=result["event_date"],
            title=result["title"],
            summary=result["summary"],
            stance=result.get("stance", "neutral"),
            stakeholders=result.get("stakeholders", []),
            source_urls=[c["url"]],
            importance=int(result.get("importance", 1)),
            origin="llm",
        ):
            added += 1

    print(f"[OK] LLM analysis: {added} new events added from {len(candidates)} candidates.")


def cmd_build_site(args) -> None:
    conn = storage.connect(DB_PATH)
    events = storage.all_events(conn)
    cfg = _load_config()
    sources = [
        {"name": s["name"], "type": s.get("type", "rss"), "url": s["url"]}
        for s in cfg.get("sources", [])
        if not s.get("disabled")
    ]
    n = timeline.export(events, SITE_DATA, sources=sources, counts=storage.counts(conn))
    print(f"[OK] Exported {n} events to {SITE_DATA}")


def cmd_stats(args) -> None:
    conn = storage.connect(DB_PATH)
    c = storage.counts(conn)
    print(json.dumps(c, indent=2, ensure_ascii=False))


# ---------- entrypoint ----------

def main() -> None:
    parser = argparse.ArgumentParser(prog="vet-drug-tracker")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="初始化資料庫")
    p.add_argument("--with-seed", action="store_true", help="載入 data/seed_events.json")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("ingest", help="抓取所有資料源")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("analyze", help="對高分項目跑 LLM 萃取（選用）")
    p.add_argument("--limit", type=int, default=15)
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("build-site", help="匯出 site/data.json 供靜態站讀取")
    p.set_defaults(func=cmd_build_site)

    p = sub.add_parser("stats", help="顯示 DB 統計")
    p.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
