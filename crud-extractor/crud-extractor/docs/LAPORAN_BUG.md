# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: token <> tidak terbaca

**Ditemukan oleh:** Muhammad Rifki Aunur Rahman · **Diperbaiki oleh:** Muhammad Rifki Aunur Rahman

**Gejala.** 
input token '<>' dibaca sebagai 2 token yang berbeda '<' dan '>' menurut spesifikasi.md bagian 2.5 operator

**Reproduksi minimal.** 

```sql
SELECT p.nama
FROM pelanggan p
WHERE p.id <> 1
```

**Akar masalah.** 
kode sebelumnya hanya mengecek kondisi '<=' dan '<' sehingga '<>' dianggap token yang berbeda

**Perbaikan.** 
lexer.py, def _scan_token
```
    def _scan_token(self) -> None:
        line, col = self.line, self.col
        ch = self._advance()
        if ch == "<":
            if self._match("="):   op = "<="
            elif self._match(">"): op = "<>"
            else:                  op = "<"
            self._add(TokenType.OP, op, line, col)
            return
```

**Test regresi.** 
def test_bug1_lexer_mengambil_operator_terpanjang():
 
**Peran AI.** 
AI membantu saya dalam mengecek semua file dalam folder crud dan spesifikasi.md. memberikan saya informasi terkait bug potensial yang ada pada kode ini. lalu saya cek dan ternyata memang hanya ada 2 kondisi untuk percabangan token '<' yang seharusnya ada 3.

---

## Bug 2: token '' tidak menghasilkan ' dalam string

**Ditemukan oleh:** Muhammad Rifki Aunur Rahman · **Diperbaiki oleh:** Muhammad Rifki Aunur Rahman

**Gejala.** 
string yang memiliki 2 kutip di dalamnya (seperti 'o''brien') menghasilkan 2 token 'o' dan 'brien'. seharusnya 1 token "o'brien" sesuai spesifikasi.md bagian 2.4 string

**Reproduksi minimal.** 

```sql
select c.id, c.nama
from pelanggan c
where c.nama = 'O''Brien' ;
```

**Akar masalah.**
kode lama selalu mengganggap char ' sebagai penutup string tanpa mengecek char setelahnya dan tidak melakukan maximal munch

**Perbaikan.** 
lexer.py, def _string

```
def _string(self, line: int, col: int) -> None:
        chars: list[str] = []
        while True:
            if self._at_end():
                raise LexError("string tidak ditutup", line, col)
            ch = self._advance()
            if ch == "'":
                if self._peek() == "'":
                    self._advance()
                else:
                    break
            chars.append(ch)
        self._add(TokenType.STRING, "".join(chars), line, col)
```
**Test regresi.** 
def test_bug2_kutip_ganda_di_dalam_string():

**Peran AI.** AI membantu saya dalam mengecek semua file dalam folder crud dan spesifikasi.md. memberikan saya informasi terkait bug potensial yang ada pada kode ini. lalu saya cek dan ternyata kode sebelumnya melakukan break langsung saat menemukan char '. kode perbaikan melakukan peek sekali lagi untuk menentukan apakah itu ' atau ''. saat menemukan char '' maka kode melakukan _anvance supaca kutip yang masuk dalam string hanya 1 (tidak jadi o''brien).

---

## Bug 3: presedendi OR dan AND setara

**Ditemukan oleh:** Muhammad Rifki Aunur Rahman · **Diperbaiki oleh:** Muhammad Rifki Aunur Rahman

**Gejala.** ekspresi yang mengandung token OR dan AND menentukan urutan prioritas berdasarkan urutan sehingga perbedaan urutan berpengaruh. seharusnya urutan berdasarkan presedensi sesuai spesifikasi.md bagian 3.1 presedensi. 

**Reproduksi minimal.**

```sql
SELECT a FROM t WHERE a = 1 OR b = 2 AND c = 3;
```

