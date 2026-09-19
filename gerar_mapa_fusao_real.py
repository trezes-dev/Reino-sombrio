from PIL import Image
import sqlite3, os, random, math

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_fusao_real.png')
LARGURA, ALTURA = 200, 200
CX, CY = 100, 100

# Cores dos 3 biomas + Lobby
COR_FLORESTA = (15, 75, 15)       # Floresta Escura
COR_DESERTO = (238, 214, 175)     # Deserto
COR_RUINAS = (115, 115, 115)      # Ruínas Cinzas
COR_LOBBY = (144, 238, 144)       # Verde claro (Lobby)
COR_LOBBY_NEON = (80, 255, 140)   # Verde brilhante (núcleo)
COR_CAMINHO = (160, 82, 45)

RAIO_NUCLEO = 12       # Núcleo neon do Lobby
RAIO_FUSAO = 85        # Distância onde começa a fusão com biomas

def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def blend(c1, c2, t):
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))

def pesos_bioma(x, y):
    """Calcula peso dos 3 biomas baseado na posição relativa ao centro."""
    dx = x - CX
    dy = y - CY
    
    # Metade de cima (dy < 0) tende a Floresta
    # Baixo esquerda (dx<0, dy>0) tende a Deserto
    # Baixo direita (dx>0, dy>0) tende a Ruínas
    
    # Fatores de proximidade (0 a 1)
    # 1 = muito perto do centro daquele bioma
    f_floresta = smoothstep(-dy / 80 + 0.3) if dy < 0 else 0
    if dy > -20:  # Transição suave perto da metade
        f_floresta = smoothstep((-dy + 30) / 80)
    
    # Fator vertical (aumenta descendo)
    v = smoothstep((dy - 10) / 90)
    
    # Fator horizontal
    h_esq = smoothstep((-dx + 30) / 80)
    h_dir = smoothstep((dx + 30) / 80)
    
    w_floresta = f_floresta
    w_deserto = v * h_esq
    w_ruinas = v * h_dir
    
    total = w_floresta + w_deserto + w_ruinas
    if total < 0.01:
        return (1.0, 0.0, 0.0)
    return (w_floresta / total, w_deserto / total, w_ruinas / total)

print("🎨 Gerando o mapa com fusão orgânica...")
img = Image.new('RGB', (LARGURA, ALTURA))
pixels = img.load()

for x in range(LARGURA):
    for y in range(ALTURA):
        dx, dy = x - CX, y - CY
        dist = math.sqrt(dx * dx + dy * dy)
        
        # Calcula o peso de cada bioma
        w_f, w_d, w_r = pesos_bioma(x, y)
        
        # Cor do bioma resultante da mistura dos 3
        r = int(COR_FLORESTA[0] * w_f + COR_DESERTO[0] * w_d + COR_RUINAS[0] * w_r)
        g = int(COR_FLORESTA[1] * w_f + COR_DESERTO[1] * w_d + COR_RUINAS[1] * w_r)
        b = int(COR_FLORESTA[2] * w_f + COR_DESERTO[2] * w_d + COR_RUINAS[2] * w_r)
        cor_bioma = (r, g, b)
        
        # --- FUSÃO COM O LOBBY ---
        if dist <= RAIO_NUCLEO:
            # Núcleo brilhante do Lobby
            pixels[x, y] = COR_LOBBY_NEON
        elif dist <= RAIO_FUSAO:
            # Zona de fusão com dither/noise
            t = (dist - RAIO_NUCLEO) / (RAIO_FUSAO - RAIO_NUCLEO)
            t_suave = smoothstep(t)
            
            # Dithering: usa ruído para decidir a cor
            ruido = random.random()
            
            if ruido < t_suave * 0.7:
                # Estilhaço do bioma invadindo o lobby
                pixels[x, y] = cor_bioma
            elif ruido < t_suave * 0.9:
                # Cor de transição suave
                pixels[x, y] = blend(COR_LOBBY, cor_bioma, t_suave)
            else:
                # Lobby
                pixels[x, y] = COR_LOBBY
        else:
            # Bioma puro com micro-variação (dither leve)
            if random.random() < 0.15:
                pixels[x, y] = blend(cor_bioma, COR_LOBBY, 0.1)
            else:
                pixels[x, y] = cor_bioma

# Desenhar os caminhos de terra (cruz central)
print("🛤️ Desenhando os caminhos...")
for y in range(ALTURA):
    for offset in range(-1, 2):
        if 0 <= CX + offset < LARGURA:
            pixels[CX + offset, y] = COR_CAMINHO

for x in range(LARGURA):
    for offset in range(-1, 2):
        if 0 <= CY + offset < ALTURA:
            pixels[x, CY + offset] = COR_CAMINHO

img.save(OUT_IMG)
print("✅ Imagem gerada! Veja em: http://127.0.0.1:5000/static/mapa_fusao_real.png")

# --- SALVAR NO BANCO DE DADOS ---
print("💾 Salvando no banco de dados...")
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("DELETE FROM mapa_tiles")
cursor.execute("DELETE FROM mapa_objetos")

def cor_para_tipo(pixel):
    r, g, b = pixel
    # Se é marrom de caminho
    if abs(r-160)<30 and abs(g-82)<30 and abs(b-45)<30:
        return 'terra_caminho'
    # Detecta o lobby
    if g > 150 and r > 80 and b > 80:
        return 'grama_lobby'
    # Senão é bioma
    menor = float('inf')
    tipo = 'grama_escura'
    for t, cor in [('grama_escura', COR_FLORESTA), ('areia_deserto', COR_DESERTO), ('pedra_ruinas', COR_RUINAS)]:
        d = (r - cor[0])**2 + (g - cor[1])**2 + (b - cor[2])**2
        if d < menor:
            menor = d
            tipo = t
    return tipo

grade = {}
for x in range(LARGURA):
    for y in range(ALTURA):
        tipo = cor_para_tipo(pixels[x, y])
        grade[(x, y)] = tipo
        cursor.execute("INSERT INTO mapa_tiles (x, y, tipo) VALUES (?, ?, ?)", (x, y, tipo))

print("🌳 Espalhando objetos...")
for (x, y), tipo in grade.items():
    if tipo == 'terra_caminho': continue
    if random.random() < 0.12:
        if tipo == 'grama_escura':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'natureza_escura', ?)", (x, y, random.choice(['arvore_escura', 'cogumelo'])))
        elif tipo == 'areia_deserto':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'deserto', ?)", (x, y, random.choice(['cacto', 'pedra_areia'])))
        elif tipo == 'pedra_ruinas':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'ruina', ?)", (x, y, random.choice(['pilar', 'entulho'])))

conn.commit()
conn.close()
print("✅ Mapa com fusão orgânica salvo no banco de dados com sucesso!")
