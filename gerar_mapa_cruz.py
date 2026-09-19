from PIL import Image, ImageDraw
import sqlite3, os, random

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_cruz.png')
LARGURA, ALTURA = 200, 200
MEIO = 100

CORES = {
    'grama_floresta': (34, 139, 34),
    'grama_escura':   (0, 100, 0),
    'areia_deserto':  (238, 214, 175),
    'pedra_ruinas':   (105, 105, 105),
    'grama_lobby':    (144, 238, 144),
    'terra_caminho':  (160, 82, 45)
}

print("🎨 Gerando o mapa da cruz...")
img = Image.new('RGB', (LARGURA, ALTURA), CORES['grama_floresta'])
draw = ImageDraw.Draw(img)

draw.rectangle([0, 0, MEIO-1, MEIO-1], fill=CORES['grama_escura'])
draw.rectangle([MEIO, 0, LARGURA-1, MEIO-1], fill=CORES['grama_floresta'])
draw.rectangle([0, MEIO, MEIO-1, ALTURA-1], fill=CORES['areia_deserto'])
draw.rectangle([MEIO, MEIO, LARGURA-1, ALTURA-1], fill=CORES['pedra_ruinas'])

for x in range(1, LARGURA - 1):
    for y in range(1, ALTURA - 1):
        if abs(x - MEIO) < 3 or abs(y - MEIO) < 3:
            if random.random() < 0.4:
                vizinhos = [img.getpixel((x+1, y)), img.getpixel((x-1, y)), img.getpixel((x, y+1)), img.getpixel((x, y-1))]
                img.putpixel((x, y), random.choice(vizinhos))

draw.rectangle([MEIO-15, MEIO-15, MEIO+15, MEIO+15], fill=CORES['grama_lobby'])
draw.line([(MEIO, 0), (MEIO, ALTURA)], fill=CORES['terra_caminho'], width=6)
draw.line([(0, MEIO), (LARGURA, MEIO)], fill=CORES['terra_caminho'], width=6)

img.save(OUT_IMG)
print("✅ Imagem gerada! Veja em: http://127.0.0.1:5000/static/mapa_cruz.png")

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
    if random.random() < 0.15:
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
print("✅ Mapa salvo no banco de dados com sucesso!")
