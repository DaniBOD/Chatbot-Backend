"""
Script de ayuda para depurar búsquedas por nombre en Boleta.
Ejecutar desde la carpeta Backend con el venv activado:
    python scripts/debug_nombre_search.py "juan perez"

Mostrará filas que contienen el término y cómo se normalizan.
"""
import os
import sys
import unicodedata

if len(sys.argv) < 2:
    print("Uso: python scripts/debug_nombre_search.py 'nombre a buscar'")
    sys.exit(1)

search = sys.argv[1]

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core-Backend.settings')
import django
django.setup()

from ModuloBoletas.models import Boleta


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

term = strip_accents(search).lower()
print(f"Search term: {search!r} -> normalized: {term!r}")

qs = Boleta.objects.all()
print(f"Total boletas in DB: {qs.count()}")

matches_token = []
for b in qs:
    if not b.nombre:
        continue
    nombre_norm = strip_accents(b.nombre).lower()
    if all(tok in nombre_norm for tok in term.split() if tok):
        matches_token.append((str(b.id_boleta), b.nombre, nombre_norm))

print(f"Matches (token strategy): {len(matches_token)}")
for _id, nombre, nombre_norm in matches_token[:20]:
    print(f"  {_id} -> {nombre!r} -> {nombre_norm!r}")

# fallback substring
matches_fallback = []
for b in qs:
    if not b.nombre:
        continue
    nombre_norm = strip_accents(b.nombre).lower()
    if term in nombre_norm:
        matches_fallback.append((str(b.id_boleta), b.nombre, nombre_norm))

print(f"Matches (fallback substring): {len(matches_fallback)}")
for _id, nombre, nombre_norm in matches_fallback[:20]:
    print(f"  {_id} -> {nombre!r} -> {nombre_norm!r}")
