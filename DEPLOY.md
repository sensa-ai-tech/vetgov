# 部署手冊 · vetgov.tw

> 從 GitHub repo 到 https://vetgov.tw,大約 15 分鐘可以全部完成。

---

## 架構總覽

```
┌─────────────────┐     git push       ┌──────────────┐     auto deploy    ┌──────────────┐
│  本機 / CI bot  │ ─────────────────▶ │   GitHub     │ ─────────────────▶ │    Vercel    │
│                 │                     │sensa-ai-tech/│                    │  CDN + SSL   │
│  CLI pipeline   │                     │   vetgov     │                    │              │
└─────────────────┘                     └──────────────┘                    └──────┬───────┘
                                               ▲                                    │
                                               │                                    │
                                   ┌───────────┴────────────┐                       │
                                   │  GitHub Actions        │                       │
                                   │  06:17 + 18:17 daily   │                       │
                                   │  (ingest → build →     │                       │
                                   │   commit data.json)    │                       │
                                   └────────────────────────┘                       │
                                                                                    ▼
                                                                            ┌──────────────┐
                                                                            │  vetgov.tw   │
                                                                            │  (DNS A/CNAME│
                                                                            │   → Vercel)  │
                                                                            └──────────────┘
```

**資料流向**:資料源(Google News RSS + 10 個政府網域) → Python pipeline 每日 2 次(ingest → classifier → Claude Haiku → build) → `site/data.json` → commit → Vercel 自動部署 → CDN。

**零成本**:主機 NT$0 / GitHub Actions NT$0 / Claude Haiku <NT$150/月 / 網域 ~NT$800/年。

---

## Step 1 · Vercel Import(約 3 分鐘)

1. 開 https://vercel.com/new
2. 用 **GitHub 帳號** 登入(使用 `sensa-ai-tech`)
3. 找到 `sensa-ai-tech/vetgov` repo → 點 **Import**
4. **Configure Project** 畫面:
   | 欄位 | 值 |
   |---|---|
   | Project Name | `vetgov` |
   | Framework Preset | `Other` |
   | Root Directory | `./` (預設) |
   | Build Command | 留空 |
   | Output Directory | 留空 (已在 `vercel.json` 設為 `site`) |
   | Install Command | 留空 |
5. **Environment Variables** 區先不填(之後再加)
6. 點 **Deploy**
7. 10–30 秒後完成,會拿到一個 `vetgov-xxx.vercel.app` 預設網址 → 打開確認設計正常

> **疑難排解**:如果頁面空白,到 Project Settings → General → Output Directory 手動設成 `site`,重新 redeploy。

---

## Step 2 · 綁定 vetgov.tw(約 5 分鐘)

### 2.1 · 在 Vercel 加入域名

1. Project → **Settings** → **Domains**
2. 在 input 輸入 `vetgov.tw` → **Add**
3. 再輸入 `www.vetgov.tw` → **Add**(Vercel 會自動把 www 301 redirect 到 root)
4. Vercel 會顯示你需要在 DNS 上加的記錄,大致如下:

```
類型     名稱           值                         TTL
─────   ────────────   ────────────────────────  ─────
A       @              76.76.21.21                 600
CNAME   www            cname.vercel-dns.com        600
```

> **實際 IP 請以 Vercel 面板顯示為準** — Vercel 可能會換 IP。

### 2.2 · 在 .tw 註冊商設 DNS

到你買 `vetgov.tw` 的 DNS 控制台(TWNIC / Gandi / GoDaddy / Cloudflare Registrar 等):

1. 刪除現有的 `A @` 與 `CNAME www` 記錄(如有預設導頁)
2. 新增上面 Vercel 給的兩筆記錄
3. 儲存

> **.tw 註冊商常見坑**:有些註冊商不支援用 `@` 代表根域,改成留空或輸入 `vetgov.tw` 本身。

### 2.3 · 等 DNS propagation(5 分鐘 ~ 數小時)

用 https://dnschecker.org/#A/vetgov.tw 觀察擴散進度。

### 2.4 · SSL 自動簽發(1–5 分鐘)

Vercel 偵測到 DNS 指過來後會自動申請 Let's Encrypt 憑證。在 Vercel Domains 頁面看到綠色勾勾即完成。

---

## Step 3 · GitHub Actions Secrets(約 1 分鐘,選用但建議)

啟用 Claude Haiku 自動萃取事件(每日增量 <NT$5)。

1. 開 https://github.com/sensa-ai-tech/vetgov/settings/secrets/actions
2. 點 **New repository secret**
3. 填入:
   - Name: `ANTHROPIC_API_KEY`
   - Value: `sk-ant-api03-...`(你的 Anthropic API key)
4. **Save**

