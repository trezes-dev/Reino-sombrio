import json, sqlite3, os, random

DB = os.path.expanduser('~/rpg/rpg.db')
MAP_JSON = os.path.expanduser('~/repos_estudo/BrowserQuest/client/maps/world_client.json')

with open(MAP_JSON) as f:
    data = json.load(f)

LARGURA = data['width']    # 172
ALTURA  = data['height']   # 314
valores = data['data']

print(f"Mapa: {LARGURA}x{ALTURA} = {LARGURA*ALTURA} tiles")

# Reconstrói a matriz 2D
matriz = []
idx = 0
for y in range(ALTURA):
    linha = []
    for x in range(LARGURA):
        if idx >= len(valores):
            linha.append(0)
            continue
        v = valores[idx]
        idx += 1
        if isinstance(v, list):
            # Pega o primeiro valor (chão base)
            linha.append(v[0] if v else 0)
        else:
            linha.append(v)
    matriz.append(linha)

print(f"Matriz reconstruída: {len(matriz)}x{len(matriz[0])}")

# Classifica cada valor em um tipo de bioma
# Estratégia: usa histograma de cores para decidir o tipo do tile
def classificar(v):
    """Mapeia valor do BrowserQuest para tipo do Reino Sombrio."""
    if v < 0:
        return 'agua'
    # Baseado nos valores observados e na lógica do BrowserQuest:
    # Valores baixos (0-100) = grama/floresta
    # Valores médios (100-300) = terra/areia
    # Valores altos (300-600) = pedra/estruturas
    # Muito altos (600+) = água, montanhas
    if v < 50:
        return 'grama_floresta'
    elif v < 150:
        return 'grama_escura'
    elif v < 250:
        return 'areia_deserto'
    elif v < 400:
        return 'pedra_ruinas'
    elif v < 500:
        return 'terra_caminho'
    else:
        return 'grama_floresta'

# Salva no banco
conn = sqlite3.connect(DB)
cursor = conn.cursor()

# Limpa o mapa antigo
cursor.execute("DELETE FROM mapa_tiles")
print("🧹 Mapa antigo limpo")

# Insere os novos tiles
contagem = {}
for y, linha in enumerate(matriz):
    for x, v in enumerate(linha):
        tipo = classificar(v)
        contagem[tipo] = contagem.get(tipo, 0) + 1
        cursor.execute(
            "INSERT INTO mapa_tiles (x, y, tipo) VALUES (?, ?, ?)",
            (x, y, tipo)
        )

conn.commit()
conn.close()

print(f"\n✅ Mapa do BrowserQuest convertido!")
for tipo, qtd in sorted(contagem.items()):
    print(f"  {tipo}: {qtd} tiles")

print(f"\n💡 Próximos passos:")
print(f"  1. Atualizar server.py: W_MAP = {LARGURA}, H_MAP = {ALTURA}")
print(f"  2. Reiniciar o servidor")
print(f"  3. Testar no jogo")
