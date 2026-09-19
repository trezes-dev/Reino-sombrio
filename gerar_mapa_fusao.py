from PIL import Image
import sqlite3, os, random, math

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_fusao.png')
LARGURA, ALTURA = 200, 200
CENTRO_X, CENTRO_Y = 100, 100

# Cores das regiões (R, G, B)
CORES = {
    'grama_lobby':    (144, 238, 144),
    'grama_escura':   (0, 100, 0),
    'grama_floresta': (34, 139, 34),
    'areia_deserto':  (238, 214, 175),
    'pedra_ruinas':   (105, 105, 105),
    'terra_caminho':  (160, 82, 45)
}

# Função para pegar a cor da região baseada no ângulo
def cor_da_regiao(angulo):
    if -90 <= angulo < 0:    return CORES['grama_floresta'] # Superior Direito
    elif 0 <= angulo < 90:   return CORES['pedra_ruinas']   # Inferior Direito
    elif 90 <= angulo < 180: return CORES['areia_deserto']  # Inferior Esquerdo
    else:                    return CORES['grama_escura']   # Superior Esquerdo

print("🎨 Gerando o mapa com fusão...")
img = Image.new('RGB', (LARGURA, ALTURA), CORES['grama_lobby'])
pixels = img.load()

# Raio de fusão (distância do centro até onde a região fica "pura")
RAIO_FUSAO = 70
RAIO_LOBBY = 20

for x in range(LARGURA):
    for y in range(ALTURA):
        # Distância e ângulo em relação ao centro
        dist = math.sqrt((x - CENTRO_X)**2 + (y - CENTRO_Y)**2)
        angulo = math.degrees(math.atan2(y - CENTRO_Y, x - CENTRO_X))

        cor_regiao = cor_da_regiao(angulo)
        cor_lobby = CORES['grama_lobby']

        # Calcula o "peso" da fusão (0 = só lobby, 1 = só região)
        if dist <= RAIO_LOBBY:
            # Área do lobby (cores claras)
            peso = 0.0
        elif dist >= RAIO_FUSAO:
            # Área das regiões (cores puras)
            peso = 1.0
        else:
            # Zona de fusão (degradê suave)
            peso = (dist - RAIO_LOBBY) / (RAIO_FUSAO - RAIO_LOBBY)

        # Interpolação linear das cores
        r = int(cor_lobby[0] * (1 - peso) + cor_regiao[0] * peso)
        g = int(cor_lobby[1] * (1 - peso) + cor_regiao[1] * peso)
        b = int(cor_lobby[2] * (1 - peso) + cor_regiao[2] * peso)

        pixels[x, y] = (r, g, b)

# Desenhar os caminhos de terra
for y in range(ALTURA):
    for offset in range(-2, 3):
        if 0 <= CENTRO_X + offset < LARGURA:
            pixels[CENTRO_X + offset, y] = CORES['terra_caminho']

for x in range(LARGURA):
    for offset in range(-2, 3):
        if 0 <= CENTRO_Y + offset < ALTURA:
            pixels[x, CENTRO_Y + offset] = CORES['terra_caminho']

img.save(OUT_IMG)
print("✅ Imagem gerada! Veja em: http://127.0.0.1:5000/static/mapa_fusao.png")

# --- SALVAR NO BANCO DE DADOS ---
print("💾 Salvando no banco de dados...")
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("DELETE FROM mapa_tiles")
cursor.execute("DELETE FROM mapa_objetos")

def cor_para_tipo(pixel):
    r, g, b = pixel
    menor_dist = float('inf')
    melhor_tipo = 'grama_lobby'
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
print("✅ Mapa de fusão salvo no banco de dados com sucesso!")
