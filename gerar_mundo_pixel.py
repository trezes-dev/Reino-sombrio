from PIL import Image, ImageDraw
import sqlite3, os, random

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mundo_pixel.png')
LARGURA, ALTURA = 200, 200

# Cores base (R, G, B) - Estilo paleta de GBA
CORES = {
    'grama_lobby': (144, 238, 144),   # Verde claro
    'grama_floresta': (34, 139, 34),  # Verde escuro
    'areia_deserto': (238, 214, 175), # Bege
    'pedra_ruinas': (169, 169, 169),  # Cinza
    'terra_caminho': (160, 82, 45)    # Marrom
}

print("🎨 Gerando o mapa semente (20x20)...")
# 1. Criar um grid menor (20x20) para servir de "semente"
SEED_SIZE = 20
seed_map = [[0 for _ in range(SEED_SIZE)] for _ in range(SEED_SIZE)]

# Preencher o grid semente
# 0 = Floresta, 1 = Lobby, 2 = Deserto, 3 = Ruínas
for y in range(SEED_SIZE):
    for x in range(SEED_SIZE):
        # Lógica de posicionamento no grid 20x20
        if 8 <= x <= 12 and 2 <= y <= 6:
            seed_map[y][x] = 1 # Lobby
        elif 12 <= x <= 19 and 6 <= y <= 14:
            seed_map[y][x] = 2 # Deserto
        elif 4 <= x <= 12 and 12 <= y <= 19:
            seed_map[y][x] = 3 # Ruínas
        else:
            seed_map[y][x] = 0 # Floresta

# 2. Aumentar a escala para 200x200 usando NEAREST (mantém os pixels quadrados)
img_seed = Image.new('RGB', (SEED_SIZE, SEED_SIZE))
pixels = img_seed.load()
for y in range(SEED_SIZE):
    for x in range(SEED_SIZE):
        cor = CORES['grama_floresta']
        if seed_map[y][x] == 1: cor = CORES['grama_lobby']
        elif seed_map[y][x] == 2: cor = CORES['areia_deserto']
        elif seed_map[y][x] == 3: cor = CORES['pedra_ruinas']
        pixels[x, y] = cor

# Redimensiona para 200x200 SEM desfoque
img = img_seed.resize((LARGURA, ALTURA), Image.Resampling.NEAREST)
draw = ImageDraw.Draw(img)

# 3. Adicionar Ruído nas bordas (para não ficar quadrado)
print("🌪️ Adicionando ruído orgânico nas bordas...")
for x in range(1, LARGURA - 1):
    for y in range(1, ALTURA - 1):
        # Pega a cor atual
        cor_atual = img.getpixel((x, y))
        
        # Se for uma borda (vizinhos diferentes)
        vizinhos = [img.getpixel((x+1, y)), img.getpixel((x-1, y)), img.getpixel((x, y+1)), img.getpixel((x, y-1))]
        if any(v != cor_atual for v in vizinhos):
            # Chance de mudar a cor deste pixel para o vizinho (cria bordas irregulares)
            if random.random() < 0.3:
                img.putpixel((x, y), random.choice(vizinhos))

# 4. Desenhar Caminhos (Terra)
draw.line([(100, 40), (50, 100)], fill=CORES['terra_caminho'], width=4)   # Lobby -> Floresta
draw.line([(100, 40), (160, 100)], fill=CORES['terra_caminho'], width=4)  # Lobby -> Deserto
draw.line([(160, 100), (100, 170)], fill=CORES['terra_caminho'], width=4) # Deserto -> Ruínas

img.save(OUT_IMG)
print("✅ Imagem pixel art gerada! Veja em: http://127.0.0.1:5000/static/mundo_pixel.png")

# --- SALVAR NO BANCO DE DADOS ---
print("💾 Salvando tiles e objetos no banco...")
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

# Espalhar objetos
for (x, y), tipo in grade.items():
    if tipo == 'terra_caminho': continue
    if random.random() < 0.12:
        if tipo in ['grama_floresta', 'grama_lobby']:
            subtipo = random.choice(['arvore', 'arvore', 'arbusto'])
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'natureza', ?)", (x, y, subtipo))
        elif tipo == 'areia_deserto':
            subtipo = random.choice(['cacto', 'pedra_areia'])
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'deserto', ?)", (x, y, subtipo))
        elif tipo == 'pedra_ruinas':
            subtipo = random.choice(['pilar', 'entulho'])
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'ruina', ?)", (x, y, subtipo))

conn.commit()
conn.close()
print("✅ Mundo salvo no banco de dados com sucesso!")