**Akar masalah.** kode lama melempar expr ke def _logical yang langsung mengecek apakah terdapat token OR dan AND dan langsung mereturn ast.BinaryOp tanpa mengecek apakah ada token dengan presedensi yang lebih tinggi.

**Perbaikan.** 
parser.py,def _logical(dihapus), def _expr, def _or(baru), def _and(baru)

```
    def _expr(self): return self._or()

    def _or(self):
        left = self._and()
        while self._match_kw("OR"):
            left = ast.BinaryOp(left, "OR", self._and())
        return left

    def _and(self):
        left = self._not()
        while self._match_kw("AND"):
            left = ast.BinaryOp(left, "AND", self._not())
        return left
```
kode ini melempar expr langsung menuju def _or yang dimana setiap pemanggilan def_or selalu memprioritaskan def_and sebagai ast.node kiri (jika ada) sebelum mengecek kondisi OR itu sendiri.

**Test regresi.** 
def test_bug3_and_di_kiri_or()

**Peran AI.** 
AI membantu saya dalam mengecek semua file dalam folder crud dan spesifikasi.md. memberikan saya informasi terkait bug potensial yang ada pada kode ini. lalu saya cek dan ternyata kode sebelumnya melempar expr menuju def logika yang tidak melakukan perbandingan presedensi terhadap OR dan AND. def logic diganti menjadi 2 def terpisah yang memprioritaskan presedensi tertinggi yaitu AND

---

## Bug 4: 

**Ditemukan oleh:** (nama) · **Diperbaiki oleh:** (nama)

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql

