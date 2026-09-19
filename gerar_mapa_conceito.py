from PIL import Image, ImageDraw
import os

LARGURA = 200
ALTURA = 200
ESCALA = 4  # 4 pixels por tile -> imagem 800x800 (bom para visualizar no celular)
OUT = os.path.expanduser('~/rpg/static/mapa_conceito.png')

# Cores e coordenadas das 4 Regiões (x_min, y_min, x_max, y_max, cor)
REGIOES = [
    (30, 0, 70, 40, (100, 180, 100)),    # Lobby (Verde claro)
    (10, 50, 90, 130, (34, 139, 34)),    # Floresta (Verde escuro)
    (110, 50, 190, 130, (230, 210, 150)), # Deserto (Bege)
    (60, 140, 140, 190, (150, 150, 150))  # Ruínas (Cinza)
]

# Monstros (home_x, home_y)
MONSTROS = [
    (50, 90, 'Slime'), (150, 90, 'Goblin'), (100, 165, 'Esqueleto')
]

# NPCs (x, y)
NPCS = [(44, 9, 'Mercador'), (42, 10, 'Ferreiro'), (46, 10, 'Alquimista')]

img = Image.new('RGB', (LARGURA * ESCALA, ALTURA * ESCALA), (20, 20, 20))
draw = ImageDraw.Draw(img)

# 1. Desenhar as Regiões
for (x1, y1, x2, y2, cor) in REGIOES:
    draw.rectangle([x1*ESCALA, y1*ESCALA, x2*ESCALA, y2*ESCALA], fill=cor)

# 2. Desenhar os Monstros (Vermelho)
for (mx, my, nome) in MONSTROS:
    draw.ellipse([mx*ESCALA-4, my*ESCALA-4, mx*ESCALA+4, my*ESCALA+4], fill=(255, 50, 50), outline=(255,255,255))

# 3. Desenhar os NPCs (Amarelo)
for (nx, ny, nome) in NPCS:
    draw.ellipse([nx*ESCALA-4, ny*ESCALA-4, nx*ESCALA+4, ny*ESCALA+4], fill=(255, 215, 0), outline=(255,255,255))

# 4. Grade a cada 10 tiles
for i in range(0, LARGURA, 10):
    draw.line([(i*ESCALA, 0), (i*ESCALA, ALTURA*ESCALA)], fill=(40, 40, 40), width=1)
    draw.line([(0, i*ESCALA), (LARGURA*ESCALA, i*ESCALA)], fill=(40, 40, 40), width=1)

img.save(OUT)
print("✅ Mapa conceitual gerado!")
print("👉 Acesse: http://127.0.0.1:5000/static/mapa_conceito.png")
