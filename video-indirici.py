import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


from yt_dlp import YoutubeDL


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video İndirici (YouTube / X / Instagram) - yt-dlp")
        self.geometry("700x420")
        self.minsize(700, 420)

        self.download_dir = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Hazır")
        self.progress_var = tk.DoubleVar(value=0.0)

        self.cookies_path = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 8}

        frm_url = ttk.LabelFrame(self, text="Video Linki")
        frm_url.pack(fill="x", **pad)

        ttk.Label(frm_url, text="URL:").pack(side="left", padx=(10, 6), pady=10)
        ent = ttk.Entry(frm_url, textvariable=self.url_var)
        ent.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)
        ent.focus()

        frm_dir = ttk.LabelFrame(self, text="İndirme Klasörü")
        frm_dir.pack(fill="x", **pad)

        ttk.Entry(frm_dir, textvariable=self.download_dir).pack(side="left", fill="x", expand=True, padx=(10, 6), pady=10)
        ttk.Button(frm_dir, text="Klasör Seç", command=self.pick_folder).pack(side="left", padx=(0, 10), pady=10)

        frm_opt = ttk.LabelFrame(self, text="Seçenekler")
        frm_opt.pack(fill="x", **pad)

        self.format_choice = tk.StringVar(value="best")
        ttk.Label(frm_opt, text="Kalite:").grid(row=0, column=0, sticky="w", padx=10, pady=10)

        cmb = ttk.Combobox(
            frm_opt,
            textvariable=self.format_choice,
            values=[
                "best",                 
                "bestvideo+bestaudio",  
                "mp4 (uyumlu)",        
                "worst"               
            ],
            state="readonly",
            width=22
        )
        cmb.grid(row=0, column=1, sticky="w", pady=10)

        ttk.Label(frm_opt, text="Cookies (opsiyonel):").grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))
        ttk.Entry(frm_opt, textvariable=self.cookies_path).grid(row=1, column=1, sticky="we", pady=(0, 10), padx=(0, 6))
        ttk.Button(frm_opt, text="Cookies Seç", command=self.pick_cookies).grid(row=1, column=2, sticky="w", pady=(0, 10), padx=(0, 10))

        frm_opt.columnconfigure(1, weight=1)

        frm_prog = ttk.LabelFrame(self, text="İlerleme")
        frm_prog.pack(fill="x", **pad)

        self.progress = ttk.Progressbar(frm_prog, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", padx=10, pady=(10, 6))

        ttk.Label(frm_prog, textvariable=self.status_var).pack(anchor="w", padx=10, pady=(0, 10))

        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill="x", **pad)

        self.btn_download = ttk.Button(frm_btn, text="İndir", command=self.start_download)
        self.btn_download.pack(side="left")

        ttk.Button(frm_btn, text="Temizle", command=self.clear).pack(side="left", padx=8)

        ttk.Label(frm_btn, text="Not: Instagram bazı linklerde cookies isteyebilir.", foreground="#555").pack(side="right")

    def pick_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_dir.get())
        if folder:
            self.download_dir.set(folder)

    def pick_cookies(self):
        path = filedialog.askopenfilename(
            title="cookies.txt seç (opsiyonel)",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            self.cookies_path.set(path)

    def clear(self):
        self.url_var.set("")
        self.progress_var.set(0)
        self.status_var.set("Hazır")

    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Eksik Bilgi", "Lütfen bir URL gir.")
            return

        out_dir = self.download_dir.get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning("Klasör Hatası", "Geçerli bir indirme klasörü seç.")
            return

        self.btn_download.config(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("Başlatılıyor...")

        t = threading.Thread(target=self._download, args=(url, out_dir), daemon=True)
        t.start()

    def _download(self, url, out_dir):
        def hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)

                if total:
                    pct = (downloaded / total) * 100
                    self._ui_progress(pct)

                speed = d.get("speed")
                eta = d.get("eta")
                msg = "İndiriliyor"
                if speed:
                    msg += f" | hız: {speed/1024/1024:.2f} MB/s"
                if eta:
                    msg += f" | kalan: {eta} sn"
                self._ui_status(msg)

            elif d["status"] == "finished":
                self._ui_progress(100)
                self._ui_status("İndirme bitti, dönüştürme/işleme olabilir...")

        fmt = self.format_choice.get()
        if fmt == "mp4 (uyumlu)":
            format_spec = "best[ext=mp4]/best"
        elif fmt == "bestvideo+bestaudio":
            format_spec = "bestvideo+bestaudio/best"
        else:
            format_spec = fmt  

        outtmpl = os.path.join(out_dir, "%(title).180s [%(id)s].%(ext)s")

        ydl_opts = {
            "format": format_spec,
            "outtmpl": outtmpl,
            "noplaylist": True,
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
        }

        cookies = self.cookies_path.get().strip()
        if cookies:
            ydl_opts["cookiefile"] = cookies

        try:
            with YoutubeDL(ydl_opts) as ydl:
                self._ui_status("Bilgi alınıyor...")
                ydl.download([url])

            self._ui_status("✅ Tamamlandı")
            messagebox.showinfo("Bitti", "İndirme tamamlandı.")
        except Exception as e:
            self._ui_status("❌ Hata oluştu")
            messagebox.showerror("Hata", f"İndirme başarısız:\n{e}")
        finally:
            self.btn_download.config(state="normal")

    def _ui_progress(self, pct):
        # Tkinter thread-safe güncelleme
        self.after(0, lambda: self.progress_var.set(max(0, min(100, pct))))

    def _ui_status(self, text):
        self.after(0, lambda: self.status_var.set(text))


if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = App()
    app.mainloop()
