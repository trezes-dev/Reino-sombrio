from flask import Flask, render_template, jsonify, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, random, functools, time, json, threading

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
                t = "grama"
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
    return tile_em(x, y) in ("agua",)

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
        WHERE inv.jogador_id=? AND i.tipo='arma' AND inv.equipado=1 LIMIT 1""", (jid,)).fetchone()
    inv = c.execute("""SELECT i.nome, i.tipo, i.bonus, inv.qtd, i.id, inv.id, COALESCE(inv.equipado,0)
        FROM inventario inv JOIN itens i ON i.id=inv.item_id
        WHERE inv.jogador_id=? ORDER BY inv.equipado DESC, i.bonus DESC""", (jid,)).fetchall()
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
    noclip_ativo = c.execute("SELECT COALESCE(noclip,0) FROM jogador WHERE id=?", (jid,)).fetchone()[0]
    if not noclip_ativo and bloqueia(nx, ny):
        c.close()
        return jsonify({"msg": "Bloqueado por " + tile_em(nx, ny), "estado": estado(jid)})
    x, y = nx, ny
    c.execute("UPDATE jogador SET x=?, y=?, ultimo_visto=? WHERE id=?", (x, y, time.time(), jid))
    msg = "Andou para " + dir
    m = c.execute("SELECT id, nome, dano FROM monstros WHERE x=? AND y=?", (x, y)).fetchone()
    if m:
        mid, mnome, mdano = m
        arma = c.execute("""SELECT i.bonus FROM inventario inv JOIN itens i ON i.id=inv.item_id
            WHERE inv.jogador_id=? AND i.tipo='arma' AND inv.equipado=1 LIMIT 1""", (jid,)).fetchone()
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

@app.route("/api/interagir")
@login_obrigatorio
def api_interagir():
    jid = session["jogador_id"]
    c = con()
    x, y = c.execute("SELECT x, y FROM jogador WHERE id=?", (jid,)).fetchone()
    npc = c.execute("""SELECT id, nome, tipo FROM npcs
        WHERE (x=? AND y=?) OR (x=? AND y=?) OR (x=? AND y=?) OR (x=? AND y=?) OR (x=? AND y=?)
        LIMIT 1""",
        (x, y, x+1, y, x-1, y, x, y+1, x, y-1)).fetchone()
    c.close()
    if not npc:
        return jsonify({"acao": "nada", "msg": "Nada por perto"})
    if npc[2] in ("loja", "ferreiro", "alquimista"):
        return jsonify({"acao": "abrir_loja", "npc_nome": npc[1], "npc_id": npc[0]})
    return jsonify({"acao": "nada", "msg": "Nada para interagir aqui"})

@app.route("/api/loja/itens")
@login_obrigatorio
def api_loja_itens():
    npc_id = request.args.get("npc_id", 0, type=int)
    c = con()
    if npc_id:
        rows = c.execute("""SELECT l.id, l.preco, l.regiao, i.nome, i.tipo, i.bonus, i.id
            FROM loja_itens l JOIN itens i ON i.id=l.item_id
            WHERE l.npc_id=? ORDER BY l.preco ASC""", (npc_id,)).fetchall()
    else:
        rows = c.execute("""SELECT l.id, l.preco, l.regiao, i.nome, i.tipo, i.bonus, i.id
            FROM loja_itens l JOIN itens i ON i.id=l.item_id
            ORDER BY l.preco ASC""").fetchall()
    c.close()
    return jsonify([{"id": r[0], "preco": r[1], "regiao": r[2], "nome": r[3],
                     "tipo": r[4], "bonus": r[5], "item_id": r[6]} for r in rows])

@app.route("/api/comprar/<int:loja_id>", methods=["GET", "POST"])
@login_obrigatorio
def api_comprar(loja_id):
    jid = session["jogador_id"]
    qtd = 1
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        try: qtd = max(1, int(data.get("qtd", 1)))
        except: qtd = 1
    c = con()
    ouro = c.execute("SELECT ouro FROM jogador WHERE id=?", (jid,)).fetchone()[0]
    linha = c.execute("SELECT item_id, preco FROM loja_itens WHERE id=?", (loja_id,)).fetchone()
    if not linha:
        c.close()
        return jsonify({"msg": "Item nao existe"})
    item_id, preco = linha
    total = preco * qtd
    if ouro < total:
        c.close()
        return jsonify({"msg": "Ouro insuficiente"})
    try:
        c.execute("BEGIN")
        c.execute("UPDATE jogador SET ouro = ouro - ? WHERE id=?", (total, jid))
        existe = c.execute("SELECT id, qtd FROM inventario WHERE jogador_id=? AND item_id=?",
                           (jid, item_id)).fetchone()
        if existe:
            c.execute("UPDATE inventario SET qtd = qtd + ? WHERE id=?", (qtd, existe[0]))
        else:
            c.execute("INSERT INTO inventario (jogador_id, item_id, qtd) VALUES (?, ?, ?)",
                      (jid, item_id, qtd))
        c.commit()
    except Exception as e:
        c.rollback()
        c.close()
        return jsonify({"msg": "Erro: " + str(e)})
    c.close()
    return jsonify({"msg": "Comprado x" + str(qtd) + "!", "estado": estado(jid)})



@app.route("/api/atacar")
@login_obrigatorio
def api_atacar():
    jid = session["jogador_id"]
    c = con()
    hp, ouro, x, y, xp, nivel, hp_max = c.execute(
        "SELECT hp, ouro, x, y, xp, nivel, hp_max FROM jogador WHERE id=?", (jid,)).fetchone()
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
        WHERE inv.jogador_id=? AND i.tipo='arma' AND inv.equipado=1 LIMIT 1""", (jid,)).fetchone()
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
        msg = "Matou " + mnome + "! +" + str(xp_ganho) + " XP"
        if subiu:
            msg += "  LEVEL UP! Nv " + str(nivel)
        c.execute("DELETE FROM monstros WHERE id=?", (mid,))
    else:
        msg = "Atingiu " + mnome + " (-" + str(dano) + " HP)"
        c.execute("UPDATE monstros SET hp=? WHERE id=?", (mhp_novo, mid))
    c.execute("UPDATE jogador SET hp=?, ouro=?, xp=?, nivel=?, hp_max=? WHERE id=?",
              (hp, ouro, xp, nivel, hp_max, jid))
    c.commit()
    c.close()
    return jsonify({"msg": msg, "estado": estado(jid)})



