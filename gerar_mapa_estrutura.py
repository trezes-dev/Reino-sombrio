from PIL import Image
import sqlite3, os, random, math

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_estrutura.png')
LARGURA, ALTURA = 200, 200
CENTRO_X, CENTRO_Y = 100, 100

# Cores dos biomas
COR_FLORESTA_ESCURA = (0, 100, 0)     # Metade Superior
COR_DESERTO = (238, 214, 175)         # Quadrante Inferior Esquerdo
COR_RUINAS = (105, 105, 105)          # Quadrante Inferior Direito
COR_LOBBY = (144, 238, 144)           # Verde brilhante (centro)
COR_LOBBY_NEON = (50, 255, 100)       # Verde neon para o núcleo
COR_CAMINHO = (160, 82, 45)

print("🎨 Gerando o mapa com a estrutura exata...")
img = Image.new('RGB', (LARGURA, ALTURA), COR_FLORESTA_ESCURA)
pixels = img.load()

# 1. Preencher os biomas base
for x in range(LARGURA):
    for y in range(ALTURA):
        if y < 100:
            # Metade Superior: Floresta Escura
            pixels[x, y] = COR_FLORESTA_ESCURA
        else:
            if x < 100:
                # Quadrante Inferior Esquerdo: Deserto
                pixels[x, y] = COR_DESERTO
            else:
                # Quadrante Inferior Direito: Ruínas
                pixels[x, y] = COR_RUINAS

# 2. Criar os estilhaços dos biomas em direção ao centro (fusão)
print("✨ Criando a fusão dos biomas com o centro...")
RAIO_FUSAO = 75
RAIO_NUCLEO = 25

for x in range(LARGURA):
    for y in range(ALTURA):
        dist = math.sqrt((x - CENTRO_X)**2 + (y - CENTRO_Y)**2)
        
        # Cor base do bioma naquela posição
        if y < 100: 
            cor_bioma = COR_FLORESTA_ESCURA
        elif x < 100: 
            cor_bioma = COR_DESERTO
        else: 
            cor_bioma = COR_RUINAS

        if dist <= RAIO_NUCLEO:
            # Núcleo do Lobby: verde neon brilhante
            pixels[x, y] = COR_LOBBY_NEON
        elif dist <= RAIO_FUSAO:
            # Zona de fusão: mistura o lobby com o bioma
            peso = (dist - RAIO_NUCLEO) / (RAIO_FUSAO - RAIO_NUCLEO)
            
            # Adiciona estilhaços aleatórios do bioma invadindo o lobby
            if random.random() < peso * 0.7:
                r = int(COR_LOBBY[0] * (1 - peso) + cor_bioma[0] * peso)
                g = int(COR_LOBBY[1] * (1 - peso) + cor_bioma[1] * peso)
                b = int(COR_LOBBY[2] * (1 - peso) + cor_bioma[2] * peso)
                pixels[x, y] = (r, g, b)
            else:
                pixels[x, y] = COR_LOBBY
        else:
            # Fora da zona de fusão: bioma puro
            pixels[x, y] = cor_bioma

# 3. Desenhar os caminhos de terra (Cruz)
print("🛤️ Desenhando os caminhos...")
for y in range(ALTURA):
    for offset in range(-2, 3):
        if 0 <= CENTRO_X + offset < LARGURA:
            pixels[CENTRO_X + offset, y] = COR_CAMINHO

for x in range(LARGURA):
    for offset in range(-2, 3):
        if 0 <= CENTRO_Y + offset < ALTURA:
            pixels[x, CENTRO_Y + offset] = COR_CAMINHO

img.save(OUT_IMG)
print("✅ Imagem gerada! Veja em: http://127.0.0.1:5000/static/mapa_estrutura.png")

# --- SALVAR NO BANCO DE DADOS ---
print("💾 Salvando no banco de dados...")
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("DELETE FROM mapa_tiles")
cursor.execute("DELETE FROM mapa_objetos")

def cor_para_tipo(pixel):
    r, g, b = pixel
    menor_dist = float('inf')
    melhor_tipo = 'grama_escura'
    for tipo, cor in {
        'grama_escura': COR_FLORESTA_ESCURA,
        'areia_deserto': COR_DESERTO,
        'pedra_ruinas': COR_RUINAS,
        'grama_lobby': COR_LOBBY,
        'terra_caminho': COR_CAMINHO
    }.items():
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
        if tipo == 'grama_escura':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'natureza_escura', ?)", (x, y, random.choice(['arvore_escura', 'cogumelo'])))
        elif tipo == 'areia_deserto':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'deserto', ?)", (x, y, random.choice(['cacto', 'pedra_areia'])))
        elif tipo == 'pedra_ruinas':
            cursor.execute("INSERT INTO mapa_objetos (x, y, tipo, subtipo) VALUES (?, ?, 'ruina', ?)", (x, y, random.choice(['pilar', 'entulho'])))

conn.commit()
conn.close()
print("✅ Mapa com estrutura exata salvo no banco de dados com sucesso!")
