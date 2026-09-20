#!/usr/bin/env python3
# ADICIONA um segundo muro ao redor do lobby (NÃO TOCA no que já existe)
# Edite os valores abaixo se quiser mudar posições

import sqlite3, os
DB = os.path.expanduser("~/rpg/rpg.db")

# ============ EDITE AQUI ============
X_MIN = 68          # borda esquerda do muro externo
X_MAX = 132         # borda direita
Y_MIN = 68          # borda superior
Y_MAX = 132         # borda inferior
LARGURA_PORTAO = 3  # tiles de abertura em cada portão
# ====================================

conn = sqlite3.connect(DB)
c = conn.cursor()

# 1. Cria tiles só onde NÃO existe
criados = 0
for y in range(Y_MIN, Y_MAX + 1):
    for x in range(X_MIN, X_MAX + 1):
        existe = c.execute("SELECT 1 FROM mapa_tiles WHERE x=? AND y=?", (x, y)).fetchone()
        if not existe:
            c.execute("INSERT INTO mapa_tiles (x, y, tipo) VALUES (?, ?, 'grama_lobby')", (x, y))
            criados += 1
print(f"Chao criado: {criados} tiles")

# 2. Adiciona muro nas 4 bordas
muros = 0
for x in range(X_MIN, X_MAX + 1):
    for y in [Y_MIN, Y_MAX]:
        c.execute("UPDATE mapa_tiles SET tipo='muro' WHERE x=? AND y=?", (x, y))
        muros += 1
for y in range(Y_MIN + 1, Y_MAX):
    for x in [X_MIN, X_MAX]:
        c.execute("UPDATE mapa_tiles SET tipo='muro' WHERE x=? AND y=?", (x, y))
        muros += 1
print(f"Muros adicionados: {muros} tiles")

# 3. Portoes no meio de cada lado
cx = (X_MIN + X_MAX) // 2
cy = (Y_MIN + Y_MAX) // 2
half = LARGURA_PORTAO // 2
for off in range(-half, half + 1):
    c.execute("UPDATE mapa_tiles SET tipo='terra_caminho' WHERE x=? AND y=?", (cx + off, Y_MIN))
    c.execute("UPDATE mapa_tiles SET tipo='terra_caminho' WHERE x=? AND y=?", (cx + off, Y_MAX))
    c.execute("UPDATE mapa_tiles SET tipo='terra_caminho' WHERE x=? AND y=?", (X_MIN, cy + off))
    c.execute("UPDATE mapa_tiles SET tipo='terra_caminho' WHERE x=? AND y=?", (X_MAX, cy + off))
print(f"Portoes em X={cx}, Y={cy}")

conn.commit()
conn.close()
print("PRONTO! Muro externo criado.")
