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
