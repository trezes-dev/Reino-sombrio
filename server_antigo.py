from flask import Flask, render_template, jsonify, request, redirect
import sqlite3, random

app = Flask(__name__)
DB = "rpg.db"
W, H = 11, 11
SENHA_ADMIN = "admin123"
XP_MONSTRO = {"Goblin": 10, "Lobo": 15, "Esqueleto": 20, "Slime": 8}

def con():
    return sqlite3.connect(DB)

def estado():
    c = con()
    linha = c.execute("SELECT nome, hp, ouro, x, y, xp, nivel, hp_max, cor FROM jogador").fetchone()
    if not linha:
        c.close()
        return None
    nome, hp, ouro, x, y, xp, nivel, hp_max, cor = linha
    arma = c.execute("SELECT i.nome, i.bonus FROM inventario inv JOIN itens i ON i.id=inv.item_id WHERE inv.jogador=? AND i.tipo=? ORDER BY i.bonus DESC LIMIT 1", (nome, "arma")).fetchone()
    inv = c.execute("SELECT i.nome, i.tipo, i.bonus, inv.qtd FROM inventario inv JOIN itens i ON i.id=inv.item_id WHERE inv.jogador=?", (nome,)).fetchall()
    mons = c.execute("SELECT id, nome, x, y, hp FROM monstros").fetchall()
    c.close()
    return {"nome": nome, "hp": hp, "ouro": ouro, "x": x, "y": y,
            "xp": xp, "nivel": nivel, "hp_max": hp_max, "cor": cor,
            "arma": arma, "inv": inv, "monstros": mons, "W": W, "H": H}

def posicao_livre(c, px, py):
    for _ in range(50):
        nx = random.randint(0, W-1)
        ny = random.randint(0, H-1)
        if nx == px and ny == py:
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

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/estado")
def api_estado():
    return jsonify(estado())

@app.route("/api/mover/<dir>")
def api_mover(dir):
    c = con()
    nome, hp, ouro, x, y, xp, nivel, hp_max, cor = c.execute(
        "SELECT nome, hp, ouro, x, y, xp, nivel, hp_max, cor FROM jogador").fetchone()
    if dir == "cima": y -= 1
    if dir == "baixo": y += 1
    if dir == "esq": x -= 1
    if dir == "dir": x += 1
    x = max(0, min(W-1, x))
    y = max(0, min(H-1, y))
    c.execute("UPDATE jogador SET x=?, y=? WHERE nome=?", (x, y, nome))
    msg = "Andou para " + dir

    m = c.execute("SELECT id, nome, dano FROM monstros WHERE x=? AND y=?", (x, y)).fetchone()
    if m:
        mid, mnome, mdano = m
        arma = c.execute("SELECT i.bonus FROM inventario inv JOIN itens i ON i.id=inv.item_id WHERE inv.jogador=? AND i.tipo=? ORDER BY i.bonus DESC LIMIT 1",
                         (nome, "arma")).fetchone()
        bonus = arma[0] if arma else 0
        dano = max(0, mdano - bonus)
        hp -= dano
        ganho = random.randint(5, 15)
        ouro += ganho
        xp_ganho = XP_MONSTRO.get(mnome, 10)
        xp += xp_ganho
        msg = "Matou " + mnome + "! -" + str(dano) + " HP, +" + str(ganho) + " ouro, +" + str(xp_ganho) + " XP"
        subiu = False
        while xp >= nivel * 50:
            xp -= nivel * 50
            nivel += 1
            hp_max += 20
            hp = hp_max
            subiu = True
        if subiu:
            msg += "  LEVEL UP! Nv " + str(nivel)
        c.execute("DELETE FROM monstros WHERE id=?", (mid,))
        nascer_monstro(c, x, y)

    c.execute("UPDATE jogador SET hp=?, ouro=?, xp=?, nivel=?, hp_max=? WHERE nome=?",
              (hp, ouro, xp, nivel, hp_max, nome))
    c.commit()
    c.close()
    return jsonify({"msg": msg, "estado": estado()})

@app.route("/api/descansar")
def api_descansar():
    c = con()
    nome, hp, hp_max = c.execute("SELECT nome, hp, hp_max FROM jogador").fetchone()
    hp = min(hp_max, hp + 5)
    c.execute("UPDATE jogador SET hp=? WHERE nome=?", (hp, nome))
    c.commit()
    c.close()
    return jsonify({"msg": "Descansou. +5 HP", "estado": estado()})

