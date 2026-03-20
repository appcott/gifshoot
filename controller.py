"""GifShoot Controller – 常駐フローティングUIパネル"""

import tkinter as tk


class ControllerUI:
    def __init__(self, on_fullscreen, on_region, on_stop, on_gallery, on_quit, recorder=None):
        self.on_fullscreen = on_fullscreen
        self.on_region = on_region
        self.on_stop = on_stop
        self.on_gallery = on_gallery
        self.on_quit = on_quit
        self.recorder = recorder

        self.root = tk.Tk()
        self.root.title("GifShoot")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        # ── ウィンドウを画面右下に配置 ──
        self.root.update_idletasks()
        w, h = 220, 300
        sx = self.root.winfo_screenwidth() - w - 20
        sy = self.root.winfo_screenheight() - h - 60
        self.root.geometry(f"{w}x{h}+{sx}+{sy}")

        # ── タイトル ──
        tk.Label(
            self.root, text="GifShoot", font=("Consolas", 14, "bold"),
            fg="#ff4444", bg="#1e1e1e"
        ).pack(pady=(10, 4))

        # ── ステータス ──
        self.status_var = tk.StringVar(value="待機中")
        tk.Label(
            self.root, textvariable=self.status_var,
            font=("Consolas", 10), fg="#aaaaaa", bg="#1e1e1e"
        ).pack()

        # ── カウントダウン ──
        self.timer_var = tk.StringVar(value="")
        tk.Label(
            self.root, textvariable=self.timer_var,
            font=("Consolas", 22, "bold"), fg="#ff6666", bg="#1e1e1e"
        ).pack(pady=(2, 2))

        # ── ボタン群 ──
        btn_cfg = dict(
            font=("Consolas", 10), width=18, relief="flat",
            activebackground="#555555", cursor="hand2", bd=0, pady=4
        )

        self.btn_full = tk.Button(
            self.root, text="⏺  全画面録画", bg="#333333", fg="white",
            command=self._on_fullscreen, **btn_cfg
        )
        self.btn_full.pack(pady=(6, 4))

        self.btn_region = tk.Button(
            self.root, text="⬜  範囲選択録画", bg="#333333", fg="white",
            command=self._on_region, **btn_cfg
        )
        self.btn_region.pack(pady=4)

        self.btn_stop = tk.Button(
            self.root, text="⏹  録画停止", bg="#cc3333", fg="white",
            command=self._on_stop, state="disabled", **btn_cfg
        )
        self.btn_stop.pack(pady=4)

        self.btn_gallery = tk.Button(
            self.root, text="🖼  ギャラリー", bg="#333333", fg="white",
            command=self._on_gallery, **btn_cfg
        )
        self.btn_gallery.pack(pady=4)

        # Wire recorder tick callback
        if self.recorder:
            self.recorder.on_tick = self._on_tick

    # ── カウントダウン表示 ──
    def _on_tick(self, remaining):
        """Called from recorder thread – schedule on main thread."""
        self.root.after(0, self._update_timer, remaining)

    def _update_timer(self, remaining):
        self.timer_var.set(f"残り {remaining}s")

    # ── 内部ハンドラ ──
    def _set_recording(self, active: bool):
        if active:
            self.status_var.set("⏺ 録画中…")
            self.btn_full.config(state="disabled")
            self.btn_region.config(state="disabled")
            self.btn_stop.config(state="normal")
        else:
            self.status_var.set("待機中")
            self.timer_var.set("") # タイマーをリセット
            self.btn_full.config(state="normal")
            self.btn_region.config(state="normal")
            self.btn_stop.config(state="disabled")

    def _on_fullscreen(self):
        self._set_recording(True)
        self.on_fullscreen()

    def _on_region(self):
        self.root.withdraw()
        self.on_region(self._after_region_selected)

    def _after_region_selected(self):
        self.root.after(0, self._restore_after_region)

    def _restore_after_region(self):
        self.root.deiconify()
        self._set_recording(True)

    def _on_stop(self):
        # 録画停止ボタンが押されたら、保存処理・UI更新は main.py / recorder.py 側のコールバックに委ねる
        self.on_stop()

    def _on_gallery(self):
        self.on_gallery()

    def _quit(self):
        self.on_quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