@app.route("/api/chat/mensagens")
@login_obrigatorio
def api_chat_mensagens():
    desde = request.args.get("desde", 0, type=int)
    c = con()
    rows = c.execute("""SELECT m.id, m.canal, m.texto, m.ts, m.jogador_id,
               j.nome_personagem, j.nome, j.cargo
        FROM mensagens m LEFT JOIN jogador j ON j.id = m.jogador_id
        WHERE m.id > ? AND m.canal IN ('global','sistema')
        ORDER BY m.id ASC LIMIT 100""", (desde,)).fetchall()
    c.close()
    out = []
    for r in rows:
        info = CARGOS.get(r[7] or "player", CARGOS["player"])
        out.append({"id": r[0], "canal": r[1], "texto": r[2], "ts": r[3],
                    "jogador_id": r[4], "nome": r[5] or r[6] or "???",
                    "cargo": r[7] or "player", "cor": info["cor"], "badge": info["badge"]})
    return jsonify(out)



@app.route("/api/equipar/<int:inv_id>", methods=["POST"])
@login_obrigatorio
def api_equipar(inv_id):
    jid = session["jogador_id"]
    c = con()
    row = c.execute("""SELECT inv.id, inv.jogador_id, i.nome, i.tipo, i.bonus
        FROM inventario inv JOIN itens i ON i.id=inv.item_id
        WHERE inv.id=?""", (inv_id,)).fetchone()
    if not row:
        c.close()
        return jsonify({"msg": "Item nao encontrado", "estado": estado(jid)})
    inv_id, dono, nome, tipo, bonus = row
    if dono != jid:
        c.close()
        return jsonify({"msg": "Esse item nao e seu", "estado": estado(jid)})
    if tipo not in ("arma", "escudo"):
        c.close()
        return jsonify({"msg": "Esse item nao pode ser equipado", "estado": estado(jid)})

    ja = c.execute("SELECT equipado FROM inventario WHERE id=?", (inv_id,)).fetchone()[0]
    if ja == 1:
        c.execute("UPDATE inventario SET equipado=0 WHERE id=?", (inv_id,))
        msg = "Desequipou " + nome
    else:
        c.execute("""UPDATE inventario SET equipado=0
            WHERE jogador_id=? AND item_id IN (SELECT id FROM itens WHERE tipo=?)""", (jid, tipo))
        c.execute("UPDATE inventario SET equipado=1 WHERE id=?", (inv_id,))
        msg = "Equipou " + nome

    total = c.execute("""SELECT COALESCE(SUM(i.bonus), 0) FROM inventario inv
        JOIN itens i ON i.id=inv.item_id
        WHERE inv.jogador_id=? AND inv.equipado=1 AND i.tipo IN ('arma', 'escudo')""", (jid,)).fetchone()[0]
    c.execute("UPDATE jogador SET dano_bonus=? WHERE id=?", (total, jid))
    c.commit()
    c.close()
    return jsonify({"msg": msg, "estado": estado(jid)})



