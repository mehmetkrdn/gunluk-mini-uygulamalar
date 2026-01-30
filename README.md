Bu repoda günlük hayatta kullanılabilecek iki adet Python masaüstü uygulaması bulunmaktadır:

1) Video İndirici (YouTube, Instagram, X)  
2) DOCX ⇄ PDF Dönüştürücü Bot  

Tüm uygulamalar grafik arayüzlüdür (GUI) ve lokal bilgisayarda çalışır.

---

## 📌 Uygulamalar

### 🎥 Video İndirici
- YouTube, Instagram ve X (Twitter) linklerinden video indirme  
- Kalite seçimi  
- Çıkış klasörü seçme  
- EXE olarak çalıştırılabilir  

Dosya:  
`video-indirici.py`

---

### 📄 DOCX ⇄ PDF Dönüştürücü Bot
- DOCX → PDF dönüştürme  
- PDF → DOCX dönüştürme  
- Çoklu dosya desteği  
- Biçim bozulmasını minimumda tutan dönüşüm  

Dosya:  
`dosyadönüştürücübot.py`

---

## ⚙️ Kurulum

```bash
pip install -r requirements.txt
```
## EXE OLUŞTURMA

pip install pyinstaller
pyinstaller --onefile --windowed video-indirici.py
pyinstaller --onefile --windowed dosyadönüştürücübot.py
