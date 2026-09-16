html = open("templates/index.html").read()

# 1) Adiciona pausa quando a aba está escondida
if "document.hidden" not in html:
    html = html.replace(
        "setInterval(async () => {",
        """function _ativo() { return !document.hidden; }
setInterval(async () => {
  if (!_ativo()) return;"""
    )
    # adiciona em todos os setInterval
    html = html.replace(
        "setInterval(() => { carregarChat(false); }, 4000);",
        "setInterval(() => { if (!_ativo()) return; carregarChat(false); }, 4000);"
    )
    print("OK: pausa quando aba escondida")

# 2) Aumenta o intervalo de estado pra 3s (era 2 ou 4s)
html = html.replace(
    'setInterval(async () => {\n  if (!_ativo()) return;\n  try {\n    const r = await fetch("/api/estado");\n    if (r.ok) render(await r.json());\n  } catch(e) {}\n}, 2000);',
    'setInterval(async () => {\n  if (!_ativo()) return;\n  if (_movendo) return;\n  try {\n    const r = await fetch("/api/estado");\n    if (r.ok) render(await r.json());\n  } catch(e) {}\n}, 3000);'
)

# 3) Throttle do chat
html = html.replace(
    "setInterval(() => { if (!_ativo()) return; carregarChat(false); }, 4000);",
    "setInterval(() => { if (!_ativo()) return; if (_movendo) return; carregarChat(false); }, 4000);"
)

# 4) Throttle global de fetch no mover - impede fila
html = html.replace(
    'if (Date.now() - _ultimoMover < 200) return;',
    'if (Date.now() - _ultimoMover < 280) return;'
)

open("templates/index.html", "w").write(html)
print("index.html salvo")
