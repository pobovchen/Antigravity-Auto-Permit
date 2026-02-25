
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import os
import pyautogui
import keyboard
import cv2
import numpy as np
from pynput import mouse
from pywinauto import Desktop
from PIL import ImageGrab

class AntigravityClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Auto-Clicker Vision")
        self.root.geometry("800x700")
        self.root.configure(bg="#1e1e2e")
        
        self.is_running = False
        self.is_picking = False
        self.click_points = []
        self.template_path = "run_template.png"
        
        self.setup_ui()
        self.setup_keyboard_listener()
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#f5c2e7")
        style.configure("Status.TLabel", font=("Segoe UI", 12), foreground="#fab387")
        style.configure("Bold.TLabel", font=("Segoe UI", 10, "bold"), foreground="#cdd6f4")
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(main_frame, text="Antigravity Auto-Clicker Vision", style="Header.TLabel")
        header.pack(pady=(0, 5))
        
        self.status_label = ttk.Label(main_frame, text="Status: IDLE", style="Status.TLabel")
        self.status_label.pack(pady=(0, 5))

        # Settings
        settings_frame = ttk.Frame(main_frame)
        settings_frame.pack(fill=tk.X, pady=5)

        # Vision Mode
        self.vision_mode = tk.BooleanVar(value=True)
        chk_vision = tk.Checkbutton(
            settings_frame, text="視覺圖像偵測 (Scan Screen for 'Run' Image)", 
            variable=self.vision_mode,
            bg="#1e1e2e", fg="#89b4fa", selectcolor="#313244",
            activebackground="#1e1e2e", activeforeground="#89b4fa",
            font=("Segoe UI", 10, "bold")
        )
        chk_vision.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Force Mode
        self.force_mode = tk.BooleanVar(value=False)
        chk_force = tk.Checkbutton(
            settings_frame, text="強制循環點擊 (Force Mode - ignore detection)", 
            variable=self.force_mode,
            bg="#1e1e2e", fg="#f38ba8", selectcolor="#313244",
            activebackground="#1e1e2e", activeforeground="#f38ba8",
            font=("Segoe UI", 10)
        )
        chk_force.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Interval Setting
        ttk.Label(settings_frame, text="掃瞄間隔 (秒):", style="Bold.TLabel").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.interval_var = tk.StringVar(value="1.0")
        self.interval_entry = ttk.Entry(settings_frame, textvariable=self.interval_var, width=10)
        self.interval_entry.grid(row=2, column=1, sticky=tk.W, pady=2)

        # Confidence Setting
        ttk.Label(settings_frame, text="圖像相似度 (0.1-1.0):", style="Bold.TLabel").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.confidence_var = tk.StringVar(value="0.8")
        self.confidence_entry = ttk.Entry(settings_frame, textvariable=self.confidence_var, width=10)
        self.confidence_entry.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Shortcut Info
        ttk.Label(settings_frame, text="📢 鍵盤 Ctrl + C 可立刻停止點擊", foreground="#f9e2af").grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Vision Controls
        vision_ctrl = ttk.Frame(main_frame)
        vision_ctrl.pack(fill=tk.X, pady=5)
        
        self.btn_capture = tk.Button(
            vision_ctrl, text="📸 截取 Run 按鈕特徵", 
            command=self.capture_template,
            bg="#cba6f7", fg="#11111b", font=("Segoe UI", 10, "bold"),
            padx=15, pady=8, borderwidth=0, cursor="hand2"
        )
        self.btn_capture.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.template_status = ttk.Label(vision_ctrl, text="特徵圖: 未設定", foreground="#f38ba8")
        self.template_status.pack(side=tk.LEFT, padx=10)
        if os.path.exists(self.template_path):
            self.template_status.configure(text="特徵圖: 已就緒", foreground="#a6e3a1")

        # Toggle Button
        self.btn_toggle = tk.Button(
            main_frame, text="▶️ 開始工作", 
            command=self.toggle_service,
            bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 14, "bold"),
            padx=40, pady=15, borderwidth=0, cursor="hand2"
        )
        self.btn_toggle.pack(pady=10)
        
        # Logs
        ttk.Label(main_frame, text="詳細日誌:").pack(anchor=tk.W)
        self.log_area = scrolledtext.ScrolledText(main_frame, height=12, bg="#181825", fg="#bac2de", font=("Consolas", 8))
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state=tk.DISABLED)

    def setup_keyboard_listener(self):
        keyboard.add_hotkey('ctrl+c', self.remote_stop)

    def remote_stop(self):
        if self.is_running:
            self.root.after(0, self.toggle_service)
            self.log("!!! 偵測到 Ctrl + C !!!")

    def log(self, message):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state=tk.DISABLED)

    def capture_template(self):
        # Allow user to select a region of the screen to save as template
        messagebox.showinfo("截錄說明", "點擊確定後，請在 3 秒內將滑鼠移到 'Run' 按鈕的左上角，按住左鍵拖曳到右下角放開。")
        self.root.withdraw() # Hide main window
        time.sleep(1)
        
        # Using a simple overlay for selection
        selection_win = tk.Toplevel()
        selection_win.attributes("-alpha", 0.3)
        selection_win.attributes("-fullscreen", True)
        selection_win.attributes("-topmost", True)
        selection_win.config(cursor="cross")
        
        canvas = tk.Canvas(selection_win, cursor="cross", bg="grey")
        canvas.pack(fill="both", expand=True)
        
        start_x, start_y = None, None
        rect_id = None
        
        def on_down(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x, event.y
            rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2)
            
        def on_move(event):
            nonlocal rect_id
            canvas.coords(rect_id, start_x, start_y, event.x, event.y)
            
        def on_up(event):
            end_x, end_y = event.x, event.y
            selection_win.destroy()
            self.finish_capture(min(start_x, end_x), min(start_y, end_y), max(start_x, end_x), max(start_y, end_y))

        canvas.bind("<ButtonPress-1>", on_down)
        canvas.bind("<B1-Motion>", on_move)
        canvas.bind("<ButtonRelease-1>", on_up)

    def finish_capture(self, x1, y1, x2, y2):
        self.root.deiconify()
        if x2 - x1 < 5 or y2 - y1 < 5:
            self.log("截取失敗：區域太小。")
            return
            
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        img.save(self.template_path)
        self.template_status.configure(text="特徵圖: 已就緒", foreground="#a6e3a1")
        self.log(f"已儲存特徵圖: {x2-x1}x{y2-y1} 像素。")

    def toggle_service(self):
        if not self.is_running:
            if self.vision_mode.get() and not os.path.exists(self.template_path):
                messagebox.showwarning("提示", "請先截取 'Run' 按鈕的圖像特徵！")
                return
            
            try:
                self.scan_interval = float(self.interval_var.get())
                self.confidence = float(self.confidence_var.get())
            except:
                messagebox.showerror("錯誤", "設定格式錯誤。")
                return

            self.is_running = True
            self.btn_toggle.configure(text="🛑 停止點擊 (Ctrl+C)", bg="#f38ba8")
            self.status_label.configure(text="Status: ACTIVE", foreground="#a6e3a1")
            self.log(f"啟動工作。模式: {'視覺偵測' if self.vision_mode.get() else '純代碼偵測'}")
            threading.Thread(target=self.click_loop, daemon=True).start()
        else:
            self.is_running = False
            self.btn_toggle.configure(text="▶️ 開始工作", bg="#a6e3a1")
            self.status_label.configure(text="Status: IDLE", foreground="#fab387")
            self.log("服務終止。")

    def click_loop(self):
        while self.is_running:
            try:
                found = False
                
                # 1. Image Recognition Mode
                if self.vision_mode.get():
                    screen = np.array(ImageGrab.grab())
                    screen_gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
                    template = cv2.imread(self.template_path, 0)
                    
                    if template is not None:
                        w, h = template.shape[::-1]
                        res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
                        loc = np.where(res >= self.confidence)
                        
                        points = list(zip(*loc[::-1]))
                        if points:
                            # Use the best match
                            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                            cx, cy = max_loc[0] + w//2, max_loc[1] + h//2
                            self.log(f"視覺命中！看到 Run 圖片在 ({cx}, {cy})，信心度: {max_val:.2f}")
                            pyautogui.click(cx, cy)
                            found = True
                            time.sleep(0.5)

                # 2. Logic Detection Mode (Fallback or Concurrent)
                if not found and not self.force_mode.get():
                    desktop = Desktop(backend="uia")
                    for window in desktop.windows():
                        title = window.window_text()
                        if title and "Antigravity" in title:
                            # Simple keywords
                            for btn in window.descendants(control_type="Button"):
                                if "Run" in btn.window_text():
                                    rect = btn.rectangle()
                                    pyautogui.click((rect.left+rect.right)//2, (rect.top+rect.bottom)//2)
                                    self.log(f"代碼命中！獲取按鈕 '{btn.window_text()}'")
                                    found = True
                                    break
                        if found: break

                # 3. Force mode
                if not found and self.force_mode.get():
                    # Manual click points could go here
                    pass
                
            except Exception as e:
                if "Access is denied" not in str(e):
                    self.log(f"偵測異常: {str(e)}")
            
            time.sleep(self.scan_interval)

if __name__ == "__main__":
    root = tk.Tk()
    app = AntigravityClicker(root)
    root.mainloop()
