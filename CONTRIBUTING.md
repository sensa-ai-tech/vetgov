# 貢獻指南 · Contributing to vetgov.tw

歡迎獸醫師、飼主、公民科技志工、法律專業者加入這個開源專案。

這是一個**公民議題追蹤平台**,不是商業產品。我們沒有 roadmap、沒有 sprint、沒有截止日 — 只有一個明確的目標:**推動藥事法第 50 條修正完成**。

---

## 🎯 最需要幫忙的事

優先順序由高到低:

### 1. 補充真實事件到時間線

編輯 `data/seed_events.json`,加入你知道但 pipeline 沒抓到的重要事件。例如:
- 立法委員在質詢台上的發言(立院 IVOD 連結)
- 公會正式聲明與連署名冊
- 第一線獸醫師遇到的具體斷藥案例
- 飼主因為新制受影響的真實經歷(匿名化處理)
- 類似議題的歷史先例(1980 年代、1990 年代、2000 年代的相關事件)

每一筆都要附上**可查證的原始連結**。沒有連結的聲明我們不收。

### 2. 擴充資料來源

編輯 `config/sources.yaml`,加入新的監測來源。目前已涵蓋:
- 8 個政府網域(Tier 1 · official)
- 9 個主流媒體(Tier 2 · media)
- 1 個公會社群(Tier 3 · community · 待擴充)

**需要**:獸醫師公會官網、臨床獸醫師協會官網、各地方公會 RSS、飼主社群、動保團體官網。如果它們沒有 RSS,用 Google News `site:` filter 替代。

### 3. 校對與事實查核

如果你看到:
- 事件日期錯誤
- 立場誤歸類(例如把中立誤標為反對)
- 統計數字失準(例如 701/144 數字需要更新)
- 摘要失實或過度情緒化

請開 issue 或直接送 PR 修正。每一則回報都會被認真看待。

### 4. 翻譯與無障礙

- 英文版介面(面向國際媒體)
- ARIA 標籤改善(讓讀屏軟體正確閱讀)
- Color contrast 檢查(WCAG AA)
- 鍵盤導覽支援

### 5. 新訴求的資料蒐集

如果議題發展出現新的焦點(例如特定藥品斷供、特定立委的立場轉變),可以新增 voice card 或 demand card。請在 issue 裡先描述你的構想。

---

## 🛠 開發環境設定

```bash
git clone https://github.com/sensa-ai-tech/vetgov.git
cd vetgov
pip install -r requirements.txt

# 初始化資料庫 + 載入種子事件
python -m src.cli init --with-seed

# 執行單元測試
python -m unittest tests.test_classifier -v

# 抓取真實資料(需網路)
python -m src.cli ingest

# (選用) LLM 萃取
export ANTHROPIC_API_KEY=sk-ant-...
python -m src.cli analyze --limit 15

# 產出站內資料
python -m src.cli build-site

# 本機預覽
python -m http.server --directory site 8080
# 開 http://localhost:8080
```

**必要環境**:
- Python 3.11+
- `feedparser` `httpx` `PyYAML` `anthropic`(已列在 `requirements.txt`)

**不需要**:
- Node.js / npm(前端是純 HTML/CSS/JS)
- 任何 build tool(直接 serve `site/` 即可)
- 資料庫(SQLite 單檔)

---

## 📐 專案結構

```
vetgov/
├── src/                     Python ingestion pipeline
│   ├── scraper.py           RSS 抓取
│   ├── classifier.py        離線關鍵字三級計分
│   ├── storage.py           SQLite 儲存層
│   ├── analyzer.py          Claude Haiku 事件萃取(選用)
│   ├── timeline.py          匯出 site/data.json
│   └── cli.py               命令列介面
├── config/
│   └── sources.yaml         資料來源清單
├── data/
│   └── seed_events.json     種子事件(人工整理)
├── site/                    靜態站(Vercel 部署目錄)
│   ├── index.html
│   ├── about.html
│   ├── style.css
│   ├── app.js
│   ├── data.json            自動產生
│   ├── favicon.svg
│   ├── og-image.svg
│   ├── robots.txt
│   └── sitemap.xml
├── tests/
│   └── test_classifier.py
├── .github/workflows/
│   └── daily-update.yml     每日自動更新
├── vercel.json              Vercel 部署設定
├── DEPLOY.md                部署手冊
├── PROPOSAL.md              專案定位
└── README.md
```

