#!/usr/bin/env bash
# 本地完整跑一次 pipeline。CI 也可直接呼叫此腳本。
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/5] Tests"
python -m unittest tests.test_classifier -v

echo "[2/5] Init DB + seed"
python -m src.cli init --with-seed

echo "[3/5] Ingest sources"
python -m src.cli ingest || echo "(some sources failed, continuing)"

echo "[4/5] LLM analyze (if ANTHROPIC_API_KEY set)"
python -m src.cli analyze --limit 15 || true

echo "[5/5] Build site"
python -m src.cli build-site

echo "Done. Preview with:  python -m http.server --directory site 8080"
