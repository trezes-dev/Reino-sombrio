html = open("templates/index.html").read()

# 1) CSS do painel de perfil
css = """
#btn-perfil {
  padding: 8px 12px; background: #222; color: #a06bff;
  border: 1px solid #a06bff; border-radius: 6px;
  text-decoration: none; font-size: 11px; font-family: inherit;
  cursor: pointer;
}
#perfil-painel {
  position: fixed; inset: 0; z-index: 50;
  background: rgba(0,0,0,0.95);
  display: none; padding: 20px; overflow-y: auto;
}
#perfil-painel.aberto { display: flex; flex-direction: column; }
#perfil-card {
  max-width: 500px; width: 100%; margin: auto;
  background: #10142a;
  border: 3px solid #a06bff;
  box-shadow: 0 0 0 3px #10142a, 0 0 0 6px #4af6ff, 0 0 30px rgba(160,107,255,0.5);
  padding: 20px; border-radius: 4px;
}
#perfil-card h2 {
  font-size: 15px; color: #4af6ff; margin: 0 0 16px; text-align: center;
  text-shadow: 2px 2px 0 #a06bff; letter-spacing: 2px;
}
#perfil-top {
  display: flex; gap: 16px; align-items: flex-start;
  margin-bottom: 16px; border-bottom: 1px solid #2a2a4a; padding-bottom: 16px;
}
#perfil-avatar {
  width: 80px; height: 80px; background: #05070f;
  border: 2px solid #4af6ff; border-radius: 8px;
  background-size: cover; background-position: center;
  image-rendering: pixelated;
  box-shadow: 0 0 10px rgba(74,246,255,0.5);
  flex-shrink: 0;
}
#perfil-info { flex: 1; }
#perfil-nome {
  font-size: 14px; font-weight: bold; margin-bottom: 4px;
  text-shadow: 0 0 6px currentColor;
}
#perfil-classe {
  font-size: 11px; color: #a0a0c0; margin-bottom: 4px;
}
#perfil-classe b { color: #4af6ff; }
#perfil-cargo {
  font-size: 10px; display: inline-block;
  padding: 2px 8px; border-radius: 3px; border: 1px solid;
  margin-top: 4px;
}
.perfil-bar {
  height: 16px; background: #05070f; border: 2px solid #2a3050;
  border-radius: 3px; overflow: hidden; position: relative;
  margin-bottom: 4px;
}
.perfil-bar .fill {
  height: 100%; transition: width 0.4s;
}
.perfil-bar .txt {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 9px; color: #fff; text-shadow: 1px 1px 2px #000; font-weight: bold;
  z-index: 2;
}
.perfil-bar.hp .fill { background: linear-gradient(90deg, #c33, #ff5566); }
.perfil-bar.xp .fill { background: linear-gradient(90deg, #4af6ff, #a06bff); }
.perfil-linha {
  display: flex; justify-content: space-between;
  font-size: 11px; padding: 6px 0;
  border-bottom: 1px dashed #2a2a4a;
}
.perfil-linha:last-child { border-bottom: none; }
.perfil-linha .label { color: #888; }
.perfil-linha .valor { color: #eee; font-weight: bold; }
#perfil-titulo-secao {
  font-size: 10px; color: #a06bff; margin: 14px 0 6px;
  letter-spacing: 2px; border-bottom: 1px solid #2a2a4a; padding-bottom: 4px;
}
#perfil-fechar {
  width: 100%; padding: 12px; margin-top: 16px;
  background: #4af6ff; color: #0a0a1a;
  border: none; border-radius: 6px;
  font-family: inherit; font-size: 12px; font-weight: bold;
  cursor: pointer; letter-spacing: 1px;
}
"""

if "#perfil-painel" not in html:
    html = html.replace("</style>", css + "</style>")
    print("OK: CSS perfil adicionado")

# 2) Botão Perfil na top bar
old_botoes = '''    <a class="painel" href="/painel">🛡️ Painel</a>
    <a class="sair" href="/logout">Sair</a>'''
new_botoes = '''    <button id="btn-perfil" onclick="abrirPerfil()">👤 Perfil</button>
    <a class="painel" href="/painel">🛡️ Painel</a>
    <a class="sair" href="/logout">Sair</a>'''
if "btn-perfil" not in html:
    html = html.replace(old_botoes, new_botoes)
    print("OK: botao Perfil adicionado")

