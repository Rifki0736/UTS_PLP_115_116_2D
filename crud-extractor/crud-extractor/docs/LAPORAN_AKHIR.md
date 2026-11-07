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

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1.
2.
3.

## 4. Pembagian kerja

Siapa mengerjakan apa, dan bagaimana kalian memastikan keduanya memahami seluruh kode.
