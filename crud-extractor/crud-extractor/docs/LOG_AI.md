# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Muhammad Rifki Aunur Rahman | analisa potensi bug pada kode berikut dan jelaskan masalah serta solusi | sebagian besar diterima | karena sesuai dengan SPESIFIKASI.md|melakukan pytest secara bertahap setiap perbaikan satu fungsi |
| 2 | Muhammad Rifki Aunur Rahman | implementasi kode untuk blok komen (TODO 1) | sebagian besar diterima | karena sesuai dengan SPESIFIKASI.md, sedikit mengubah posisi return dan pesan lex error|melakukan pytest secara bertahap setiap perbaikan satu fungsi |
| 3 | Muhammad Rifki Aunur Rahman | implementasi kode untuk insert select (TODO 3) | sebagian besar diterima | karena sesuai dengan SPESIFIKASI.md, mengubah self._peek_next() menjadi self._peek(1) sesuai helper yang ada sebelumnya|melakukan pytest secara bertahap setiap perbaikan satu fungsi |

**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?

AI membantu saya dalam menganalisa source code berukuran besar dalam waktu singkat dan merangkum point-point penting sehingga lebih mudah untuk memperbaiki source code. AI terkadang keliru ketika konteks tidak diberikan secara utuh seperti menggunakan fungsi helper yang tidak ada di source code awal.