@app.route("/api/hotbar/salvar", methods=["POST"])
@login_obrigatorio
def api_hotbar_salvar():
    jid = session["jogador_id"]
    data = request.get_json(silent=True) or {}
    slots = data.get("slots", [])
    if not isinstance(slots, list):
        return jsonify({"msg": "Formato invalido"}), 400
    slots = [int(x) if str(x).isdigit() else 0 for x in slots][:8]
    while len(slots) < 8:
        slots.append(0)
    c = con()
    c.execute("UPDATE jogador SET hotbar=? WHERE id=?", (json.dumps(slots), jid))
    c.commit()
    c.close()
    return jsonify({"msg": "Hotbar salva", "slots": slots})



@app.route("/api/dev/acao", methods=["POST"])
@login_obrigatorio
def api_dev_acao():
    jid = session["jogador_id"]
    c = con()
    row = c.execute("SELECT cargo FROM jogador WHERE id=?", (jid,)).fetchone()
    cargo = row[0] if row else "player"
    permitidos = ["ajudante", "mod", "admin", "dev"]
    if cargo not in permitidos:
        c.close()
        return jsonify({"erro": "Sem permissao"}), 403

    data = request.get_json(silent=True) or {}
    acao = data.get("acao")
    valor = data.get("valor")

    if acao == "god":
        if cargo != "dev":
            c.close()
            return jsonify({"erro": "Apenas dev"}), 403
        atual = c.execute("SELECT god FROM jogador WHERE id=?", (jid,)).fetchone()[0] or 0
        novo = 0 if atual else 1
        c.execute("UPDATE jogador SET god=? WHERE id=?", (novo, jid))
        msg = "God " + ("ON" if novo else "OFF")
    elif acao == "curar":
        c.execute("UPDATE jogador SET hp=hp_max WHERE id=?", (jid,))
        msg = "Curado"
    elif acao == "ouro":
        try: v = int(valor)
        except: v = 0
        c.execute("UPDATE jogador SET ouro=MAX(0, ouro+?) WHERE id=?", (v, jid))
        msg = "+" + str(v) + " ouro"
    elif acao == "setar_ouro":
        if cargo != "dev":
            c.close()
            return jsonify({"erro": "Apenas dev"}), 403
        try: v = max(0, int(valor))
        except: v = 0
        c.execute("UPDATE jogador SET ouro=? WHERE id=?", (v, jid))
        msg = "Ouro = " + str(v)
    elif acao == "nivel":
        try: v = int(valor)
        except: v = 1
        c.execute("UPDATE jogador SET nivel=?, hp=hp_max WHERE id=?", (v, jid))
        msg = "Nivel " + str(v)
    elif acao == "dano":
        try: v = int(valor)
        except: v = 0
        c.execute("UPDATE jogador SET dano_bonus=? WHERE id=?", (v, jid))
        msg = "Dano bonus " + str(v)
    elif acao == "speed":
        try: v = int(valor)
        except: v = 1
        c.execute("UPDATE jogador SET speed=? WHERE id=?", (v, jid))
        msg = "Speed " + str(v)
    elif acao == "teleporte":
        try:
            tx = int(data.get("x", 0))
            ty = int(data.get("y", 0))
        except:
            tx, ty = 0, 0
        c.execute("UPDATE jogador SET x=?, y=? WHERE id=?", (tx, ty, jid))
        msg = "Teleportado para (" + str(tx) + "," + str(ty) + ")"
    elif acao == "spawn_perto":
        mn = data.get("mob_nome", "Monstro")
        try: mh = int(data.get("mob_hp", 50))
        except: mh = 50
        try: md = int(data.get("mob_dano", 5))
        except: md = 5
        px, py = c.execute("SELECT x, y FROM jogador WHERE id=?", (jid,)).fetchone()
        import random as _r
        sx = px + _r.randint(-3, 3)
        sy = py + _r.randint(-3, 3)
        c.execute("INSERT INTO monstros (nome, x, y, hp, dano) VALUES (?,?,?,?,?)", (mn, sx, sy, mh, md))
        msg = "Spawnou " + mn + " (" + str(mh) + " HP)"
    elif acao == "banir":
        alvo = (data.get("alvo") or "").strip()
        if not alvo:
            msg = "Nome vazio"
        else:
            r = c.execute("SELECT id FROM jogador WHERE nome=? OR nome_personagem=?", (alvo, alvo)).fetchone()
            if not r:
                msg = "Jogador nao encontrado: " + alvo
            else:
                c.execute("UPDATE jogador SET cargo='banido' WHERE id=?", (r[0],))
                msg = "Banido: " + alvo
    elif acao == "dar_cargo":
        alvo = (data.get("alvo") or "").strip()
        novo_cargo = data.get("novo_cargo", "vip")
        if not alvo:
            msg = "Nome vazio"
        else:
            r = c.execute("SELECT id FROM jogador WHERE nome=? OR nome_personagem=?", (alvo, alvo)).fetchone()
            if not r:
                msg = "Jogador nao encontrado: " + alvo
            else:
                c.execute("UPDATE jogador SET cargo=? WHERE id=?", (novo_cargo, r[0]))
                msg = "Cargo '" + novo_cargo + "' dado a " + alvo
    elif acao == "dar_item":
        chave = str(valor or "")
        try: qtd = int(data.get("qtd", 1) or 1)
        except: qtd = 1
        if qtd < 1: qtd = 1
        item_row = None
        if chave.isdigit():
            item_row = c.execute("SELECT id, nome FROM itens WHERE id=?", (int(chave),)).fetchone()
        if not item_row:
            item_row = c.execute("SELECT id, nome FROM itens WHERE LOWER(nome) LIKE LOWER(?) LIMIT 1", ("%" + chave + "%",)).fetchone()
        if not item_row:
            msg = "Item nao encontrado: " + chave
        else:
            iid, inome = item_row
            ja = c.execute("SELECT id FROM inventario WHERE jogador_id=? AND item_id=?", (jid, iid)).fetchone()
            if ja:
                c.execute("UPDATE inventario SET qtd=qtd+? WHERE id=?", (qtd, ja[0]))
            else:
                c.execute("INSERT INTO inventario (jogador_id, item_id, qtd) VALUES (?,?,?)", (jid, iid, qtd))
            msg = "Adicionado: " + inome + " x" + str(qtd)
    elif acao == "dar_xp":
        try: v = int(valor)
        except: v = 0
        c.execute("UPDATE jogador SET xp=xp+? WHERE id=?", (v, jid))
        msg = "+" + str(v) + " XP"
    elif acao == "setar_hp":
        try: v = int(valor)
        except: v = 0
        c.execute("UPDATE jogador SET hp=? WHERE id=?", (v, jid))
        msg = "HP = " + str(v)
    elif acao == "invisivel":
        if cargo != "dev":
            c.close()
            return jsonify({"erro": "Apenas dev"}), 403
        atual = c.execute("SELECT COALESCE(invisivel,0) FROM jogador WHERE id=?", (jid,)).fetchone()[0]
        novo = 0 if atual else 1
        c.execute("UPDATE jogador SET invisivel=? WHERE id=?", (novo, jid))
        msg = "Invisivel " + ("ON" if novo else "OFF")
    elif acao == "kickar":
        alvo = (data.get("alvo") or "").strip()
        if not alvo:
            msg = "Nome vazio"
        else:
            r = c.execute("SELECT id FROM jogador WHERE nome=? OR nome_personagem=?", (alvo, alvo)).fetchone()
            if not r:
                msg = "Jogador nao encontrado: " + alvo
            else:
                c.execute("UPDATE jogador SET ultimo_visto=0, hotbar='[]' WHERE id=?", (r[0],))
                msg = "Kickado: " + alvo
    elif acao == "ver_inventario":
        alvo = (data.get("alvo") or "").strip()
        if not alvo:
            msg = "Nome vazio"
        else:
            r = c.execute("SELECT id FROM jogador WHERE nome=? OR nome_personagem=?", (alvo, alvo)).fetchone()
            if not r:
                msg = "Jogador nao encontrado: " + alvo
            else:
                invs = c.execute("""SELECT i.nome, inv.qtd FROM inventario inv
                    JOIN itens i ON i.id=inv.item_id WHERE inv.jogador_id=?""", (r[0],)).fetchall()
                if not invs:
                    msg = alvo + ": inventario vazio"
                else:
                    msg = alvo + ": " + ", ".join([n + " x" + str(q) for n, q in invs])
    elif acao == "listar_itens":
        rows = c.execute("SELECT id, nome, tipo, bonus FROM itens ORDER BY id").fetchall()
        if not rows:
            msg = "Nenhum item cadastrado"
        else:
            msg = " | ".join([str(r[0]) + ":" + r[1] + "(" + r[2] + ",+" + str(r[3]) + ")" for r in rows[:25]])
            if len(rows) > 25:
                msg += " ... (+" + str(len(rows) - 25) + " itens)"
    elif acao == "listar_monstros":
        rows = c.execute("SELECT id, nome, hp, x, y FROM monstros ORDER BY id").fetchall()
        if not rows:
            msg = "Nenhum monstro ativo"
        else:
            msg = " | ".join([str(r[0]) + ":" + r[1] + "(" + str(r[2]) + "hp)" for r in rows[:20]])
    elif acao == "criar_item":
        nome_novo = (data.get("nome") or "").strip()
        tipo_novo = (data.get("tipo") or "arma").strip()
        try: bonus_novo = int(data.get("bonus", 0))
        except: bonus_novo = 0
        if not nome_novo:
            msg = "Nome vazio"
        else:
            ex = c.execute("SELECT id FROM itens WHERE LOWER(nome)=LOWER(?)", (nome_novo,)).fetchone()
            if ex:
                msg = "Item ja existe: " + nome_novo + " (id " + str(ex[0]) + ")"
            else:
                c.execute("INSERT INTO itens (nome, tipo, bonus) VALUES (?,?,?)", (nome_novo, tipo_novo, bonus_novo))
                msg = "Criado: " + nome_novo + " (" + tipo_novo + ", +" + str(bonus_novo) + ")"
    elif acao == "noclip":
        if cargo != "dev":
            c.close()
            return jsonify({"erro": "Apenas dev"}), 403
        atual = c.execute("SELECT COALESCE(noclip,0) FROM jogador WHERE id=?", (jid,)).fetchone()[0]
        novo = 0 if atual else 1
        c.execute("UPDATE jogador SET noclip=? WHERE id=?", (novo, jid))
        msg = "Noclip " + ("ON" if novo else "OFF")
    elif acao == "id_item":
        chave = str(valor or "").strip()
        if not chave:
            msg = "Digite um nome"
        else:
            r = c.execute("SELECT id, nome FROM itens WHERE LOWER(nome) LIKE LOWER(?) LIMIT 1", ("%" + chave + "%",)).fetchone()
            if not r:
                msg = "Nao encontrado: " + chave
            else:
                msg = "ID " + str(r[0]) + " = " + r[1]
    else:
        c.close()
        return jsonify({"erro": "Acao desconhecida: " + str(acao)}), 400

    c.commit()
    c.close()
    return jsonify({"msg": msg, "estado": estado(jid)})



