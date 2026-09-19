from PIL import Image, ImageDraw, ImageFont
import os, glob

BASE = os.path.expanduser('~/rpg/static/sprites/terreno')

# Regiões para gerar contato
REGIOES = {
    'ruinas':   os.path.join(BASE, 'ruinas/Tiles'),
    'lobby':    os.path.join(BASE, 'lobby/Tiles'),
    'floresta': os.path.join(BASE, 'floresta/usaveis'),
    'deserto':  os.path.join(BASE, 'deserto/usaveis'),
}

def gerar_contato(nome_regiao, pasta):
    if not os.path.isdir(pasta):
        print(f"⚠️  Pasta não existe: {pasta}")
        return
    
    arquivos = sorted(glob.glob(os.path.join(pasta, '*.png')))
    if not arquivos:
        print(f"⚠️  Nenhum PNG em {pasta}")
        return
    
    # Limita a 80 tiles para caber na imagem
    arquivos = arquivos[:80]
    
    COLS = 10
    TAM = 32   # tamanho de cada célula
    PAD = 2
    LABEL_H = 10
    
    linhas = (len(arquivos) + COLS - 1) // COLS
    largura = COLS * (TAM + PAD) + PAD
    altura = linhas * (TAM + LABEL_H + PAD) + PAD
    
    img = Image.new('RGB', (largura, altura), (40, 40, 40))
    draw = ImageDraw.Draw(img)
    
    for i, caminho in enumerate(arquivos):
        col = i % COLS
        lin = i // COLS
        x = PAD + col * (TAM + PAD)
        y = PAD + lin * (TAM + LABEL_H + PAD)
        
        try:
            tile = Image.open(caminho).convert('RGBA')
            # Redimensiona mantendo pixels nítidos
            tile = tile.resize((TAM, TAM), Image.Resampling.NEAREST)
            # Cola com fundo xadrez para ver transparência
            fundo = Image.new('RGBA', (TAM, TAM), (60, 60, 60, 255))
            # Xadrez
            for xx in range(0, TAM, 8):
                for yy in range(0, TAM, 8):
                    if (xx // 8 + yy // 8) % 2 == 0:
                        for dx in range(8):
                            for dy in range(8):
                                if xx+dx < TAM and yy+dy < TAM:
                                    fundo.putpixel((xx+dx, yy+dy), (90, 90, 90, 255))
            fundo.paste(tile, (0, 0), tile)
            img.paste(fundo.convert('RGB'), (x, y))
        except Exception as e:
            draw.rectangle([x, y, x+TAM, y+TAM], fill=(200, 50, 50))
        
        # Nome do arquivo (só o número)
        nome = os.path.basename(caminho).replace('.png', '')
        # Extrai só o número
        num = ''.join(filter(str.isdigit, nome))
        texto = num[-3:] if num else nome[:4]
        
        draw.text((x + 2, y + TAM), texto, fill=(255, 255, 255))
    
    out = os.path.expanduser(f'~/rpg/static/contato_{nome_regiao}.png')
    img.save(out)
    print(f"✅ {nome_regiao}: {len(arquivos)} tiles → http://127.0.0.1:5000/static/contato_{nome_regiao}.png")

print("🎨 Gerando folhas de contato...")
for nome, pasta in REGIOES.items():
    gerar_contato(nome, pasta)
print("\n✅ Pronto! Abra as URLs acima no navegador.")
