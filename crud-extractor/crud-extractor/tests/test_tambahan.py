"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud import ast_nodes as ast
from crud import cli
from crud.lexer import LexError, TokenType as T, tokenize
from crud.parser import parse_sql
from crud.pipeline import analyze_source
from crud.resolver import Resolver


def _cols(node):
    return [c for c in ast.iter_nodes(node) if isinstance(c, ast.ColumnRef)]


# =========================================================================
# 1. TEST REGRESI PER BUG (Gagal sebelum perbaikan, lulus sesudahnya)
# =========================================================================

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


def test_bug4_parser_menerima_left_outer_join():
    # Regresi B5: keyword OUTER opsional setelah LEFT sebelumnya memicu ParseError (SPEK 3)
    stmt = parse_sql("SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id;").statements[0]
    assert stmt.joins[0].kind == "LEFT" and stmt.joins[0].source.name == "b"


def test_bug5_panic_mode_recovery_berhenti_di_titik_koma():
    # Regresi B6: _synchronize sebelumnya membuang token sampai EOF, bukan sampai ';' (SPEK 6)
    script = parse_sql("SELECT FROM a; SELECT x FROM b; DELETE FROM c WHERE i = 1;")
    assert len(script.errors) == 1
    assert [type(s).__name__ for s in script.statements] == ["Select", "Delete"]


def test_bug6_resolver_kolom_tanpa_qualifier_ambigu_dan_tanpa_tabel():
    # Regresi T2 (lanjutan): >1 tabel atau 0 tabel di scope terdalam harus memberi warning (SPEK 4.3)
    script1 = parse_sql("SELECT nama FROM pelanggan p, pesanan o;")
    diags1 = Resolver().resolve_script(script1)
    assert _cols(script1)[0].resolved is None
    assert len(diags1) == 1 and diags1[0].level == "warning"
    assert diags1[0].message == "kolom 'nama' ambigu tanpa skema"

    script2 = parse_sql("INSERT INTO t (a) VALUES (b);")
    diags2 = Resolver().resolve_script(script2)
    assert _cols(script2)[0].resolved is None
    assert len(diags2) == 1 and diags2[0].level == "warning"


def test_bug7_resolver_shadowing_lookup_dari_scope_terdalam():
    # Regresi B7: _lookup sebelumnya memakai reversed(chain) sehingga mencari dari scope terluar (SPEK 4.3)
    script = parse_sql(
        "SELECT x.id FROM pelanggan x WHERE x.id IN "
        "(SELECT x.pelanggan_id FROM pesanan x WHERE x.total > 5);"
    )
    Resolver().resolve_script(script)
    outer_col = _cols(script.statements[0].columns)[0]
    inner_cols = _cols(script.statements[0].where.query)
    assert outer_col.resolved == "pelanggan"
    assert {c.resolved for c in inner_cols} == {"pesanan"}


def test_bug8_resolver_scope_delete_tidak_bocor_ke_statement_berikutnya():
    # Regresi B8: _delete sebelumnya tidak memanggil _pop() sehingga alias bocor (SPEK 4.5)
    script = parse_sql("DELETE FROM sesi s WHERE s.a = 1; SELECT s.id FROM pengguna u;")
    resolver = Resolver()
    diags = resolver.resolve_script(script)
    assert _cols(script.statements[1])[0].resolved is None
    assert len(diags) == 1 and diags[0].level == "error" and "'s'" in diags[0].message
    assert resolver.scope is None


def test_bug9_analyzer_subquery_dalam_update_selalu_read():
    # Regresi B9: subquery di SET dan WHERE pada UPDATE sebelumnya diberi operasi 'U', bukan 'R' (SPEK 5)
    res = analyze_source(
        "UPDATE pesanan SET total = (SELECT ongkir FROM tarif WHERE id = 1) "
        "WHERE pelanggan_id IN (SELECT id FROM pelanggan WHERE aktif = 1);"
    )
    assert res.matrix() == {"pelanggan": "R", "pesanan": "U", "tarif": "R"}


