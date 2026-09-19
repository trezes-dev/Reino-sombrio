from PIL import Image, ImageDraw
import sqlite3, os, random

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_conectado.png')
LARGURA, ALTURA = 200, 200

CORES = {
    'grama_floresta': (34, 139, 34),
    'grama_escura':   (0, 100, 0),
    'areia_deserto':  (238, 214, 175),
    'pedra_ruinas':   (105, 105, 105),
    'grama_lobby':    (144, 238, 144),
    'terra_caminho':  (160, 82, 45)
}

print("🎨 Gerando o mapa com regiões conectadas...")
img = Image.new('RGB', (LARGURA, ALTURA), CORES['grama_floresta'])
draw = ImageDraw.Draw(img)

# 1. Desenhar os 4 quadrantes que se tocam no centro (x=100, y=100)
# Superior Esquerdo: Floresta Escura
draw.rectangle([0, 0, 100, 100], fill=CORES['grama_escura'])
# Superior Direito: Floresta Normal
draw.rectangle([100, 0, 199, 100], fill=CORES['grama_floresta'])
# Inferior Esquerdo: Deserto
draw.rectangle([0, 100, 100, 199], fill=CORES['areia_deserto'])
# Inferior Direito: Ruínas
draw.rectangle([100, 100, 199, 199], fill=CORES['pedra_ruinas'])

# 2. Adicionar ruído nas bordas de contato (x=100 e y=100) para não ficar reto
for x in range(1, LARGURA - 1):
    for y in range(1, ALTURA - 1):
        # Se estiver perto das linhas de divisão (x=100 ou y=100)
        if abs(x - 100) < 4 or abs(y - 100) < 4:
            if random.random() < 0.5:
                # Pega a cor de um vizinho para misturar e criar bordas irregulares
                vizinhos = [
                    img.getpixel((x+1, y)), img.getpixel((x-1, y)), 
                    img.getpixel((x, y+1)), img.getpixel((x, y-1))
                ]
                img.putpixel((x, y), random.choice(vizinhos))

# 3. Desenhar o Lobby Central (Círculo)
draw.ellipse([100-15, 100-15, 100+15, 100+15], fill=CORES['grama_lobby'])

# 4. Desenhar os Caminhos (Cruz) - Agora eles cruzam as fronteiras diretamente
draw.line([(100, 0), (100, ALTURA)], fill=CORES['terra_caminho'], width=4)
draw.line([(0, 100), (LARGURA, 100)], fill=CORES['terra_caminho'], width=4)

img.save(OUT_IMG)
print("✅ Imagem gerada! Veja em: http://127.0.0.1:5000/static/mapa_conectado.png")

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
print("✅ Mapa conectado salvo no banco de dados com sucesso!")
