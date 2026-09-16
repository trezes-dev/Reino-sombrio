from flask import Flask, render_template, jsonify, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, random, functools, time, json

app = Flask(__name__)
app.secret_key = "troque-essa-chave-por-algo-aleatorio-grande"
DB = "rpg.db"
W_MAP = 50
H_MAP = 50
VIEW = 15
XP_MONSTRO = {"Goblin": 10, "Lobo": 15, "Esqueleto": 20, "Slime": 8}

CARGOS = {
    "player":   {"nome": "Player",   "cor": "#cccccc", "badge": "",   "perms": []},
    "vip":      {"nome": "VIP",      "cor": "#ffd700", "badge": "⭐", "perms": ["cor"]},
    "ajudante": {"nome": "Ajudante", "cor": "#8fff8f", "badge": "🛡️", "perms": ["cor", "curar", "teleportar"]},
    "mod":      {"nome": "Mod",      "cor": "#4af6ff", "badge": "🔨", "perms": ["cor", "curar", "teleportar", "kick", "ouro_pequeno"]},
    "admin":    {"nome": "Admin",    "cor": "#ff5566", "badge": "⚡", "perms": ["*"]},
    "dev":      {"nome": "Dev",      "cor": "#a06bff", "badge": "👑", "perms": ["*"]},
}
HIERARQUIA = ["player", "vip", "ajudante", "mod", "admin", "dev"]

CLASSES = {
    "cavaleiro": {"nome": "Cavaleiro", "hp_max": 120, "arma": "Espada Curta", "cor": "#ff5566",
                  "descricao": "Tanque resistente. Comeca com Espada Curta (+5).", "emoji": "⚔️"},
    "mago":      {"nome": "Mago",      "hp_max": 80,  "arma": "Cajado",       "cor": "#4af6ff",
                  "descricao": "Dano magico alto. Comeca com Cajado (+8).",     "emoji": "🔮"},
    "arqueiro":  {"nome": "Arqueiro",  "hp_max": 100, "arma": "Arco Curto",   "cor": "#8fff8f",
                  "descricao": "Equilibrado. Comeca com Arco Curto (+6).",      "emoji": "🏹"},
}

MAPA_CACHE = {}

def con():
    return sqlite3.connect(DB)

