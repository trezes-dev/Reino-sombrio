from PIL import Image
import sqlite3, os

DB = os.path.expanduser('~/rpg/rpg.db')
OUT = os.path.expanduser('~/rpg/static/mapa_completo.png')

CORES = {
    'grama_lobby':    (144, 238, 144),
    'grama_floresta': (34, 139, 34),
    'grama_escura':   (0, 100, 0),
    'areia_deserto':  (238, 214, 175),
    'pedra_ruinas':   (105, 105, 105),
    'terra_caminho':  (160, 82, 45),
}

conn = sqlite3.connect(DB)
cursor = conn.cursor()

# Aumenta o mapa 4x para ficar visível no celular (200 * 4 = 800x800)
ESCALA = 4
img = Image.new('RGB', (200 * ESCALA, 200 * ESCALA), (30, 30, 30))
pixels = img.load()

cursor.execute("SELECT x, y, tipo FROM mapa_tiles")
for x, y, tipo in cursor.fetchall():
    cor = CORES.get(tipo, (255, 0, 255))
    for dx in range(ESCALA):
        for dy in range(ESCALA):
            pixels[x*ESCALA + dx, y*ESCALA + dy] = cor

# Marcar NPCs (amarelo, tamanho 5x5)
cursor.execute("SELECT x, y FROM npcs")
for x, y in cursor.fetchall():
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            px, py = x*ESCALA + dx*2, y*ESCALA + dy*2
            if 0 <= px < 800 and 0 <= py < 800:
                pixels[px, py] = (255, 215, 0)

# Marcar Monstros (vermelho, tamanho 5x5)
cursor.execute("SELECT x, y FROM monstros")
for x, y in cursor.fetchall():
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            px, py = x*ESCALA + dx*2, y*ESCALA + dy*2
            if 0 <= px < 800 and 0 <= py < 800:
                pixels[px, py] = (255, 50, 50)

conn.close()
img.save(OUT)
print("✅ Mapa completo gerado!")
print("👉 Acesse: http://127.0.0.1:5000/static/mapa_completo.png")
