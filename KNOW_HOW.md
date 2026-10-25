# 📚 專案 Know-How 與變現架構資產庫 (Real Estate Platform Know-How Archive)

本文件完整歸檔「台南房產 AI 雷達」從 0 到 1 的所有實戰 Know-How、變現架構、Google AdSense 審核解法與自動化運營機制，供團隊後續所有專案（包含全新**「汽車選購比較平台」**）全面繼承與複用。

---

## 1. 💰 Google AdSense 變現與審核破關 Know-How (Kevin 總結)
* **發布商 ID**: `ca-pub-9735167683544437`
* **根網域與 GitHub Pages 404 陷阱破解**：
  * **痛點**：Google AdSense 申請時只接受根網域 `username.github.io`，但專案 Repo `username.github.io/repo_name` 會導致根目錄 404，造成 Google 爬蟲判定「無法驗證您的網站」。
  * **解法**：在 GitHub 建立專屬根目錄倉庫 `username.github.io`，將帶有 AdSense 代碼的頁面與 `ads.txt` 推送到根倉庫，即可在 3 秒內通過「驗證網站擁有權」。
* **`ads.txt` 標準規格**：
  ```text
  google.com, pub-9735167683544437, DIRECT, f08c47fec0942fa0
  ```
* **三大高轉換版位佈局哲學**：
  1. **骨架屏/載入預留位**：在資料非同步載入時展示，不突兀且先佔版面。
  2. **核心決策樞紐原生流式 (In-feed Unit)**：置於使用者比較、試算規格時的最精華閱讀視角，並搭配 `try { (adsbygoogle = window.adsbygoogle || []).push({}); } catch(e){}` 安全初始化，避免 SPA / 切換頁面拋錯。
  3. **次級轉換彈窗橫幅**：在付費彈窗或比較清單底部展示，變現未立即付費的訪客注意力。

---

## 2. 🚗 汽車選購比較網站之延伸變現策略 (Stan 收益洞察)
汽車與房產同屬**高客單價、高決策成本的大額消費市場**，以下是汽車網站的高額變現點子：
1. **汽車貸款與車險試算器 (Car Loan & Insurance Calculator)**：
   - 轉介銀行車貸、中古車分期、產險（強制險/乙式/丙式）留單分潤 (CPA: NT$ 500 ~ 1,500 / 筆)。
2. **新車菜單/中古車商「預約賞車」名單轉介 (Lead Generation)**：
   - 訪客比較完兩款車型後，提供「一鍵向全台業務索取最佳購車菜單」或「預約試駕」，名單直接對接車廠業務或優選車商。
3. **熱門車型規配與折舊率深度比較 (Car Comparison Pro)**：
   - 比較車輛空間、油耗/電耗成本、主被動安全配備（Level 2 ADAS）、三年折舊保值率。
4. **Google AdSense 高 CPM 廣告單元**：
   - 汽車周邊（隔熱紙、行車記錄器、輪胎、鍍膜美容）為高價值競價廣告。

---

## 3. 🧸 前端 UI/UX 與品質巡檢規範 (Bob 總結)
* **響應式斷點**：嚴格支援最小 360px+ 手機端小螢幕，避免水平卷軸破版。
* **雙重品質把關 (Event-Driven Quality Gate)**：
  - 本地 `pre-commit hook`：提交前自動執行測試。
  - GitHub Actions CI/CD：自動化排程爬蟲與構建更新。
* **無障礙體驗 (WCAG 2.1 AA)**：文字對比度、焦點環與鍵盤方向鍵支援。

---

## 4. 🕶️ 團隊組織分工手冊 (Gru 統籌)
* 🕶️ **Gru (總指揮)**：全局協調、整合把關、每日 07:00 晨報。
* 💼 **Stan (Pro)**：商業變現專家，負責比較維度設計、收益點子與高價值 MVP 開發。
* 🧸 **Bob (Flash)**：UI/UX 專家，負責汽車規格比對卡片、外觀視覺、響應式排版與自動巡檢。
* 🍌 **Kevin (Flash-Lite)**：AdSense 變現專員，負責汽車站廣告版位佈局、`ads.txt` 維護與流量監控。
