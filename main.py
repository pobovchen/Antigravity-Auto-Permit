
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import os
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
import pyautogui
import keyboard
import cv2
import numpy as np
import random
from pynput import mouse
from pywinauto import Desktop
from PIL import ImageGrab

class AntigravityClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Butler V3.5 - Maximum Safety")
        self.root.geometry("850x820")
        self.root.configure(bg="#1e1e2e")
        
        self.is_running = False
        self.click_history = []
        self.template_cache = {} 
        
        # Security Metrics
        self.handled_triggers = set()
        self.trigger_last_seen = {}
        self.session_start_time = 0
        self.total_click_count = 0
        
        # Multiple Template Support
        self.templates_dir = "templates"
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            
        # ROI Support
        self.roi = None # (x1, y1, x2, y2)
        
        pyautogui.FAILSAFE = True
        
        self.setup_ui()
        self.setup_keyboard_listener()
        self.load_templates()
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#f5c2e7")
        style.configure("Status.TLabel", font=("Segoe UI", 12), foreground="#fab387")
        style.configure("Info.TLabel", foreground="#89b4fa", font=("Segoe UI", 9))
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        header = ttk.Label(main_frame, text="Antigravity Butler V3.5 - 熔斷與安全監控", style="Header.TLabel")
        header.pack(pady=(0, 5))
        
        self.status_label = ttk.Label(main_frame, text="Status: IDLE", style="Status.TLabel")
        self.status_label.pack(pady=(0, 5))

        # Security Info Labels
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=2)
        self.timer_label = ttk.Label(info_frame, text="運行時間: 00:00 / 30:00", style="Info.TLabel")
        self.timer_label.pack(side=tk.LEFT, padx=10)
        self.counter_label = ttk.Label(info_frame, text="總點擊數: 0 / 100", style="Info.TLabel")
        self.counter_label.pack(side=tk.RIGHT, padx=10)

        ctrl_panel = ttk.Frame(main_frame)
        ctrl_panel.pack(fill=tk.X, pady=10)

        tk.Button(ctrl_panel, text="🎯 設定區域 (ROI)", command=self.select_roi,
                  bg="#f9e2af", fg="#11111b", font=("Segoe UI", 10, "bold"),
                  padx=10, pady=5, borderwidth=0, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(ctrl_panel, text="📸 捕捉特徵圖", command=self.capture_template,
                  bg="#cba6f7", fg="#11111b", font=("Segoe UI", 10, "bold"),
                  padx=10, pady=5, borderwidth=0, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(ctrl_panel, text="🔄 刷新特徵庫", command=self.load_templates,
                  bg="#89b4fa", fg="#11111b", font=("Segoe UI", 10),
                  padx=10, pady=5, borderwidth=0, cursor="hand2").pack(side=tk.LEFT, padx=5)

        settings_frame = ttk.Frame(main_frame)
        settings_frame.pack(fill=tk.X, pady=5)

        self.preview_mode = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_frame, text="預覽模式 (不執行動手)", variable=self.preview_mode,
                       bg="#1e1e2e", fg="#f9e2af", selectcolor="#313244", activebackground="#1e1e2e",
                       font=("Segoe UI", 10)).grid(row=0, column=0, sticky=tk.W)

        self.protocol_mode = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_frame, text="啟用序列判定 (智慧記憶機制)", variable=self.protocol_mode,
                       bg="#1e1e2e", fg="#89b4fa", selectcolor="#313244", activebackground="#1e1e2e",
                       font=("Segoe UI", 10)).grid(row=1, column=0, sticky=tk.W)

        ttk.Label(settings_frame, text="掃瞄間隔 (秒):", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky=tk.W)
        self.interval_var = tk.StringVar(value="2") # Changed from 0.5 to 2 as per user edit
        ttk.Entry(settings_frame, textvariable=self.interval_var, width=10).grid(row=2, column=1, sticky=tk.W)

        ttk.Label(settings_frame, text="辨識信心度:", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky=tk.W)
        self.confidence_var = tk.StringVar(value="0.8")
        ttk.Entry(settings_frame, textvariable=self.confidence_var, width=10).grid(row=3, column=1, sticky=tk.W)

        self.btn_toggle = tk.Button(main_frame, text="🚀 啟動系統", command=self.toggle_service,
                                    bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 14, "bold"),
                                    padx=40, pady=15, borderwidth=0, cursor="hand2")
        self.btn_toggle.pack(pady=10)
        
        self.log_area = scrolledtext.ScrolledText(main_frame, height=12, bg="#181825", fg="#bac2de", font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state=tk.DISABLED)

    def load_templates(self):
        self.template_cache = {}
        if not os.path.exists(self.templates_dir): return
        count = 0
        for f in os.listdir(self.templates_dir):
            if f.endswith(".png"):
                img = cv2.imread(os.path.join(self.templates_dir, f), 0)
                if img is not None:
                    h, w = img.shape
                    self.template_cache[f] = (img, w, h)
                    count += 1
        self.log(f"系統：已載入 {count} 個特徵圖。")

    def select_roi(self):
        self.root.withdraw(); time.sleep(0.5)
        selection_win = tk.Toplevel()
        user32 = ctypes.windll.user32
        vx, vy = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
        vw, vh = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
        selection_win.geometry(f"{vw}x{vh}+{vx}+{vy}")
        selection_win.overrideredirect(True)
        selection_win.attributes("-alpha", 0.3, "-topmost", True)
        canvas = tk.Canvas(selection_win, cursor="cross", bg="grey"); canvas.pack(fill="both", expand=True)
        sx, sy, rid = None, None, None
        def on_down(e): nonlocal sx, sy, rid; sx, sy = e.x, e.y; rid = canvas.create_rectangle(sx, sy, sx, sy, outline="yellow", width=3)
        def on_up(e):
            ex, ey = e.x, e.y; selection_win.destroy()
            self.roi = (min(sx, ex) + vx, min(sy, ey) + vy, max(sx, ex) + vx, max(sy, ey) + vy)
            self.log(f"區域設定: {self.roi}"); self.root.deiconify()
        canvas.bind("<ButtonPress-1>", on_down); canvas.bind("<B1-Motion>", lambda e: canvas.coords(rid, sx, sy, e.x, e.y)); canvas.bind("<ButtonRelease-1>", on_up)

    def capture_template(self):
        name_win = tk.Toplevel(self.root); name_win.title("捕捉特徵")
        prefix_var = tk.StringVar(value="target_")
        prefixes = [("點擊 (target_)", "target_"), ("觸發 (trigger_)", "trigger_"), ("讚 (like_)", "like_"), ("輸入 (input_)", "input_")]
        for text, val in prefixes: tk.Radiobutton(name_win, text=text, variable=prefix_var, value=val).pack(anchor=tk.W, padx=20)
        entry = tk.Entry(name_win); entry.pack(padx=20, pady=5); entry.insert(0, "new")
        def do_capture():
            fname = f"{prefix_var.get()}{entry.get()}.png"
            name_win.destroy(); self.root.withdraw(); time.sleep(0.5)
            selection_win = tk.Toplevel()
            user32 = ctypes.windll.user32
            vx, vy = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
            vw, vh = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
            selection_win.geometry(f"{vw}x{vh}+{vx}+{vy}")
            selection_win.overrideredirect(True)
            selection_win.attributes("-alpha", 0.3, "-topmost", True)
            canvas = tk.Canvas(selection_win, cursor="cross", bg="grey"); canvas.pack(fill="both", expand=True)
            sx, sy, rid = None, None, None
            def d_cap(e): nonlocal sx, sy, rid; sx, sy = e.x, e.y; rid = canvas.create_rectangle(sx, sy, sx, sy, outline="red", width=2)
            def u_cap(e):
                ex, ey = e.x, e.y; selection_win.destroy()
                abs_box = (min(sx, ex) + vx, min(sy, ey) + vy, max(sx, ex) + vx, max(sy, ey) + vy)
                img = ImageGrab.grab(bbox=abs_box, all_screens=True)
                img.save(os.path.join(self.templates_dir, fname))
                self.log(f"捕捉完成: {fname}"); self.load_templates(); self.root.deiconify()
            canvas.bind("<ButtonPress-1>", d_cap); canvas.bind("<B1-Motion>", lambda e: canvas.coords(rid, sx, sy, e.x, e.y)); canvas.bind("<ButtonRelease-1>", u_cap)
        tk.Button(name_win, text="確定捕捉", command=do_capture).pack(pady=10)

    def setup_keyboard_listener(self):
        keyboard.add_hotkey('ctrl+c', self.remote_stop)

    def remote_stop(self):
        if self.is_running: self.root.after(0, self.toggle_service); self.log("!!! 🛑 緊急中斷 !!!")

    def log(self, message):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_area.see(tk.END); self.log_area.configure(state=tk.DISABLED)

    def toggle_service(self):
        if not self.is_running:
            self.total_click_count = 0
            self.session_start_time = time.time()
            self.is_running = True
            self.btn_toggle.configure(text="🛑 停止運行", bg="#f38ba8")
            self.status_label.configure(text="Status: ACTIVE", foreground="#a6e3a1")
            self.update_security_display()
            threading.Thread(target=self.click_loop, daemon=True).start()
        else:
            self.is_running = False
            self.btn_toggle.configure(text="🚀 啟動系統", bg="#a6e3a1")
            self.status_label.configure(text="Status: IDLE", foreground="#fab387")

    def update_security_display(self):
        if not self.is_running: return
        elapsed = time.time() - self.session_start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        self.timer_label.configure(text=f"運行時間: {mins:02d}:{secs:02d} / 30:00")
        self.counter_label.configure(text=f"總點擊數: {self.total_click_count} / 100")
        
        # Color warning
        if mins >= 25: self.timer_label.configure(foreground="#f38ba8")
        if self.total_click_count >= 80: self.counter_label.configure(foreground="#f38ba8")
        
        self.root.after(1000, self.update_security_display)

    def find_matches_in_cache(self, screen_gray, prefix, threshold, ox, oy):
        matches = []
        for name, (tpl, w, h) in self.template_cache.items():
            if name.startswith(prefix):
                if h > screen_gray.shape[0] or w > screen_gray.shape[1]: continue
                res = cv2.matchTemplate(screen_gray, tpl, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                if max_val >= threshold:
                    matches.append({'x': max_loc[0] + w//2 + ox, 'y': max_loc[1] + h//2 + oy, 'w': w, 'h': h, 'val': max_val, 'name': name})
        return sorted(matches, key=lambda x: x['val'], reverse=True)

    def human_click(self, x, y):
        tx, ty = x + random.randint(-2, 2), y + random.randint(-2, 2)
        pyautogui.moveTo(tx, ty, duration=random.uniform(0.2, 0.4), tween=pyautogui.easeInOutQuad)
        pyautogui.mouseDown(); time.sleep(random.uniform(0.05, 0.12)); pyautogui.mouseUp()
        self.click_history.append(time.time())
        self.total_click_count += 1
        self.log(f"點擊 @ ({tx}, {ty}) [總計: {self.total_click_count}]")

    def highlight(self, m):
        h = tk.Toplevel()
        h.geometry(f"{m['w']}x{m['h']}+{m['x']-m['w']//2}+{m['y']-m['h']//2}")
        h.overrideredirect(True); h.attributes("-topmost", True, "-alpha", 0.6); h.configure(bg="red")
        self.root.after(500, h.destroy)

    def click_loop(self):
        while self.is_running:
            try:
                now = time.time()
                # 1. Session Timeout Check (30 mins)
                elapsed = now - self.session_start_time
                if elapsed > 1800:
                    self.log("🕒 熔斷預警：執行已滿 30 分鐘，系統自動斷電保護。")
                    self.root.after(0, self.toggle_service)
                    messagebox.showinfo("安全提示", "自動化工作已滿 30 分鐘，為了帳號安全已自動停止。")
                    return

                # 2. Total Click Limit (100 clicks)
                if self.total_click_count >= 100:
                    self.log("🛑 熔斷預警：總點擊量已達 100 次，系統自動停止。")
                    self.root.after(0, self.toggle_service)
                    messagebox.showwarning("熔斷警報", "總點擊量已達 100 次安全限制，請人工檢查。")
                    return

                conf = float(self.confidence_var.get())
                bbox = self.roi if self.roi else None
                if bbox is None:
                    user32 = ctypes.windll.user32
                    vx, vy = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
                    vw, vh = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
                    bbox = (vx, vy, vx + vw, vy + vh)
                
                screen = np.array(ImageGrab.grab(bbox=bbox, all_screens=True))
                screen_gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
                ox, oy = bbox[0], bbox[1]

                # Protocol Logic: Update unseen triggers for cooldown reset
                for handled_name in list(self.handled_triggers):
                    if now - self.trigger_last_seen.get(handled_name, 0) > 300:
                        self.handled_triggers.remove(handled_name)
                        self.log(f"記憶重置：{handled_name} 已清空記憶位。")

                # 3. Messenger Protocol
                if self.protocol_mode.get():
                    triggers = self.find_matches_in_cache(screen_gray, "trigger_", conf, ox, oy)
                    for t in triggers:
                        self.trigger_last_seen[t['name']] = now
                        if t['name'] in self.handled_triggers: continue
                        
                        self.log(f"🔥 觸發判定: {t['name']}")
                        fb_found = False
                        for _ in range(3):
                            s_fb = np.array(ImageGrab.grab(bbox=bbox, all_screens=True))
                            g_fb = cv2.cvtColor(s_fb, cv2.COLOR_RGB2GRAY)
                            likes = self.find_matches_in_cache(g_fb, "like_", conf, ox, oy)
                            if likes:
                                l = likes[0]; self.log(f"👍 執行行為回應 {l['name']}")
                                if self.preview_mode.get(): self.highlight(l)
                                else: self.human_click(l['x'], l['y'])
                                fb_found = True; break
                            inputs = self.find_matches_in_cache(g_fb, "input_", conf, ox, oy)
                            if inputs:
                                i = inputs[0]; self.log(f"✍️ 執行文字回應 {i['name']}")
                                if self.preview_mode.get(): self.highlight(i)
                                else: 
                                    self.human_click(i['x'], i['y'])
                                    time.sleep(0.1); pyautogui.write("Done!", interval=0.05); pyautogui.press('enter')
                                fb_found = True; break
                            time.sleep(0.2)
                        
                        if fb_found:
                            self.handled_triggers.add(t['name'])
                        time.sleep(1.0); break 

                # 4. General Target Click
                targets = self.find_matches_in_cache(screen_gray, "target_", conf, ox, oy)
                if targets:
                    t = targets[0]
                    if self.preview_mode.get(): self.highlight(t)
                    else:
                        # Short-term burst check
                        self.click_history = [th for th in self.click_history if now - th < 300]
                        if len(self.click_history) >= 15: self.log("⚠️ 密度過載"); self.root.after(0, self.toggle_service); return
                        self.human_click(t['x'], t['y'])
                    time.sleep(1.0)
                    
            except Exception as e: self.log(f"ERROR: {str(e)}")
            time.sleep(float(self.interval_var.get()))

if __name__ == "__main__":
    root = tk.Tk(); app = AntigravityClicker(root); root.mainloop()
