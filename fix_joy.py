html = open("templates/index.html").read()

# 1) Adiciona trava de requisição
if "let _movendo = false;" not in html:
    html = html.replace(
        'let J = null;',
        'let J = null;\nlet _movendo = false;\nlet _ultimoMover = 0;'
    )

# 2) Substitui a função mover por versão com trava
old_mover = 'async function mover(dir) { const r = await fetch("/api/mover/" + dir); const j = await r.json(); document.getElementById("log").textContent = j.msg; render(j.estado); }'
new_mover = '''async function mover(dir) {
  if (_movendo) return;
  if (Date.now() - _ultimoMover < 200) return;
  _movendo = true;
  _ultimoMover = Date.now();
  try {
    const r = await fetch("/api/mover/" + dir);
    const j = await r.json();
    document.getElementById("log").textContent = j.msg;
    if (j.estado) render(j.estado);
  } catch(e) {}
  _movendo = false;
}'''
if old_mover in html:
    html = html.replace(old_mover, new_mover)
    print("OK: mover com throttle")

# 3) Reduz o setInterval do joystick de 160 pra 250ms
html = html.replace('}, 160);', '}, 250);')

# 4) Aumenta throttle interno do joystick
html = html.replace('Date.now() - ultimoMov > 180', 'Date.now() - ultimoMov > 250')

# 5) Reduz polling geral de 2s pra 4s (alivia o servidor)
html = html.replace('}, 2000);\nsetInterval(() => { carregarChat(false); }, 2000);', '}, 4000);\nsetInterval(() => { carregarChat(false); }, 4000);')

open("templates/index.html", "w").write(html)
print("index.html salvo")