# 3) Painel de perfil (HTML)
painel = '''
<div id="perfil-painel">
  <div id="perfil-card">
    <h2>👤 PERSONAGEM</h2>
    <div id="perfil-top">
      <div id="perfil-avatar"></div>
      <div id="perfil-info">
        <div id="perfil-nome"></div>
        <div id="perfil-classe"></div>
        <div id="perfil-cargo"></div>
      </div>
    </div>
    <div id="perfil-titulo-secao">❤️ VIDA</div>
    <div class="perfil-bar hp">
      <div class="fill" id="perfil-hp-fill"></div>
      <div class="txt" id="perfil-hp-txt">0/0</div>
    </div>
    <div id="perfil-titulo-secao">⭐ EXPERIENCIA</div>
    <div class="perfil-bar xp">
      <div class="fill" id="perfil-xp-fill"></div>
      <div class="txt" id="perfil-xp-txt">0/0</div>
    </div>
    <div id="perfil-titulo-secao">📊 ATRIBUTOS</div>
    <div class="perfil-linha"><span class="label">Nivel</span><span class="valor" id="perfil-nivel">-</span></div>
    <div class="perfil-linha"><span class="label">Classe</span><span class="valor" id="perfil-classe-txt">-</span></div>
    <div class="perfil-linha"><span class="label">Ouro</span><span class="valor" id="perfil-ouro">-</span></div>
    <div class="perfil-linha"><span class="label">Posicao</span><span class="valor" id="perfil-pos">-</span></div>
    <div id="perfil-titulo-secao">⚔️ COMBATE</div>
    <div class="perfil-linha"><span class="label">Arma equipada</span><span class="valor" id="perfil-arma">-</span></div>
    <div class="perfil-linha"><span class="label">Bonus de ataque</span><span class="valor" id="perfil-bonus">-</span></div>
    <div class="perfil-linha"><span class="label">Dano base</span><span class="valor" id="perfil-dano">-</span></div>
    <button id="perfil-fechar" onclick="fecharPerfil()">FECHAR</button>
  </div>
</div>
'''

if "perfil-painel" not in html:
    html = html.replace("</body>", painel + "</body>")
    print("OK: painel adicionado")

# 4) JS
js = '''
<script>
const EMOJI_CLASSE = {
  "cavaleiro": "⚔️ Cavaleiro",
  "arqueiro": "🏹 Arqueiro",
  "mago": "🔮 Mago"
};
const SPRITE_CLASSE = {
  "cavaleiro": "/static/sprites/player-cavaleiro.png",
  "arqueiro": "/static/sprites/player-arqueiro.png",
  "mago": "/static/sprites/player-mago.png"
};
function abrirPerfil() {
  if (!J) return;
  const j = J;
  const classe = j.classe || "cavaleiro";
  document.getElementById("perfil-avatar").style.backgroundImage = `url('${SPRITE_CLASSE[classe] || SPRITE_CLASSE.cavaleiro}')`;
  const cor = j.cargo_cor || "#4af6ff";
  const badge = j.cargo_badge || "";
  const nomeEl = document.getElementById("perfil-nome");
  nomeEl.innerHTML = `${badge} ${j.nome}`;
  nomeEl.style.color = cor;
  document.getElementById("perfil-classe").innerHTML = `<b>${EMOJI_CLASSE[classe] || classe}</b>`;
  const cargoEl = document.getElementById("perfil-cargo");
  cargoEl.textContent = (j.cargo_nome || "Player").toUpperCase();
  cargoEl.style.color = cor;
  cargoEl.style.borderColor = cor;

  const hpPct = Math.max(0, Math.min(100, (j.hp / j.hp_max) * 100));
  document.getElementById("perfil-hp-fill").style.width = hpPct + "%";
  document.getElementById("perfil-hp-txt").textContent = `${j.hp} / ${j.hp_max}`;

  const xpProx = (j.nivel) * 50;
  const xpPct = Math.min(100, (j.xp / xpProx) * 100);
  document.getElementById("perfil-xp-fill").style.width = xpPct + "%";
  document.getElementById("perfil-xp-txt").textContent = `${j.xp} / ${xpProx}`;

  document.getElementById("perfil-nivel").textContent = "Nv " + j.nivel;
  document.getElementById("perfil-classe-txt").textContent = EMOJI_CLASSE[classe] || classe;
  document.getElementById("perfil-ouro").textContent = j.ouro;
  document.getElementById("perfil-pos").textContent = `(${j.x}, ${j.y})`;
  const arma = j.arma ? j.arma[0] : "Punhos";
  const bonus = j.arma ? j.arma[1] : 0;
  document.getElementById("perfil-arma").textContent = arma;
  document.getElementById("perfil-bonus").textContent = "+" + bonus;
  document.getElementById("perfil-dano").textContent = (8 + bonus) + " ~ " + (15 + bonus);

  document.getElementById("perfil-painel").classList.add("aberto");
}
function fecharPerfil() {
  document.getElementById("perfil-painel").classList.remove("aberto");
}
</script>
'''
if "function abrirPerfil" not in html:
    html = html.replace("</body>", js + "</body>")
    print("OK: JS perfil adicionado")

open("templates/index.html", "w").write(html)
print("index.html salvo")
