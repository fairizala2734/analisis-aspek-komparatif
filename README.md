# Analisis Aspek Komparatif

Aplikasi Streamlit lokal untuk analisis kualitatif-komparatif dari CSV
pertanyaan dan jawaban.

## Menjalankan

```powershell
.\venv\Scripts\streamlit.exe run app.py
```

Atau instal dependency terlebih dahulu:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Konfigurasi API Key

Salin template konfigurasi:

```powershell
Copy-Item .streamlit\secrets.example.toml .streamlit\secrets.toml
```

Kemudian buka `.streamlit/secrets.toml` dan ganti:

```toml
api_key = "ISI_OPENROUTER_API_KEY_DI_SINI"
```

dengan API key OpenRouter milik Anda.

## Alur Analisis

`CSV + hal yang dibandingkan -> validasi -> opinion unit -> POS -> candidate code -> normalisasi -> ringkasan`

Output utama tetap memakai nama:

- `01_raw_dataset.csv`
- `01_entity_validation.csv`
- `02_opinion_units.csv`
- `02c_opinion_units_pos.csv`
- `03_candidate_codes.csv`
- `04_candidate_summary.csv`
- `05_candidate_code_mapping.csv`
- `05_candidate_code_normalized.csv`
- `06_candidate_summary_normalized.csv`

## Struktur Folder

```text
app.py                 Entry point Streamlit
pages/                 Halaman Run dan Hasil
pipeline/              Engine 01-06, konfigurasi, ingest, Stanza, dan normalisasi
llm/                   OpenRouter, cache, parser JSON, dan prompt
storage/               SQLite, manifest, folder project, ZIP
ui/                    Komponen tampilan Streamlit
tests/                 Pengujian otomatis
local_results/         Database, cache LLM, dan hasil analisis
```

Hasil run baru disimpan di:

```text
local_results/projects/<judul-project>__<signature>/
```