@app.route("/api/vender/<int:inv_id>", methods=["POST"])
@login_obrigatorio
def api_vender(inv_id):
    jid = session["jogador_id"]
    c = con()
    row = c.execute("""SELECT inv.id, inv.jogador_id, inv.qtd, inv.item_id, i.nome, i.tipo
        FROM inventario inv JOIN itens i ON i.id=inv.item_id
        WHERE inv.id=?""", (inv_id,)).fetchone()
    if not row:
        c.close()
        return jsonify({"msg": "Item nao encontrado", "estado": estado(jid)})
    rid, dono, qtd, item_id, nome, tipo = row
    if dono != jid:
        c.close()
        return jsonify({"msg": "Item nao e seu", "estado": estado(jid)})
    if qtd <= 0:
        c.close()
        return jsonify({"msg": "Sem unidades para vender", "estado": estado(jid)})

    preco_loja = c.execute("SELECT preco FROM loja_itens WHERE item_id=? ORDER BY preco ASC LIMIT 1", (item_id,)).fetchone()
    if preco_loja:
        valor_base = preco_loja[0]
    else:
        # Preco padrao por tipo (arma/escudo/pocao)
        valor_base = {"arma": 20, "escudo": 15, "pocao": 10}.get(tipo, 10)

    valor_venda = max(1, int(valor_base / 2))

    if qtd == 1:
        c.execute("DELETE FROM inventario WHERE id=?", (inv_id,))
    else:
        c.execute("UPDATE inventario SET qtd=qtd-1 WHERE id=?", (inv_id,))
    c.execute("UPDATE jogador SET ouro=ouro+? WHERE id=?", (valor_venda, jid))
    c.commit()
    c.close()
    return jsonify({"msg": "Vendeu " + nome + " por " + str(valor_venda) + " ouro", "estado": estado(jid)})



def ia_monstros():
    while True:
        time.sleep(3)
        try:
            c = con()
            monstros = c.execute("SELECT id, x, y FROM monstros").fetchall()
            for mid, mx, my in monstros:
                dx, dy = random.choice([(0,-1),(0,1),(-1,0),(1,0)])
                nx, ny = mx + dx, my + dy
                if nx < 0 or ny < 0 or nx >= W_MAP or ny >= H_MAP:
                    continue
                if bloqueia(nx, ny):
                    continue
                existe = c.execute("SELECT id FROM monstros WHERE x=? AND y=?", (nx, ny)).fetchone()
                if existe:
                    continue
                c.execute("UPDATE monstros SET x=?, y=? WHERE id=?", (nx, ny, mid))
            c.commit()
            c.close()
        except Exception as e:
            print("Erro ia_monstros:", e)

if __name__ == "__main__":
    carregar_mapa()
    threading.Thread(target=ia_monstros, daemon=True).start()
    print("IA de monstros iniciada")
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
