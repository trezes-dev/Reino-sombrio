import sqlite3
import os

db_path = os.path.expanduser('~/rpg/rpg.db')

def gerar_lobby():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mapa_tiles (
            x INTEGER,
            y INTEGER,
            tipo TEXT,
            PRIMARY KEY (x, y)
        )
    ''')

    X_MIN, X_MAX = 88, 112
    Y_MIN, Y_MAX = 88, 112

    cursor.execute('''
        DELETE FROM mapa_tiles 
        WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ?
    ''', (X_MIN, X_MAX, Y_MIN, Y_MAX))

    portoes_norte = {(99, 88), (100, 88), (101, 88)}
    portoes_sul   = {(99, 112), (100, 112), (101, 112)}
    portoes_oeste = {(88, 99), (88, 100), (88, 101)}
    portoes_leste = {(112, 99), (112, 100), (112, 101)}

    todos_portoes = portoes_norte | portoes_sul | portoes_oeste | portoes_leste

    fonte_centro = {
        (x, y) 
        for x in range(99, 102) 
        for y in range(99, 102)
    }

    cnt_muros = 0
    cnt_caminhos = 0
    cnt_grama = 0

    tiles_para_inserir = []

    for x in range(X_MIN, X_MAX + 1):
        for y in range(Y_MIN, Y_MAX + 1):
            coord = (x, y)

            if coord in todos_portoes:
                tipo = 'terra_caminho'
                cnt_caminhos += 1
            elif y == Y_MIN or y == Y_MAX:
                tipo = 'muro_topo'
                cnt_muros += 1
            elif x == X_MIN or x == X_MAX:
                tipo = 'muro_vertical'
                cnt_muros += 1
            elif coord in fonte_centro:
                tipo = 'pedra_ruinas'
                cnt_caminhos += 1
            elif (99 <= x <= 101) or (99 <= y <= 101):
                tipo = 'terra_caminho'
                cnt_caminhos += 1
            else:
                tipo = 'grama_lobby'
                cnt_grama += 1

            tiles_para_inserir.append((x, y, tipo))

    cursor.executemany('''
        INSERT OR REPLACE INTO mapa_tiles (x, y, tipo) 
        VALUES (?, ?, ?)
    ''', tiles_para_inserir)

    conn.commit()
    conn.close()

    print(f"OK: Lobby gerado com {cnt_muros} muros e {cnt_caminhos} caminhos")

if __name__ == '__main__':
    gerar_lobby()
