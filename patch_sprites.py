html = open("templates/index.html").read()

# 1) CSS: adicionar background-image nos tiles
css_novo = """
.tile {
  background-size: cover;
  background-position: center;
  image-rendering: pixelated;
  background-color: #2d5a1e;
}
.tile.grama { background-image: url('/static/sprites/grama.png'); }
.tile.agua { background-image: url('/static/sprites/agua.png'); }
.tile.arvore { background-image: url('/static/sprites/arvore.png'); }
.tile.pedra { background-image: url('/static/sprites/pedra.png'); }
.tile.monstro { background-image: url('/static/sprites/monstro.png'); background-color: transparent; }
.tile.npc { background-image: url('/static/sprites/npc.png'); background-color: transparent; box-shadow: none; }
.tile.player { background-image: url('/static/sprites/player.png'); background-color: transparent; box-shadow: 0 0 10px #4af6ff; }
.tile.outro { background-color: transparent; }
.tile.outro .sprite-outro { width: 100%; height: 100%; background-image: url('/static/sprites/player.png'); background-size: cover; image-rendering: pixelated; }
"""

# Substituir CSS antigo dos tiles
html = html.replace(
    ".tile { width:28px; height:28px; background:#222; border-radius:3px; }",
    ".tile { width:28px; height:28px; border-radius:3px; }" + css_novo
)

# 2) Substituir o render do mapa principal
old_render = '''  for (let yy = 0; yy < j.H; yy++) {
    for (let xx = 0; xx < j.W; xx++) {
      const d = document.createElement("div");
      d.className = "tile";
      if (xx === j.x && yy === j.y) d.className += " player";
      else if (mons.has(xx + "," + yy)) d.className += " monstro";
      else if (npcs.has(xx + "," + yy)) d.className += " npc";
      else if (outros.has(xx + "," + yy)) {
        d.className += " outro";
        const o = mapaOutros[xx + "," + yy];
        d.style.background = o.cor;
        d.title = (o.badge || "") + " " + o.nome;
      }
      mapa.appendChild(d);
    }
  }'''

new_render = '''  for (let yy = 0; yy < j.H; yy++) {
    for (let xx = 0; xx < j.W; xx++) {
      const d = document.createElement("div");
      d.className = "tile grama";
      if (xx === j.x && yy === j.y) {
        d.className = "tile player";
      } else if (mons.has(xx + "," + yy)) {
        d.className = "tile monstro";
      } else if (npcs.has(xx + "," + yy)) {
        d.className = "tile npc";
      } else if (outros.has(xx + "," + yy)) {
        d.className = "tile outro";
        const o = mapaOutros[xx + "," + yy];
        d.style.background = o.cor;
        d.style.opacity = "0.85";
        d.title = (o.badge || "") + " " + o.nome;
      }
      mapa.appendChild(d);
    }
  }'''

if old_render in html:
    html = html.replace(old_render, new_render)
    print("OK: render do mapa substituido")
else:
    print("AVISO: render do mapa nao bateu")

open("templates/index.html", "w").write(html)
print("index.html salvo")
