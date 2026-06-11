# Cara Kerja Sistem

Dokumen ini menjelaskan alur aplikasi dari input pengguna sampai menghasilkan
ringkasan candidate code ternormalisasi.

## Gambaran Umum

```text
CSV pertanyaan-jawaban
        |
        v
Validasi entity dan pertanyaan komparatif
        |
        v
01 Raw dataset
        |
        v
02 Opinion units
        |
        v
02c POS tagging
        |
        v
03 Candidate codes
        |
        v
04 Ringkasan awal
        |
        v
05 Normalisasi candidate code
        |
        v
06 Ringkasan akhir
```

Sistem menggunakan kombinasi:

- **Python dan pandas** untuk membaca, membersihkan, memvalidasi, mengelompokkan,
  serta menyimpan data.
- **LLM melalui OpenRouter** untuk memahami makna bahasa, memecah pendapat,
  menentukan pertanyaan komparatif, mengambil aspek, dan menormalisasi label.
- **Stanza** untuk analisis struktur bahasa dan POS tagging.
- **SQLite dan file lokal** untuk menyimpan indeks run, cache, serta hasil analisis.

## Input Pengguna

Pengguna menyiapkan:

1. Judul analisis.
2. File CSV yang memiliki kolom pertanyaan dan jawaban.
3. Minimal dua hal yang dibandingkan, misalnya `batik tulis` dan `batik cap`.
4. Nama lain atau alias jika penyebutan dalam pertanyaan berbeda.
5. Mode analisis dan pengaturan proses.

Judul digunakan sebagai bagian nama folder hasil. Isi judul tidak memengaruhi
hasil ilmiah analisis.

## Validasi Awal

### 1. Membaca CSV

**Teknologi:** Python dan pandas.

Sistem:

- mencoba beberapa encoding CSV;
- mendeteksi kolom pertanyaan dan jawaban;
- memberi pengguna kesempatan mengoreksi pilihan kolom;
- membuat `row_id`;
- membersihkan spasi, baris baru, Unicode, dan tanda baca secara mekanis.

Pembersihan Python hanya merapikan bentuk teks dan tidak dimaksudkan untuk
mengubah makna jawaban.

### 2. Memeriksa Entity

**Teknologi:** Python.

Nama entity dan alias dinormalisasi dengan:

- Unicode NFKC;
- huruf kecil;
- penghapusan pemisah yang tidak diperlukan;
- pencocokan batas kata.

Pertanyaan harus memuat minimal dua entity yang telah ditentukan pengguna.
Jika syarat ini tidak terpenuhi, pertanyaan ditolak sebelum dikirim untuk
pemeriksaan komparatif.

Pemeriksaan ini bukan klasifikasi semantik dan tidak memakai kamus domain.
Python hanya memastikan nama hal yang dibandingkan benar-benar muncul.

### 3. Memeriksa Bentuk Pertanyaan

**Teknologi:** LLM melalui OpenRouter.

Jika minimal dua entity ditemukan, LLM menentukan apakah pertanyaan:

- benar-benar meminta perbandingan;
- meminta kontras atau preferensi;
- meminta penilaian relatif;
- atau hanya menyebut dua hal tanpa membandingkannya.

Penilaian dilakukan berdasarkan makna pertanyaan dan konteks entity, bukan
daftar kata kunci komparatif di dalam kode.

Hasil seluruh validasi disimpan dalam:

```text
01_entity_validation.csv
```

## Tahap 01: Raw Dataset

**Teknologi:** Python dan pandas.

Hanya pertanyaan yang lolos validasi yang masuk ke tahap ini. Sistem menyimpan:

- `row_id`;
- pertanyaan asli;
- jawaban asli;
- jawaban yang telah dibersihkan secara mekanis.

Output:

```text
01_raw_dataset.csv
```

## Tahap 02: Opinion Units

**Teknologi:** LLM melalui OpenRouter.

LLM menerima satu pasangan pertanyaan-jawaban per request. Tugasnya:

1. Merapikan jawaban tanpa mengubah makna responden.
2. Memecah jawaban menjadi klaim atomik.
3. Memisahkan sebab, proses, hasil, penilaian, atau daftar atribut jika membawa
   makna analitis berbeda.
4. Menentukan `main_entity` dan `counterpart_entity`.
5. Menyimpan opini, sentimen, sumber bukti, dan tingkat keyakinan.

Satu `opinion_unit` ditujukan untuk membawa satu aspek utama dan satu klaim
utama. Pada tahap ini LLM belum membuat candidate code.

Output:

```text
02_opinion_units.csv
02_errors.csv
```

## Tahap 02c: Struktur Bahasa

**Teknologi:** Stanza NLP.

Stanza dijalankan secara lazy dan dapat menggunakan model yang sudah tersimpan
di komputer. Sistem melakukan:

- tokenisasi;
- lemmatisasi;
- POS tagging;
- pengambilan kandidat kata benda atau frasa nominal.

POS tagging berfungsi sebagai bukti linguistik tambahan. Hasil Stanza bukan
keputusan akhir candidate code.

Output:

```text
02c_opinion_units_pos.csv
02c_pos_errors.csv
```

## Tahap 03: Candidate Codes

