"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import csv

import pytest

from crud import ast_nodes as ast
from crud import cli
from crud import parser as parser_module
from crud.analyzer import analyze_statement, column_usage
from crud.lexer import LexError, TokenType as T, tokenize
from crud.parser import parse_sql
from crud.pipeline import analyze_source
from crud.resolver import Resolver

def test_bug1_lexer_mengambil_operator_terpanjang():
    tokens = tokenize("a <> b ")
    ops = [t.value for t in tokens if t.type == T.OP]
    assert ops == ["<>"]

def test_bug2_kutip_ganda_di_dalam_string():
    tokens = tokenize("'O''Brien'")
    assert [(t.type, t.value) for t in tokens[:-1]] == [(T.STRING, "O'Brien")]

def test_bug3_and_di_kiri_or():
    where = parse_sql("SELECT a FROM t WHERE a = 1 AND b = 2 OR c = 3;").statements[0].where
    assert where.op == "OR"
    assert where.left.op == "AND"

def _toks(src):
    return [(t.type, t.value) for t in tokenize(src) if t.type != T.EOF]


# ======================= LEXER: regresi =======================

def test_regresi_T3_komentar_blok_tidak_menghasilkan_token():
    # T3: sebelumnya LexError "komentar blok belum didukung".
    assert _toks("SELECT /* abaikan */ a") == [(T.KEYWORD, "SELECT"), (T.IDENT, "a")]


def test_regresi_B1_keyword_tidak_peka_huruf_dan_dinormalisasi_besar():
    # B1: sebelumnya "select" menjadi IDENT bernilai 'select'.
    assert _toks("select Select SELECT") == [(T.KEYWORD, "SELECT")] * 3


def test_regresi_B1_kata_berawalan_keyword_tetap_ident():
    # B1 (sisi sebaliknya): perbaikan case-insensitive tidak boleh memotong
    # identifier yang hanya diawali keyword.
    assert _toks("selection fromage Orders") == [
        (T.IDENT, "selection"), (T.IDENT, "fromage"), (T.IDENT, "Orders")]


def test_regresi_B2_kutip_ganda_dalam_string_satu_token():
    # B2: sebelumnya 'O''Brien' pecah menjadi STRING 'O' dan STRING 'Brien'.
    assert _toks("'O''Brien'") == [(T.STRING, "O'Brien")]


def test_regresi_B3_operator_tidak_sama_satu_token():
    # B3: sebelumnya "<>" menjadi "<" lalu ">" (melanggar maximal munch).
    assert _toks("a <> b") == [(T.IDENT, "a"), (T.OP, "<>"), (T.IDENT, "b")]


# ======================= LEXER: kasus tepi =======================

def test_tepi_komentar_blok_boleh_berisi_bintang_dan_lintas_baris():
    # Berisiko: "*" di dalam komentar bisa salah dikira penutup; posisi baris
    # setelah komentar lintas baris harus tetap benar.
    toks = tokenize("/* a * b ** c\n  d */ SELECT")
    assert toks[0].value == "SELECT" and (toks[0].line, toks[0].col) == (2, 8)


def test_tepi_komentar_blok_tidak_ditutup_adalah_lexerror():
    # Berisiko: lexer bisa diam-diam menelan sisa file. Posisi error = awal komentar.
    with pytest.raises(LexError) as info:
        tokenize("SELECT 1\n/* tidak ditutup")
    assert (info.value.line, info.value.col) == (2, 1)


def test_tepi_string_hanya_kutip_ganda_dan_string_kosong():
    # Berisiko: '''' (isi satu kutip) vs '' (string kosong) mudah tertukar.
    assert _toks("''''") == [(T.STRING, "'")]
    assert _toks("''") == [(T.STRING, "")]


def test_tepi_string_tidak_ditutup_setelah_kutip_ganda():
    # Berisiko: "'abc''" berakhir dengan '' yang bukan penutup -> harus LexError.
    with pytest.raises(LexError):
        tokenize("'abc''")


def test_tepi_operator_berdampingan_maximal_munch():
    # Berisiko: "<=" vs "<" "=", dan "<>" vs "<" ">" bila urutan cek salah.
    assert [v for _, v in _toks("a<=b<>c<d>=e!=f")] == [
        "a", "<=", "b", "<>", "c", "<", "d", ">=", "e", "!=", "f"]


