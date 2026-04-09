# vetgov.tw · 第一線告白

> 來自獸醫師的請願 — 請主管機關正視問題

**🌐 Live**: https://vetgov.tw
**📦 Repo**: https://github.com/sensa-ai-tech/vetgov

[![pipeline](https://img.shields.io/badge/pipeline-GitHub_Actions-blue)]()
[![license](https://img.shields.io/badge/license-MIT-green)]()
[![stack](https://img.shields.io/badge/stack-Python_%2B_SQLite_%2B_Static-orange)]()

我們是台灣的獸醫師。我們不反對處方制度——我們反對的是一個沒有配套、沒有溝通、沒有問過第一線能不能做到的倉促新制。

本站每天自動抓取與 2026/7/1 特定寵物動物用藥品指定獸醫師處方制度相關的公開資訊，並以第一線獸醫師視角呈現政策進程與配套缺口。**主要訴求：請農業部與動植物防疫檢疫署正視問題，暫緩強制上路，先完成配套。**

---

## 快速開始（本地）

```bash
cd projects/08-vet-drug-policy-tracker
pip install -r requirements.txt

# 初始化資料庫 + 載入種子事件
python -m src.cli init --with-seed

# 抓取所有資料源（需連網）
python -m src.cli ingest

# （選用）跑 Claude LLM 萃取 — 需設 ANTHROPIC_API_KEY
python -m src.cli analyze --limit 15

# 產出靜態網站資料
python -m src.cli build-site

# 本地預覽
python -m http.server --directory site 8080
# 開 http://localhost:8080
```

## 專案結構

```
08-vet-drug-policy-tracker/
├── PROPOSAL.md              專案定位與背景
├── README.md                本檔
├── requirements.txt         Python 相依
├── config/
│   └── sources.yaml         資料來源清單（RSS/HTML）
├── src/
│   ├── scraper.py           RSS/HTML 抓取
│   ├── classifier.py        離線關鍵字相關度分類
│   ├── storage.py           SQLite 儲存層
│   ├── analyzer.py          Claude LLM 事件萃取（選用）
│   ├── timeline.py          匯出為靜態站 JSON
│   └── cli.py               命令列介面
├── data/
│   ├── events.db            SQLite（.gitignored）
│   └── seed_events.json     種子事件（進入 git）
├── site/
│   ├── index.html           時間線首頁
│   ├── about.html           專案說明
│   ├── style.css
│   ├── app.js
│   └── data.json            自動產生（進入 git 以供靜態部署）
├── tests/
│   └── test_classifier.py
└── .github/workflows/
    └── daily-update.yml     每日自動更新 + commit
```

## 部署到自訂網域（三選一，都免費）

### 選項 A：Cloudflare Pages（推薦）
1. 把整個專案 push 到 GitHub
2. Cloudflare Dashboard → Pages → Connect to Git
3. Build command: （留空）
4. Build output directory: `projects/08-vet-drug-policy-tracker/site`
5. Custom domain → 綁上你買的網域
6. Cloudflare 會自動處理 SSL 與 CDN

### 選項 B：Vercel
1. `npx vercel --prod` 在 `site/` 資料夾裡
2. Settings → Domains → 綁網域

### 選項 C：GitHub Pages
1. Settings → Pages → Source: GitHub Actions
2. 用內建的 Static workflow，path 設為 `projects/08-vet-drug-policy-tracker/site`

## 每日自動更新

`.github/workflows/daily-update.yml` 每日 06:17（台北時間）自動跑：
1. `ingest` 抓取所有資料源
2. `analyze` 跑 LLM 萃取（如果有設定 `ANTHROPIC_API_KEY`）
3. `build-site` 更新 `site/data.json`
4. 自動 commit + push，觸發 Cloudflare/Vercel 重新部署

要啟用：
- GitHub repo Settings → Secrets → 新增 `ANTHROPIC_API_KEY`（選用，省略則只跑關鍵字分類）

## 手動新增事件

如果你想人工加入重要事件（例如記者會、立院質詢重點），編輯 `data/seed_events.json` 再跑：

```bash
python -m src.cli init --with-seed
python -m src.cli build-site
```

## 測試

```bash
python -m unittest tests.test_classifier -v
```

## 授權

MIT — 歡迎 fork 用於追蹤其他公民議題。只要把 `config/sources.yaml` 和 `classifier.py` 的關鍵字換掉就能轉到任何主題。

---

由 [Claude Code](https://claude.com/claude-code) 輔助開發，2026 年 4 月。
