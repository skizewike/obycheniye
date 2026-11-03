"""Создаёт базу из schema.sql и xlsx-файлов.

python create_db.py          -> shop.db из папки import
python create_db.py import2  -> shop_import2.db из папки import2
"""
import datetime
import sqlite3
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).parent
SRC = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "import")
DB = ROOT / ("shop.db" if SRC.name == "import" else f"shop_{SRC.name}.db")


def rows(name, skip_header=True):
    ws = openpyxl.load_workbook(SRC / name, data_only=True).active
    it = ws.iter_rows(values_only=True)
    if skip_header:
        next(it)
    for r in it:
        if r[0] is not None:
            yield [v.strip().replace("\xa0", " ") if isinstance(v, str) else v for v in r]


def to_date(v):
    if isinstance(v, datetime.datetime):
        return v.date().isoformat()
    d, m, y = str(v).split(".")  # строка вида ДД.ММ.ГГГГ (в исходнике есть 30.02.2025)
    return f"{y}-{m}-{d}"


def lookup(cur, table, value):
    """Возвращает id значения в справочнике, добавляя его при отсутствии."""
    row = cur.execute(f"SELECT id FROM {table} WHERE {table} = ?", (value,)).fetchone()
    if row:
        return row[0]
    return cur.execute(f"INSERT INTO {table} ({table}) VALUES (?)", (value,)).lastrowid


DB.unlink(missing_ok=True)
con = sqlite3.connect(DB)
con.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
cur = con.cursor()

for (addr,) in rows("Пункты выдачи_import.xlsx", skip_header=False):
    cur.execute("INSERT INTO pvz (addr) VALUES (?)", (addr,))

for role, fio, login, pwd in rows("user_import.xlsx"):
    cur.execute("INSERT INTO users (role_id, fio, login, pass) VALUES (?, ?, ?, ?)",
                (lookup(cur, "role", role), fio, login, pwd))

for art, name, unit, price, suppl, manuf, cat, disc, quant, descr, photo in rows("Tovar.xlsx"):
    cur.execute(
        "INSERT INTO tovar (art, name, unit, price, suppl, manuf, cat, discount, quant, descr, photo)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (art, name, unit, price, lookup(cur, "suppl", suppl), lookup(cur, "manuf", manuf),
         lookup(cur, "cat", cat), disc, quant, descr, photo))

for num, items, zdate, ddate, pvz, fio, code, status, *_ in rows("Заказ_import.xlsx"):
    user = cur.execute("SELECT id FROM users WHERE fio = ?", (fio,)).fetchone()
    if user is None:
        sys.exit(f"Заказ {num}: клиент «{fio}» не найден в users")
    cur.execute(
        "INSERT INTO zakaz (id, zak_date, dost_date, pvz_id, user_id, code, status_id)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (num, to_date(zdate), to_date(ddate), pvz, user[0], code, lookup(cur, "status", status)))
    parts = [p.strip() for p in items.split(",")]
    for art, qty in zip(parts[::2], parts[1::2]):
        tovar = cur.execute("SELECT id FROM tovar WHERE art = ?", (art,)).fetchone()
        if tovar is None:
            sys.exit(f"Заказ {num}: товар {art} не найден в tovar")
        cur.execute("INSERT INTO zakaz_tovar (zak_id, tovar_id, quant) VALUES (?, ?, ?)",
                    (num, tovar[0], int(qty)))

con.commit()
for (t,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
    print(f"{t:12} {cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]} строк")
print("FK-ошибок:", len(cur.execute("PRAGMA foreign_key_check").fetchall()))
con.close()
print("Готово:", DB)