```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---
## Bug 5: Urutan pencarian scope terbalik pada _lookup menggagalkan shadowing alias di subquery

**Ditemukan oleh:** Muhammad Nafis Idris · **Diperbaiki oleh:** Muhammad Nafis Idris

**Gejala.**
Ketika query luar dan subquery di dalamnya sama-sama mendefinisikan alias bernama x (misalnya pelanggan x di luar dan pesanan x di dalam subquery pada audit.sql baris 12–14), referensi kolom x.pelanggan_id dan x.total di dalam subquery justru ter-resolve ke tabel luar pelanggan, bukan ke pesanan. Ini melanggar SPESIFIKASI.md bagian 4.3.

**Reproduksi minimal.** 

```sql
SELECT x.id FROM pelanggan x
WHERE x.id IN (SELECT x.pelanggan_id FROM pesanan x WHERE x.total > 5);
```

**Akar masalah.** 
Berdasarkan konsep lexical scoping dan variable shadowing (Crafting Interpreters Bab 11, Resolving and Binding), pencarian nama dalam rantai lingkungan (environment/scope chain) wajib berjalan dari scope terdalam (innermost) menuju scope terluar (outermost), dan berhenti pada kecocokan pertama agar deklarasi lokal dapat menutupi (shadow) deklarasi luar yang bernama sama. Kode lama di Resolver._lookup() justru mengumpulkan rantai scope ke dalam list lalu membaliknya dengan reversed(chain), sehingga pencarian dimulai dari scope paling luar.

**Perbaikan.** 
Di crud/resolver.py pada metode _lookup(self, name: str), pembalikan reversed(chain) dihapus dan diganti dengan penelusuran langsung menggunakan pointer scope = self.scope lalu bergerak naik melalui scope = scope.parent sampai ditemukan atau None. Alternatif menyalin semua entri scope induk ke dalam dictionary scope anak saat _push() ditolak karena akan menyulitkan pendeteksian deklarasi alias ganda di dalam satu scope yang sama (aturan 4.2) serta membingungkan resolusi kolom tanpa qualifier yang hanya boleh melihat scope terdalam (aturan 4.3).

**Test regresi.**
test_bug7_resolver_shadowing_lookup_dari_scope_terdalam di tests/test_tambahan.py.

**Peran AI.** 
AI membantu menunjukkan bahwa pada output --ast untuk audit.sql baris 12, x.total mengarah ke -> pelanggan. dan Membantu membuatkan test secara keseluruhhan. Saya memeriksa metode _lookup di crud/resolver.py, menghapus reversed(), dan memverifikasi hasilnya kembali menggunakan py -m crud.cli data/sample/audit.sql --ast serta py -m pytest.

---

## Bug 6: Scope pada statement DELETE bocor ke statement berikutnya karena tidak di-pop
**Ditemukan oleh:** Muhammad Nafis Idris · **Diperbaiki oleh:** Muhammad Nafis Idris

**Gejala.** 
Setelah mengeksekusi DELETE FROM sesi s WHERE ...;, statement SELECT s.id FROM pengguna u; di bawahnya (seperti pada audit.sql baris 16–18) tidak menghasilkan error alias 's' tidak terdefinisi, melainkan me-resolve s.id ke tabel sesi dari statement DELETE sebelumnya. Ini melanggar SPESIFIKASI.md bagian 4.5.

**Reproduksi minimal.** 
```sql
DELETE FROM sesi s WHERE s.a = 1;
SELECT s.id FROM pengguna u;
```

**Akar masalah.** 
Dalam pengelolaan block scope berbentuk tumpukan (stack-based lexical scope, Crafting Interpreters Bab 11), setiap operasi pembukaan scope (beginScope / _push()) ketika memasuki suatu unit sintaksis wajib dipasangkan secara seimbang dengan penutupan scope (endScope / _pop()) saat keluar dari unit tersebut. Pada metode Resolver._delete(), kode memanggil self._push() di awal untuk mendaftarkan tabel target DELETE, tetapi lupa memanggil self._pop() di akhir metode. Akibatnya, scope milik DELETE tertinggal di self.scope dan menjadi scope induk bagi statement berikutnya.

**Perbaikan.** 
Di crud/resolver.py pada akhir metode _delete(), ditambahkan pemanggilan self._pop() setelah self._expr(dele.where). Alternatif mereset self.scope = None secara paksa di awal resolve_statement() ditolak sebagai perbaikan utama karena hanya menyembunyikan gejala ketidakseimbangan tumpukan scope jika kelak ada struktur bersarang, meskipun menjaga invarian self.scope is None tetap baik.

**Test regresi.**
test_bug8_resolver_scope_delete_tidak_bocor_ke_statement_berikutnya di tests/test_tambahan.py

**Peran AI.** 
AI membantu menemukan bahwa diagnostik error pada audit.sql baris 18 tidak muncul karena self.scope masih berisi alias s. dan Membantu membuatkan test secara keseluruhan. Saya memeriksa _delete() di crud/resolver.py, menambahkan self._pop(), dan memverifikasinya dengan pytest.

---

## Bug 7: Tabel di dalam subquery pada statement UPDATE ditandai sebagai operasi U (Update), bukan R (Read)
**Ditemukan oleh:** Muhammad Nafis Idris · **Diperbaiki oleh:** Muhammad Nafis Idris

**Gejala.** 
Pada statement UPDATE yang memiliki subquery di klausa SET maupun WHERE (seperti di laporan_penjualan.sql baris 12 dan audit.sql baris 20), tabel yang berada di dalam subquery ikut tercatat memiliki operasi U di matriks CRUD. Seharusnya menurut SPESIFIKASI.md bagian 5, membaca tabel lewat subquery selalu menghasilkan operasi R, apa pun jenis statement luarnya.

**Reproduksi minimal.** 
```sql
UPDATE pesanan SET status = 'BATAL'
WHERE pelanggan_id IN (SELECT id FROM pelanggan WHERE diblokir = 1);
```

**Akar masalah.** 
Dalam analisis semantik berbasis pohon sintaks abstrak (AST traversal pass, Crafting Interpreters Bab 5 & Bab 11), peran semantik sebuah node bergantung pada konteks strukturalnya di dalam AST. Pada crud/analyzer.py di cabang elif isinstance(stmt, ast.Update):, setelah menandai tabel target usage[stmt.table.name].add("U"), kode lama meneruskan argumen operasi "U" ke pemanggilan rekursif _collect(assignment.value, usage, "U") dan _collect(stmt.where, usage, "U"). Akibatnya, operasi "U" merambat turun ke seluruh subtree ekspresi termasuk subquery SELECT di dalamnya.

**Perbaikan.** 
Di crud/analyzer.py pada cabang ast.Update di dalam analyze_statement(), parameter operasi yang diteruskan ke _collect(assignment.value, usage, ...) dan _collect(stmt.where, usage, ...) diubah dari "U" menjadi "R", selaras dengan cabang ast.Delete dan ast.Insert. Alternatif memaksa _collect_select() untuk selalu menggunakan "R" dan menghapus parameter op ditolak karena akan mengubah tanda tangan fungsi internal yang sudah dipakai secara konsisten di modul tersebut.

**Test regresi.**
test_bug9_analyzer_subquery_dalam_update_selalu_read di tests/test_tambahan.py (serta test_matrix_laporan_penjualan di tests/test_analyzer.py).

**Peran AI.** 
AI membantu menganalisis mengapa test_matrix_laporan_penjualan menghasilkan pesanan: RUD alih-alih RD, dan Membantu membuatkan test secara keseluruhan. Saya memeriksa fungsi analyze_statement di crud/analyzer.py, mengubah "U" menjadi "R" pada penelusuran ekspresi UPDATE, dan memverifikasinya dengan pytest.

---

## Bug 8: Mode --ast pada CLI mengalami crash (unhandled traceback) ketika file SQL mengandung LexError
**Ditemukan oleh:** Muhammad Nafis Idris · **Diperbaiki oleh:** Muhammad Nafis Idris

**Gejala.** 
Menjalankan python -m crud.cli <file> --ast pada file yang memiliki kesalahan leksikal (seperti string atau komentar blok yang tidak ditutup) menyebabkan program berhenti mendadak dengan Python traceback LexError, alih-alih mencetak pesan error yang rapi seperti pada mode normal. Ini melanggar SPESIFIKASI.md bagian 2.7.

**Reproduksi minimal.** 
```sql
SELECT 'string tidak ditutup
```

**Akar masalah.** 
Menurut arsitektur penanganan error kompilator (Crafting Interpreters Bab 4), kesalahan leksikal adalah kesalahan input pengguna yang harus dilaporkan secara terkendali oleh antarmuka utama (driver/CLI), bukan dibiarkan meledak sebagai uncaught exception dari runtime bahasa implementasi. Sementara analyze_source() di pipeline.py sudah membungkus parse_sql() dengan blok try ... except LexError, fungsi _print_ast() di crud/cli.py memanggil parse_sql() secara langsung tanpa menangkap LexError.

**Perbaikan.** 
Di crud/cli.py, LexError diimpor dari .lexer, kemudian pemanggilan parse_sql() di dalam _print_ast() dibungkus dengan try ... except LexError as err: yang mencetak f"LEX ERROR: {err}" lalu keluar (return) dari fungsi tersebut. Alternatif menangkap LexError di dalam parse_sql() ditolak karena docstring parse_sql dan kontrak API publik secara eksplisit menyatakan bahwa LexError tidak ditangkap di parse_sql.

**Test regresi.**
test_bug10_cli_ast_menangani_lex_error_tanpa_traceback di tests/test_tambahan.py.

**Peran AI.** 
AI menunjukkan bahwa jalur --ast di cli.py memotong kompas langsung ke parse_sql tanpa melewati analyze_source. dan Membantu membuatkan test secara keseluruhan. Saya menambahkan blok try-except LexError di _print_ast dan memverifikasinya melalui pytest.

---