> 不設也 OK — workflow 會自動跳過 LLM 步驟,只跑關鍵字分類。

---

## Step 4 · 驗證部署

### 4.1 · 打開 https://vetgov.tw

應該看到:
- 頂部黑色跑馬燈(倒數天數閃動血橙色)
- Hero 巨大襯線「我們 / 不反對 / 改革。」
- 墨黑倒數框「83 DAYS · 2026.07.01」
- 「701 → 144 = 20.5%」三段數字
- 五大訴求網格(第 5 格黑底)
- 七張第一線真實案例(#07 為寬版黑底)
- 時間線 7 筆種子事件
- 深墨黑 CTA「請在 5 月底前排入審議」

### 4.2 · 手動觸發第一次 workflow

1. 開 https://github.com/sensa-ai-tech/vetgov/actions/workflows/daily-update.yml
2. 右上 **Run workflow** → **Run workflow**
3. 等 3–5 分鐘,查看 log
4. 完成後 `site/data.json` 會被 tracker-bot 自動 commit,Vercel 會再重新部署一次

### 4.3 · 檢查 og:image 預覽

用 https://opengraph.dev 輸入 `https://vetgov.tw`,確認:
- Title: 修正藥事法第 50 條 · 致立法院的一封公開信
- Description: 701 項藥品 · 僅 144 項登錄 · …
- Image: og-image.svg 正確顯示(墨黑 + 血橙 + 「我們不反對改革」)

> **注意**:少數平台(如 LINE 預覽)對 SVG og 支援較差,必要時可用 Figma 或 Playwright 把 `og-image.svg` 轉成 PNG 後覆蓋 `og-image.png`,並把 meta 的附檔名改掉。

---

## Step 5 · 後續自動化

部署完成後,以下事情會**自動發生**,不需人工介入:

| 時間 | 動作 |
|---|---|
| **每日 06:17** 台北 | GitHub Actions ingest → classify → LLM → build → commit → Vercel redeploy |
| **每日 18:17** 台北 | 同上(傍晚追蹤) |
| push 到 main(修改 src / config / workflow) | 立即觸發一次 |
| 手動觸發 | Actions 頁面 → Run workflow |

---

## 常見問題

### Q. Vercel 部署後頁面空白
→ Settings → General → Output Directory 改成 `site`

### Q. vetgov.tw 顯示「DNS 尚未生效」
→ 等 DNS propagation,用 dnschecker.org 觀察。`.tw` 有時會慢到 1–2 小時

### Q. 中文字顯示為方框
→ 確認瀏覽器有連線(Google Fonts 需要網路),或打開 devtools 看 fonts 請求是否 200

### Q. GitHub Actions 跑失敗
→ Actions 頁面打開該次 run,通常是 source URL 變動或 timeout。workflow 已設 `continue-on-error` 所以不會全面掛掉

### Q. LLM 沒萃取出事件
→ 確認 ANTHROPIC_API_KEY secret 已設定,且額度夠用。用 `workflow_dispatch` 手動觸發除錯

### Q. data.json 沒更新到 live 站
→ 確認 GitHub Actions 有成功 commit(Repo → Commits),Vercel 會自動跟上。也可以在 Vercel 手動 Redeploy

---

## 本機開發

```bash
git clone https://github.com/sensa-ai-tech/vetgov.git
cd vetgov
pip install -r requirements.txt

# 初始化 + 載入種子
python -m src.cli init --with-seed

# (選用) 抓取真實資料
python -m src.cli ingest

# (選用 · 需 ANTHROPIC_API_KEY) LLM 萃取
export ANTHROPIC_API_KEY=sk-ant-...
python -m src.cli analyze --limit 15

# 產出 site/data.json
python -m src.cli build-site

# 啟動本機預覽
python -m http.server --directory site 8080
# 開 http://localhost:8080
```

---

## 緊急停機

如果網站需要下架:

1. Vercel Dashboard → Project → Settings → General → **Delete Project**
2. 或 Domains 頁面移除 `vetgov.tw` 綁定,流量會回到 `vetgov-xxx.vercel.app` 預設 URL
3. GitHub repo 可保留或設 private

---

## 成本追蹤

| 項目 | 月費 | 備註 |
|---|---|---|
| Vercel (Hobby) | NT$0 | 100GB/月頻寬 |
| GitHub Actions | NT$0 | 2000 分鐘/月 |
| Anthropic Claude Haiku | ~NT$150 | 每日 ~20 筆萃取 |
| `.tw` 網域 | ~NT$800/年 | 約 NT$67/月 |
| **合計** | **~NT$217/月** | |

---

**維護者**:獸醫用藥權修法推動聯盟
**技術**:Claude Code 輔助開發
**授權**:MIT
