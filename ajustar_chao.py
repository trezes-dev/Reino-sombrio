from PIL import Image, ImageEnhance
import os, shutil

BASE = os.path.expanduser('~/rpg/static/sprites/terreno')
DEST = os.path.join(BASE, 'chao')
RUINAS = os.path.join(BASE, 'ruinas/Tiles')
LOBBY = os.path.join(BASE, 'lobby/Tiles')

def t(num):
    return os.path.join(RUINAS, f'tile_{num:04d}.png')

# --- NOVOS TILES ESCOLHIDOS ---
# Areia: tile 048 ou 049 (tons de laranja claro)
# Pedra: tile 057 ou 058 (tijolos cinzas)
TILE_AREIA_NOVA = t(48)
TILE_PEDRA_NOVA = t(57)

# Verifica se existem
if not os.path.exists(TILE_AREIA_NOVA):
    print(f"⚠️ Não achei {TILE_AREIA_NOVA}, tentando 49...")
    TILE_AREIA_NOVA = t(49)

if not os.path.exists(TILE_PEDRA_NOVA):
    print(f"⚠️ Não achei {TILE_PEDRA_NOVA}, tentando 58...")
    TILE_PEDRA_NOVA = t(58)

print(f"📌 Areia nova: {os.path.basename(TILE_AREIA_NOVA)}")
print(f"📌 Pedra nova: {os.path.basename(TILE_PEDRA_NOVA)}")

# 1. Areia (cópia direta)
shutil.copy(TILE_AREIA_NOVA, os.path.join(DEST, 'areia_deserto.png'))
print("✅ areia_deserto.png")

# 2. Pedra (cópia direta)
shutil.copy(TILE_PEDRA_NOVA, os.path.join(DEST, 'pedra_ruinas.png'))
print("✅ pedra_ruinas.png")

# 3. Lobby - refazer com cor mais suave (grama um pouco mais clara)
grama = Image.open(os.path.join(LOBBY, 'tile_0000.png')).convert('RGBA')
grama_lobby = ImageEnhance.Brightness(grama).enhance(1.25)
grama_lobby = ImageEnhance.Color(grama_lobby).enhance(1.1)
grama_lobby.save(os.path.join(DEST, 'grama_lobby.png'))
print("✅ grama_lobby.png (refeito, mais suave)")

print("\n✅ Pronto! Rode agora: python3 ~/rpg/ver_chao.py")
