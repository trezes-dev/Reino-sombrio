html = open("templates/index.html").read()

if "function abrirPicker" in html and "id=\"picker\"" in html:
    print("Picker ja existe, nada a fazer")
else:
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
    div.innerHTML = '<span class="em">' + emojiDe(x[0]) + '</span><div class="info"><div class="nome">' + x[0] + '</div><div class="tipo">' + x[1] + ' +' + x[2] + ' · x' + x[3] + '</div></div>';
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
    # Adicionar declaração da variável slotEditando antes
    if "let slotEditando" not in html:
        picker = "<script>let slotEditando = -1;</script>\n" + picker

    html = html.replace("</body>", picker + "</body>")
    open("templates/index.html", "w").write(html)
    print("OK: picker adicionado")
