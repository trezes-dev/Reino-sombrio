import sqlite3
import os

db_path = os.path.expanduser('~/rpg/rpg.db')

def is_portao(x, y, rx1, rx2, ry1, ry2):
    return (
        (y == ry1 and 99 <= x <= 101) or
        (y == ry2 and 99 <= x <= 101) or
        (x == rx1 and 99 <= y <= 101) or
        (x == rx2 and 99 <= y <= 101)
    )

def gerar_aneis():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    X1, X2 = 72, 128
    Y1, Y2 = 72, 128
    LX1, LX2 = 88, 112
    LY1, LY2 = 88, 112
    
    c.execute("""
        DELETE FROM mapa_tiles 
        WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ?
        AND NOT (x BETWEEN ? AND ? AND y BETWEEN ? AND ?)
    """, (X1, X2, Y1, Y2, LX1, LX2, LY1, LY2))
    
    tiles = []
    
    for x in range(X1, X2 + 1):
        for y in range(Y1, Y2 + 1):
            if LX1 <= x <= LX2 and LY1 <= y <= LY2:
                continue
            
            if x == X1 or x == X2 or y == Y1 or y == Y2:
                if is_portao(x, y, X1, X2, Y1, Y2):
                    tipo = 'terra_caminho'
                elif y == Y1 or y == Y2:
                    tipo = 'muro_topo'
                else:
                    tipo = 'muro_vertical'
            elif x == 80 or x == 120 or y == 80 or y == 120:
                if is_portao(x, y, 80, 120, 80, 120):
                    tipo = 'terra_caminho'
                elif y == 80 or y == 120:
                    tipo = 'muro_topo'
                else:
                    tipo = 'muro_vertical'
            elif 99 <= x <= 101 or 99 <= y <= 101:
                tipo = 'terra_caminho'
            else:
                tipo = 'grama_lobby'
            
            tiles.append((x, y, tipo))
    
    c.executemany("INSERT OR REPLACE INTO mapa_tiles (x, y, tipo) VALUES (?,?,?)", tiles)
    conn.commit()
    conn.close()
    
    muros = sum(1 for t in tiles if 'muro' in t[2])
    caminhos = sum(1 for t in tiles if t[2] == 'terra_caminho')
    print(f"OK: Aneis 2 e 3 gerados. {len(tiles)} tiles, {muros} muros, {caminhos} caminhos")

if __name__ == '__main__':
    gerar_aneis()