def test_tepi_minus_tunggal_bukan_komentar_dan_garis_miring_bukan_blok():
    # Berisiko: "-" dan "/" adalah awal dari "--" dan "/*"; sendirian harus OP.
    assert _toks("a - b / c") == [
        (T.IDENT, "a"), (T.OP, "-"), (T.IDENT, "b"), (T.OP, "/"), (T.IDENT, "c")]


# ======================= LEXER: regresi tambahan =======================

def test_regresi_angka_desimal_satu_digit_satu_token():
    # Regresi dari perubahan _number: "2.5" pecah menjadi NUMBER '2', DOT, NUMBER '5'
    # karena pengecekan '.' ikut masuk ke dalam loop digit. SPEK 2.6: satu NUMBER.
    assert _toks("2.5") == [(T.NUMBER, "2.5")]
    assert _toks("x > 2.5") == [(T.IDENT, "x"), (T.OP, ">"), (T.NUMBER, "2.5")]
    assert _toks("10.25") == [(T.NUMBER, "10.25")]


def test_tepi_angka_titik_tanpa_digit_sesudahnya_bukan_desimal():
    # Berisiko: "t.1" / "5." jangan dianggap desimal; titik tanpa digit adalah DOT.
    assert _toks("5.") == [(T.NUMBER, "5"), (T.DOT, ".")]


# ======================= PARSER =======================
from crud import ast_nodes as ast
from crud.parser import parse_sql
from crud.pipeline import analyze_source


