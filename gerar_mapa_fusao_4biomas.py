from PIL import Image, ImageDraw
import sqlite3, os, random, math

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_mundo_fusao.png')
LARGURA, ALTURA = 200, 200
CX, CY = 100, 100

# ============ CORES DOS 4 BIOMAS ============
COR_FLORESTA_NORMAL = (60, 160, 60)     # Verde vivo (Sup. Esquerdo)
COR_FLORESTA_ESCURA = (45, 35, 70)      # Roxo/sombrio (Sup. Direito)
COR_DESERTO         = (230, 180, 90)    # Bege/areia (Inf. Esquerdo)
COR_RUINAS          = (140, 140, 130)   # Cinza/pedra (Inf. Direito)

# ============ CORES DO LOBBY ============
COR_LOBBY_PEDRA   = (170, 170, 165)     # Piso de pedra
COR_LOBBY_TERRA   = (140, 110, 80)      # Terra em volta
COR_FOGUEIRA       = (255, 150, 40)     # Fogueira central
COR_CAMINHO       = (170, 130, 90)      # Caminhos de terra

RAIO_LOBBY   = 40   # Raio do piso de pedra
RAIO_FUSAO   = 85   # Raio da zona de fusão orgânica

def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def blend(c1, c2, t):
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))

def pesos_bioma(x, y):
    """Retorna 4 pesos baseados na posição relativa ao centro (0..1 cada)."""
    dx = x - CX
    dy = y - CY
    
    # Contribuição horizontal e vertical normalizadas (-1 a 1)
    h = dx / 100.0    # -1 esquerda, +1 direita
    v = dy / 100.0    # -1 cima, +1 baixo
    
    # Cada bioma tem peso baseado em quão "perto" está do seu canto
    # Canto Superior Esquerdo (h<0, v<0)
    w_floresta_normal = smoothstep((-h + 0.3)) * smoothstep((-v + 0.3))
    # Canto Superior Direito (h>0, v<0)
    w_floresta_escura = smoothstep((h + 0.3)) * smoothstep((-v + 0.3))
    # Canto Inferior Esquerdo (h<0, v>0)
    w_deserto = smoothstep((-h + 0.3)) * smoothstep((v + 0.3))
    # Canto Inferior Direito (h>0, v>0)
    w_ruinas = smoothstep((h + 0.3)) * smoothstep((v + 0.3))
    
    total = w_floresta_normal + w_floresta_escura + w_deserto + w_ruinas
    if total < 0.01:
        return (0.25, 0.25, 0.25, 0.25)
    return (w_floresta_normal/total, w_floresta_escura/total, w_deserto/total, w_ruinas/total)

print("🎨 Gerando o Mapa do Mundo da Fusão...")
img = Image.new('RGB', (LARGURA, ALTURA), (0, 0, 0))
pixels = img.load()

for x in range(LARGURA):
    for y in range(ALTURA):
        dx, dy = x - CX, y - CY
        dist = math.sqrt(dx * dx + dy * dy)
        
        w_fn, w_fe, w_d, w_r = pesos_bioma(x, y)
        
        # Cor base misturando os 4 biomas
        r = int(COR_FLORESTA_NORMAL[0]*w_fn + COR_FLORESTA_ESCURA[0]*w_fe + COR_DESERTO[0]*w_d + COR_RUINAS[0]*w_r)
        g = int(COR_FLORESTA_NORMAL[1]*w_fn + COR_FLORESTA_ESCURA[1]*w_fe + COR_DESERTO[1]*w_d + COR_RUINAS[1]*w_r)
        b = int(COR_FLORESTA_NORMAL[2]*w_fn + COR_FLORESTA_ESCURA[2]*w_fe + COR_DESERTO[2]*w_d + COR_RUINAS[2]*w_r)
        cor_bioma = (r, g, b)
        
        # --- FUSÃO COM O LOBBY ---
        if dist <= RAIO_LOBBY * 0.7:
            # Núcleo do Lobby: pedra pura
            pixels[x, y] = COR_LOBBY_PEDRA
        elif dist <= RAIO_LOBBY:
            # Pedra com textura de variação
            if random.random() < 0.2:
                pixels[x, y] = blend(COR_LOBBY_PEDRA, COR_LOBBY_TERRA, 0.4)
            else:
                pixels[x, y] = COR_LOBBY_PEDRA
        elif dist <= RAIO_FUSAO:
            # Zona de FUSÃO ORGÂNICA (dithering)
            t = (dist - RAIO_LOBBY) / (RAIO_FUSAO - RAIO_LOBBY)
            t_s = smoothstep(t)
            
            ruido = random.random()
            if ruido < t_s * 0.85:
                # Estilhaço do bioma invadindo
                pixels[x, y] = cor_bioma
            else:
                # Transição suave pedra ↔ bioma
                pixels[x, y] = blend(COR_LOBBY_TERRA, cor_bioma, t_s)
        else:
            # Bioma puro com micro-variação (dither)
            if random.random() < 0.15:
                pixels[x, y] = blend(cor_bioma, (255, 255, 255), 0.08)
            else:
                pixels[x, y] = cor_bioma

