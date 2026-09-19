from PIL import Image, ImageEnhance
import os, shutil, glob

BASE = os.path.expanduser('~/rpg/static/sprites/terreno')
DEST = os.path.join(BASE, 'chao')
os.makedirs(DEST, exist_ok=True)

def achar_tile(pasta, numero):
    """Procura um tile pelo número, testando 3 e 4 dígitos."""
    for formato in [f'tile_{numero:04d}.png', f'tile_{numero:03d}.png', f'tile_{numero}.png']:
        caminho = os.path.join(pasta, formato)
        if os.path.exists(caminho):
            return caminho
    return None

# Descobre qual formato está sendo usado
print("🔍 Detectando formato dos arquivos...")
amostras_lobby = sorted(glob.glob(os.path.join(BASE, 'lobby/Tiles/tile_*.png')))[:3]
amostras_ruinas = sorted(glob.glob(os.path.join(BASE, 'ruinas/Tiles/tile_*.png')))[:3]
print(f"  LOBBY:  {[os.path.basename(a) for a in amostras_lobby]}")
print(f"  RUÍNAS: {[os.path.basename(a) for a in amostras_ruinas]}")

# Buscar tiles específicos (tenta vários números até achar)
def achar_primeiro_disponivel(pasta, numeros):
    for n in numeros:
        caminho = achar_tile(pasta, n)
        if caminho:
            return caminho
    return None

TILE_GRAM = achar_primeiro_disponivel(os.path.join(BASE, 'lobby/Tiles'), [0, 1])
TILE_AREIA = achar_primeiro_disponivel(os.path.join(BASE, 'ruinas/Tiles'), [30, 48, 49, 50, 51, 52, 53, 54])
TILE_PEDRA = achar_primeiro_disponivel(os.path.join(BASE, 'ruinas/Tiles'), [36, 37, 38, 39, 40, 14])
TILE_TERRA = achar_primeiro_disponivel(os.path.join(BASE, 'ruinas/Tiles'), [0, 1, 2, 3])

print(f"\n📌 Encontrados:")
print(f"  Grama:  {os.path.basename(TILE_GRAM) if TILE_GRAM else 'NÃO ACHOU'}")
print(f"  Areia:  {os.path.basename(TILE_AREIA) if TILE_AREIA else 'NÃO ACHOU'}")
print(f"  Pedra:  {os.path.basename(TILE_PEDRA) if TILE_PEDRA else 'NÃO ACHOU'}")
print(f"  Terra:  {os.path.basename(TILE_TERRA) if TILE_TERRA else 'NÃO ACHOU'}")

if not all([TILE_GRAM, TILE_AREIA, TILE_PEDRA, TILE_TERRA]):
    print("\n❌ Faltou algum tile. Me manda a saída acima.")
    exit(1)

# 1. Grama Normal
shutil.copy(TILE_GRAM, os.path.join(DEST, 'grama_normal.png'))
print("\n✅ grama_normal.png")

# 2. Grama Escura
grama = Image.open(TILE_GRAM).convert('RGBA')
grama_escura = ImageEnhance.Brightness(grama).enhance(0.45)
grama_escura.save(os.path.join(DEST, 'grama_escura.png'))
print("✅ grama_escura.png")

# 3. Lobby (clarear)
grama_lobby = ImageEnhance.Brightness(grama).enhance(1.5)
grama_lobby = ImageEnhance.Color(grama_lobby).enhance(1.3)
grama_lobby.save(os.path.join(DEST, 'grama_lobby.png'))
print("✅ grama_lobby.png")

# 4. Areia
shutil.copy(TILE_AREIA, os.path.join(DEST, 'areia_deserto.png'))
print("✅ areia_deserto.png")

# 5. Pedra/Ruínas
shutil.copy(TILE_PEDRA, os.path.join(DEST, 'pedra_ruinas.png'))
print("✅ pedra_ruinas.png")

# 6. Terra/Caminho
shutil.copy(TILE_TERRA, os.path.join(DEST, 'terra_caminho.png'))
print("✅ terra_caminho.png")

print(f"\n📁 Arquivos em: {DEST}")
