from PIL import Image, ImageDraw
import sqlite3
import os

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_final.png')

LARGURA, ALTURA = 200, 200

# Cores do mapa (R, G, B)
COR_GRAM_DURA = (100, 180, 100)   # Lobby
COR_FLORESTA  = (34, 139, 34)     # Floresta
COR_DESERTO   = (230, 210, 150)   # Deserto
COR_RUINAS    = (150, 150, 150)   # Ruínas
COR_CAMINHO   = (139, 69, 19)     # Terra batida

img = Image.new('RGB', (LARGURA, ALTURA), COR_FLORESTA) # Fundo base = Floresta
draw = ImageDraw.Draw(img)

# 1. Desenhar o Deserto (Grande área à direita)
draw.ellipse([100, 20, 220, 140], fill=COR_DESERTO)
draw.ellipse([130, 80, 200, 180], fill=COR_DESERTO) # Extensão ao sul

# 2. Desenhar as Ruínas (Parte inferior central)
draw.ellipse([60, 130, 140, 200], fill=COR_RUINAS)
draw.rectangle([80, 140, 120, 190], fill=COR_RUINAS) # Área mais quadrada para estruturas

# 3. Desenhar o Lobby (Oásis no centro-norte)
draw.ellipse([70, 10, 130, 70], fill=COR_GRAM_DURA)
draw.ellipse([85, 30, 115, 55], fill=COR_GRAM_DURA) # Extensão da cidade

# 4. Desenhar Caminhos conectando tudo (Terra)
draw.line([(100, 40), (50, 100)], fill=COR_CAMINHO, width=4)  # Lobby -> Floresta Oeste
draw.line([(100, 40), (160, 60)], fill=COR_CAMINHO, width=4)  # Lobby -> Deserto
draw.line([(160, 100), (120, 160)], fill=COR_CAMINHO, width=4) # Deserto -> Ruínas
draw.line([(50, 120), (100, 170)], fill=COR_CAMINHO, width=4)  # Floresta -> Ruínas

img.save(OUT_IMG)
print("✅ Imagem do mapa final gerada! Veja em: http://127.0.0.1:5000/static/mapa_final.png")

# --- AGORA VAMOS SALVAR NO BANCO DE DADOS ---
print("⏳ Lendo a imagem e salvando no banco de dados (pode demorar um pouco)...")
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("DELETE FROM mapa_tiles")

# Mapeamento de cor RGB para o nome do tile no jogo
mapa_cores = {
    COR_GRAM_DURA: 'grama_lobby',
    COR_FLORESTA: 'grama_floresta',
    COR_DESERTO: 'areia_deserto',
    COR_RUINAS: 'pedra_ruinas',
    COR_CAMINHO: 'terra_caminho'
}

for x in range(LARGURA):
    for y in range(ALTURA):
        # Pega a cor do pixel na posição (x, y)
        r, g, b = img.getpixel((x, y))
        tipo = mapa_cores.get((r, g, b), 'grama_floresta') # Padrão é floresta
        cursor.execute("INSERT INTO mapa_tiles (x, y, tipo) VALUES (?, ?, ?)", (x, y, tipo))

conn.commit()
conn.close()
print("✅ Mapa contínuo salvo no banco de dados com sucesso!")