---

## 🎨 設計系統

如果你要修改前端視覺,請遵循既有的設計 tokens(定義在 `site/style.css` :root):

| Token | 用途 |
|---|---|
| `--ink #0a0a0a` | 主背景深色 / 主文字 |
| `--paper #f6f2e9` | 奶油紙背景 / 反白文字 |
| `--blood #c9531a` | 血橙強調色(取代紅色) |
| `--moss #1a3d2e` | 深苔綠(sources 區) |
| `--gold #c9a34a` | 金色(官方公文 tier) |

**字體**:
- `--serif` Noto Serif TC — 用於所有大標
- `--sans` Noto Sans TC — 用於內文  
- `--mono` JetBrains Mono — 用於標籤與資料

**不要**:
- 加入鮮紅色(避免情緒對立)
- 加入 emoji 裝飾(editorial 風格)
- 改 Google Analytics 或任何追蹤器

---

## 📝 Commit 訊息規範

使用 [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>
```

**type**:`feat` / `fix` / `refactor` / `docs` / `style` / `test` / `chore`

**scope**(建議):`tracker` / `site` / `data` / `workflow` / `sources`

**範例**:
```
feat(sources): 新增獸醫師公會官網 RSS 來源
fix(classifier): 修正藥事法第 50 條關鍵字誤判
docs(deploy): 補充 Cloudflare DNS 設定步驟
data(seed): 加入 2015 年腫瘤藥斷供事件
```

---

## 🚦 Pull Request 流程

1. Fork repo
2. 建立 feature branch(`feat/add-xxx-source`)
3. 本地跑過 `python -m unittest tests.test_classifier`
4. 若修改 sources.yaml,跑 `python -m src.cli ingest` 確認沒 error
5. 若修改前端,用 preview server 跑過一次確認視覺沒壞
6. Push 到你的 fork
7. 開 PR 對 `sensa-ai-tech/vetgov:main`
8. 在 PR 描述說明:改了什麼、為什麼、怎麼驗證

**審查標準**:
- 事實必須可查證(附連結)
- 不做個人攻擊
- 不違反 editorial 風格指引
- tests 全綠
- 不引入新依賴(除非必要且已討論)

---

## 🙅 我們不接受的貢獻

- **個人攻擊或情緒化文案**:寫給人看的,不是寫給仇恨看的
- **未經查證的指控**:每一句批評必須有原始來源
- **商業贊助置入**:本站不接受任何廠商、公司、藥廠的贊助
- **個資敏感資料**:請勿上傳飼主身分證、醫療記錄等可識別個資
- **AI 幻覺事件**:若是 LLM 產生的事件,必須人工驗證後才能進時間線

---

## 💬 溝通管道

- **Issues**:https://github.com/sensa-ai-tech/vetgov/issues(錯誤回報、資料補充、功能建議)
- **Pull Requests**:https://github.com/sensa-ai-tech/vetgov/pulls
- **Live site**:https://vetgov.tw

---

## 🏛 專案目標提醒

當你在猶豫要不要貢獻時,記得我們的單一目標:

> **推動藥事法第 50 條修正完成。**
> **5 月底前排入委員會審議。**
> **負面表列取代正面表列。**
> **暫緩管理辦法 7/1 強制上路。**

不是開會。不是協商。不是再等兩年。是修法完成。

—— 獸醫用藥權修法推動聯盟
