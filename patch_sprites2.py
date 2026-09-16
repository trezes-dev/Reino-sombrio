html = open("templates/index.html").read()

# Remove as regras antigas que deixam transparente
html = html.replace(
    ".tile.monstro { background-image: url('/static/sprites/monstro.png'); background-color: transparent; }",
    ".tile.monstro { background-image: url('/static/sprites/monstro.png'); }"
)
html = html.replace(
    ".tile.npc { background-image: url('/static/sprites/npc.png'); background-color: transparent; box-shadow: none; }",
    ".tile.npc { background-image: url('/static/sprites/npc.png'); box-shadow: none; }"
)
html = html.replace(
    ".tile.player { background-image: url('/static/sprites/player.png'); background-color: transparent; box-shadow: 0 0 10px #4af6ff; }",
    ".tile.player { background-image: url('/static/sprites/player.png'); box-shadow: 0 0 10px #4af6ff; z-index: 2; }"
)

open("templates/index.html", "w").write(html)
print("OK - patch aplicado")
