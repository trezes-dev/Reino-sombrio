import re

html = open("templates/index.html").read()

# Backup
open("templates/index.html.bkp", "w").write(html)
print("Backup: templates/index.html.bkp")

# 1) CSS
css_add = """
#joystick { position:fixed; left:20px; bottom:90px; width:140px; height:140px; z-index:25; touch-action:none; }
#joy-base { position:absolute; inset:0; border-radius:50%; background:radial-gradient(circle, rgba(74,246,255,0.15), rgba(74,246,255,0.05)); border:3px solid rgba(74,246,255,0.5); box-shadow:0 0 20px rgba(74,246,255,0.3), inset 0 0 20px rgba(74,246,255,0.15); }
#joy-thumb { position:absolute; top:50%; left:50%; width:60px; height:60px; margin:-30px 0 0 -30px; border-radius:50%; background:radial-gradient(circle, #4af6ff, #2a90a0); box-shadow:0 0 15px #4af6ff, inset 0 0 8px rgba(255,255,255,0.5); }
#botoes-acao { position:fixed; right:20px; bottom:70px; width:170px; height:170px; z-index:25; }
.btn-acao { position:absolute; border-radius:50%; border:3px solid; display:flex; align-items:center; justify-content:center; cursor:pointer; user-select:none; box-shadow:0 4px 12px rgba(0,0,0,0.5); font-size:28px; }
#btn-ataque { right:0; bottom:0; width:74px; height:74px; background:radial-gradient(circle, #ff5566, #a02030); border-color:#ff8899; }
#btn-ferramenta { right:58px; bottom:58px; width:62px; height:62px; font-size:22px; background:radial-gradient(circle, #ffd700, #a08000); border-color:#ffee88; }
#btn-acao { right:0; bottom:58px; width:62px; height:62px; font-size:22px; background:radial-gradient(circle, #4af6ff, #1a6a80); border-color:#88e8ff; }
.dano-flutuante { position:absolute; z-index:10; font-weight:bold; font-size:16px; pointer-events:none; animation: subirDano 1s ease-out forwards; text-shadow: 2px 2px 0 #000, -1px -1px 0 #000; }
@keyframes subirDano { 0% { transform:translateY(0); opacity:1; } 100% { transform:translateY(-40px); opacity:0; } }
.dano-flutuante.dano { color:#ff4466; }
.dano-flutuante.info { color:#4af6ff; font-size:12px; }
"""
if "#joystick" not in html:
    html = html.replace("</style>", css_add + "</style>")
    print("OK: CSS adicionado")

# 2) HTML - remove .ctrl, adiciona joystick + botões
old = re.search(r'<div class="ctrl">.*?</div>\s*</div>', html, re.DOTALL)
if old and "id=\"joystick\"" not in old.group(0):
    novo = '''<div id="joystick">
    <div id="joy-base"></div>
    <div id="joy-thumb"></div>
  </div>
  <div id="botoes-acao">
    <button class="btn-acao" id="btn-ferramenta" onclick="usarFerramenta()">🧪</button>
    <button class="btn-acao" id="btn-acao" onclick="acaoInteragir()">✋</button>
    <button class="btn-acao" id="btn-ataque" onclick="atacar()">⚔️</button>
  </div>'''
    html = html.replace(old.group(0), novo)
    print("OK: HTML substituido")
else:
    print("AVISO: nao achei .ctrl")

# 3) JS - insere antes de carregar();
js_add = '''
(function() {
  const joy = document.getElementById("joystick");
  if (!joy) return;
  const thumb = document.getElementById("joy-thumb");
  let ativo = false, idToque = null, cx = 0, cy = 0;
  const raio = 45;
  let direcaoAtual = null, ultimoMov = 0;
  function resetar() { ativo=false; idToque=null; thumb.style.transform="translate(0,0)"; direcaoAtual=null; }
  joy.addEventListener("touchstart", (e) => {
    e.preventDefault();
    const t = e.changedTouches[0];
    idToque = t.identifier;
    const r = joy.getBoundingClientRect();
    cx = r.left + r.width/2; cy = r.top + r.height/2;
    ativo = true;
    movendo(t.clientX, t.clientY);
  }, {passive:false});
  joy.addEventListener("touchmove", (e) => {
    e.preventDefault();
    for (const t of e.changedTouches) if (t.identifier === idToque) movendo(t.clientX, t.clientY);
  }, {passive:false});
  joy.addEventListener("touchend", (e) => {
    for (const t of e.changedTouches) if (t.identifier === idToque) resetar();
  });
  joy.addEventListener("touchcancel", resetar);
  function movendo(px, py) {
    let dx = px - cx, dy = py - cy;
    const dist = Math.hypot(dx, dy);
    if (dist > raio) { dx = dx/dist*raio; dy = dy/dist*raio; }
    thumb.style.transform = `translate(${dx}px, ${dy}px)`;
    if (dist < 10) { direcaoAtual = null; return; }
    let novaDir;
    if (Math.abs(dx) > Math.abs(dy)) novaDir = dx > 0 ? "dir" : "esq";
    else novaDir = dy > 0 ? "baixo" : "cima";
    if (novaDir !== direcaoAtual || Date.now() - ultimoMov > 180) {
      direcaoAtual = novaDir;
      ultimoMov = Date.now();
      mover(novaDir);
    }
  }
  setInterval(() => {
    if (ativo && direcaoAtual && Date.now() - ultimoMov > 180) {
      ultimoMov = Date.now();
      mover(direcaoAtual);
    }
  }, 160);
})();

async function atacar() {
  const r = await fetch("/api/atacar");
  const j = await r.json();
  document.getElementById("log").textContent = j.msg;
  if (j.estado) render(j.estado);
}
async function usarFerramenta() { await pocao(); }
function acaoInteragir() { document.getElementById("log").textContent = "Nada para interagir aqui"; }
'''
if "async function atacar()" not in html:
    html = html.replace("carregar();", js_add + "\ncarregar();")
    print("OK: JS adicionado")
else:
    print("AVISO: JS ja existe")

open("templates/index.html", "w").write(html)
print("index.html salvo (" + str(len(html)) + " bytes)")
