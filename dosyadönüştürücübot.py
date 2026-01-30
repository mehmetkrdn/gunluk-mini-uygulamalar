import os
import sys
import threading
import subprocess
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from pdf2docx import Converter

try:
    from docx2pdf import convert as docx2pdf_convert
except Exception:
    docx2pdf_convert = None


def which_soffice():
    candidates = [
        "soffice",
        "soffice.exe",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for c in candidates:
        p = shutil.which(c) if not os.path.isabs(c) else (c if os.path.exists(c) else None)
        if p:
            return p
    return None


def to_abs(path):
    return os.path.abspath(os.path.expanduser(path))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DOCX ⇄ PDF Dönüştürücü Bot")
        self.geometry("820x520")
        self.minsize(820, 520)

        self.mode = tk.StringVar(value="docx2pdf")
        self.out_dir = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.status = tk.StringVar(value="Hazır")
        self.progress = tk.DoubleVar(value=0.0)

        self.files = []
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 12, "pady": 10}

        top = ttk.Frame(self)
        top.pack(fill="x", **pad)

        mode_box = ttk.LabelFrame(top, text="Mod")
        mode_box.pack(side="left", fill="x", expand=True)

        ttk.Radiobutton(mode_box, text="DOCX → PDF", variable=self.mode, value="docx2pdf").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        ttk.Radiobutton(mode_box, text="PDF → DOCX", variable=self.mode, value="pdf2docx").grid(row=0, column=1, sticky="w", padx=10, pady=10)

        out_box = ttk.LabelFrame(top, text="Çıkış Klasörü")
        out_box.pack(side="left", fill="x", expand=True, padx=(12, 0))

        ttk.Entry(out_box, textvariable=self.out_dir).grid(row=0, column=0, sticky="we", padx=10, pady=10)
        ttk.Button(out_box, text="Seç", command=self.pick_out_dir).grid(row=0, column=1, padx=(0, 10), pady=10)
        out_box.columnconfigure(0, weight=1)

        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True, **pad)

        files_box = ttk.LabelFrame(mid, text="Dosyalar")
        files_box.pack(fill="both", expand=True, side="left")

        btns = ttk.Frame(files_box)
        btns.pack(fill="x", padx=10, pady=(10, 6))
        ttk.Button(btns, text="Dosya Seç", command=self.pick_files).pack(side="left")
        ttk.Button(btns, text="Klasörden Ekle", command=self.pick_folder_files).pack(side="left", padx=8)
        ttk.Button(btns, text="Listeyi Temizle", command=self.clear_files).pack(side="left", padx=8)

        self.listbox = tk.Listbox(files_box, height=14, selectmode=tk.EXTENDED)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        right = ttk.Frame(mid)
        right.pack(fill="y", side="left", padx=(12, 0))

        act_box = ttk.LabelFrame(right, text="İşlem")
        act_box.pack(fill="x")

        self.btn_start = ttk.Button(act_box, text="DÖNÜŞTÜR", command=self.start)
        self.btn_start.pack(fill="x", padx=10, pady=10)

        ttk.Button(act_box, text="Seçiliyi Listeden Sil", command=self.remove_selected).pack(fill="x", padx=10, pady=(0, 10))

        info_box = ttk.LabelFrame(right, text="Bilgi")
        info_box.pack(fill="x", pady=(12, 0))

        self.info_text = tk.Text(info_box, height=10, width=30)
        self.info_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.info_text.configure(state="disabled")

        bottom = ttk.LabelFrame(self, text="Durum")
        bottom.pack(fill="x", **pad)

        self.pbar = ttk.Progressbar(bottom, maximum=100, variable=self.progress)
        self.pbar.pack(fill="x", padx=10, pady=(10, 6))
        ttk.Label(bottom, textvariable=self.status).pack(anchor="w", padx=10, pady=(0, 10))

        self._refresh_info()

    def log_info(self, text):
        def _do():
            self.info_text.configure(state="normal")
            self.info_text.insert("end", text + "\n")
            self.info_text.see("end")
            self.info_text.configure(state="disabled")
        self.after(0, _do)

    def _refresh_info(self):
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.configure(state="disabled")
        self.log_info("Çalışma:")
        self.log_info("• Çoklu dosya destekli")
        self.log_info("• DOCX→PDF: docx2pdf → LibreOffice fallback")
        self.log_info("• PDF→DOCX: pdf2docx")
        self.log_info("")
        self.log_info("İpuçları:")
        self.log_info("• DOCX→PDF için Word varsa en iyi sonuç")
        self.log_info("• Word yoksa LibreOffice kurulu olmalı")

    def pick_out_dir(self):
        d = filedialog.askdirectory(initialdir=self.out_dir.get())
        if d:
            self.out_dir.set(d)

    def pick_files(self):
        mode = self.mode.get()
        if mode == "docx2pdf":
            types = [("Word", "*.docx"), ("All", "*.*")]
        else:
            types = [("PDF", "*.pdf"), ("All", "*.*")]
        paths = filedialog.askopenfilenames(filetypes=types)
        if paths:
            self.add_files(list(paths))

    def pick_folder_files(self):
        d = filedialog.askdirectory(initialdir=self.out_dir.get())
        if not d:
            return
        mode = self.mode.get()
        ext = ".docx" if mode == "docx2pdf" else ".pdf"
        found = []
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith(ext):
                    found.append(os.path.join(root, f))
        if not found:
            messagebox.showinfo("Bulunamadı", f"Klasörde {ext} uzantılı dosya yok.")
            return
        self.add_files(found)

    def add_files(self, paths):
        new = 0
        for p in paths:
            p = to_abs(p)
            if os.path.isfile(p) and p not in self.files:
                self.files.append(p)
                new += 1
        self.refresh_listbox()
        self.status.set(f"{len(self.files)} dosya listede (+{new})")

    def refresh_listbox(self):
        self.listbox.delete(0, "end")
        for p in self.files:
            self.listbox.insert("end", p)

    def clear_files(self):
        self.files = []
        self.refresh_listbox()
        self.progress.set(0)
        self.status.set("Hazır")

    def remove_selected(self):
        sel = list(self.listbox.curselection())
        if not sel:
            return
        sel_paths = {self.files[i] for i in sel}
        self.files = [p for p in self.files if p not in sel_paths]
        self.refresh_listbox()
        self.status.set(f"{len(self.files)} dosya listede")

    def start(self):
        if not self.files:
            messagebox.showwarning("Eksik", "Dosya seçmedin.")
            return
        out = to_abs(self.out_dir.get())
        if not os.path.isdir(out):
            messagebox.showwarning("Hata", "Geçerli bir çıkış klasörü seç.")
            return

        self.btn_start.config(state="disabled")
        self.progress.set(0)
        self.status.set("Başlatılıyor...")
        self.log_info("")
        self.log_info("---- Başladı ----")

        t = threading.Thread(target=self._run, args=(out,), daemon=True)
        t.start()

    def _safe_name(self, path):
        base = os.path.splitext(os.path.basename(path))[0]
        base = base.strip().replace("\n", " ").replace("\r", " ")
        if not base:
            base = "dosya"
        return base[:180]

    def _docx_to_pdf_docx2pdf(self, src, dst_pdf):
        if docx2pdf_convert is None:
            raise RuntimeError("docx2pdf kullanılamıyor.")
        dst_dir = os.path.dirname(dst_pdf)
        os.makedirs(dst_dir, exist_ok=True)
        docx2pdf_convert(src, dst_dir)
        produced = os.path.join(dst_dir, os.path.splitext(os.path.basename(src))[0] + ".pdf")
        if not os.path.exists(produced):
            raise RuntimeError("PDF üretilemedi.")
        if os.path.abspath(produced) != os.path.abspath(dst_pdf):
            if os.path.exists(dst_pdf):
                os.remove(dst_pdf)
            os.replace(produced, dst_pdf)

    def _docx_to_pdf_libreoffice(self, src, out_dir):
        soffice = which_soffice()
        if not soffice:
            raise RuntimeError("LibreOffice (soffice) bulunamadı.")
        os.makedirs(out_dir, exist_ok=True)
        cmd = [soffice, "--headless", "--nologo", "--nolockcheck", "--nodefault", "--norestore", "--convert-to", "pdf", "--outdir", out_dir, src]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout or "LibreOffice dönüşüm hatası").strip())
        produced = os.path.join(out_dir, os.path.splitext(os.path.basename(src))[0] + ".pdf")
        if not os.path.exists(produced):
            raise RuntimeError("LibreOffice PDF üretmedi.")
        return produced

    def _pdf_to_docx(self, src, dst_docx):
        os.makedirs(os.path.dirname(dst_docx), exist_ok=True)
        cv = Converter(src)
        try:
            cv.convert(dst_docx, start=0, end=None)
        finally:
            cv.close()

    def _run(self, out_dir):
        mode = self.mode.get()
        total = len(self.files)
        ok = 0
        fail = 0

        for i, src in enumerate(list(self.files), start=1):
            try:
                base = self._safe_name(src)
                if mode == "docx2pdf":
                    dst_pdf = os.path.join(out_dir, base + ".pdf")
                    self._ui_status(f"[{i}/{total}] DOCX→PDF: {os.path.basename(src)}")
                    try:
                        self._docx_to_pdf_docx2pdf(src, dst_pdf)
                        self.log_info(f"OK  : {os.path.basename(src)}  →  {os.path.basename(dst_pdf)} (docx2pdf)")
                    except Exception as e1:
                        produced = self._docx_to_pdf_libreoffice(src, out_dir)
                        if os.path.abspath(produced) != os.path.abspath(dst_pdf):
                            if os.path.exists(dst_pdf):
                                os.remove(dst_pdf)
                            os.replace(produced, dst_pdf)
                        self.log_info(f"OK  : {os.path.basename(src)}  →  {os.path.basename(dst_pdf)} (LibreOffice)")
                else:
                    dst_docx = os.path.join(out_dir, base + ".docx")
                    self._ui_status(f"[{i}/{total}] PDF→DOCX: {os.path.basename(src)}")
                    self._pdf_to_docx(src, dst_docx)
                    self.log_info(f"OK  : {os.path.basename(src)}  →  {os.path.basename(dst_docx)}")
                ok += 1
            except Exception as e:
                fail += 1
                self.log_info(f"FAIL: {os.path.basename(src)} | {str(e).strip()}")
            self._ui_progress((i / total) * 100)

        self._ui_status(f"Bitti. Başarılı: {ok} | Hatalı: {fail}")
        self.log_info("---- Bitti ----")
        self.after(0, lambda: self.btn_start.config(state="normal"))
        if fail == 0:
            self.after(0, lambda: messagebox.showinfo("Tamam", f"Bitti.\nBaşarılı: {ok}"))
        else:
            self.after(0, lambda: messagebox.showwarning("Bitti", f"Bitti.\nBaşarılı: {ok}\nHatalı: {fail}"))

    def _ui_status(self, text):
        self.after(0, lambda: self.status.set(text))

    def _ui_progress(self, pct):
        self.after(0, lambda: self.progress.set(max(0, min(100, pct))))


if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = App()
    app.mainloop()
