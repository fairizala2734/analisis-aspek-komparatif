# Analisis Aspek Komparatif

Aplikasi Streamlit lokal untuk membantu analisis kualitatif-komparatif dari data
pertanyaan dan jawaban berbentuk CSV. Sistem memeriksa hal yang dibandingkan,
memecah jawaban menjadi unit pendapat, mengambil aspek, merapikan label yang
serupa, lalu menyusun ringkasan hasil.

## Kebutuhan Sistem

Siapkan perangkat berikut sebelum instalasi:

- Python 3.10 atau lebih baru
- Git, jika menggunakan metode clone
- Akun dan API key OpenRouter
- Koneksi internet untuk OpenRouter dan pengunduhan model Stanza pertama kali

Periksa instalasi Python dan Git:

```text
python --version
git --version
```

Pada Linux dan macOS, perintah Python biasanya menggunakan `python3`.

## 1. Mendapatkan Proyek

### Pilihan A: Clone dengan Git (disarankan)

Metode ini paling mudah untuk mengambil pembaruan berikutnya.

**Windows PowerShell**

```powershell
New-Item -ItemType Directory -Force "$HOME\Projects" | Out-Null
Set-Location "$HOME\Projects"
git clone https://github.com/fairizala2734/analisis-aspek-komparatif.git
cd analisis-aspek-komparatif
```

**Linux**

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/fairizala2734/analisis-aspek-komparatif.git
cd analisis-aspek-komparatif
```

**macOS**

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/fairizala2734/analisis-aspek-komparatif.git
cd analisis-aspek-komparatif
```

Folder `Projects` boleh diganti dengan lokasi lain.

### Pilihan B: Download ZIP

1. Buka halaman repository GitHub.
2. Pilih **Code**, lalu **Download ZIP**.
3. Ekstrak ZIP ke folder yang diinginkan.
4. Buka PowerShell atau Terminal di dalam folder hasil ekstrak.

Folder `.streamlit` diawali tanda titik sehingga dianggap tersembunyi oleh
macOS dan Linux. Folder tersebut tetap diperlukan. Gunakan perintah berikut
untuk memastikannya tersedia:

```bash
ls -la
```

Di Finder macOS, tekan `Command + Shift + .` untuk menampilkan file tersembunyi.

## 2. Membuat Virtual Environment

Virtual environment menjaga dependency aplikasi agar tidak bercampur dengan
instalasi Python lain.

### Windows PowerShell

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Jika perintah aktivasi ditolak oleh PowerShell, jalankan ini hanya untuk sesi
PowerShell yang sedang digunakan, lalu aktifkan kembali:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Jika perintah `py` tidak tersedia, gunakan `python -m venv venv`.

### Linux

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Pada distribusi Debian/Ubuntu, paket `python3-venv` mungkin perlu dipasang jika
pembuatan virtual environment gagal.

### macOS

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Pastikan `python3 --version` menunjukkan Python 3.10 atau lebih baru. Python
bawaan macOS yang terlalu lama tidak disarankan.

## 3. Mengatur API Key OpenRouter

Jangan menulis API key ke `secrets.example.toml`. Salin file contoh menjadi
`secrets.toml`, kemudian isi salinannya.

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

Ubah nilai berikut dengan API key milik Anda:

```toml
[llm]
api_key = "sk-or-v1-..."
```

File `.streamlit/secrets.toml` sudah masuk `.gitignore` dan tidak boleh diunggah
ke GitHub. Setelah mengganti API key ketika aplikasi sedang berjalan, restart
Streamlit agar key baru dimuat.

## 4. Menjalankan Aplikasi

Pastikan virtual environment masih aktif.

### Windows PowerShell

```powershell
python -m streamlit run app.py
```

### Linux

```bash
python -m streamlit run app.py
```

### macOS

```bash
python -m streamlit run app.py
```

Buka alamat berikut jika browser tidak terbuka otomatis:

```text
http://localhost:8501
```

Hentikan aplikasi dengan menekan `Ctrl + C` pada PowerShell atau Terminal.

## 5. Menggunakan Aplikasi

1. Buka halaman **Mulai Analisis**.
2. Upload CSV yang memiliki kolom pertanyaan dan jawaban.
3. Isi minimal dua hal yang dibandingkan beserta nama lainnya jika diperlukan.
4. Pilih mode analisis. Gunakan **Cek cepat 5 baris** untuk pengujian awal.
5. Jalankan analisis dan tunggu seluruh tahap selesai.
6. Buka halaman **Hasil Analisis** untuk meninjau, mengedit aspek, dan mengunduh hasil.

Alur utama sistem:

```text
CSV + hal yang dibandingkan
  -> validasi entity dan pertanyaan komparatif
  -> opinion unit
  -> POS Stanza
  -> candidate code
  -> normalisasi
  -> ringkasan
```

## 6. Memperbarui Proyek Hasil Clone

Perintah berikut sama pada Windows PowerShell, Linux, dan macOS:

```text
git pull origin main
python -m pip install -r requirements.txt
```

Restart Streamlit setelah pembaruan selesai. Metode ini tidak berlaku untuk
proyek yang diperoleh melalui Download ZIP; unduh ZIP terbaru dan ekstrak ulang.

## Output Analisis

Hasil setiap analisis disimpan di:

```text
local_results/projects/<judul-project>__<signature>/
```

Output utama memakai nama berikut:

- `01_raw_dataset.csv`
- `01_entity_validation.csv`
- `02_opinion_units.csv`
- `02c_opinion_units_pos.csv`
- `03_candidate_codes.csv`
- `04_candidate_summary.csv`
- `05_candidate_code_mapping.csv`
- `05_candidate_code_normalized.csv`
- `06_candidate_summary_normalized.csv`

Folder `local_results` hanya disimpan secara lokal dan tidak diunggah ke GitHub.

## Struktur Folder

```text
app.py                 Entry point Streamlit
pages/                 Halaman Mulai Analisis dan Hasil Analisis
pipeline/              Pipeline 01-06, ingest, Stanza, dan normalisasi
llm/                   Client OpenRouter, cache, parser JSON, dan prompt
storage/               Database, manifest, folder project, dan ZIP
ui/                    Komponen tampilan Streamlit
tests/                 Pengujian otomatis
local_results/         Database, cache LLM, dan hasil lokal
```

## Masalah Umum

### `OPENROUTER_API_KEY` belum diisi

Pastikan file yang dibuat bernama `.streamlit/secrets.toml`, bukan
`secrets.example.toml` atau `secrets.toml.txt`, lalu restart Streamlit.

### Error OpenRouter `401 User not found`

API key tidak valid, sudah dicabut, atau aplikasi masih memakai key lama.
Regenerasi key jika diperlukan, isi `secrets.toml`, lalu restart aplikasi.

### Folder `.streamlit` tidak terlihat di macOS atau Linux

Jalankan `ls -la`. Di Finder macOS, tekan `Command + Shift + .`.

### Port `8501` sudah digunakan

Jalankan aplikasi pada port lain:

```text
python -m streamlit run app.py --server.port 8502
```
