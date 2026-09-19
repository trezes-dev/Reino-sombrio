from PIL import Image, ImageDraw
import os, glob

BASE = os.path.expanduser('~/rpg/static/sprites/terreno/chao')
arquivos = sorted(glob.glob(os.path.join(BASE, '*.png')))

if not arquivos:
    print(f"❌ Nenhum PNG em: {BASE}")
    exit(1)

print(f"📁 Encontrados {len(arquivos)} arquivos em {BASE}")

TAM = 64
PAD = 15
LABEL_H = 14
COLS = 2
linhas = (len(arquivos) + COLS - 1) // COLS

largura = COLS * (TAM + PAD) + PAD
altura = linhas * (TAM + LABEL_H + PAD) + PAD

img = Image.new('RGB', (largura, altura), (40, 40, 40))
draw = ImageDraw.Draw(img)

for i, arq in enumerate(arquivos):
    col = i % COLS
    lin = i // COLS
    x = PAD + col * (TAM + PAD)
    y = PAD + lin * (TAM + LABEL_H + PAD)
    
    try:
        tile = Image.open(arq).convert('RGBA')
        tile = tile.resize((TAM, TAM), Image.Resampling.NEAREST)
        fundo = Image.new('RGBA', (TAM, TAM), (60, 60, 60, 255))
        fundo.paste(tile, (0, 0), tile)
        img.paste(fundo.convert('RGB'), (x, y))
    except Exception as e:
        draw.rectangle([x, y, x + TAM, y + TAM], fill=(200, 50, 50))
        print(f"⚠️ Erro lendo {arq}: {e}")
    
    nome = os.path.basename(arq).replace('.png', '')
    draw.text((x + 2, y + TAM + 2), nome, fill=(255, 255, 255))

out = os.path.expanduser('~/rpg/static/chao_final.png')
img.save(out)
print(f"\n✅ Gerado com sucesso!")
print(f"👉 Acesse: http://127.0.0.1:5000/static/chao_final.png")