# ============ DESENHAR A FOGUEIRA CENTRAL ============
draw = ImageDraw.Draw(img)
# Fogueira (círculo laranja no centro)
for dy in range(-3, 4):
    for dx in range(-3, 4):
        if dx*dx + dy*dy <= 9:
            pixels[CX+dx, CY+dy] = COR_FOGUEIRA
# Base da fogueira (pedra escura)
for dy in range(-5, 6):
    for dx in range(-5, 6):
        d = dx*dx + dy*dy
        if 16 < d <= 25:
            pixels[CX+dx, CY+dy] = (80, 70, 60)

# ============ DESENHAR OS CAMINHOS (Cruz de terra) ============
print("🛤️ Desenhando os caminhos de terra...")
for y in range(ALTURA):
    for off in range(-2, 3):
        px = CX + off
        if 0 <= px < LARGURA:
            # Só desenha caminho fora do lobby
            dx, dy = px - CX, y - CY
            if math.sqrt(dx*dx + dy*dy) > RAIO_LOBBY * 0.8:
                pixels[px, y] = COR_CAMINHO

for x in range(LARGURA):
    for off in range(-2, 3):
        py = CY + off
        if 0 <= py < ALTURA:
            dx, dy = x - CX, py - CY
            if math.sqrt(dx*dx + dy*dy) > RAIO_LOBBY * 0.8:
                pixels[x, py] = COR_CAMINHO

img.save(OUT_IMG)
print("✅ Imagem gerada! Veja em: http://127.0.0.1:5000/static/mapa_mundo_fusao.png")

# ============ SALVAR NO BANCO DE DADOS ============
print("💾 Salvando no banco de dados...")
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("DELETE FROM mapa_tiles")
cursor.execute("DELETE FROM mapa_objetos")

def classificar_tile(pixel):
    r, g, b = pixel
    # Fogueira
    if r > 220 and g > 120 and g < 190 and b < 100:
        return 'grama_lobby'
    # Caminho de terra
    if abs(r-170)<25 and abs(g-130)<25 and abs(b-90)<25:
        return 'terra_caminho'
    # Pedra do Lobby (cinza claro)
    if abs(r-170)<30 and abs(g-170)<30 and abs(b-165)<30:
        return 'grama_lobby'
    # Compara com as 4 cores de bioma
    menor = float('inf')
    tipo = 'grama_floresta'
    for t, cor in [
        ('grama_floresta', COR_FLORESTA_NORMAL),
        ('grama_escura', COR_FLORESTA_ESCURA),
        ('areia_deserto', COR_DESERTO),
        ('pedra_ruinas', COR_RUINAS),
    ]:
        d = (r - cor[0])**2 + (g - cor[1])**2 + (b - cor[2])**2
        if d < menor:
            menor = d
            tipo = t
    return tipo

grade = {}
for x in range(LARGURA):
    for y in range(ALTURA):
        tipo = classificar_tile(pixels[x, y])
        grade[(x, y)] = tipo
        cursor.execute("INSERT INTO mapa_tiles (x, y, tipo) VALUES (?, ?, ?)", (x, y, tipo))

print("🌳 Espalhando objetos (árvores, cactos, ruínas)...")
for (x, y), tipo in grade.items():
    if tipo in ['terra_caminho', 'grama_lobby']: continue
    # Mais objetos perto das bordas (biomas puros)
    dx, dy = x - CX, y - CY
    dist = math.sqrt(dx*dx + dy*dy)
    chance = 0.08 + (dist / 200) * 0.15  # Mais objetos longe do centro
    
    if random.random() < chance:
        if tipo == 'grama_floresta':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'natureza', ?)", (x, y, random.choice(['arvore', 'arbusto', 'flor'])))
        elif tipo == 'grama_escura':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'natureza_escura', ?)", (x, y, random.choice(['arvore_escura', 'cogumelo', 'pedra_sombria'])))
        elif tipo == 'areia_deserto':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'deserto', ?)", (x, y, random.choice(['cacto', 'pedra_areia', 'ossada'])))
        elif tipo == 'pedra_ruinas':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'ruina', ?)", (x, y, random.choice(['pilar', 'entulho', 'estatua', 'coluna']))) 

conn.commit()
conn.close()
print("✅ Mapa do Mundo da Fusão salvo no banco de dados com sucesso!")