def test_bug10_cli_ast_menangani_lex_error_tanpa_traceback(tmp_path, capsys):
    # Regresi B10: mode --ast sebelumnya tidak menangkap LexError (SPEK 2.7)
    bad_sql = tmp_path / "rusak.sql"
    bad_sql.write_text("SELECT 'string tidak ditutup", encoding="utf-8")
    exit_code = cli.main([str(bad_sql), "--ast"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "LEX ERROR:" in captured.out


# =========================================================================
# 2. LIMA TEST KASUS TEPI (EDGE CASES)
# =========================================================================

def test_tepi1_komentar_blok_berisi_bintang_dan_tidak_tertutup():
    # Berisiko: karakter '*' tunggal di dalam komentar blok bisa salah dianggap penutup '*/',
    # dan komentar blok tanpa penutup harus melempar LexError pada posisi awal komentar.
    toks = tokenize("/* a * b ** c\n  d */ SELECT")
    assert toks[0].value == "SELECT" and (toks[0].line, toks[0].col) == (2, 8)
    with pytest.raises(LexError) as info:
        tokenize("SELECT 1\n/* tidak ditutup")
    assert (info.value.line, info.value.col) == (2, 1)


def test_tepi2_kata_berawalan_keyword_dan_angka_desimal():
    # Berisiko: normalisasi keyword huruf besar tidak boleh mengubah identifier yang kebetulan
    # diawali keyword ('selection', 'fromage'), dan angka desimal '2.5' harus utuh 1 token NUMBER.
    toks = [(t.type, t.value) for t in tokenize("selection fromage 2.5") if t.type != T.EOF]
    assert toks == [(T.IDENT, "selection"), (T.IDENT, "fromage"), (T.NUMBER, "2.5")]


def test_tepi3_between_and_berdampingan_dengan_logical_and():
    # Berisiko: kata kunci AND di dalam BETWEEN tidak boleh ditelan sebagai operator logika AND
    # oleh _and(), melainkan harus menjadi pembatas batas bawah dan atas BETWEEN (SPEK 3.2).
    stmt = parse_sql("SELECT x FROM t WHERE a BETWEEN 1 AND 2 AND b = 3;").statements[0]
    assert stmt.where.op == "AND"
    assert isinstance(stmt.where.left, ast.Between)
    assert stmt.where.right.op == "="


def test_tepi4_subquery_di_from_tidak_melihat_tabel_saudara_tapi_melihat_scope_luar():
    # Berisiko: sesuai SPEK 4.4, derived table di FROM di-resolve sebelum scope SELECT pemuatnya
    # dibuat, sehingga tidak boleh melihat tabel sebelahnya di FROM yang sama, namun tetap
    # bisa melihat alias dari query terluar (correlated).
    script_err = parse_sql("SELECT 1 FROM a, (SELECT a.x FROM b) d;")
    diags_err = Resolver().resolve_script(script_err)
    assert len(diags_err) == 1 and diags_err[0].level == "error"

    script_ok = parse_sql(
        "SELECT p.id FROM pelanggan p WHERE EXISTS "
        "(SELECT 1 FROM (SELECT 1 FROM pesanan o WHERE o.pid = p.id) d);"
    )
    diags_ok = Resolver().resolve_script(script_ok)
    assert diags_ok == []


def test_tepi5_kolom_tanpa_qualifier_hanya_melihat_scope_terdalam():
    # Berisiko: berbeda dengan qualified column yang mencari sampai ke scope luar, kolom tanpa
    # qualifier di subquery hanya boleh memeriksa scope terdalam saja (SPEK 4.3).
    script = parse_sql("SELECT 1 FROM a WHERE EXISTS (SELECT 1 FROM b, c WHERE z = 1);")
    diags = Resolver().resolve_script(script)
    z_col = [c for c in _cols(script) if c.name == "z"][0]
    assert z_col.resolved is None
    assert len(diags) == 1 and diags[0].level == "warning"