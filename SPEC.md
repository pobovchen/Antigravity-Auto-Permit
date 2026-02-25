# 🛠️ Project Spec: Vision-Triggered Automation Butler (V3)

## 1. 核心邏輯 (The "See & Do" Principle)

本工具採純影像驅動模式。所有動作必須符合以下公式：

**IF** 偵測到 [截圖 A] **THEN** 點擊 [位置 P]
*(位置 P 可以是 A 的中心，或是另一個偵測到的截圖 B 的中心)*

---

## 2. 功能需求與觸發場景

### A. 授權自動化 (Antigravity Allow/Run)

* **觸發條件**：螢幕出現 `allow_button.png` 或 `run_button.png`。
* **執行動作**：移動至該圖示中心點並執行 `click`。
* **頻率控制**：偵測到並點擊後，必須進入 1 秒的短暫冷卻，避免重複點擊。

### B. 通知與回饋 (Messenger Notify)

* **觸發條件**：在左下角 ROI 區域偵測到 `command_icon.png` (指令圖示) 或 `done_text.png` (完成文字)。
* **執行動作**：
1. 在同一 ROI 區域尋找 `like_hand.png` (讚手勢)。
2. 若找到，點擊該位置。
3. 若未找到「讚」，則點擊 `input_field.png` (Aa 輸入框) 並執行模擬打字發送。

---

## 3. 技術實作指引 (給 AI 的重點)

### 影像辨識強化

* **多圖比對**：支援同一個邏輯綁定多張樣本圖（例如不同大小或顏色的 Allow 鈕）。
* **灰階處理**：預設將所有截圖轉為灰階比對，提高對環境光與透明度的容錯率。
* **信心值過濾**：僅在 max_val > threshold (預設 0.8) 時才觸發動作。

### 操作安全性 (Stealth & Safety)

* **非線性移動 (Non-Linear Movement)**：禁止使用瞬間移動。應使用 `pyautogui.moveTo(x, y, duration=random.uniform(0.2, 0.5))` 模擬人類滑鼠移動軌跡。
* **隨機偏移 (Random Offset)**：點擊位置應在目標中心點 ± 2 像素內隨機漂移，避免每次點擊同一個絕對像素。
* **點擊壓力模擬 (Click Pressure)**：將點擊拆解為 `mouseDown` -> `time.sleep(random.uniform(0.05, 0.15))` -> `mouseUp`，模擬真人按壓時間。
* **ROI 限制**：允許使用者框選「通知監控區」與「任務監控區」，避免全螢幕掃描導致 CPU 飆升。
* **緊急停止**：強制監控 Ctrl + C 並開啟 `pyautogui.FAILSAFE`。

### 4. 異常處理與防禦 (Risk Mitigation)

* **單位時間點擊上限 (Rate Limiting)**：
    * **規則**：若 300 秒內偵測到並執行點擊超過 5 次。
    * **動作**：立即停止自動化服務，將狀態設為「異常鎖定」，並發出警報（如蜂鳴聲或 Debug 顏色變更）。
    * **擴充**：發送通知至 FB Messenger (透過專屬邏輯) 提醒「偵測到異常頻繁授權要求，請人工檢查」。
* **無限循環防禦**：若 10 秒內針對同一目標連續重複點擊，應暫停。

---

## 💡 給 Poyen 的實作建議

這份規格強調了「全截圖驅動」。當你讓 Antigravity 編寫時，可以請它先寫一個 **「腳本預覽模式」**：

「在正式執行點擊前，先讓程式在螢幕上用紅框標示出它『目前偵測到的所有目標』但不執行點擊。」

這樣你可以先確認它對 Allow 鈕和 FB 視窗的判斷是否準確，再開啟自動點擊功能。
