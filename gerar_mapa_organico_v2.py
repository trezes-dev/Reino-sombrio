from PIL import Image, ImageDraw
import sqlite3, os, random, math

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_organico_v2.png')
LARGURA, ALTURA = 200, 200

CORES = {
    'grama_floresta': (34, 139, 34),
    'grama_escura':   (0, 100, 0),
    'areia_deserto':  (238, 214, 175),
    'pedra_ruinas':   (105, 105, 105),
    'grama_lobby':    (144, 238, 144),
    'terra_caminho':  (160, 82, 45)
}

print("🎨 Gerando o mapa com o Lobby central...")
img = Image.new('RGB', (LARGURA, ALTURA), CORES['grama_floresta'])
draw = ImageDraw.Draw(img)

# 1. Desenhar os 4 Quadrantes (Grandes áreas, mas deixando espaço para o lobby)
# Q1: Floresta Escura (Superior Esquerdo)
draw.rectangle([0, 0, 85, 85], fill=CORES['grama_escura'])
# Q2: Floresta Normal (Superior Direito)
draw.rectangle([115, 0, 199, 85], fill=CORES['grama_floresta'])
# Q3: Deserto (Inferior Esquerdo)
draw.rectangle([0, 115, 85, 199], fill=CORES['areia_deserto'])
# Q4: Ruínas (Inferior Direito)
draw.rectangle([115, 115, 199, 199], fill=CORES['pedra_ruinas'])

# 2. Desenhar o Lobby Central (Um círculo grande no meio)
draw.ellipse([85, 85, 115, 115], fill=CORES['grama_lobby'])

# 3. Adicionar Ruído nas bordas dos quadrantes (para não ficar quadrado)
for x in range(1, LARGURA - 1):
    for y in range(1, ALTURA - 1):
        # Perto das bordas dos quadrantes (x=85/115 e y=85/115)
        if abs(x - 85) < 3 or abs(x - 115) < 3 or abs(y - 85) < 3 or abs(y - 115) < 3:
            if random.random() < 0.4:
                vizinhos = [
                    img.getpixel((x+1, y)), img.getpixel((x-1, y)), 
                    img.getpixel((x, y+1)), img.getpixel((x, y-1))
                ]
                img.putpixel((x, y), random.choice(vizinhos))

# 4. Desenhar os Caminhos de Terra (A Cruz)
draw.line([(100, 0), (100, ALTURA)], fill=CORES['terra_caminho'], width=4)
draw.line([(0, 100), (LARGURA, 100)], fill=CORES['terra_caminho'], width=4)

img.save(OUT_IMG)
print("✅ Imagem gerada! Veja em: http://127.0.0.1:5000/static/mapa_organico_v2.png")

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

print("🌳 Espalhando objetos...")
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
print("✅ Mapa orgânico v2 salvo no banco de dados com sucesso!")
