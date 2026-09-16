html = open("templates/index.html").read()

# 1) CSS novo
css_add = """
.slot.vazio-item { border-color: #333; }
.slot.vazio-item .icon { opacity: 0.25; filter: grayscale(1); }
.slot .icon { display: inline-block; }
#picker { position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 40; display: none; flex-direction: column; padding: 20px; overflow-y: auto; }
#picker.aberto { display: flex; }
#picker h3 { color: #4af6ff; margin: 0 0 12px; font-size: 15px; }
#picker .item-pick { background: #1a1a2a; border: 2px solid #444; border-radius: 8px; padding: 12px; margin-bottom: 8px; display: flex; align-items: center; gap: 12px; cursor: pointer; font-size: 13px; }
#picker .item-pick:hover { border-color: #4af6ff; }
#picker .item-pick .em { font-size: 26px; }
#picker .item-pick .info { flex: 1; }
#picker .item-pick .info .nome { font-weight: bold; }
#picker .item-pick .info .tipo { color: #888; font-size: 11px; }
#picker .botoes { display: flex; gap: 8px; margin-top: 12px; }
#picker button { flex: 1; padding: 12px; background: #222; color: #eee; border: 1px solid #555; border-radius: 6px; font-family: inherit; font-size: 13px; cursor: pointer; }
#picker .limpar { border-color: #ff5566; color: #ff5566; }
"""

if ".slot.vazio-item" not in html:
    html = html.replace(".slot.vazio { opacity: 0.4; }", ".slot.vazio { opacity: 0.4; }" + css_add)
    print("OK: CSS adicionado")

# 2) Substituir o bloco de render da hotbar
old_render = '''  const hb = document.getElementById("hotbar");
  hb.innerHTML = "";
  const itens = j.inv || [];
  for (let i = 0; i < 6; i++) {
    const slot = document.createElement("div");
    if (i < itens.length) {
      const [nome, tipo, bonus, qtd] = itens[i];
      slot.className = "slot " + tipo;
      slot.innerHTML = `${emojiDe(nome)}<span class="qtd">${qtd}</span><span class="nome-pequeno">${nome}</span>`;
      slot.onclick = () => usarSlot(nome, tipo);
      slot.title = `${nome} (${tipo} +${bonus}) x${qtd}`;
    } else {
      slot.className = "slot vazio";
      slot.textContent = "·";
    }
    hb.appendChild(slot);
  }'''

new_render = '''  const hb = document.getElementById("hotbar");
  hb.innerHTML = "";
  const itens = j.inv || [];
  const invPorId = {};
  itens.forEach(x => {
    const id = x[4];
    invPorId[id] = { nome: x[0], tipo: x[1], bonus: x[2], qtd: x[3] };
  });
  let hbIds = j.hotbar || [];
  if (!hbIds.some(x => x > 0)) {
    hbIds = itens.slice(0, 6).map(x => x[4]);
    while (hbIds.length < 6) hbIds.push(0);
  }
  for (let i = 0; i < 6; i++) {
    const slot = document.createElement("div");
    const itemId = hbIds[i] || 0;
    if (itemId && invPorId[itemId]) {
      const it = invPorId[itemId];
      const semQtd = it.qtd <= 0;
      slot.className = "slot " + it.tipo + (semQtd ? " vazio-item" : "");
      slot.innerHTML = `<span class="icon">${emojiDe(it.nome)}</span><span class="qtd">${it.qtd}</span><span class="nome-pequeno">${it.nome}</span>`;
      slot.title = `${it.nome} (${it.tipo} +${it.bonus}) x${it.qtd} - clique para trocar`;
      slot.onclick = () => abrirPicker(i);
    } else {
      slot.className = "slot vazio";
      slot.textContent = "·";
      slot.title = "vazio - clique para escolher";
      slot.onclick = () => abrirPicker(i);
    }
    hb.appendChild(slot);
  }'''

if old_render in html:
    html = html.replace(old_render, new_render)
    print("OK: render da hotbar substituido")
else:
    print("AVISO: bloco de render nao bateu")

# 3) Remover a função usarSlot antiga (nao usada agora)
old_usar = '''async function usarSlot(nome, tipo) {
  if (tipo === "pocao") {
    await pocao();
  } else if (tipo === "arma") {
    document.getElementById("log").textContent = `${nome} ja esta em uso (melhor arma do inventario)`;
  } else if (tipo === "escudo" || tipo === "armadura") {
    document.getElementById("log").textContent = `${nome} equipado (bonus aplicado automaticamente)`;
  } else {
    document.getElementById("log").textContent = `${nome} — sem uso definido`;
  }
}'''
new_usar = '''async function usarSlot(nome, tipo) {
  if (tipo === "pocao") await pocao();
  else if (tipo === "arma") document.getElementById("log").textContent = `${nome} ja esta em uso`;
  else document.getElementById("log").textContent = `${nome} equipado`;
}'''
if old_usar in html:
    html = html.replace(old_usar, new_usar)
    print("OK: usarSlot simplificado")

# 4) Adicionar picker antes de </body>
picker = '''
<div id="picker">
  <h3>Escolher item para o slot</h3>
  <div id="picker-lista"></div>
  <div class="botoes">
    <button class="limpar" onclick="limparSlot()">Limpar slot</button>
    <button onclick="fecharPicker()">Cancelar</button>
  </div>
</div>
<script>
let slotEditando = -1;
function abrirPicker(idx) {
  slotEditando = idx;
  const lista = document.getElementById("picker-lista");
  lista.innerHTML = "";
  const itens = (J && J.inv) || [];
  if (!itens.length) {
    lista.innerHTML = "<div style='color:#666;padding:20px;text-align:center'>Inventario vazio</div>";
  }
  itens.forEach(x => {
    const id = x[4];
    const div = document.createElement("div");
    div.className = "item-pick";
    div.innerHTML = `<span class="em">${emojiDe(x[0])}</span><div class="info"><div class="nome">${x[0]}</div><div class="tipo">${x[1]} +${x[2]} · x${x[3]}</div></div>`;
    div.onclick = () => escolherItem(id);
    lista.appendChild(div);
  });
  document.getElementById("picker").classList.add("aberto");
}
function fecharPicker() {
  document.getElementById("picker").classList.remove("aberto");
  slotEditando = -1;
}
async function escolherItem(itemId) {
  if (!J) return;
  let hb = (J.hotbar || []).slice();
  while (hb.length < 6) hb.push(0);
  for (let i = 0; i < 6; i++) if (i !== slotEditando && hb[i] === itemId) hb[i] = 0;
  hb[slotEditando] = itemId;
  await fetch("/api/hotbar/salvar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({slots: hb})});
  fecharPicker();
  const r = await fetch("/api/estado");
  render(await r.json());
}
async function limparSlot() {
  if (!J) return;
  let hb = (J.hotbar || []).slice();
  while (hb.length < 6) hb.push(0);
  hb[slotEditando] = 0;
  await fetch("/api/hotbar/salvar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({slots: hb})});
  fecharPicker();
  const r = await fetch("/api/estado");
  render(await r.json());
}
</script>
'''
if "abrirPicker" not in html:
    html = html.replace("</body>", picker + "</body>")
    print("OK: picker adicionado")

open("templates/index.html", "w").write(html)
print("index.html salvo")