@app.route("/api/pocao")
def api_pocao():
    c = con()
    nome, hp, hp_max = c.execute("SELECT nome, hp, hp_max FROM jogador").fetchone()
    linha = c.execute("SELECT inv.id, inv.qtd, i.nome, i.bonus FROM inventario inv JOIN itens i ON i.id=inv.item_id WHERE inv.jogador=? AND i.tipo=? AND inv.qtd > 0 LIMIT 1",
                      (nome, "pocao")).fetchone()
    if not linha:
        c.close()
        return jsonify({"msg": "Sem pocao", "estado": estado()})
    inv_id, qtd, n, b = linha
    hp = min(hp_max, hp + b)
    if qtd - 1 <= 0:
        c.execute("DELETE FROM inventario WHERE id=?", (inv_id,))
    else:
        c.execute("UPDATE inventario SET qtd=? WHERE id=?", (qtd-1, inv_id))
    c.execute("UPDATE jogador SET hp=? WHERE nome=?", (hp, nome))
    c.commit()
    c.close()
    return jsonify({"msg": "Usou " + n + ". +" + str(b) + " HP", "estado": estado()})

# ---------- ADMIN ----------

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("senha") == SENHA_ADMIN:
            return redirect("/admin/painel?senha=" + SENHA_ADMIN)
        return "Senha errada"
    return render_template("admin_login.html")

@app.route("/admin/painel")
def admin_painel():
    if request.args.get("senha") != SENHA_ADMIN:
        return redirect("/admin")
    return render_template("admin.html", senha=SENHA_ADMIN)

@app.route("/admin/acao")
def admin_acao():
    if request.args.get("senha") != SENHA_ADMIN:
        return jsonify({"erro": "sem permissao"}), 403
    tipo = request.args.get("tipo")
    c = con()
    nome = c.execute("SELECT nome FROM jogador").fetchone()[0]
    msg = "?"

    if tipo == "ouro":
        v = int(request.args.get("v", 0))
        c.execute("UPDATE jogador SET ouro = ouro + ? WHERE nome=?", (v, nome))
        msg = "Ouro +" + str(v)
    elif tipo == "curar":
        c.execute("UPDATE jogador SET hp = hp_max WHERE nome=?", (nome,))
        msg = "Curado ao maximo"
    elif tipo == "teleporte":
        x, y = int(request.args.get("x", 5)), int(request.args.get("y", 5))
        c.execute("UPDATE jogador SET x=?, y=? WHERE nome=?", (x, y, nome))
        msg = "Teleportou para " + str(x) + "," + str(y)
    elif tipo == "cor":
        cor = request.args.get("cor", "#ffffff")
        c.execute("UPDATE jogador SET cor=? WHERE nome=?", (cor, nome))
        msg = "Cor = " + cor
    elif tipo == "nivel":
        v = int(request.args.get("v", 1))
        hp_max = 100 + (v-1)*20
        c.execute("UPDATE jogador SET nivel=?, hp_max=?, xp=0, hp=? WHERE nome=?", (v, hp_max, hp_max, nome))
        msg = "Nivel = " + str(v)
    elif tipo == "item":
        iid = int(request.args.get("id", 1))
        qtd = int(request.args.get("qtd", 1))
        c.execute("INSERT INTO inventario (jogador, item_id, qtd) VALUES (?,?,?)", (nome, iid, qtd))
        msg = "Item id " + str(iid) + " x" + str(qtd)
    elif tipo == "limpar_monstros":
        c.execute("DELETE FROM monstros")
        msg = "Todos os monstros removidos"
    elif tipo == "spawn":
        n = request.args.get("nome", "Goblin")
        x = int(request.args.get("x", 5))
        y = int(request.args.get("y", 5))
        hpm = int(request.args.get("hp", 20))
        dmg = int(request.args.get("dano", 5))
        c.execute("INSERT INTO monstros (nome, x, y, hp, dano) VALUES (?,?,?,?,?)", (n, x, y, hpm, dmg))
        msg = "Spawnou " + n + " em " + str(x) + "," + str(y)
    else:
        msg = "Acao desconhecida"

    c.commit()
    c.close()
    return jsonify({"msg": msg, "estado": estado()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
