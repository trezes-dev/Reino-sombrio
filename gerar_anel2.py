import sqlite3
import os

db_path = os.path.expanduser('~/rpg/rpg.db')

def is_portao_3(x, y, linhas_ou_colunas):
    # Portoes de 3 tiles de largura centrados em 100
    for lin, col in linhas_ou_colunas:
        if y == lin and 99 <= x <= 101:
            return True
        if x == col and 99 <= y <= 101:
            return True
    return False

def gerar_anel2():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Regiao do Anel 2 (maior)
    X1, X2 = 74, 126
    Y1, Y2 = 74, 126
    
    # Lobby atual (NAO TOCAR)
    LX1, LX2 = 88, 112
    LY1, LY2 = 88, 112
    
    # Limpa regiao toda, exceto o lobby
    c.execute("""
        DELETE FROM mapa_tiles 
        WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ?
        AND NOT (x BETWEEN ? AND ? AND y BETWEEN ? AND ?)
    """, (X1, X2, Y1, Y2, LX1, LX2, LY1, LY2))
    
    # Definicao do Anel 2 (muro GROSSO, 2 tiles de espessura)
    # Linhas horizontais (topo e base): 74,75 e 125,126
    # Colunas verticais (esq e dir): 74,75 e 125,126
    linhas_h = [74, 75, 125, 126]
    colunas_v = [74, 75, 125, 126]
    
    tiles = []
    
    for x in range(X1, X2 + 1):
        for y in range(Y1, Y2 + 1):
            # Pula o lobby
            if LX1 <= x <= LX2 and LY1 <= y <= LY2:
                continue
            
            # Pega so as bordas do Anel 2 (2 tiles de espessura)
            na_borda_h = y in linhas_h
            na_borda_v = x in colunas_v
            
            if na_borda_h or na_borda_v:
                # Verifica se e portao (3 tiles no centro)
                if (y in linhas_h and 99 <= x <= 101) or (x in colunas_v and 99 <= y <= 101):
                    tipo = 'terra_caminho'
                elif na_borda_h:
                    tipo = 'muro_topo'
                else:
                    tipo = 'muro_vertical'
            
            # Caminhos conectores (entre Anel 1 e Anel 2)
            # Verticais: x=99-101, y=76-87 e y=113-124
            # Horizontais: y=99-101, x=76-87 e x=113-124
            elif (99 <= x <= 101 and (76 <= y <= 87 or 113 <= y <= 124)):
                tipo = 'terra_caminho'
            elif (99 <= y <= 101 and (76 <= x <= 87 or 113 <= x <= 124)):
                tipo = 'terra_caminho'
            
            # Chao entre os dois aneis
            else:
                tipo = 'grama_lobby'
            
            tiles.append((x, y, tipo))
    
    c.executemany("INSERT OR REPLACE INTO mapa_tiles (x, y, tipo) VALUES (?,?,?)", tiles)
    conn.commit()
    conn.close()
    
    muros = sum(1 for t in tiles if 'muro' in t[2])
    caminhos = sum(1 for t in tiles if t[2] == 'terra_caminho')
    print(f"OK: Anel 2 gerado. {len(tiles)} tiles, {muros} muros, {caminhos} caminhos")

if __name__ == '__main__':
    gerar_anel2()
