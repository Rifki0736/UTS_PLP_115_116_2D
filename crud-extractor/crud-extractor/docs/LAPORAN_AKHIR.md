# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

```text
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')
```

## 2. Tiga kasus di mana regex salah

**1. Teks di dalam string dan komentar dianggap SQL**

pada laporan_penjualan.sql terdapat baris kode sebagai berikut
```sql
-- DELETE FROM pelanggan   (baris ini komentar, bukan perintah)
SELECT p.nama, SUM(o.total) AS omzet
FROM pelanggan p
JOIN pesanan o ON o.pelanggan_id = p.id
WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'
GROUP BY p.nama;
```

parser menghasilkan output sebagai berikut
```
laporan_penjualan.sql,3,pelanggan,R
laporan_penjualan.sql,3,pesanan,R
```
sedangkan regex malah melakukan tokenizing pada baris komen sehingga menghasilkan token tambahan seperti berikut
```
laporan_penjualan.sql,1,pelanggan,D
....
```
regex bekerja pada teks mentah dan memotong dengan split(";"). Lexer mengubah '--' menjadi satu token STRING dan membuang token komentar sebelum parser melihat apa pun. Jadi kata DELETE pada baris komen tetap dianggap KEYWORD oleh regex.

**2.Sumber tabel yang dipisah koma**

pada audit.sql terdapat baris kode sebagai berikut
```sql
-- Audit akses data
SELECT p.id, p.nama
FROM pelanggan p, pesanan o
WHERE o.pelanggan_id = p.id
  AND o.tanggal BETWEEN :mulai AND :akhir
  OR p.level = 'gold' AND p.aktif = 1;
```

parser menghasilkan output sebagai berikut
```
audit.sql,2,pelanggan,R
audit.sql,2,pesanan,R
```
sedangkan regex hanya melakukan tokenizing pada tabel pertama saja. tabel kedua diabaikan karena tidak diawali oleh KEYWORD `FROM`
```
audit.sql,2,pelanggan,R
```
pola `\bFROM\s+NAME` hanya menangkap satu nama tepat setelah FROM. Tabel kedua muncul setelah koma dan tempat regex tidak punya pola. regex akan menghasilkan 2 token jika penulisannya seperti ini
```sql
FROM pelanggan p; from pesanan o
```
sedangkan parser mengumpulkan daftar table dalam `table_ref` sehingga mengetahui struktur datanya.

**3.Literal String yang Memuat Kata Kunci SQL**

pada laporan_penjualan.sql terdapat baris kode sebagai berikut
```sql
-- DELETE FROM pelanggan   (baris ini komentar, bukan perintah)
SELECT p.nama, SUM(o.total) AS omzet
FROM pelanggan p
JOIN pesanan o ON o.pelanggan_id = p.id
WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'
GROUP BY p.nama;
```

parser menghasilkan output sebagai berikut
```
laporan_penjualan.sql,3,pelanggan,R
laporan_penjualan.sql,3,pesanan,R
```
sedangkan regex malah melakukan tokenizing pada string literal sehingga menghasilkan token tambahan seperti berikut
```
...
laporan_penjualan.sql, 2, rahasia, R
```
regex bekerja pada teks mentah dan membaca token FROM dalam string 'FROM rahasia' sebagai token KEYWORD dan 'rahasia' sebagai nama tabel. disisi lain, lexer mengubah semua yang ada diantara 2 kutip `'...'` sebagai token string yang tidak dianggap sebagai KEYWORD.

## 3. Batas pendekatan kami

Pengujian di bawah dijalankan pada tool setelah semua bug diperbaiki, lewat `analyze_source`.

1. **Sintaks di luar lingkup spesifikasi (SPESIFIKASI.md bagian 9) membuat statement tidak dihitung.**
   Contoh: `SELECT id FROM pelanggan UNION SELECT id FROM pemasok;`, `WITH x AS (SELECT id FROM pesanan) SELECT id FROM x;`,
   `SELECT p.* FROM pelanggan p;`, dan `EXEC('DELETE FROM sesi');`.
   Akibat: setiap contoh menghasilkan satu parse error dan 0 statement, sehingga CRUD matrix kosong untuk statement itu
   (pada contoh UNION, `pelanggan` dan `pemasok` tidak muncul sama sekali). Kesalahan ini dilaporkan sebagai parse error,
   bukan diam-diam, tetapi matrix tetap kurang lengkap.
   Yang dibutuhkan: grammar diperluas (UNION, CTE beserta aturan scope-nya, `t.*`). Untuk `EXEC`, yang dibutuhkan adalah
   isi string SQL saat runtime, yang tidak ada di teks file.

