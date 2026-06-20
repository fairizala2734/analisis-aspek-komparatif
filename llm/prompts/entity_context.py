"""Runtime entity constraints for comparative opinion extraction."""

ENTITY_CONTEXT_RULES = """
KONTEKS HAL YANG DIBANDINGKAN DARI PENGGUNA
- Payload berisi comparison_entities: daftar nama utama beserta alias yang sudah divalidasi.
- main_entity dan counterpart_entity wajib merujuk pada dua nama dari daftar tersebut.
- Gunakan nama utama pada output, bukan alias.
- Jangan membuat entity baru di luar daftar.
- Jangan menukar nama entity dengan aspek, produk turunan, bahan, proses, atau atribut.
- Jika jawaban memakai kata rujukan, selesaikan rujukan hanya memakai daftar dan konteks pertanyaan.
""".strip()
