from PIL import Image, ImageDraw
import sqlite3, os, math, random

DB = os.path.expanduser('~/rpg/rpg.db')
OUT_IMG = os.path.expanduser('~/rpg/static/mapa_coa.png')
LARGURA, ALTURA = 200, 200

# Cores base para o debug
CORES = {
    'grama_lobby': (100, 180, 100),
    'grama_floresta': (34, 139, 34),
    'areia_deserto': (230, 210, 150),
    'pedra_ruinas': (150, 150, 150),
    'terra_caminho': (139, 69, 19)
}

img = Image.new('RGB', (LARGURA, ALTURA), CORES['grama_floresta'])
draw = ImageDraw.Draw(img)

print("⏳ Gerando o mundo (isso pode levar alguns segundos)...")

# Função para descobrir o tipo de terreno baseado na posição (x, y)
def obter_terreno(x, y):
    # Distância do centro do mapa (100, 100)
    dist = math.sqrt((x - 100)**2 + (y - 100)**2)
    
    # Adiciona ruído para as bordas não serem perfeitas
    ruido = random.uniform(-15, 15)
    dist_ruidosa = dist + ruido
    
    # Ângulo para dividir as áreas (0 a 360 graus)
    angulo = math.degrees(math.atan2(y - 100, x - 100))
    
    # Lógica das Regiões
    if dist_ruidosa < 25:
        return 'grama_lobby'       # Centro: Cidade Principal
    elif dist_ruidosa < 70:
        return 'grama_floresta'    # Anel intermediário: Floresta
    else:
        # Divisão externa: Direita = Deserto, Esquerda = Ruínas
        if angulo > 0 and angulo < 180:
            return 'areia_deserto'
        else:
            return 'pedra_ruinas'

# 1. Preencher o mapa com os terrenos
grade = {}
for x in range(LARGURA):
    for y in range(ALTURA):
        tipo = obter_terreno(x, y)
        grade[(x, y)] = tipo
        draw.point((x, y), fill=CORES[tipo])

# 2. Desenhar Caminhos (Estradas de terra saindo do centro)
# Para o Norte, Sul, Leste e Oeste
for i in range(25, 100):
    # Norte
    if i < ALTURA: grade[(100, i)] = 'terra_caminho'; draw.point((100, i), fill=CORES['terra_caminho'])
    # Sul
    if i < ALTURA: grade[(100, ALTURA - i)] = 'terra_caminho'; draw.point((100, ALTURA - i), fill=CORES['terra_caminho'])
    # Leste
    if i < LARGURA: grade[(i, 100)] = 'terra_caminho'; draw.point((i, 100), fill=CORES['terra_caminho'])
    # Oeste
    if i < LARGURA: grade[(LARGURA - i, 100)] = 'terra_caminho'; draw.point((LARGURA - i, 100), fill=CORES['terra_caminho'])

img.save(OUT_IMG)
print("✅ Imagem do mapa contínuo gerada! Veja em: http://127.0.0.1:5000/static/mapa_coa.png")

# --- SALVAR NO BANCO DE DADOS ---
print("💾 Salvando tiles e espalhando objetos...")
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("DELETE FROM mapa_tiles")
cursor.execute("DELETE FROM mapa_objetos")

for (x, y), tipo in grade.items():
    cursor.execute("INSERT INTO mapa_tiles (x, y, tipo) VALUES (?, ?, ?)", (x, y, tipo))
    
    # Espalhar objetos (Árvores, pedras, etc) se não for caminho
    if tipo != 'terra_caminho' and random.random() < 0.15: # 15% de chance
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
print("✅ Mundo gerado e salvo no banco de dados com sucesso!")