def _one(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    assert len(script.statements) == 1
    return script.statements[0]


def test_regresi_T1_insert_select_values_adalah_list_kosong():
    # T1: Insert.values untuk INSERT ... SELECT sempat berisi None sehingga
    # analyzer/resolver (for row in stmt.values) melempar TypeError.
    s = _one("INSERT INTO arsip (id) SELECT id FROM pesanan")
    assert s.values == [] and isinstance(s.query, ast.Select)


def test_regresi_T1_insert_select_masuk_matriks_crud():
    # SPEK 5: tabel target C, tabel sumber R.
    res = analyze_source("INSERT INTO arsip (id) SELECT id FROM pesanan WHERE total > 2.5;")
    assert res.parse_errors == [] and res.matrix() == {"arsip": "C", "pesanan": "R"}


def test_regresi_B4_and_lebih_kuat_dari_or():
    # SPEK 3.1: a=1 OR b=2 AND c=3  ==  a=1 OR (b=2 AND c=3).
    w = _one("SELECT x FROM t WHERE a = 1 OR b = 2 AND c = 3").where
    assert w.op == "OR" and w.right.op == "AND" and w.left.op == "="
    w = _one("SELECT x FROM t WHERE a = 1 AND b = 2 OR c = 3").where
    assert w.op == "OR" and w.left.op == "AND"


def test_regresi_B5_left_outer_join_diterima():
    # SPEK 3: join = [INNER | LEFT [OUTER]] JOIN. Sebelumnya error "diharapkan JOIN".
    s = _one("SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id")
    assert s.joins[0].kind == "LEFT" and s.joins[0].source.name == "b"


def test_regresi_B6_recovery_berhenti_di_titik_koma():
    # SPEK 6: buang token sampai dan termasuk ';', lalu lanjut. Sebelumnya
    # semua token sampai EOF dibuang sehingga statement valid sesudahnya hilang.
    script = parse_sql("SELECT FROM a; SELECT x FROM b; DELETE FROM c WHERE i = 1")
    assert len(script.errors) == 1
    assert [type(s).__name__ for s in script.statements] == ["Select", "Delete"]


# ======================= PARSER: kasus tepi =======================

def test_tepi_between_and_milik_between_bukan_logika():
    # Berisiko: AND pertama milik BETWEEN, AND kedua milik and_expr (SPEK 3.2).
    w = _one("SELECT x FROM t WHERE a BETWEEN 1 AND 2 AND b = 3").where
    assert w.op == "AND" and isinstance(w.left, ast.Between) and w.right.op == "="


def test_tepi_not_mengikat_lebih_kuat_dari_and():
    # Berisiko: NOT a = 1 AND b = 2 harus (NOT (a=1)) AND (b=2), bukan NOT ((a=1) AND ..).
    w = _one("SELECT x FROM t WHERE NOT a = 1 AND b = 2").where
    assert w.op == "AND" and isinstance(w.left, ast.UnaryOp) and w.left.op == "NOT"


def test_tepi_bintang_semua_kolom_vs_perkalian_vs_count():
    # Berisiko: STAR punya tiga makna; parser membedakannya dari posisi.
    s = _one("SELECT a * b, COUNT(*) FROM t")
    assert s.columns[0].expr.op == "*" and s.columns[1].expr.star is True


def test_tepi_recovery_error_tepat_di_titik_koma_dan_error_beruntun():
    # Berisiko: bila error terdeteksi PADA ';' atau dua statement rusak berurutan,
    # recovery harus tetap satu error per statement dan tidak menelan statement valid.
    script = parse_sql("SELECT FROM a; SELECT FROM b; SELECT x FROM c;")
    assert len(script.errors) == 2 and len(script.statements) == 1
    assert script.statements[0].sources[0].name == "c"


def test_tepi_titik_koma_berlebih_dan_perbandingan_tidak_berantai():
    # Berisiko: ';;' harus diabaikan; 'a = b = c' melanggar "tidak berantai" (SPEK 3.1).
    assert len(parse_sql(";;SELECT a FROM t;;").statements) == 1
    assert len(parse_sql("SELECT a FROM t WHERE a = b = c").errors) == 1


def test_tepi_insert_select_tanpa_daftar_kolom():
    # Berisiko: pengecekan '(' + SELECT untuk daftar kolom tidak boleh salah jalur.
    s = _one("INSERT INTO arsip SELECT id FROM pesanan")
    assert s.columns == [] and s.values == [] and s.query is not None


# ======================= RESOLVER =======================
from crud.resolver import Resolver


def _res(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    resolver = Resolver()
    diags = resolver.resolve_script(script)
    return script, diags, resolver


def _cols(node):
    return [c for c in ast.iter_nodes(node) if isinstance(c, ast.ColumnRef)]


def _map(node):
    return {(c.qualifier, c.name): c.resolved for c in _cols(node)}


def test_regresi_T2_kolom_tanpa_qualifier_satu_tabel_di_resolve():
    # SPEK 4.3: tepat satu tabel di scope terdalam -> resolved = tabel itu (lengkap skema).
    script, diags, _ = _res("SELECT nama FROM crm.pelanggan WHERE aktif = 1")
    assert {c.resolved for c in _cols(script)} == {"crm.pelanggan"}
    assert diags == []


def test_regresi_T2_kolom_ambigu_warning_dan_resolved_none():
    # SPEK 4.3: >1 tabel -> warning "kolom 'nama' ambigu tanpa skema", resolved None.
    script, diags, _ = _res("SELECT nama FROM pelanggan p, pesanan o")
    assert _cols(script)[0].resolved is None
    assert [d.level for d in diags] == ["warning"]
    assert diags[0].message == "kolom 'nama' ambigu tanpa skema"


def test_regresi_T2_kolom_tanpa_tabel_warning_tanpa_crash():
    # SPEK 4.3: tidak ada tabel -> warning. INSERT ... VALUES tidak punya scope
    # (SPEK 4.1), jadi kolom di VALUES tidak punya tabel; jangan crash.
    script, diags, _ = _res("INSERT INTO t (a) VALUES (b)")
    assert _cols(script)[0].resolved is None
    assert [d.level for d in diags] == ["warning"]


def test_regresi_B7_shadowing_alias_dalam_menutupi_alias_luar():
    # SPEK 4.3: pencarian qualifier dari scope TERDALAM ke luar. Kode lama mencari
    # dari terluar, sehingga x.total di subquery ter-resolve ke pelanggan.
    script, _, _ = _res(
        "SELECT x.id FROM pelanggan x WHERE x.id IN "
        "(SELECT x.pelanggan_id FROM pesanan x WHERE x.total > 5)")
    outer = _cols(script.statements[0].columns)[0]
    inner = _cols(script.statements[0].where.query)
    assert outer.resolved == "pelanggan"
    assert {c.resolved for c in inner} == {"pesanan"}


def test_regresi_B7_correlated_subquery_merujuk_alias_luar():
    # SPEK 4.3: subquery tetap bisa merujuk alias luar bila alias itu tidak ditutupi.
    script, diags, _ = _res(
        "SELECT p.id FROM pelanggan p WHERE EXISTS "
        "(SELECT 1 FROM pembayaran b WHERE b.pelanggan_id = p.id)")
    m = _map(script.statements[0].where.query)
    assert m[("b", "pelanggan_id")] == "pembayaran" and m[("p", "id")] == "pelanggan"
    assert diags == []


def test_regresi_B8_scope_delete_tidak_bocor_ke_statement_berikutnya():
    # SPEK 4.5: alias 's' milik DELETE tidak boleh terlihat di SELECT berikutnya.
    # Kode lama tidak memanggil _pop() di _delete.
    script, diags, resolver = _res("DELETE FROM sesi s WHERE s.a = 1; SELECT s.id FROM pengguna u")
    assert _cols(script.statements[1])[0].resolved is None
    assert [d.level for d in diags] == ["error"] and "'s'" in diags[0].message
    assert resolver.scope is None          # tidak ada scope tersisa


# ======================= RESOLVER: kasus tepi =======================

def test_tepi_subquery_from_tidak_melihat_tabel_saudara():
    # SPEK 4.4: subquery di FROM di-resolve SEBELUM scope SELECT pemuatnya dibuat,
    # jadi alias 'a' (saudara di FROM yang sama) tidak terlihat di dalamnya.
    _, diags, _ = _res("SELECT 1 FROM a, (SELECT a.x FROM b) d")
    assert [d.level for d in diags] == ["error"] and "'a'" in diags[0].message


def test_tepi_subquery_from_masih_melihat_scope_di_luar_select():
    # SPEK 4.4: tetapi tetap melihat scope DI LUAR SELECT pemuatnya (mis. subquery
    # di dalam WHERE yang memuat derived table yang merujuk alias terluar).
    script, diags, _ = _res(
        "SELECT p.id FROM pelanggan p WHERE EXISTS "
        "(SELECT 1 FROM (SELECT 1 FROM pesanan o WHERE o.pid = p.id) d)")
    m = {(c.qualifier, c.name): c.resolved for c in _cols(script.statements[0].where)}
    assert m[("p", "id")] == "pelanggan" and diags == []


def test_tepi_tanpa_qualifier_hanya_scope_terdalam():
    # SPEK 4.3: kolom tanpa qualifier hanya melihat scope terdalam. Subquery dengan
    # dua tabel -> ambigu, walau scope luar hanya punya satu tabel.
    script, diags, _ = _res(
        "SELECT 1 FROM a WHERE EXISTS (SELECT 1 FROM b, c WHERE z = 1)")
    z = [c for c in _cols(script) if c.name == "z"][0]
    assert z.resolved is None and [d.level for d in diags] == ["warning"]
    script, diags, _ = _res("SELECT 1 FROM a WHERE EXISTS (SELECT 1 FROM b WHERE z = 1)")
    assert [c for c in _cols(script) if c.name == "z"][0].resolved == "b"


def test_tepi_deklarasi_ganda_error_tetapi_nama_sama_beda_scope_boleh():
    # SPEK 4.2: nama ganda di scope yang SAMA = error; di scope berbeda = shadowing sah.
    _, diags, _ = _res("SELECT 1 FROM a x JOIN b x ON 1 = 1")
    assert [d.level for d in diags] == ["error"]
    _, diags, _ = _res("SELECT 1 FROM a x WHERE EXISTS (SELECT 1 FROM b x)")
    assert diags == []


def test_tepi_alias_statement_sebelumnya_tidak_terlihat():
    # SPEK 4.5: setiap statement berdiri sendiri.
    _, diags, resolver = _res("SELECT p.id FROM a p; SELECT p.id FROM b q")
    assert [d.level for d in diags] == ["error"] and resolver.scope is None


def test_tepi_nama_berskema_tanpa_alias_dirujuk_dengan_bagian_terakhir():
    # SPEK 4.2: crm.pelanggan masuk scope sebagai 'pelanggan', resolved nama lengkap.
    script, diags, _ = _res("SELECT pelanggan.nama FROM crm.pelanggan")
    assert _cols(script)[0].resolved == "crm.pelanggan" and diags == []


def test_tepi_derived_table_resolved_ke_subquery_dan_tanpa_alias_warning():
    # SPEK 4.2: kolom yang merujuk subquery di FROM -> "<subquery ...>"; tanpa alias -> warning.
    script, diags, _ = _res("SELECT d.x FROM (SELECT x FROM t) d")
    assert _cols(script.statements[0].columns)[0].resolved.startswith("<subquery")
    _, diags, _ = _res("SELECT 1 FROM (SELECT x FROM t)")
    assert [d.level for d in diags] == ["warning"]


def test_tepi_update_kolom_target_dan_nilai_tanpa_qualifier():
    # Berisiko: scope UPDATE harus ada sebelum kolom target/SET/WHERE di-resolve.
    script, diags, _ = _res("UPDATE produk SET stok = stok - 1 WHERE id = 3")
    assert {c.resolved for c in _cols(script)} == {"produk"} and diags == []
