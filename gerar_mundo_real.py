from PIL import Image, ImageDraw, ImageFilter
import sqlite3, os, random

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mundo_real.png')
LARGURA, ALTURA = 200, 200

# Cores base (R, G, B)
CORES = {
    'grama_lobby': (100, 180, 100),
    'grama_floresta': (34, 139, 34),
    'areia_deserto': (230, 210, 150),
    'pedra_ruinas': (150, 150, 150),
    'terra_caminho': (139, 69, 19)
}

print("🎨 Desenhando o continente...")
# 1. Criar a imagem base (fundo preto)
img = Image.new('RGB', (LARGURA, ALTURA), (0, 0, 0))
draw = ImageDraw.Draw(img)

# 2. Desenhar as grandes áreas (Blobs) se sobrepondo
# Floresta (Base do mapa - ocupa quase tudo)
draw.ellipse([-20, -20, 220, 220], fill=CORES['grama_floresta'])

# Lobby (Centro-norte)
draw.ellipse([70, 30, 130, 90], fill=CORES['grama_lobby'])

# Deserto (Leste)
draw.ellipse([120, 60, 220, 160], fill=CORES['areia_deserto'])
draw.ellipse([130, 40, 190, 120], fill=CORES['areia_deserto'])

# Ruínas (Sul)
draw.ellipse([40, 120, 140, 220], fill=CORES['pedra_ruinas'])
draw.ellipse([80, 140, 160, 200], fill=CORES['pedra_ruinas'])

# 3. Aplicar Desfoque (Blur) para suavizar as bordas
# Isso cria a transição gradual entre os biomas
img = img.filter(ImageFilter.GaussianBlur(radius=12))

# 4. Desenhar Caminhos de Terra (Por cima, sem blur)
draw = ImageDraw.Draw(img)
draw.line([(100, 60), (50, 140)], fill=CORES['terra_caminho'], width=4)  # Lobby -> Floresta
draw.line([(100, 60), (170, 100)], fill=CORES['terra_caminho'], width=4) # Lobby -> Deserto
draw.line([(170, 100), (100, 180)], fill=CORES['terra_caminho'], width=4) # Deserto -> Ruínas

img.save(OUT_IMG)
print("✅ Imagem do continente gerada! Veja em: http://127.0.0.1:5000/static/mundo_real.png")

# --- CONVERTER PARA TILES E SALVAR NO BANCO ---
print("💾 Convertendo pixels para tiles e salvando no banco...")
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("DELETE FROM mapa_tiles")
cursor.execute("DELETE FROM mapa_objetos")

# Função para achar a cor mais próxima
def cor_mais_proxima(pixel):
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
        tipo = cor_mais_proxima(img.getpixel((x, y)))
        grade[(x, y)] = tipo
        cursor.execute("INSERT INTO mapa_tiles (x, y, tipo) VALUES (?, ?, ?)", (x, y, tipo))

# --- ESPALHAR OBJETOS ---
print("🌳 Espalhando árvores, pedras e ruínas...")
for (x, y), tipo in grade.items():
    if tipo == 'terra_caminho': continue

    # Chance de 12% de ter um objeto
    if random.random() < 0.12:
        if tipo in ['grama_floresta', 'grama_lobby']:
            subtipo = random.choice(['arvore', 'arvore', 'arbusto'])
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'natureza', ?)", (x, y, subtipo))
        elif tipo == 'areia_deserto':
            subtipo = random.choice(['cacto', 'pedra_areia', 'ossada'])
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'deserto', ?)", (x, y, subtipo))
        elif tipo == 'pedra_ruinas':
            subtipo = random.choice(['pilar', 'entulho', 'estatua'])
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'ruina', ?)", (x, y, subtipo))

conn.commit()
conn.close()
print("✅ Mundo real gerado e salvo no banco de dados com sucesso!")
