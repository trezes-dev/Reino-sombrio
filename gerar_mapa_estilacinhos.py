from PIL import Image, ImageDraw
import sqlite3, os, random, math

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_estilacinhos.png')
LARGURA, ALTURA = 200, 200
CENTRO_X, CENTRO_Y = 100, 100

CORES = {
    'vazio_branco':   (240, 240, 240), # Espaço branco no meio
    'grama_lobby':    (144, 238, 144), # Bola verde do Lobby
    'grama_escura':   (0, 100, 0),     # Q1: Superior Esquerdo
    'grama_floresta': (34, 139, 34),   # Q2: Superior Direito
    'areia_deserto':  (238, 214, 175), # Q3: Inferior Esquerdo
    'pedra_ruinas':   (105, 105, 105), # Q4: Inferior Direito
    'terra_caminho':  (160, 82, 45)    # Caminhos
}

print("🎨 Gerando o mapa com estilacinhos...")
# 1. Fundo branco (espaço vazio)
img = Image.new('RGB', (LARGURA, ALTURA), CORES['vazio_branco'])
draw = ImageDraw.Draw(img)

# 2. Desenhar as 4 regiões nas bordas (deixando o centro vazio)
# Definindo onde cada quadrante começa (deixando 50px de margem para o centro)
# Q1: Superior Esquerdo
draw.rectangle([0, 0, CENTRO_X-50, CENTRO_Y-50], fill=CORES['grama_escura'])
# Q2: Superior Direito
draw.rectangle([CENTRO_X+50, 0, LARGURA, CENTRO_Y-50], fill=CORES['grama_floresta'])
# Q3: Inferior Esquerdo
draw.rectangle([0, CENTRO_Y+50, CENTRO_X-50, ALTURA], fill=CORES['areia_deserto'])
# Q4: Inferior Direito
draw.rectangle([CENTRO_X+50, CENTRO_Y+50, LARGURA, ALTURA], fill=CORES['pedra_ruinas'])

# 3. Desenhar a Bola do Lobby no centro
draw.ellipse([CENTRO_X-20, CENTRO_Y-20, CENTRO_X+20, CENTRO_Y+20], fill=CORES['grama_lobby'])

# 4. Criar os "Estilacinhos" (Dispersão Radial)
print("✨ Criando os estilacinhos de conexão...")
for x in range(LARGURA):
    for y in range(ALTURA):
        # Calcula a distância e o ângulo em relação ao centro
        dist = math.sqrt((x - CENTRO_X)**2 + (y - CENTRO_Y)**2)
        angulo = math.degrees(math.atan2(y - CENTRO_Y, x - CENTRO_X))

        # Se estiver na zona de transição (fora da bola do lobby e antes das bordas)
        if 20 < dist < 50:
            # Calcula a probabilidade de colocar um pixel (mais perto do centro, menos pixels)
            prob = (dist - 20) / 30.0
            if random.random() < prob:
                # Descobre qual região está naquela direção
                cor_regiao = CORES['grama_escura']
                if -90 <= angulo < 0:    cor_regiao = CORES['grama_floresta'] # Superior Direito
                elif 0 <= angulo < 90:   cor_regiao = CORES['pedra_ruinas']   # Inferior Direito
                elif 90 <= angulo < 180: cor_regiao = CORES['areia_deserto']  # Inferior Esquerdo
                elif -180 <= angulo < -90: cor_regiao = CORES['grama_escura'] # Superior Esquerdo
                
                img.putpixel((x, y), cor_regiao)

# 5. Desenhar os Caminhos de Terra
draw.line([(CENTRO_X, 0), (CENTRO_X, ALTURA)], fill=CORES['terra_caminho'], width=3)
draw.line([(0, CENTRO_Y), (LARGURA, CENTRO_Y)], fill=CORES['terra_caminho'], width=3)

img.save(OUT_IMG)
print("✅ Imagem gerada! Veja em: http://127.0.0.1:5000/static/mapa_estilacinhos.png")

# --- SALVAR NO BANCO DE DADOS ---
print("💾 Salvando no banco de dados...")
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("DELETE FROM mapa_tiles")
cursor.execute("DELETE FROM mapa_objetos")

def cor_para_tipo(pixel):
    r, g, b = pixel
    menor_dist = float('inf')
    melhor_tipo = 'vazio_branco'
    for tipo, cor in CORES.items():
        dist = (r - cor[0])**2 + (g - cor[1])**2 + (b - cor[2])**2
        if dist < menor_dist:
            menor_dist = dist
            melhor_tipo = tipo
    return melhor_tipo

grade = {}
for x in range(LARGURA):
    for y in range(ALTURA):
        tipo = cor_para_tipo(img.getpixel((x, y)))
        grade[(x, y)] = tipo
        cursor.execute("INSERT INTO mapa_tiles (x, y, tipo) VALUES (?, ?, ?)", (x, y, tipo))

print("🌳 Espalhando objetos...")
for (x, y), tipo in grade.items():
    if tipo in ['terra_caminho', 'vazio_branco']: continue
    if random.random() < 0.12:
        if tipo == 'grama_floresta':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'natureza', ?)", (x, y, random.choice(['arvore', 'arbusto'])))
        elif tipo == 'grama_escura':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'natureza_escura', ?)", (x, y, random.choice(['arvore_escura', 'cogumelo'])))
        elif tipo == 'areia_deserto':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'deserto', ?)", (x, y, random.choice(['cacto', 'pedra_areia'])))
        elif tipo == 'pedra_ruinas':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'ruina', ?)", (x, y, random.choice(['pilar', 'entulho'])))

conn.commit()
conn.close()
print("✅ Mapa dos estilacinhos salvo no banco de dados com sucesso!")
