from PIL import Image, ImageDraw
import sqlite3, os, random, math

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_organico.png')
LARGURA, ALTURA = 200, 200
SEED_SIZE = 50 # Grid menor para desenhar as formas orgânicas

CORES = {
    'grama_floresta': (34, 139, 34),
    'grama_escura':   (0, 100, 0),
    'areia_deserto':  (238, 214, 175),
    'pedra_ruinas':   (105, 105, 105),
    'grama_lobby':    (144, 238, 144),
    'terra_caminho':  (160, 82, 45)
}

print("🎨 Gerando o mapa orgânico (formas arredondadas)...")
# 1. Criar a imagem base no grid menor (50x50)
img_seed = Image.new('RGB', (SEED_SIZE, SEED_SIZE), CORES['grama_floresta'])
draw = ImageDraw.Draw(img_seed)

# 2. Desenhar os Biomas como grandes círculos que se sobrepõem
# Q1: Floresta Escura (Canto Superior Esquerdo)
draw.ellipse([25-35, 25-35, 25+35, 25+35], fill=CORES['grama_escura'])
# Q2: Floresta Normal (Canto Superior Direito)
draw.ellipse([75-35, 25-35, 75+35, 25+35], fill=CORES['grama_floresta'])
# Q3: Deserto (Canto Inferior Esquerdo)
draw.ellipse([25-35, 75-35, 25+35, 75+35], fill=CORES['areia_deserto'])
# Q4: Ruínas (Canto Inferior Direito)
draw.ellipse([75-35, 75-35, 75+35, 75+35], fill=CORES['pedra_ruinas'])

# 3. Desenhar o Lobby no Centro
draw.ellipse([50-12, 50-12, 50+12, 50+12], fill=CORES['grama_lobby'])

# 4. Desenhar os Caminhos de Terra (A Cruz) com uma leve curva (usando matemática)
# Caminho Vertical
for y in range(SEED_SIZE):
    offset = int(4 * math.sin(y / 5)) # Cria a curva
    draw.rectangle([50 + offset - 2, y, 50 + offset + 2, y+1], fill=CORES['terra_caminho'])
# Caminho Horizontal
for x in range(SEED_SIZE):
    offset = int(4 * math.sin(x / 5)) # Cria a curva
    draw.rectangle([x, 50 + offset - 2, x+1, 50 + offset + 2], fill=CORES['terra_caminho'])

# 5. Aumentar a escala para 200x200 SEM borrar (Nearest Neighbor)
img = img_seed.resize((LARGURA, ALTURA), Image.Resampling.NEAREST)
img.save(OUT_IMG)
print("✅ Imagem gerada! Veja em: http://127.0.0.1:5000/static/mapa_organico.png")

# --- SALVAR NO BANCO DE DADOS ---
print("💾 Salvando no banco de dados...")
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("DELETE FROM mapa_tiles")
cursor.execute("DELETE FROM mapa_objetos")

def cor_para_tipo(pixel):
    r, g, b = pixel
    menor_dist = float('inf')
    melhor_tipo = 'grama_floresta'
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

print("🌳 Espalhando objetos (árvores, cactos, ruínas)...")
for (x, y), tipo in grade.items():
    if tipo == 'terra_caminho': continue
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
print("✅ Mapa orgânico salvo no banco de dados com sucesso!")
