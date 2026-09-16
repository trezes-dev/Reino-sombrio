html = open("templates/index.html").read()

if "loading-screen" in html:
    print("Ja tem tela de carregamento")
else:
    # 1) CSS
    css = """
#loading-screen {
  position: fixed; inset: 0; z-index: 9999;
  background: #000 url('/static/loading/fundo.jpg') center/cover no-repeat;
  display: flex; flex-direction: column; align-items: center; justify-content: space-between;
  padding: 30px 20px; transition: opacity 0.8s;
}
#loading-screen.saindo { opacity: 0; pointer-events: none; }
#loading-screen h1 {
  font-family: monospace; font-size: 20px; color: #4af6ff;
  text-shadow: 0 0 20px #4af6ff, 2px 2px 0 #0a0a1a;
  letter-spacing: 3px; margin: 0; text-align: center;
  animation: brilho 2s infinite;
}
#loading-screen h1 span { display: block; font-size: 11px; color: #a06bff; margin-top: 6px; letter-spacing: 6px; }
@keyframes brilho { 0%,100% { text-shadow: 0 0 20px #4af6ff, 2px 2px 0 #0a0a1a; } 50% { text-shadow: 0 0 35px #4af6ff, 2px 2px 0 #0a0a1a; } }
#loading-bottom { width: 100%; max-width: 400px; }
#loading-msg {
  font-family: monospace; font-size: 11px; color: #8fff8f;
  text-align: center; margin-bottom: 10px; min-height: 16px;
  text-shadow: 0 0 8px #8fff8f;
}
#loading-bar {
  width: 100%; height: 20px; background: #0a0a1a;
  border: 3px solid #4af6ff; border-radius: 3px;
  box-shadow: 0 0 15px rgba(74,246,255,0.5);
  position: relative; overflow: hidden;
}
#loading-fill {
  height: 100%; width: 0%; background: linear-gradient(90deg, #4af6ff, #a06bff);
  transition: width 0.3s; box-shadow: 0 0 10px #4af6ff inset;
}
#loading-pct {
  font-family: monospace; font-size: 10px; color: #4af6ff;
  text-align: center; margin-top: 6px;
}
"""
    if "#loading-screen" not in html:
        html = html.replace("</style>", css + "</style>")

    # 2) HTML da tela
    html_screen = '''
<div id="loading-screen">
  <h1>REINO SOMBRIO<span>MMORPG</span></h1>
  <div id="loading-bottom">
    <div id="loading-msg">acordando o dragão...</div>
    <div id="loading-bar"><div id="loading-fill"></div></div>
    <div id="loading-pct">0%</div>
  </div>
</div>
'''
    html = html.replace("<body>", "<body>" + html_screen)

    # 3) JS
    js = '''
<script>
(function() {
  const frases = [
    "acordando o dragão...",
    "invocando monstros...",
    "carregando mapa...",
    "afinando as espadas...",
    "abrindo os portões do castelo...",
    "esquentando a forja...",
    "acendendo as tochas...",
    "Reino Sombrio te aguarda..."
  ];
  let pct = 0;
  const fill = document.getElementById("loading-fill");
  const pctEl = document.getElementById("loading-pct");
  const msgEl = document.getElementById("loading-msg");
  let idxFrase = 0;
  const trocaFrase = setInterval(() => {
    idxFrase = (idxFrase + 1) % frases.length;
    msgEl.textContent = frases[idxFrase];
  }, 900);
  const avanca = setInterval(() => {
    pct += Math.random() * 12 + 4;
    if (pct > 100) pct = 100;
    fill.style.width = pct + "%";
    pctEl.textContent = Math.floor(pct) + "%";
    if (pct >= 100) {
      clearInterval(avanca);
      clearInterval(trocaFrase);
      msgEl.textContent = "entrando no reino...";
    }
  }, 250);
  window._fecharLoading = function() {
    pct = 100;
    fill.style.width = "100%";
    pctEl.textContent = "100%";
    msgEl.textContent = "entrando no reino...";
    setTimeout(() => {
      const ls = document.getElementById("loading-screen");
      if (ls) {
        ls.classList.add("saindo");
        setTimeout(() => ls.remove(), 900);
      }
    }, 400);
  };
})();
</script>
'''
    html = html.replace("</body>", js + "</body>")

    # 4) Chamar fecharLoading depois do primeiro carregar()
    old = "carregar();\n</script>\n</body>"
    new = '''carregar().then(() => {
  if (window._fecharLoading) setTimeout(window._fecharLoading, 800);
}).catch(() => {
  if (window._fecharLoading) setTimeout(window._fecharLoading, 1500);
});
</script>
</body>'''
    if old in html:
        html = html.replace(old, new)
        print("OK: fecharLoading conectado")
    else:
        # tenta outra forma
        html = html.replace("carregar();", "carregar().then(() => { if (window._fecharLoading) setTimeout(window._fecharLoading, 800); });")
        print("OK: fallback aplicado")

    open("templates/index.html", "w").write(html)
    print("OK: tela de carregamento adicionada")
