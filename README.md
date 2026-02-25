# Antigravity Auto-Clicker (Local)

這是一個專為控制 Windows 特定 APP（特別是 Antigravity.exe）而設計的自動點擊工具。

### 功能特點：
- **完全本地化**：不連接網路，所有操作均在您的電腦上本地執行。
- **針對性自動點擊**：自動偵測並點擊以下按鈕：
  - `Run Alt+Enter`
  - `Allow This Conversation`
  - `Allow Once`
- **現代化介面**：提供清晰的日誌記錄與狀態顯示。

### 如何使用：
1. 確保已安裝 Python。
2. 執行 `run_clicker.bat`。
3. 在介面中點擊 **"START SERVICE"**。
4. 程式會開始循環掃描您的桌面窗口，發現目標按鈕時會自動點擊。

### 依賴項：
- `pywinauto` (已自動為您安裝)
- `pywin32` (已自動為您安裝)

---
*註：此工具僅在本地作業，不會上傳任何數據。*