def gerar_mapa():
    rnd = random.Random(12345)
    grid = 6
    gw = (W_MAP // grid) + 3
    gh = (H_MAP // grid) + 3
    r = [[rnd.random() for _ in range(gw)] for _ in range(gh)]
    def smooth(t):
        return t * t * (3 - 2 * t)
    def ruido(x, y, escala=1.0):
        xx = x * escala
        yy = y * escala
        x0 = int(xx)
        y0 = int(yy)
        if x0 + 1 >= gw or y0 + 1 >= gh or x0 < 0 or y0 < 0:
            return 0.5
        tx = smooth(xx - x0)
        ty = smooth(yy - y0)
        v00 = r[y0][x0]
        v10 = r[y0][x0 + 1]
        v01 = r[y0 + 1][x0]
        v11 = r[y0 + 1][x0 + 1]
        v0 = v00 * (1 - tx) + v10 * tx
        v1 = v01 * (1 - tx) + v11 * tx
        return v0 * (1 - ty) + v1 * ty
    tiles = {}
    for y in range(H_MAP):
        for x in range(W_MAP):
            n = ruido(x, y, 1/6) * 0.7 + ruido(x, y, 1/3) * 0.3
            borda = min(x, y, W_MAP - 1 - x, H_MAP - 1 - y)
            if borda < 2:
                t = "agua"
            elif n < 0.36:
                t = "agua"
            elif n < 0.42:
                t = "areia"
            elif n < 0.66:
                t = "grama"
            elif n < 0.78:
                t = "arvore"
            else:
                t = "pedra"
            tiles[(x, y)] = t
    # zona inicial sempre grama (5,5)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            x, y = 5 + dx, 5 + dy
            if 0 <= x < W_MAP and 0 <= y < H_MAP:
                tiles[(x, y)] = "grama"
    return tiles

def carregar_mapa():
    global MAPA_CACHE
    c = con()
    n = c.execute("SELECT COUNT(*) FROM mapa_tiles").fetchone()[0]
    if n == 0:
        print("Gerando mapa...")
        tiles = gerar_mapa()
        for (x, y), t in tiles.items():
            c.execute("INSERT INTO mapa_tiles (x, y, tipo) VALUES (?,?,?)", (x, y, t))
        c.commit()
    rows = c.execute("SELECT x, y, tipo FROM mapa_tiles").fetchall()
    c.close()
    MAPA_CACHE = {(r[0], r[1]): r[2] for r in rows}
    print("Mapa carregado: " + str(len(MAPA_CACHE)) + " tiles")

def tile_em(x, y):
    return MAPA_CACHE.get((x, y), "agua")

def bloqueia(x, y):
    return tile_em(x, y) in ("agua", "arvore")

def tem_perm(cargo, perm):
    if cargo not in CARGOS:
        return False
    perms = CARGOS[cargo]["perms"]
    return "*" in perms or perm in perms

def cargo_ok(meu, minimo):
    try:
        return HIERARQUIA.index(meu) >= HIERARQUIA.index(minimo)
    except:
        return False

def so_logado(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("jogador_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def login_obrigatorio(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        jid = session.get("jogador_id")
        if not jid:
            return redirect(url_for("login"))
        c = con()
        row = c.execute("SELECT personagem_criado FROM jogador WHERE id=?", (jid,)).fetchone()
        c.close()
        if not row or row[0] == 0:
            return redirect(url_for("criar_personagem"))
        return f(*args, **kwargs)
    return wrapper

def achar_jogador(c, nome):
    return c.execute("SELECT id, nome_personagem, nome FROM jogador WHERE nome_personagem=? OR nome=?",
                     (nome, nome)).fetchone()

def estado(jid):
    c = con()
    linha = c.execute("""SELECT id, nome, nome_personagem, classe, cargo, hp, ouro, x, y, xp, nivel, hp_max, cor, COALESCE(hotbar,'[]')
        FROM jogador WHERE id=?""", (jid,)).fetchone()
    if not linha:
        c.close()
        return None
    (jid_, nome_login, nome_pers, classe, cargo, hp, ouro, x, y, xp, nivel, hp_max, cor, hotbar_str) = linha
    try:
        hotbar_ids = json.loads(hotbar_str or "[]")
    except:
        hotbar_ids = []
    arma = c.execute("""SELECT i.nome, i.bonus FROM inventario inv JOIN itens i ON i.id=inv.item_id
        WHERE inv.jogador_id=? AND i.tipo='arma' ORDER BY i.bonus DESC LIMIT 1""", (jid,)).fetchone()
    inv = c.execute("""SELECT i.nome, i.tipo, i.bonus, inv.qtd, i.id FROM inventario inv
        JOIN itens i ON i.id=inv.item_id WHERE inv.jogador_id=?""", (jid,)).fetchall()
    mons = c.execute("SELECT id, nome, x, y, hp FROM monstros").fetchall()
    npcs = c.execute("SELECT id, nome, x, y, tipo FROM npcs").fetchall()
    agora = time.time()
    outros_rows = c.execute("""SELECT id, nome_personagem, nome, cargo, x, y, hp, hp_max, nivel
        FROM jogador WHERE id != ? AND ultimo_visto > ? AND personagem_criado = 1""",
        (jid, agora - 15)).fetchall()
    c.close()
    # Busca guilda do jogador na tabela nova
    try:
        c2 = con()
        g_row = c2.execute("""SELECT g.nome FROM guilda_membros gm
            JOIN guildas g ON g.id = gm.guilda_id
            WHERE gm.jogador_id = ?""", (jid,)).fetchone()
        guilda_nome = g_row[0] if g_row else None
        c2.close()
    except Exception:
        guilda_nome = None
    info = CARGOS.get(cargo or "player", CARGOS["player"])
    lista_outros = []
    for o in outros_rows:
        info_o = CARGOS.get(o[3] or "player", CARGOS["player"])
        lista_outros.append({
            "id": o[0], "nome": o[1] or o[2], "cargo": o[3] or "player",
            "x": o[4], "y": o[5], "hp": o[6], "hp_max": o[7], "nivel": o[8],
            "cor": info_o["cor"], "badge": info_o["badge"]
        })
    # viewport 15x15
    metade = VIEW // 2
    vp = []
    for vy in range(VIEW):
        linha_vp = []
        for vx in range(VIEW):
            mx = x - metade + vx
            my = y - metade + vy
            linha_vp.append(tile_em(mx, my))
        vp.append(linha_vp)
    # monstros e npcs no viewport
    mons_vp = []
    for m in mons:
        if abs(m[2] - x) <= metade and abs(m[3] - y) <= metade:
            mons_vp.append(m)
    npcs_vp = []
    for n in npcs:
        if abs(n[2] - x) <= metade and abs(n[3] - y) <= metade:
            npcs_vp.append(n)
    outros_vp = []
    for o in lista_outros:
        if abs(o["x"] - x) <= metade and abs(o["y"] - y) <= metade:
            outros_vp.append(o)
    return {"id": jid_, "nome": nome_pers or nome_login, "login": nome_login,
            "classe": classe, "cargo": cargo or "player",
            "cargo_nome": info["nome"], "cargo_cor": info["cor"], "cargo_badge": info["badge"],
            "hp": hp, "ouro": ouro, "x": x, "y": y,
            "xp": xp, "nivel": nivel, "hp_max": hp_max, "cor": cor,
            "arma": arma, "inv": inv, "monstros": mons_vp, "npcs": npcs_vp, "outros": outros_vp,
            "viewport": vp, "view": VIEW, "metade": metade,
            "hotbar": hotbar_ids, "guilda": guilda_nome, "W_MAP": W_MAP, "H_MAP": H_MAP}

def posicao_livre(c, px, py):
    for _ in range(50):
        nx = random.randint(0, W_MAP-1)
        ny = random.randint(0, H_MAP-1)
        if nx == px and ny == py:
            continue
        if bloqueia(nx, ny):
            continue
        if not c.execute("SELECT 1 FROM monstros WHERE x=? AND y=?", (nx, ny)).fetchone():
            return nx, ny
    return None

def nascer_monstro(c, px, py):
    pos = posicao_livre(c, px, py)
    if not pos:
        return
    tipos = [("Goblin", 20, 5), ("Lobo", 25, 7), ("Esqueleto", 30, 6), ("Slime", 15, 3)]
    n, hpm, dmg = random.choice(tipos)
    c.execute("INSERT INTO monstros (nome, x, y, hp, dano) VALUES (?, ?, ?, ?, ?)",
              (n, pos[0], pos[1], hpm, dmg))

def salvar_mensagem(jid, texto, canal="global"):
    c = con()
    row = c.execute("SELECT x, y FROM jogador WHERE id=?", (jid,)).fetchone()
    x, y = row if row else (None, None)
    c.execute("INSERT INTO mensagens (jogador_id, canal, texto, x, y) VALUES (?, ?, ?, ?, ?)",
              (jid, canal, texto[:200], x, y))
    c.commit()
    c.close()

def msg_privada(jid_dest, texto):
    c = con()
    row = c.execute("SELECT x, y FROM jogador WHERE id=?", (jid_dest,)).fetchone()
    x, y = row if row else (None, None)
    c.execute("""INSERT INTO mensagens (jogador_id, canal, texto, x, y, destinatario)
                 VALUES (?, 'sistema', ?, ?, ?, ?)""",
              (jid_dest, texto[:200], x, y, jid_dest))
    c.commit()
    c.close()

def achar_troca_ativa(c, jid):
    return c.execute("""SELECT id, jogador_a, jogador_b, ouro_a, ouro_b, aceito_a, aceito_b, status
        FROM trocas WHERE status IN ('pendente','aguardando')
        AND (jogador_a=? OR jogador_b=?)""", (jid, jid)).fetchone()

def troca_resumo(c, tid):
    t = c.execute("""SELECT id, jogador_a, jogador_b, ouro_a, ouro_b, aceito_a, aceito_b, status
        FROM trocas WHERE id=?""", (tid,)).fetchone()
    if not t:
        return "Troca nao existe"
    _, ja, jb, oa, ob, aa, ab, status = t
    na = c.execute("SELECT nome_personagem, nome FROM jogador WHERE id=?", (ja,)).fetchone()
    nb = c.execute("SELECT nome_personagem, nome FROM jogador WHERE id=?", (jb,)).fetchone()
    itens_a = c.execute("""SELECT i.nome, ti.qtd FROM troca_itens ti
        JOIN itens i ON i.id=ti.item_id WHERE ti.troca_id=? AND ti.jogador_id=?""", (tid, ja)).fetchall()
    itens_b = c.execute("""SELECT i.nome, ti.qtd FROM troca_itens ti
        JOIN itens i ON i.id=ti.item_id WHERE ti.troca_id=? AND ti.jogador_id=?""", (tid, jb)).fetchall()
    a_str = ", ".join([f"{q}x {n}" for n, q in itens_a]) or "(nada)"
    b_str = ", ".join([f"{q}x {n}" for n, q in itens_b]) or "(nada)"
    linha_a = f"  {'[OK]' if aa else '[..]'} {na[0] or na[1]}: {a_str} + {oa} ouro"
    linha_b = f"  {'[OK]' if ab else '[..]'} {nb[0] or nb[1]}: {b_str} + {ob} ouro"
    return f"Troca #{tid} [{status}]\n{linha_a}\n{linha_b}"

def executar_troca_final(c, tid):
    t = c.execute("SELECT jogador_a, jogador_b, ouro_a, ouro_b FROM trocas WHERE id=?", (tid,)).fetchone()
    if not t:
        return "Troca nao existe"
    ja, jb, oa, ob = t
    itens_a = c.execute("SELECT item_id, qtd FROM troca_itens WHERE troca_id=? AND jogador_id=?", (tid, ja)).fetchall()
    itens_b = c.execute("SELECT item_id, qtd FROM troca_itens WHERE troca_id=? AND jogador_id=?", (tid, jb)).fetchall()
    for item_id, qtd in itens_a:
        inv = c.execute("SELECT qtd FROM inventario WHERE jogador_id=? AND item_id=?", (ja, item_id)).fetchone()
        if not inv or inv[0] < qtd:
            c.execute("UPDATE trocas SET status='falhou' WHERE id=?", (tid,))
            c.commit()
            msg_privada(ja, "FALHA: item sumiu"); msg_privada(jb, "FALHA: item sumiu do outro lado")
            return "TROCA FALHOU (item A)"
    for item_id, qtd in itens_b:
        inv = c.execute("SELECT qtd FROM inventario WHERE jogador_id=? AND item_id=?", (jb, item_id)).fetchone()
        if not inv or inv[0] < qtd:
            c.execute("UPDATE trocas SET status='falhou' WHERE id=?", (tid,))
            c.commit()
            msg_privada(jb, "FALHA: item sumiu"); msg_privada(ja, "FALHA: item sumiu do outro lado")
            return "TROCA FALHOU (item B)"
    ouro_a = c.execute("SELECT ouro FROM jogador WHERE id=?", (ja,)).fetchone()[0]
    ouro_b = c.execute("SELECT ouro FROM jogador WHERE id=?", (jb,)).fetchone()[0]
    if ouro_a < oa or ouro_b < ob:
        c.execute("UPDATE trocas SET status='falhou' WHERE id=?", (tid,))
        c.commit()
        return "TROCA FALHOU (ouro)"
    for item_id, qtd in itens_a:
        c.execute("UPDATE inventario SET qtd=qtd-? WHERE jogador_id=? AND item_id=?", (qtd, ja, item_id))
    for item_id, qtd in itens_b:
        c.execute("UPDATE inventario SET qtd=qtd-? WHERE jogador_id=? AND item_id=?", (qtd, jb, item_id))
    c.execute("DELETE FROM inventario WHERE qtd <= 0")
    for item_id, qtd in itens_a:
        ex = c.execute("SELECT id FROM inventario WHERE jogador_id=? AND item_id=?", (jb, item_id)).fetchone()
        if ex:
            c.execute("UPDATE inventario SET qtd=qtd+? WHERE id=?", (qtd, ex[0]))
        else:
            c.execute("INSERT INTO inventario (jogador_id, item_id, qtd) VALUES (?,?,?)", (jb, item_id, qtd))
    for item_id, qtd in itens_b:
        ex = c.execute("SELECT id FROM inventario WHERE jogador_id=? AND item_id=?", (ja, item_id)).fetchone()
        if ex:
            c.execute("UPDATE inventario SET qtd=qtd+? WHERE id=?", (qtd, ex[0]))
        else:
            c.execute("INSERT INTO inventario (jogador_id, item_id, qtd) VALUES (?,?,?)", (ja, item_id, qtd))
    c.execute("UPDATE jogador SET ouro = ouro - ? + ? WHERE id=?", (oa, ob, ja))
    c.execute("UPDATE jogador SET ouro = ouro - ? + ? WHERE id=?", (ob, oa, jb))
    c.execute("UPDATE trocas SET status='concluida' WHERE id=?", (tid,))
    c.commit()
    msg_privada(ja, "TROCA CONCLUIDA"); msg_privada(jb, "TROCA CONCLUIDA")
    return "TROCA CONCLUIDA"

def executar_troca(jid, args):
    c = con()
    eu = c.execute("SELECT nome_personagem, nome FROM jogador WHERE id=?", (jid,)).fetchone()
    if not eu:
        c.close()
        return "erro interno"
    if not args:
        c.close()
        return "Uso: /troca <nome> | add <id> <qtd> | ouro <v> | ver | aceitar | cancelar"
    sub = args[0].lower()
    if sub == "ver":
        t = achar_troca_ativa(c, jid)
        if not t:
            c.close()
            return "Sem troca ativa"
        r = troca_resumo(c, t[0])
        c.close()
        return r
    if sub == "cancelar":
        t = achar_troca_ativa(c, jid)
        if not t:
            c.close()
            return "Sem troca ativa"
        c.execute("UPDATE trocas SET status='cancelada' WHERE id=?", (t[0],))
        c.commit()
        c.close()
        return "Troca cancelada"
    if sub == "add":
        if len(args) < 3:
            c.close()
            return "Uso: /troca add <item_id> <qtd>"
        try:
            item_id = int(args[1]); qtd = int(args[2])
        except:
            c.close()
            return "id/qtd invalidos"
        if qtd <= 0:
            c.close()
            return "Quantidade deve ser positiva"
        t = achar_troca_ativa(c, jid)
        if not t:
            c.close()
            return "Sem troca ativa"
        if t[7] == "aguardando":
            c.close()
            return "Troca em confirmacao"
        inv = c.execute("SELECT qtd FROM inventario WHERE jogador_id=? AND item_id=?", (jid, item_id)).fetchone()
        if not inv or inv[0] < qtd:
            c.close()
            return "Voce nao tem esse item suficiente"
        item = c.execute("SELECT nome FROM itens WHERE id=?", (item_id,)).fetchone()
        if not item:
            c.close()
            return "Item nao existe"
        ja = c.execute("SELECT id, qtd FROM troca_itens WHERE troca_id=? AND jogador_id=? AND item_id=?",
                       (t[0], jid, item_id)).fetchone()
        if ja:
            nova_qtd = ja[1] + qtd
            if nova_qtd > inv[0]:
                c.close()
                return f"Voce so tem {inv[0]}"
            c.execute("UPDATE troca_itens SET qtd=? WHERE id=?", (nova_qtd, ja[0]))
        else:
            c.execute("INSERT INTO troca_itens (troca_id, jogador_id, item_id, qtd) VALUES (?,?,?,?)",
                      (t[0], jid, item_id, qtd))
        c.commit()
        c.close()
        return f"Adicionado {qtd}x {item[0]}"
    if sub == "ouro":
        if len(args) < 2:
            c.close()
            return "Uso: /troca ouro <valor>"
        try:
            valor = int(args[1])
        except:
            c.close()
            return "Valor invalido"
        if valor < 0:
            c.close()
            return "Valor deve ser positivo"
        t = achar_troca_ativa(c, jid)
        if not t:
            c.close()
            return "Sem troca ativa"
        if t[7] == "aguardando":
            c.close()
            return "Troca em confirmacao"
        ouro = c.execute("SELECT ouro FROM jogador WHERE id=?", (jid,)).fetchone()[0]
        if ouro < valor:
            c.close()
            return f"Voce so tem {ouro} ouro"
        if jid == t[1]:
            c.execute("UPDATE trocas SET ouro_a=? WHERE id=?", (valor, t[0]))
        else:
            c.execute("UPDATE trocas SET ouro_b=? WHERE id=?", (valor, t[0]))
        c.commit()
        c.close()
        return f"Ouro definido: {valor}"
    if sub in ("aceitar", "aceito", "confirmar"):
        t = achar_troca_ativa(c, jid)
        if not t:
            c.close()
            return "Sem troca ativa"
        tid, ja, jb, oa, ob, aa, ab, status = t
        if jid == ja:
            if aa:
                c.close()
                return "Voce ja aceitou"
            c.execute("UPDATE trocas SET aceito_a=1, status='aguardando' WHERE id=?", (tid,))
            aa = 1
        else:
            if ab:
                c.close()
                return "Voce ja aceitou"
            c.execute("UPDATE trocas SET aceito_b=1, status='aguardando' WHERE id=?", (tid,))
            ab = 1
        c.commit()
        if aa and ab:
            resultado = executar_troca_final(c, tid)
            c.close()
            return resultado
        c.close()
        return "Voce aceitou. Aguardando o outro"
    alvo = achar_jogador(c, args[0])
    if not alvo:
        c.close()
        return "Jogador nao encontrado"
    if alvo[0] == jid:
        c.close()
        return "Nao pode trocar consigo mesmo"
    if achar_troca_ativa(c, jid):
        c.close()
        return "Voce ja tem troca ativa"
    if achar_troca_ativa(c, alvo[0]):
        c.close()
        return "Esse jogador ja esta em troca"
    c.execute("INSERT INTO trocas (jogador_a, jogador_b) VALUES (?, ?)", (jid, alvo[0]))
    tid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.commit()
    c.close()
    msg_privada(alvo[0], f"Troca #{tid} aberta por {eu[0] or eu[1]}. Use /troca ver")
    return f"Troca #{tid} aberta com {alvo[1] or alvo[2]}"

# ============ AUTH ============

@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        acao = request.form.get("acao")
        usuario = request.form.get("usuario", "").strip().lower()
        senha = request.form.get("senha", "")
        if len(usuario) < 3 or len(usuario) > 16:
            erro = "Usuario precisa ter entre 3 e 16 caracteres"
        elif not usuario.replace("_", "").isalnum():
            erro = "Use so letras, numeros e underline"
        elif len(senha) < 4:
            erro = "Senha precisa ter ao menos 4 caracteres"
        else:
            c = con()
            conta = c.execute("SELECT id, senha_hash, jogador_id FROM contas WHERE usuario=?", (usuario,)).fetchone()
            if acao == "registrar":
                if conta:
                    erro = "Esse nome ja existe, escolha outro"
                else:
                    c.execute("""INSERT INTO jogador
                        (nome, nome_personagem, classe, cargo, hp, ouro, x, y, xp, nivel, hp_max, cor, admin, personagem_criado)
                        VALUES (?, NULL, 'cavaleiro', 'player', 100, 0, 5, 5, 0, 1, 100, '#4af', 0, 0)""", (usuario,))
                    jid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
                    c.execute("INSERT INTO contas (usuario, senha_hash, jogador_id) VALUES (?, ?, ?)",
                              (usuario, generate_password_hash(senha), jid))
                    c.commit()
                    c.close()
                    session["jogador_id"] = jid
                    session["usuario"] = usuario
                    return redirect(url_for("criar_personagem"))
            elif acao == "entrar":
                if not conta:
                    erro = "Usuario nao existe"
                else:
                    conta_id, senha_hash, jid = conta
                    if senha_hash == "migrar":
                        c.execute("UPDATE contas SET senha_hash=? WHERE id=?",
                                  (generate_password_hash(senha), conta_id))
                        c.commit()
                        session["jogador_id"] = jid
                        session["usuario"] = usuario
                        c.close()
                        return redirect(url_for("home"))
                    elif not check_password_hash(senha_hash, senha):
                        erro = "Senha errada"
                    else:
                        session["jogador_id"] = jid
                        session["usuario"] = usuario
                        c.close()
                        return redirect(url_for("home"))
            c.close()
    return render_template("login.html", erro=erro)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/criar_personagem", methods=["GET", "POST"])
@so_logado
def criar_personagem():
    jid = session["jogador_id"]
    c = con()
    row = c.execute("SELECT personagem_criado FROM jogador WHERE id=?", (jid,)).fetchone()
    if row and row[0] == 1:
        c.close()
        return redirect(url_for("home"))
    c.close()
    erro = None
    if request.method == "POST":
        nome_pers = request.form.get("nome_personagem", "").strip()
        classe = request.form.get("classe", "").strip().lower()
        if len(nome_pers) < 3 or len(nome_pers) > 16:
            erro = "Nome do personagem precisa ter entre 3 e 16 caracteres"
        elif not nome_pers.replace(" ", "").isalnum():
            erro = "Use so letras, numeros e espaco"
        elif classe not in CLASSES:
            erro = "Escolha uma classe valida"
        else:
            c = con()
            existe = c.execute("SELECT 1 FROM jogador WHERE nome_personagem=? AND id!=?",
                               (nome_pers, jid)).fetchone()
            if existe:
                erro = "Ja existe um personagem com esse nome"
                c.close()
            else:
                info = CLASSES[classe]
                arma_id = c.execute("SELECT id FROM itens WHERE nome=?", (info["arma"],)).fetchone()
                poco_id = c.execute("SELECT id FROM itens WHERE nome='Poção de Cura'").fetchone()
                c.execute("""UPDATE jogador SET nome_personagem=?, classe=?, hp=?, hp_max=?, personagem_criado=1, x=5, y=5
                             WHERE id=?""", (nome_pers, classe, info["hp_max"], info["hp_max"], jid))
                if arma_id:
                    c.execute("INSERT INTO inventario (jogador_id, item_id, qtd) VALUES (?, ?, 1)", (jid, arma_id[0]))
                if poco_id:
                    c.execute("INSERT INTO inventario (jogador_id, item_id, qtd) VALUES (?, ?, 3)", (jid, poco_id[0]))
                c.commit()
                c.close()
                return redirect(url_for("home"))
    return render_template("criar_personagem.html", classes=CLASSES, erro=erro)

@app.route("/")
@login_obrigatorio
def home():
    return render_template("index.html", usuario=session["usuario"], jogador_id=session["jogador_id"])

@app.route("/api/estado")
@login_obrigatorio
def api_estado():
    jid = session["jogador_id"]
    c = con()
    c.execute("UPDATE jogador SET ultimo_visto = ? WHERE id = ?", (time.time(), jid))
    c.commit()
    c.close()
    return jsonify(estado(jid))

@app.route("/api/mover/<dir>")
@login_obrigatorio
def api_mover(dir):
    jid = session["jogador_id"]
    c = con()
    hp, ouro, x, y, xp, nivel, hp_max = c.execute(
        "SELECT hp, ouro, x, y, xp, nivel, hp_max FROM jogador WHERE id=?", (jid,)).fetchone()
    nx, ny = x, y
    if dir == "cima": ny -= 1
    if dir == "baixo": ny += 1
    if dir == "esq": nx -= 1
    if dir == "dir": nx += 1
    nx = max(0, min(W_MAP-1, nx))
    ny = max(0, min(H_MAP-1, ny))
    if bloqueia(nx, ny):
        c.close()
        return jsonify({"msg": "Bloqueado por " + tile_em(nx, ny), "estado": estado(jid)})
    x, y = nx, ny
    c.execute("UPDATE jogador SET x=?, y=?, ultimo_visto=? WHERE id=?", (x, y, time.time(), jid))
    msg = "Andou para " + dir
    m = c.execute("SELECT id, nome, dano FROM monstros WHERE x=? AND y=?", (x, y)).fetchone()
    if m:
        mid, mnome, mdano = m
        arma = c.execute("""SELECT i.bonus FROM inventario inv JOIN itens i ON i.id=inv.item_id
            WHERE inv.jogador_id=? AND i.tipo='arma' ORDER BY i.bonus DESC LIMIT 1""", (jid,)).fetchone()
        bonus = arma[0] if arma else 0
        dano = max(0, mdano - bonus)
        hp -= dano
        ganho = random.randint(5, 15)
        ouro += ganho
        xp_ganho = XP_MONSTRO.get(mnome, 10)
        xp += xp_ganho
        msg = "Matou " + mnome + "! -" + str(dano) + " HP, +" + str(ganho) + " ouro, +" + str(xp_ganho) + " XP"
        subiu = False
        while xp >= int(100 * (nivel ** 1.5)):
            xp -= int(100 * (nivel ** 1.5))
            nivel += 1
            hp_max += 20
            hp = hp_max
            subiu = True
        if subiu:
            msg += "  LEVEL UP! Nv " + str(nivel)
        c.execute("DELETE FROM monstros WHERE id=?", (mid,))
        nascer_monstro(c, x, y)
    c.execute("UPDATE jogador SET hp=?, ouro=?, xp=?, nivel=?, hp_max=? WHERE id=?",
              (hp, ouro, xp, nivel, hp_max, jid))
    c.commit()
    c.close()
    return jsonify({"msg": msg, "estado": estado(jid)})

@app.route("/api/descansar")
@login_obrigatorio
def api_descansar():
    jid = session["jogador_id"]
    c = con()
    hp, hp_max = c.execute("SELECT hp, hp_max FROM jogador WHERE id=?", (jid,)).fetchone()
    hp = min(hp_max, hp + 5)
    c.execute("UPDATE jogador SET hp=? WHERE id=?", (hp, jid))
    c.commit()
    c.close()
    return jsonify({"msg": "Descansou. +5 HP", "estado": estado(jid)})

@app.route("/api/pocao")
@login_obrigatorio
def api_pocao():
    jid = session["jogador_id"]
    c = con()
    hp, hp_max = c.execute("SELECT hp, hp_max FROM jogador WHERE id=?", (jid,)).fetchone()
    linha = c.execute("""SELECT inv.id, inv.qtd, i.nome, i.bonus FROM inventario inv
        JOIN itens i ON i.id=inv.item_id
        WHERE inv.jogador_id=? AND i.tipo='pocao' AND inv.qtd > 0 LIMIT 1""", (jid,)).fetchone()
    if not linha:
        c.close()
        return jsonify({"msg": "Sem pocao", "estado": estado(jid)})
    inv_id, qtd, n, b = linha
    hp = min(hp_max, hp + b)
    if qtd - 1 <= 0:
        c.execute("DELETE FROM inventario WHERE id=?", (inv_id,))
    else:
        c.execute("UPDATE inventario SET qtd=? WHERE id=?", (qtd-1, inv_id))
    c.execute("UPDATE jogador SET hp=? WHERE id=?", (hp, jid))
    c.commit()
    c.close()
    return jsonify({"msg": "Usou " + n + ". +" + str(b) + " HP", "estado": estado(jid)})

@app.route("/api/loja")
@login_obrigatorio
def api_loja():
    c = con()
    catalogo = c.execute("SELECT id, nome, preco FROM loja_itens").fetchall()
    c.close()
    return jsonify([{"id": i, "nome": n, "preco": p} for i, n, p in catalogo])

@app.route("/api/comprar/<int:item_id>")
@login_obrigatorio
def api_comprar(item_id):
    jid = session["jogador_id"]
    c = con()
    ouro = c.execute("SELECT ouro FROM jogador WHERE id=?", (jid,)).fetchone()[0]
    linha = c.execute("SELECT nome, preco FROM loja_itens WHERE id=?", (item_id,)).fetchone()
    if not linha:
        c.close()
        return jsonify({"msg": "Item nao existe"})
    inome, preco = linha
    if ouro < preco:
        c.close()
        return jsonify({"msg": "Ouro insuficiente"})
    try:
        c.execute("BEGIN")
        c.execute("UPDATE jogador SET ouro = ouro - ? WHERE id=?", (preco, jid))
        item_id_real = c.execute("SELECT id FROM itens WHERE nome=? LIMIT 1", (inome,)).fetchone()
        if not item_id_real:
            c.rollback()
            c.close()
            return jsonify({"msg": "Item sem cadastro"})
        c.execute("INSERT INTO inventario (jogador_id, item_id, qtd) VALUES (?, ?, 1)", (jid, item_id_real[0]))
        c.commit()
    except Exception as e:
        c.rollback()
        c.close()
        return jsonify({"msg": "Erro: " + str(e)})
    c.close()
    return jsonify({"msg": "Comprou " + inome, "estado": estado(jid)})

@app.route("/api/hotbar/salvar", methods=["POST"])
@login_obrigatorio
def api_hotbar_salvar():
    jid = session["jogador_id"]
    d = request.get_json() or {}
    slots = d.get("slots", [])
    clean = []
    for s in slots[:6]:
        try:
            clean.append(int(s) if s else 0)
        except:
            clean.append(0)
    while len(clean) < 6:
        clean.append(0)
    c = con()
    c.execute("UPDATE jogador SET hotbar=? WHERE id=?", (json.dumps(clean), jid))
    c.commit()
    c.close()
    return jsonify({"ok": True, "hotbar": clean})

# ============ CHAT ============

@app.route("/api/chat/mensagens")
@login_obrigatorio
def api_chat_mensagens():
    jid = session["jogador_id"]
    desde = request.args.get("desde", 0, type=int)
    c = con()
    rows = c.execute("""
        SELECT m.id, m.canal, m.texto, m.ts, m.jogador_id,
               j.nome_personagem, j.nome, j.cargo
        FROM mensagens m LEFT JOIN jogador j ON j.id = m.jogador_id
        WHERE m.id > ? AND m.canal IN ('global','sistema')
          AND (m.destinatario IS NULL OR m.destinatario = ?)
        ORDER BY m.id ASC LIMIT 100
    """, (desde, jid)).fetchall()
    c.close()
    out = []
    for r in rows:
        info = CARGOS.get(r[7] or "player", CARGOS["player"])
        out.append({"id": r[0], "canal": r[1], "texto": r[2], "ts": r[3],
                    "jogador_id": r[4], "nome": r[5] or r[6] or "???",
                    "cargo": r[7] or "player", "cor": info["cor"], "badge": info["badge"]})
    return jsonify(out)

@app.route("/api/chat/enviar", methods=["POST"])
@login_obrigatorio
def api_chat_enviar():
    jid = session["jogador_id"]
    d = request.get_json() or {}
    texto = (d.get("texto") or "").strip()
    if not texto:
        return jsonify({"erro": "vazio"})
    if texto.startswith("/"):
        executar_comando(jid, texto)
        return jsonify({"ok": True})
    salvar_mensagem(jid, texto, "global")
    return jsonify({"ok": True})

def guilda_do_jogador(c, jid):
    r = c.execute("""SELECT g.id, g.nome, gm.cargo FROM guilda_membros gm
        JOIN guildas g ON g.id = gm.guilda_id WHERE gm.jogador_id = ?""", (jid,)).fetchone()
    return r

def guilda_lidera(c, jid):
    return c.execute("SELECT id, nome FROM guildas WHERE lider_id = ?", (jid,)).fetchone()

def cmd_guild(jid, args):
    c = con()
    meu = c.execute("SELECT nome_personagem, nome, cargo, ouro FROM jogador WHERE id=?", (jid,)).fetchone()
    meu_nome = meu[0] or meu[1]
    meu_cargo = meu[2]
    meu_ouro = meu[3]
    def resp(t):
        c.close()
        return t
    if not args:
        g = guilda_do_jogador(c, jid)
        if g:
            return resp("Voce esta na guilda [" + g[1] + "] como " + g[2])
        return resp("Uso: /guild criar|convidar|aceitar|sair|info|membros|renomear|expulsar")
    sub = args[0].lower()
    resto = args[1:]
    if sub == "criar":
        if not cargo_ok(meu_cargo, "vip"):
            return resp("Precisa ser VIP+ para criar guilda")
        if not resto:
            return resp("Uso: /guild criar <nome>")
        nome_g = " ".join(resto)[:20].strip()
        if len(nome_g) < 3:
            return resp("Nome muito curto")
        if guilda_lidera(c, jid):
            return resp("Voce ja lidera uma guilda")
        if guilda_do_jogador(c, jid):
            return resp("Saia da guilda atual primeiro")
        ex = c.execute("SELECT id FROM guildas WHERE nome=?", (nome_g,)).fetchone()
        if ex:
            return resp("Ja existe guilda com esse nome")
        c.execute("INSERT INTO guildas (nome, lider_id) VALUES (?, ?)", (nome_g, jid))
        gid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.execute("INSERT INTO guilda_membros (guilda_id, jogador_id, cargo) VALUES (?, ?, 'lider')", (gid, jid))
        c.commit()
        return resp("Guilda [" + nome_g + "] criada! Voce e o lider")
    if sub == "convidar":
        g = guilda_do_jogador(c, jid)
        if not g:
            return resp("Voce nao esta em guilda")
        if g[2] != "lider":
            return resp("So o lider convida")
        if not resto:
            return resp("Uso: /guild convidar <nome>")
        alvo = c.execute("SELECT id, nome_personagem, nome FROM jogador WHERE nome_personagem=? OR nome=?", (resto[0], resto[0])).fetchone()
        if not alvo:
            return resp("Jogador nao encontrado")
        if alvo[0] == jid:
            return resp("Nao pode se convidar")
        if guilda_do_jogador(c, alvo[0]):
            return resp("Ja esta em uma guilda")
        c.execute("INSERT INTO convites_guilda (guilda_id, convidado_id) VALUES (?, ?)", (g[0], alvo[0]))
        c.commit()
        msg_privada(alvo[0], "Convite para [" + g[1] + "]. Use /guild aceitar")
        return resp("Convite enviado para " + (alvo[1] or alvo[2]))
    if sub == "aceitar":
        conv = c.execute("SELECT cg.id, cg.guilda_id, g.nome FROM convites_guilda cg JOIN guildas g ON g.id=cg.guilda_id WHERE cg.convidado_id=? ORDER BY cg.id DESC LIMIT 1", (jid,)).fetchone()
        if not conv:
            return resp("Sem convites pendentes")
        if guilda_do_jogador(c, jid):
            return resp("Voce ja esta em guilda")
        c.execute("INSERT INTO guilda_membros (guilda_id, jogador_id, cargo) VALUES (?, ?, 'membro')", (conv[1], jid))
        c.execute("DELETE FROM convites_guilda WHERE id=?", (conv[0],))
        c.commit()
        return resp("Entrou na guilda [" + conv[2] + "]")
    if sub == "sair":
        g = guilda_do_jogador(c, jid)
        if not g:
            return resp("Voce nao esta em guilda")
        if g[2] == "lider":
            membros = c.execute("SELECT jogador_id FROM guilda_membros WHERE guilda_id=? AND jogador_id!=?", (g[0], jid)).fetchall()
            if not membros:
                c.execute("DELETE FROM guilda_membros WHERE guilda_id=?", (g[0],))
                c.execute("DELETE FROM guildas WHERE id=?", (g[0],))
                c.commit()
                return resp("Guilda [" + g[1] + "] dissolvida")
            novo = membros[0][0]
            c.execute("UPDATE guildas SET lider_id=? WHERE id=?", (novo, g[0]))
            c.execute("UPDATE guilda_membros SET cargo='lider' WHERE guilda_id=? AND jogador_id=?", (g[0], novo))
            c.execute("DELETE FROM guilda_membros WHERE guilda_id=? AND jogador_id=?", (g[0], jid))
            c.commit()
            return resp("Saiu. Lideranca transferida")
        c.execute("DELETE FROM guilda_membros WHERE guilda_id=? AND jogador_id=?", (g[0], jid))
        c.commit()
        return resp("Saiu da guilda [" + g[1] + "]")
    if sub == "info":
        g = guilda_do_jogador(c, jid)
        if not g:
            return resp("Voce nao esta em guilda")
        lider = c.execute("SELECT nome_personagem, nome FROM jogador WHERE id=(SELECT lider_id FROM guildas WHERE id=?)", (g[0],)).fetchone()
        nm = c.execute("SELECT COUNT(*) FROM guilda_membros WHERE guilda_id=?", (g[0],)).fetchone()[0]
        return resp("[" + g[1] + "] | Lider: " + (lider[0] or lider[1]) + " | " + str(nm) + " membros | Voce: " + g[2])
    if sub == "membros":
        g = guilda_do_jogador(c, jid)
        if not g:
            return resp("Voce nao esta em guilda")
        mems = c.execute("SELECT j.nome_personagem, j.nome, gm.cargo FROM guilda_membros gm JOIN jogador j ON j.id=gm.jogador_id WHERE gm.guilda_id=? ORDER BY gm.cargo DESC", (g[0],)).fetchall()
        return resp("Membros: " + " | ".join([(m[0] or m[1]) + "(" + m[2] + ")" for m in mems]))
    if sub == "renomear":
        g = guilda_do_jogador(c, jid)
        if not g:
            return resp("Voce nao esta em guilda")
        if g[2] != "lider":
            return resp("So o lider renomeia")
        if not resto:
            return resp("Uso: /guild renomear <nome>")
        novo_nome = " ".join(resto)[:20].strip()
        if len(novo_nome) < 3:
            return resp("Nome muito curto")
        ex = c.execute("SELECT id FROM guildas WHERE nome=?", (novo_nome,)).fetchone()
        if ex:
            return resp("Ja existe guilda com esse nome")
        CUSTO = 5000000
        if meu_ouro < CUSTO:
            return resp("Custa 5.000.000 ouro. Voce tem " + str(meu_ouro))
        c.execute("UPDATE jogador SET ouro = ouro - ? WHERE id=?", (CUSTO, jid))
        c.execute("UPDATE guildas SET nome=? WHERE id=?", (novo_nome, g[0]))
        c.commit()
        return resp("Renomeada para [" + novo_nome + "]. -5.000.000 ouro")
    if sub == "expulsar":
        g = guilda_do_jogador(c, jid)
        if not g or g[2] != "lider":
            return resp("So o lider expulsa")
        if not resto:
            return resp("Uso: /guild expulsar <nome>")
        alvo = c.execute("SELECT id, nome_personagem, nome FROM jogador WHERE nome_personagem=? OR nome=?", (resto[0], resto[0])).fetchone()
        if not alvo:
            return resp("Nao encontrado")
        if alvo[0] == jid:
            return resp("Use /guild sair")
        c.execute("DELETE FROM guilda_membros WHERE guilda_id=? AND jogador_id=?", (g[0], alvo[0]))
        c.commit()
        msg_privada(alvo[0], "Expulso da guilda [" + g[1] + "]")
        return resp("Expulsou " + (alvo[1] or alvo[2]))
    return resp("Sub-comando desconhecido")


def cmd_amigo(jid, args):
    c = con()
    meu = c.execute("SELECT nome_personagem, nome FROM jogador WHERE id=?", (jid,)).fetchone()
    meu_nome = meu[0] or meu[1]
    def resp(t):
        c.close()
        return t
    if not args:
        return resp("Uso: /amigo add|aceitar|remover|listar")
    sub = args[0].lower()
    resto = args[1:]
    if sub == "add":
        if not resto:
            return resp("Uso: /amigo add <nome>")
        alvo = c.execute("SELECT id, nome_personagem, nome FROM jogador WHERE nome_personagem=? OR nome=?", (resto[0], resto[0])).fetchone()
        if not alvo:
            return resp("Jogador nao encontrado")
        if alvo[0] == jid:
            return resp("Nao pode se adicionar")
        # Verifica se ja tem amizade
        ex = c.execute("SELECT id, status FROM amizades WHERE (solicitante_id=? AND destinatario_id=?) OR (solicitante_id=? AND destinatario_id=?)", (jid, alvo[0], alvo[0], jid)).fetchone()
        if ex:
            if ex[1] == "aceita":
                return resp("Ja sao amigos")
            else:
                return resp("Pedido pendente")
        c.execute("INSERT INTO amizades (solicitante_id, destinatario_id, status) VALUES (?, ?, 'pendente')", (jid, alvo[0]))
        c.commit()
        msg_privada(alvo[0], meu_nome + " quer ser seu amigo. Use /amigo aceitar " + meu_nome)
        return resp("Pedido enviado para " + (alvo[1] or alvo[2]))
    if sub == "aceitar":
        if not resto:
            return resp("Uso: /amigo aceitar <nome>")
        quem = c.execute("SELECT id, nome_personagem, nome FROM jogador WHERE nome_personagem=? OR nome=?", (resto[0], resto[0])).fetchone()
        if not quem:
            return resp("Nao encontrado")
        ped = c.execute("SELECT id FROM amizades WHERE solicitante_id=? AND destinatario_id=? AND status='pendente'", (quem[0], jid)).fetchone()
        if not ped:
            return resp("Sem pedido pendente desse jogador")
        c.execute("UPDATE amizades SET status='aceita' WHERE id=?", (ped[0],))
        c.commit()
        msg_privada(quem[0], meu_nome + " aceitou seu pedido de amizade!")
        return resp("Agora voce e amigo de " + (quem[1] or quem[2]))
    if sub == "remover":
        if not resto:
            return resp("Uso: /amigo remover <nome>")
        alvo = c.execute("SELECT id, nome_personagem, nome FROM jogador WHERE nome_personagem=? OR nome=?", (resto[0], resto[0])).fetchone()
        if not alvo:
            return resp("Nao encontrado")
        c.execute("DELETE FROM amizades WHERE (solicitante_id=? AND destinatario_id=?) OR (solicitante_id=? AND destinatario_id=?)", (jid, alvo[0], alvo[0], jid))
        c.commit()
        return resp("Removeu " + (alvo[1] or alvo[2]) + " dos amigos")
    if sub == "listar" or sub == "lista":
        rows = c.execute("""SELECT j.id, j.nome_personagem, j.nome, j.cargo, j.ultimo_visto
            FROM amizades a
            JOIN jogador j ON (j.id = a.solicitante_id OR j.id = a.destinatario_id)
            WHERE a.status='aceita' AND (a.solicitante_id=? OR a.destinatario_id=?) AND j.id != ?""",
            (jid, jid, jid)).fetchall()
        if not rows:
            return resp("Sem amigos ainda. Use /amigo add <nome>")
        agora = time.time()
        partes = []
        for r in rows:
            online = (r[4] and (agora - r[4]) < 15)
            simbolo = "🟢" if online else "⚫"
            partes.append(simbolo + " " + (r[1] or r[2]))
        return resp("Amigos: " + " | ".join(partes))
    if sub == "pedidos" or sub == "solicitacoes":
        rows = c.execute("""SELECT j.nome_personagem, j.nome FROM amizades a
            JOIN jogador j ON j.id=a.solicitante_id
            WHERE a.destinatario_id=? AND a.status='pendente'""", (jid,)).fetchall()
        if not rows:
            return resp("Sem pedidos pendentes")
        return resp("Pedidos de: " + " | ".join([(r[0] or r[1]) for r in rows]))
    return resp("Sub-comando /amigo " + sub + " desconhecido")


def executar_comando(jid, texto):
    c = con()
    eu = c.execute("SELECT nome_personagem, nome, cargo FROM jogador WHERE id=?", (jid,)).fetchone()
    if not eu:
        c.close()
        return
    meu_nome = eu[0] or eu[1]
    meu_cargo = eu[2] or "player"
    c.close()
    partes = texto[1:].split()
    cmd = partes[0].lower() if partes else ""
    args = partes[1:]
    if cmd in ("ajuda", "help"):
        linhas = ["[bases] /ajuda /online /me /ping /perfil /onde /troca"]
        if cargo_ok(meu_cargo, "mod"):
            linhas.append("[mod] /kick /mute /limpar /dar")
        if cargo_ok(meu_cargo, "admin"):
            linhas.append("[admin] /spawn /limpamobs /cargo /hp /nivel")
        if meu_cargo == "dev":
            linhas.append("[dev] /sql /console")
        msg_privada(jid, " | ".join(linhas))
        return
    if cmd == "ping":
        msg_privada(jid, "pong"); return
    if cmd == "online":
        c = con(); n = c.execute("SELECT COUNT(*) FROM jogador WHERE personagem_criado=1").fetchone()[0]; c.close()
        msg_privada(jid, "Total: " + str(n) + " personagens"); return
    if cmd == "me":
        if not args: msg_privada(jid, "Uso: /me <acao>"); return
        salvar_mensagem(jid, "* " + meu_nome + " " + " ".join(args), "global"); return
    if cmd == "perfil":
        c = con()
        alvo = achar_jogador(c, args[0]) if args else None
        jid_alvo = alvo[0] if alvo else jid
        d = c.execute("SELECT nome_personagem, nome, classe, cargo, nivel, hp, hp_max, ouro FROM jogador WHERE id=?", (jid_alvo,)).fetchone()
        c.close()
        if not d: msg_privada(jid, "Nao achei"); return
        info = CARGOS.get(d[3], CARGOS["player"])
        msg_privada(jid, f"{info['badge']} {d[0] or d[1]} | {d[2]} | Nv {d[4]} | HP {d[5]}/{d[6]} | {d[7]} ouro")
        return
    if cmd == "onde":
        c = con()
        if args:
            a = achar_jogador(c, args[0])
            if not a: c.close(); msg_privada(jid, "Nao achei"); return
            x, y = c.execute("SELECT x, y FROM jogador WHERE id=?", (a[0],)).fetchone()
            c.close(); msg_privada(jid, f"{a[1] or a[2]} esta em ({x},{y})")
        else:
            x, y = c.execute("SELECT x, y FROM jogador WHERE id=?", (jid,)).fetchone()
            c.close(); msg_privada(jid, f"Voce esta em ({x},{y})")
        return
    if cmd == "troca":
        resultado = executar_troca(jid, args)
        msg_privada(jid, resultado)
        return
    if cmd in ("guild", "guilda", "g"):
        resultado = cmd_guild(jid, args)
        msg_privada(jid, resultado)
        return
    if cmd in ("amigo", "amigos", "amiga"):
        resultado = cmd_amigo(jid, args)
        msg_privada(jid, resultado)
        return
    if cmd == "sql":
        if meu_cargo != "dev": msg_privada(jid, "So dev"); return
        if not args: msg_privada(jid, "Uso: /sql <select>"); return
        q = " ".join(args)
        if not q.strip().lower().startswith("select"): msg_privada(jid, "Apenas SELECT"); return
        try:
            c = con(); r = c.execute(q).fetchall()[:5]; c.close()
            msg_privada(jid, "SQL: " + str(r)[:200])
        except Exception as e:
            msg_privada(jid, "Erro: " + str(e)[:100])
        return
    msg_privada(jid, "Comando /" + cmd + " desconhecido")

# ============ PAINEL ============

@app.route("/painel")
@login_obrigatorio
def painel():
    jid = session["jogador_id"]
    c = con()
    cargo = c.execute("SELECT cargo FROM jogador WHERE id=?", (jid,)).fetchone()[0]
    c.close()
    if not cargo_ok(cargo, "mod"):
        return redirect(url_for("home"))
    return render_template("painel.html", cargo=cargo, cargos=CARGOS)

@app.route("/api/painel/jogadores")
@login_obrigatorio
def api_painel_jogadores():
    jid = session["jogador_id"]
    c = con()
    cargo = c.execute("SELECT cargo FROM jogador WHERE id=?", (jid,)).fetchone()[0]
    if not cargo_ok(cargo, "mod"):
        c.close(); return jsonify({"erro": "sem permissao"}), 403
    lista = c.execute("SELECT id, nome, nome_personagem, classe, cargo, nivel, hp, hp_max, ouro FROM jogador ORDER BY id").fetchall()
    c.close()
    return jsonify([{"id": r[0], "login": r[1], "nome": r[2] or r[1], "classe": r[3],
        "cargo": r[4], "nivel": r[5], "hp": r[6], "hp_max": r[7], "ouro": r[8],
        "cargo_cor": CARGOS.get(r[4], CARGOS["player"])["cor"],
        "cargo_badge": CARGOS.get(r[4], CARGOS["player"])["badge"]} for r in lista])

@app.route("/api/mod/curar/<int:alvo>")
@login_obrigatorio
def mod_curar(alvo):
    jid = session["jogador_id"]
    c = con()
    cargo = c.execute("SELECT cargo FROM jogador WHERE id=?", (jid,)).fetchone()[0]
    if not cargo_ok(cargo, "ajudante"):
        c.close(); return jsonify({"erro": "sem permissao"}), 403
    c.execute("UPDATE jogador SET hp=hp_max WHERE id=?", (alvo,)); c.commit(); c.close()
    return jsonify({"msg": "Curado #" + str(alvo)})

@app.route("/api/mod/ouro/<int:alvo>/<int:valor>")
@login_obrigatorio
def mod_ouro(alvo, valor):
    jid = session["jogador_id"]
    c = con()
    cargo = c.execute("SELECT cargo FROM jogador WHERE id=?", (jid,)).fetchone()[0]
    if not cargo_ok(cargo, "mod") or (not cargo_ok(cargo, "admin") and abs(valor) > 100):
        c.close(); return jsonify({"erro": "sem permissao"}), 403
    c.execute("UPDATE jogador SET ouro=ouro+? WHERE id=?", (valor, alvo)); c.commit(); c.close()
    return jsonify({"msg": "Ouro +" + str(valor)})

@app.route("/api/mod/cargo/<int:alvo>/<novo_cargo>")
@login_obrigatorio
def mod_cargo(alvo, novo_cargo):
    jid = session["jogador_id"]
    c = con()
    cargo = c.execute("SELECT cargo FROM jogador WHERE id=?", (jid,)).fetchone()[0]
    if not cargo_ok(cargo, "admin") or novo_cargo not in CARGOS:
        c.close(); return jsonify({"erro": "sem permissao"}), 403
    c.execute("UPDATE jogador SET cargo=? WHERE id=?", (novo_cargo, alvo)); c.commit(); c.close()
    return jsonify({"msg": "Cargo -> " + novo_cargo})


@app.route("/api/atacar")
@login_obrigatorio
def api_atacar():
    jid = session["jogador_id"]
    c = con()
    hp, ouro, x, y, xp, nivel, hp_max = c.execute(
        "SELECT hp, ouro, x, y, xp, nivel, hp_max FROM jogador WHERE id=?", (jid,)).fetchone()
    # acha monstro mais proximo em 2 tiles
    alvo = None
    dist_min = 999
    for m in c.execute("SELECT id, nome, x, y, hp, dano FROM monstros").fetchall():
        d = abs(m[2] - x) + abs(m[3] - y)
        if d <= 2 and d < dist_min:
            dist_min = d
            alvo = m
    if not alvo:
        c.close()
        return jsonify({"msg": "Nenhum monstro por perto", "estado": estado(jid)})
    mid, mnome, mx, my, mhp, mdano = alvo
    arma = c.execute("""SELECT i.bonus FROM inventario inv JOIN itens i ON i.id=inv.item_id
        WHERE inv.jogador_id=? AND i.tipo='arma' ORDER BY i.bonus DESC LIMIT 1""", (jid,)).fetchone()
    bonus = arma[0] if arma else 0
    dano = random.randint(8, 15) + bonus
    mhp_novo = mhp - dano
    if mhp_novo <= 0:
        ganho = random.randint(5, 15)
        ouro += ganho
        xp_ganho = XP_MONSTRO.get(mnome, 10)
        xp += xp_ganho
        subiu = False
        while xp >= int(100 * (nivel ** 1.5)):
            xp -= int(100 * (nivel ** 1.5))
            nivel += 1
            hp_max += 20
            hp = hp_max
            subiu = True
        msg = "Matou " + mnome + "! -" + str(dano) + " dano, +" + str(ganho) + " ouro, +" + str(xp_ganho) + " XP"
        if subiu:
            msg += "  LEVEL UP! Nv " + str(nivel)
        c.execute("DELETE FROM monstros WHERE id=?", (mid,))
        nascer_monstro(c, x, y)
    else:
        msg = "Atingiu " + mnome + " com " + str(dano) + " dano (HP: " + str(mhp_novo) + "/" + str(mhp) + ")"
        c.execute("UPDATE monstros SET hp=? WHERE id=?", (mhp_novo, mid))
    c.execute("UPDATE jogador SET hp=?, ouro=?, xp=?, nivel=?, hp_max=? WHERE id=?",
              (hp, ouro, xp, nivel, hp_max, jid))
    c.commit()
    c.close()
    return jsonify({"msg": msg, "estado": estado(jid)})




@app.route("/api/guild/info")
@login_obrigatorio
def api_guild_info():
    jid = session["jogador_id"]
    c = con()
    g = guilda_do_jogador(c, jid)
    if not g:
        c.close()
        return jsonify({"tem": False})
    lider = c.execute("SELECT nome_personagem, nome FROM jogador WHERE id=(SELECT lider_id FROM guildas WHERE id=?)", (g[0],)).fetchone()
    mems = c.execute("""SELECT j.id, j.nome_personagem, j.nome, j.cargo, gm.cargo, j.ultimo_visto
        FROM guilda_membros gm JOIN jogador j ON j.id=gm.jogador_id
        WHERE gm.guilda_id=? ORDER BY gm.cargo DESC, j.nivel DESC""", (g[0],)).fetchall()
    agora = time.time()
    lista = []
    for m in mems:
        lista.append({
            "id": m[0], "nome": m[1] or m[2], "cargo_player": m[3],
            "cargo_guilda": m[4],
            "online": m[5] and (agora - m[5]) < 15
        })
    c.close()
    return jsonify({
        "tem": True, "id": g[0], "nome": g[1], "cargo_meu": g[2],
        "lider": lider[0] or lider[1] if lider else "?",
        "membros": lista
    })

@app.route("/api/guild/acoes")
@login_obrigatorio
def api_guild_acoes():
    jid = session["jogador_id"]
    c = con()
    g = guilda_do_jogador(c, jid)
    c.close()
    pode_criar = False
    c = con()
    meu = c.execute("SELECT cargo FROM jogador WHERE id=?", (jid,)).fetchone()
    if meu and cargo_ok(meu[0], "vip"):
        pode_criar = True
    ja_lidera = bool(guilda_lidera(c, jid))
    c.close()
    return jsonify({"pode_criar": pode_criar, "ja_lidera": ja_lidera})

@app.route("/api/amigos/listar")
@login_obrigatorio
def api_amigos_listar():
    jid = session["jogador_id"]
    c = con()
    rows = c.execute("""SELECT j.id, j.nome_personagem, j.nome, j.cargo, j.ultimo_visto
        FROM amizades a JOIN jogador j ON (j.id = a.solicitante_id OR j.id = a.destinatario_id)
        WHERE a.status='aceita' AND (a.solicitante_id=? OR a.destinatario_id=?) AND j.id != ?""",
        (jid, jid, jid)).fetchall()
    agora = time.time()
    amigos = []
    for r in rows:
        amigos.append({"id": r[0], "nome": r[1] or r[2], "cargo": r[3],
                       "online": r[4] and (agora - r[4]) < 15})
    # pedidos pendentes
    ped = c.execute("""SELECT j.id, j.nome_personagem, j.nome FROM amizades a
        JOIN jogador j ON j.id=a.solicitante_id
        WHERE a.destinatario_id=? AND a.status='pendente'""", (jid,)).fetchall()
    pedidos = [{"id": p[0], "nome": p[1] or p[2]} for p in ped]
    c.close()
    return jsonify({"amigos": amigos, "pedidos": pedidos})

@app.route("/api/guild/acao", methods=["POST"])
@login_obrigatorio
def api_guild_acao():
    jid = session["jogador_id"]
    d = request.get_json() or {}
    acao = d.get("acao", "")
    args = []
    if acao == "criar": args = ["criar", d.get("nome", "")]
    elif acao == "convidar": args = ["convidar", d.get("nome", "")]
    elif acao == "aceitar": args = ["aceitar"]
    elif acao == "sair": args = ["sair"]
    elif acao == "renomear": args = ["renomear", d.get("nome", "")]
    elif acao == "expulsar": args = ["expulsar", d.get("nome", "")]
    r = cmd_guild(jid, args)
    return jsonify({"msg": r})

@app.route("/api/amigos/acao", methods=["POST"])
@login_obrigatorio
def api_amigos_acao():
    jid = session["jogador_id"]
    d = request.get_json() or {}
    acao = d.get("acao", "")
    args = []
    if acao == "add": args = ["add", d.get("nome", "")]
    elif acao == "aceitar": args = ["aceitar", d.get("nome", "")]
    elif acao == "remover": args = ["remover", d.get("nome", "")]
    r = cmd_amigo(jid, args)
    return jsonify({"msg": r})



@app.route("/api/chat/guild")
@login_obrigatorio
def api_chat_guild_msg():
    jid = session["jogador_id"]
    desde = request.args.get("desde", 0, type=int)
    c = con()
    g = guilda_do_jogador(c, jid)
    if not g:
        c.close()
        return jsonify([])
    rows = c.execute("""SELECT m.id, m.texto, m.ts, m.jogador_id, j.nome_personagem, j.nome, j.cargo
        FROM mensagens m LEFT JOIN jogador j ON j.id = m.jogador_id
        WHERE m.canal='guilda' AND m.guilda_id=? AND m.id > ?
        ORDER BY m.id ASC LIMIT 50""", (g[0], desde)).fetchall()
    c.close()
    out = []
    for r in rows:
        info = CARGOS.get(r[6] or "player", CARGOS["player"])
        out.append({"id": r[0], "texto": r[1], "ts": r[2], "jogador_id": r[3],
                    "nome": r[4] or r[5] or "?", "cor": info["cor"], "badge": info["badge"]})
    return jsonify(out)

@app.route("/api/chat/guild/enviar", methods=["POST"])
@login_obrigatorio
def api_chat_guild_enviar():
    jid = session["jogador_id"]
    d = request.get_json() or {}
    texto = (d.get("texto") or "").strip()
    if not texto:
        return jsonify({"erro": "vazio"})
    c = con()
    g = guilda_do_jogador(c, jid)
    if not g:
        c.close()
        return jsonify({"erro": "sem guilda"})
    row = c.execute("SELECT x, y FROM jogador WHERE id=?", (jid,)).fetchone()
    x, y = row if row else (None, None)
    c.execute("INSERT INTO mensagens (jogador_id, canal, texto, x, y, guilda_id) VALUES (?, 'guilda', ?, ?, ?, ?)",
              (jid, texto[:200], x, y, g[0]))
    c.commit()
    c.close()
    return jsonify({"ok": True})

@app.route("/api/chat/privado/<int:amigo_id>")
@login_obrigatorio
def api_chat_priv_msg(amigo_id):
    jid = session["jogador_id"]
    desde = request.args.get("desde", 0, type=int)
    c = con()
    # Verifica se sao amigos
    amigo = c.execute("""SELECT 1 FROM amizades WHERE status='aceita'
        AND ((solicitante_id=? AND destinatario_id=?) OR (solicitante_id=? AND destinatario_id=?))""",
        (jid, amigo_id, amigo_id, jid)).fetchone()
    if not amigo:
        c.close()
        return jsonify([])
    rows = c.execute("""SELECT m.id, m.texto, m.ts, m.jogador_id, j.nome_personagem, j.nome, j.cargo
        FROM mensagens m LEFT JOIN jogador j ON j.id = m.jogador_id
        WHERE m.canal='privado' AND m.id > ?
          AND ((m.jogador_id=? AND m.destinatario=?) OR (m.jogador_id=? AND m.destinatario=?))
        ORDER BY m.id ASC LIMIT 50""",
        (desde, jid, amigo_id, amigo_id, jid)).fetchall()
    c.close()
    out = []
    for r in rows:
        info = CARGOS.get(r[6] or "player", CARGOS["player"])
        out.append({"id": r[0], "texto": r[1], "ts": r[2], "jogador_id": r[3],
                    "nome": r[4] or r[5] or "?", "cor": info["cor"], "badge": info["badge"]})
    return jsonify(out)

@app.route("/api/chat/privado/<int:amigo_id>/enviar", methods=["POST"])
@login_obrigatorio
def api_chat_priv_enviar(amigo_id):
    jid = session["jogador_id"]
    d = request.get_json() or {}
    texto = (d.get("texto") or "").strip()
    if not texto:
        return jsonify({"erro": "vazio"})
    c = con()
    amigo = c.execute("""SELECT 1 FROM amizades WHERE status='aceita'
        AND ((solicitante_id=? AND destinatario_id=?) OR (solicitante_id=? AND destinatario_id=?))""",
        (jid, amigo_id, amigo_id, jid)).fetchone()
    if not amigo:
        c.close()
        return jsonify({"erro": "nao e amigo"})
    row = c.execute("SELECT x, y FROM jogador WHERE id=?", (jid,)).fetchone()
    x, y = row if row else (None, None)
    c.execute("INSERT INTO mensagens (jogador_id, canal, texto, x, y, destinatario) VALUES (?, 'privado', ?, ?, ?, ?)",
              (jid, texto[:200], x, y, amigo_id))
    c.commit()
    c.close()
    return jsonify({"ok": True})

if __name__ == "__main__":
    carregar_mapa()
    # zera monstros pra nascer tudo do zero
    c = con()
    c.execute("DELETE FROM monstros")
    c.commit()
    for _ in range(20):
        nascer_monstro(c, 5, 5)
    c.commit()
    c.close()
import os
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
