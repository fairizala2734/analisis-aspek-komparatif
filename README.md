# Analisis Aspek Komparatif

Aplikasi ini membantu menemukan aspek atau tema dari jawaban responden yang
membandingkan dua hal atau lebih.

Contoh:

```text
Pertanyaan: Apa keunggulan batik tulis dibandingkan batik cap?
Hal yang dibandingkan: batik tulis dan batik cap
```

Sistem akan memproses jawaban, menemukan aspek yang muncul, menyatukan nama
aspek yang serupa, lalu menampilkan frekuensi dan contoh pendapatnya.

## Yang Perlu Disiapkan

- Python versi 3.10 atau lebih baru
- API key OpenRouter
- Koneksi internet
- Git, hanya jika ingin menggunakan metode clone

## 1. Download Aplikasi

### Cara Termudah: Download ZIP

1. Buka halaman repository ini di GitHub.
2. Klik tombol **Code**.
3. Pilih **Download ZIP**.
4. Ekstrak file ZIP.
5. Buka folder hasil ekstrak.

### Cara Alternatif: Clone dengan Git

Buka PowerShell atau Terminal, lalu jalankan:

```text
git clone https://github.com/fairizala2734/analisis-aspek-komparatif.git
cd analisis-aspek-komparatif
```

## 2. Instal Aplikasi

Pastikan PowerShell atau Terminal sudah berada di dalam folder aplikasi.

### Windows PowerShell

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Jika `py` tidak tersedia, ganti perintah pertama dengan:

```powershell
python -m venv venv
```

Jika aktivasi ditolak PowerShell, jalankan:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### Linux

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

Jika virtual environment gagal dibuat pada Ubuntu atau Debian, instal paket
`python3-venv` terlebih dahulu.

### macOS

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## 3. Masukkan API Key

### Windows PowerShell

```powershell
Copy-Item .streamlit\secrets.example.toml .streamlit\secrets.toml
notepad .streamlit\secrets.toml
```

### Linux

```bash
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
nano .streamlit/secrets.toml
```

### macOS

```bash
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
open -e .streamlit/secrets.toml
```

Cari bagian berikut, lalu masukkan API key OpenRouter Anda:

```toml
[llm]
api_key = "sk-or-v1-..."
```

Jangan membagikan atau mengunggah file `.streamlit/secrets.toml` ke GitHub.

## 4. Jalankan Aplikasi

### Windows PowerShell

```powershell
python -m streamlit run app.py
```

### Linux dan macOS

```bash
python -m streamlit run app.py
```

Browser biasanya terbuka otomatis. Jika tidak, buka:

```text
http://localhost:8501
```

Untuk menghentikan aplikasi, tekan `Ctrl + C` pada PowerShell atau Terminal.

## 5. Cara Menggunakan

1. Buka halaman **Mulai Analisis**.
2. Upload CSV yang berisi kolom pertanyaan dan jawaban.
3. Isi minimal dua hal yang dibandingkan.
4. Pilih **Cek cepat 5 baris** untuk percobaan awal atau **Analisis penuh** untuk seluruh data.
5. Klik tombol untuk memulai analisis.
6. Setelah selesai, buka halaman **Hasil Analisis**.
7. Tinjau aspek, contoh pendapat, dan download hasil jika diperlukan.

## Catatan Penting

- Proses pertama dapat lebih lama karena model bahasa Stanza perlu diunduh.
- Setelah mengganti API key, hentikan lalu jalankan ulang aplikasi.
- Hasil analisis disimpan secara lokal di folder `local_results`.
- Di macOS, folder `.streamlit` mungkin tersembunyi. Tekan `Command + Shift + .`
  di Finder untuk menampilkannya.
- Jika muncul error OpenRouter `401`, periksa API key lalu restart aplikasi.

## Memperbarui Aplikasi

Jika aplikasi diperoleh melalui Git clone, jalankan:

```text
git pull origin main
python -m pip install -r requirements.txt
```

Jika menggunakan ZIP, download kembali versi terbaru dari GitHub.