**Teknologi:** LLM melalui OpenRouter, dibantu hasil Stanza.

Untuk setiap opinion unit, LLM menentukan:

- `candidate_code`;
- `main_position`;
- `counterpart_position`;
- alasan pemilihan;
- tingkat keyakinan.

`candidate_code` berarti aspek yang dibandingkan, bukan penilaian atau
sentimen. Contoh:

```text
candidate_code: daya tahan
main_position: lebih awet
counterpart_position: kurang awet
```

Prompt meminta label:

- netral terhadap posisi kedua pihak;
- berbentuk aspek atau frasa nominal;
- ringkas tetapi tidak terlalu umum;
- tidak menggunakan nama entity sebagai code;
- tidak menggabungkan beberapa aspek sekaligus.

Output:

```text
03_candidate_codes.csv
03_candidate_errors.csv
```

## Tahap 04: Ringkasan Candidate Code Awal

**Teknologi:** Python dan pandas.

Sistem melakukan pengelompokan deterministik menggunakan `groupby` berdasarkan
candidate code. Untuk setiap code dihitung:

- frekuensi;
- opinion unit pendukung;
- contoh opinion unit;
- entity;
- sentimen;
- posisi;
- alasan candidate code.

Tahap ini tidak meminta keputusan baru dari LLM.

Output:

```text
04_candidate_summary.csv
```

## Tahap 05: Normalisasi Candidate Code

**Teknologi:** LLM, pemeriksaan struktural Python, dan fallback Python.

Tujuan normalisasi adalah menyatukan label yang memiliki makna aspek sama
tanpa meruntuhkan dimensi yang berbeda.

LLM membaca daftar candidate code secara global beserta contoh dan konteksnya.
LLM kemudian dapat:

- `merge` untuk sinonim atau varian;
- `rename` untuk memperbaiki bentuk label;
- `specificize` untuk memperjelas label terlalu umum;
- mempertahankan label yang sudah tepat.

Sistem menjaga keseimbangan dua risiko:

- **over-merge:** dimensi berbeda digabung menjadi label terlalu umum;
- **under-merge:** sinonim atau variasi label dibiarkan terpisah.

Setelah respons LLM diterima, Python:

- memeriksa kontrak JSON;
- memastikan semua code telah ditinjau;
- mendeteksi label kepala yang terlalu generik berdasarkan struktur data;
- meminta relabel tambahan jika over-merge terdeteksi;
- memakai fallback konservatif jika request normalisasi gagal.

Output:

```text
05_candidate_code_mapping.csv
05_candidate_code_normalized.csv
05_candidate_normalization_errors.csv
```

## Tahap 06: Ringkasan Akhir

**Teknologi:** Python dan pandas.

Sistem mengelompokkan seluruh opinion unit berdasarkan
`normalized_candidate_code`, lalu menghitung:

- frekuensi akhir;
- candidate code asal;
- opinion unit pendukung;
- contoh opinion unit;
- entity dan sentimen;
- posisi utama dan pembanding;
- alasan candidate code dan normalisasi.

Output utama:

```text
06_candidate_summary_normalized.csv
```

File ini merupakan ringkasan akhir untuk meninjau aspek komparatif yang telah
dinormalisasi.

## Koreksi Manual di Halaman Hasil

Pengguna dapat meninjau:

- `normalized_candidate_code`;
- frekuensi;
- contoh opinion unit.

Candidate code dapat dipindahkan ke label lain yang sudah tersedia atau ke
label baru buatan pengguna. Setelah perubahan disimpan, sistem memperbarui:

- mapping step 05;
- data normalized step 05;
- ringkasan step 06.

Riwayat koreksi manual dicatat dalam:

```text
manual_candidate_code_edits.jsonl
```

## Cache dan Proses Ulang

Sistem memiliki dua jenis penggunaan ulang hasil:

1. **Cache panggilan LLM**, berdasarkan hash prompt, input, dan model.
2. **Output project**, berdasarkan signature dataset dan pengaturan analisis.

Jika `Proses ulang dari awal` dipilih:

- output lama tidak dipakai sebagai sumber proses;
- cache baca LLM dilewati;
- request baru dikirim ke OpenRouter;
- respons baru tetap dapat memperbarui cache.

Jika tidak dipaksa, sistem dapat melanjutkan output yang sudah ada untuk
menghemat waktu dan request.

## Penyimpanan Hasil

Setiap run disimpan di:

```text
local_results/projects/<judul-project>__<signature>/
```

Metadata proses disimpan dalam:

```text
manifest.json
```

Manifest mencatat model, parameter, versi step, hash prompt, dan identitas run.
SQLite digunakan sebagai indeks daftar run agar halaman Hasil dapat menemukan
dan menampilkan project yang pernah diproses.

## Prinsip Metodologis

- Sistem bersifat domain-agnostik.
- Candidate code adalah aspek, bukan posisi atau sentimen.
- Prompt LLM menjadi mekanisme utama interpretasi bahasa.
- Python digunakan untuk validasi mekanis, kontrak data, agregasi, audit, dan
  fallback.
- Tidak ada fine-tuning model.
- Stanza membantu analisis linguistik, tetapi tidak menentukan code secara
  otomatis.
