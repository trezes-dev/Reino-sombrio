html = open("templates/index.html").read()

# 1) CSS: cada classe tem seu sprite
old_css = ".tile.player { background-image: url('/static/sprites/player.png'); box-shadow: 0 0 10px #4af6ff; z-index: 2; }"
new_css = """.tile.player { background-image: url('/static/sprites/player.png'); box-shadow: 0 0 10px #4af6ff; z-index: 2; }
.tile.player.classe-cavaleiro { background-image: url('/static/sprites/player-cavaleiro.png'); }
.tile.player.classe-arqueiro { background-image: url('/static/sprites/player-arqueiro.png'); }
.tile.player.classe-mago { background-image: url('/static/sprites/player-mago.png'); }"""

if ".tile.player.classe-cavaleiro" not in html:
    html = html.replace(old_css, new_css)
    print("OK: CSS das classes adicionado")

# 2) Render: adicionar classe do jogador no tile
old_render = '''      if (xx === j.x && yy === j.y) {
        d.className = "tile player";
      } else if (mons.has(xx + "," + yy)) {'''
new_render = '''      if (xx === j.x && yy === j.y) {
        d.className = "tile player classe-" + (j.classe || "cavaleiro");
      } else if (mons.has(xx + "," + yy)) {'''
if old_render in html:
    html = html.replace(old_render, new_render)
    print("OK: render da classe atualizado")
else:
    print("AVISO: render nao bateu")

open("templates/index.html", "w").write(html)
print("index.html salvo")
