import sqlite3
import os

db_path = os.path.expanduser('~/rpg/rpg.db')

def gerar_mundo():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. Apaga TUDO e regera do zero
    c.execute("DELETE FROM mapa_tiles")

    tiles = []

    # Lobby bounds (pra pular aqui - deixa pro gerar_lobby.py)
    LX1, LX2, LY1, LY2 = 88, 112, 88, 112

    # 2. Preenche os 4 quadrantes
    for x in range(200):
        for y in range(200):
            # Pula o lobby (vai ser preenchido pelo gerar_lobby.py depois)
            if LX1 <= x <= LX2 and LY1 <= y <= LY2:
                continue

            # Cruz de caminhos (3 tiles de largura, centro em 100)
            if 99 <= x <= 101 or 99 <= y <= 101:
                tipo = 'terra_caminho'
            # Q1: sup-esq (floresta escura)
            elif x <= 87 and y <= 87:
                tipo = 'grama_escura'
            # Q2: sup-dir (floresta normal)
            elif x >= 113 and y <= 87:
                tipo = 'grama_normal'
            # Q3: inf-esq (deserto)
            elif x <= 87 and y >= 113:
                tipo = 'areia_deserto'
            # Q4: inf-dir (ruinas)
            elif x >= 113 and y >= 113:
                tipo = 'pedra_ruinas'
            else:
                tipo = 'grama_normal'

            tiles.append((x, y, tipo))

    c.executemany("INSERT INTO mapa_tiles (x, y, tipo) VALUES (?,?,?)", tiles)
    conn.commit()
    conn.close()
    print(f"OK: Mundo gerado com {len(tiles)} tiles (lobby fora)")

if __name__ == "__main__":
    gerar_mundo()
