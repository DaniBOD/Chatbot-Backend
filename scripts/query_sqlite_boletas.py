"""
Consulta directa a sqlite DB para listar boletas que contengan un término en `nombre`.
Uso:
  python scripts/query_sqlite_boletas.py "juan perez"
"""
import sys
import sqlite3
import unicodedata

if len(sys.argv) < 2:
    print("Uso: python scripts/query_sqlite_boletas.py 'término de búsqueda'")
    sys.exit(1)

term = sys.argv[1]

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

norm_term = strip_accents(term).lower()
print(f"Normalized search term: {norm_term}")

db_path = 'db.sqlite3'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# select id_boleta, nombre, rut
cur.execute("SELECT id_boleta, nombre, rut FROM ModuloBoletas_boleta")
rows = cur.fetchall()
print(f"Total rows: {len(rows)}")

matches_token = []
matches_substr = []
for row in rows:
    _id, nombre, rut = row
    if not nombre:
        continue
    nombre_norm = strip_accents(nombre).lower()
    tokens = [t for t in norm_term.split() if t]
    if all(tok in nombre_norm for tok in tokens):
        matches_token.append((_id, nombre, rut, nombre_norm))
    if norm_term in nombre_norm:
        matches_substr.append((_id, nombre, rut, nombre_norm))

print(f"Matches (token strategy): {len(matches_token)}")
for _id, nombre, rut, nombre_norm in matches_token[:20]:
    print(f"  {_id} | {nombre} | {rut} -> {nombre_norm}")

print(f"Matches (substring): {len(matches_substr)}")
for _id, nombre, rut, nombre_norm in matches_substr[:20]:
    print(f"  {_id} | {nombre} | {rut} -> {nombre_norm}")

conn.close()