2. **Satu karakter tak dikenal oleh lexer, misalnya quoted identifier, menghentikan seluruh file (bagian 2.2 dan 2.7).**
   Contoh: file berisi `DELETE FROM sesi;`, lalu `SELECT 1 FROM "pelanggan";`, lalu `UPDATE produk SET stok = 0;`.
   Akibat: `LexError` di baris 2 menghentikan pemrosesan file, sehingga `DELETE` dan `UPDATE` yang valid ikut hilang dan
   matrix file itu kosong. Ini lebih buruk daripada parse error, yang hanya membuang satu statement.
   Yang dibutuhkan: dukungan token quoted identifier, atau recovery di tingkat lexer yang melompat ke `;` berikutnya
   seperti recovery parser.

3. **Tanpa skema database, kolom tanpa qualifier tidak bisa diatribusikan dengan pasti (bagian 4.3 dan 7 butir 4).**
   Contoh A (ambigu): `SELECT nama FROM pelanggan p, pemasok s` membuat kolom `nama` tidak ter-resolve, sehingga hilang
   dari keluaran `--kolom`.
   Contoh B (salah atribusi): `SELECT 1 FROM pesanan o WHERE EXISTS (SELECT 1 FROM pelanggan p WHERE p.id = pelanggan_id)`.
   Kolom `pelanggan_id` tanpa qualifier hanya dicari di scope terdalam, sehingga tercatat sebagai kolom tabel `pelanggan`,
   padahal kemungkinan besar milik `pesanan`.
   Akibat: CRUD matrix per tabel tidak terpengaruh (kedua tabel tetap `R`), tetapi laporan per kolom bisa hilang atau salah.
   Yang dibutuhkan: katalog skema (daftar kolom setiap tabel) untuk menentukan pemilik kolom.

4. **Hal yang tidak terlihat dari teks query: nama tabel, view, trigger, dan foreign key.**
   Contoh: `SELECT 1 FROM pelanggan;` dan `SELECT 1 FROM crm.pelanggan;` dihitung sebagai dua tabel berbeda
   padahal bisa jadi tabel yang sama. `SELECT * FROM v_laporan_bulanan;` dicatat sebagai `R` pada `v_laporan_bulanan`,
   bukan pada tabel dasar yang dibaca view itu. `DELETE FROM induk WHERE id = 1;` hanya mencatat `induk: D`, padahal
   `ON DELETE CASCADE` atau trigger bisa menghapus atau mengubah tabel lain.
   Akibat: matrix terpecah untuk tabel yang sama, dan operasi tak langsung pada tabel lain tidak tercatat.
   Yang dibutuhkan: DDL atau katalog database (skema default atau `search_path`, definisi view, daftar trigger dan
   foreign key).

## 4. Pembagian kerja
Rincian Pembagian Kerja:

Muhammad Rifki Aunur Rahman:

- Lexer & Parser: Menemukan dan memperbaiki normalisasi keyword case-insensitive (crud/lexer.py), operator pembanding <> (crud/lexer.py), dukungan komentar blok lintas baris /* ... */ (T3), serta sintaks INSERT INTO ... SELECT (T1) di crud/parser.py.

- Error Recovery & Test: Memperbaiki mekanisme panic mode error recovery pada _synchronize() di crud/parser.py agar berhenti di batasan statement (;), serta menyusun unit test regresi dan kasus tepi di tests/test_tambahan.py untuk komponen lexer dan parser.

Muhammad Nafis Idris:

- Resolver & Analyzer: Mengimplementasikan resolusi kolom tanpa qualifier untuk scope tunggal serta deteksi warning ambiguitas untuk scope jamak (T2 di crud/resolver.py).

- Scope Lifecycle & Subquery: Memperbaiki arah pencarian scope _lookup untuk shadowing (B7), menambahkan self._pop() pada statement DELETE (B8) agar scope tidak bocor, serta memperbaiki penandaan operasi tabel pada subquery di klausa SET dan WHERE pada statement UPDATE (B9 di crud/analyzer.py) agar bertipe R.

- CLI & Evaluasi: Menangani pencegahan crash (LexError) pada antarmuka CLI --ast (B10 di crud/cli.py), serta melengkapi pelabelan manual data evaluasi di data/ground_truth.csv untuk berkas audit.sql dan pemeliharaan.sql.
