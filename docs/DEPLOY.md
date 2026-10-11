# 部署指南（給 Sam）

整個網站（Next.js 前端 + Python API）部署在 **一個 Vercel 項目** 裏。全程大約 15 分鐘，全部免費。

## 已部署的項目

- 公開網站：<https://tickmark-gules.vercel.app>
- 源碼：<https://github.com/yuzonglinsam/tickmark>
- Vercel 項目：`tick-ace/tickmark`（Hobby）；已連接 GitHub 自動部署。
- 生產環境已驗證：免登入瀏覽、來源追溯、SHAK 即時 SEC 分析、SHAK 英文及繁中 memo、KO 即時 DeepSeek 問答。
- GitHub Actions 的 SEC／DeepSeek secrets 已配置；尚未執行整批週更流程。

## 你需要的東西

| 項目 | 用途 | 費用 |
|---|---|---|
| GitHub 帳號 | 存放代碼；Vercel 從這裏讀取 | 免費 |
| Vercel 帳號（用 GitHub 登入） | 托管網站 + Python API；不會休眠 | 免費（Hobby） |
| DeepSeek API key | 「Ask Tickmark」問答、即時生成 memo | 按用量，問一次約 0.001 美元 |

## 第一步：把代碼放上 GitHub

1. 登入 GitHub → 右上角 **+** → **New repository**
2. Repository name 填 `tickmark`，選 **Public**，**不要** 勾選 “Add a README”（項目已經有），按 **Create repository**
3. 在電腦上打開項目文件夾（`Sam/tickmark`），在該文件夾開啟終端機（Windows：在文件夾地址欄輸入 `cmd` 再按 Enter），依次輸入：

```bash
git remote add origin https://github.com/<你的用戶名>/tickmark.git
git push -u origin main
```

> 文件夾裏已經有完整的 git 歷史，所以只需要 `remote add` + `push`。第一次 push 時瀏覽器會彈出 GitHub 登入。
> `.env`（含 DeepSeek key）已被 `.gitignore` 排除，不會被上傳。

## 第二步：部署到 Vercel

1. 打開 <https://vercel.com>，按 **Continue with GitHub**
2. **Add New… → Project** → 在列表中找到 `tickmark` → **Import**
3. Framework Preset 會自動識別為 **Next.js**，其他設定保持默認
4. 展開 **Environment Variables**，加入：

| Name | Value |
|---|---|
| `SEC_USER_AGENT` | `Tickmark research Your Name you@example.com`（換成真實聯絡資料） |
| `DEEPSEEK_API_KEY` | 你的 DeepSeek key |
| `DEEPSEEK_MODEL` | `deepseek-flash` |
| `NEXT_PUBLIC_REPO_URL` | `https://github.com/yuzonglinsam/tickmark` |
| `NEXT_PUBLIC_LINKEDIN_URL` | （可選）你的 LinkedIn 個人頁網址，首頁 About 會顯示按鈕 |

5. 按 **Deploy**，等 2–3 分鐘。完成後會得到網址，例如 `https://tickmark-xxxx.vercel.app`
6. （可選）Settings → Domains 可以把網址改成 `tickmark-samyu.vercel.app` 之類更好記的名字
7. 在 Vercel 加入 `NEXT_PUBLIC_SITE_URL` = 你的最終網址，然後 **Redeploy** 一次（讓 LinkedIn 分享預覽圖使用正確網址）

## 第三步：驗收（5 分鐘）

用手機和電腦分別打開網址，逐項確認：

- [ ] 首頁動畫、截圖正常顯示
- [ ] `/terminal` 的 treemap、清單正常
- [ ] 搜索 `KO` → 打開 Coca-Cola；點任何數字旁的 ✓ → 右側彈出來源
- [ ] AI memo 分頁可切換 EN / 繁中
- [ ] **Ask Tickmark** 問一條問題，有答案和「figures verified」標記（測試 Python API + DeepSeek）
- [ ] 搜索一個不在名單裏的公司，例如 `SHAK`（Shake Shack）→ 出現 **LIVE ANALYSIS**（測試 SEC 即時抓取）

如果 Ask 或 LIVE 失敗：Vercel → 項目 → **Logs**，看 `api/index.py` 的錯誤；最常見是環境變量沒填或填錯。

**後備方案（Python API 在 Vercel 部署不成功時）**：把同一個 GitHub repo 在 [Render](https://render.com) 建一個免費 *Web Service*：
Build command `pip install -r requirements.txt gunicorn`，Start command `gunicorn api.index:app`，環境變量同上。
然後在 Vercel 加入 `API_ORIGIN` = Render 給你的網址（例如 `https://tickmark-api.onrender.com`）並 Redeploy。
網站其餘部分（497 家公司）完全不依賴 API，即使 API 暫時不可用也能正常瀏覽。

## 每週自動更新數據（可選）

`.github/workflows/refresh-data.yml` 每週一自動重新抓取 SEC 數據、為有變化的公司重新生成 memo，並把新數據 commit 回 GitHub；Vercel 會自動重新部署。
啟用方法：GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**，加入 `SEC_USER_AGENT` 和 `DEEPSEEK_API_KEY`。

## 費用與安全

- 網站本身（靜態頁面 + 497 家公司數據）不調用 AI，訪客瀏覽零成本
- 只有「Ask」和「為新公司生成 memo」會調用 DeepSeek；API 內建每 IP 每小時限額及全站每日上限（`api/index.py` 的 `LIMITS`）
- 如果 key 被濫用，到 DeepSeek 後台作廢並換一條新 key，再更新 Vercel 環境變量即可
