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

