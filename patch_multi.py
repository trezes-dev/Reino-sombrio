import time

with open("server.py", "r") as f:
    code = f.read()

if '"outros": lista_outros' in code:
    print("Ja patchado")
    exit()

# 1. import time
if ", time" not in code.split("\n")[2]:
    code = code.replace(
        "import sqlite3, random, functools",
        "import sqlite3, random, functools, time", 1
    )

# 2. Nova função estado
nova = '''def estado(jid):
    c = con()
    linha = c.execute("""SELECT id, nome, nome_personagem, classe, cargo, hp, ouro, x, y, xp, nivel, hp_max, cor
        FROM jogador WHERE id=?""", (jid,)).fetchone()
    if not linha:
        c.close()
        return None
    (jid_, nome_login, nome_pers, classe, cargo, hp, ouro, x, y, xp, nivel, hp_max, cor) = linha
    arma = c.execute("""SELECT i.nome, i.bonus FROM inventario inv JOIN itens i ON i.id=inv.item_id
        WHERE inv.jogador_id=? AND i.tipo='arma' ORDER BY i.bonus DESC LIMIT 1""", (jid,)).fetchone()
    inv = c.execute("""SELECT i.nome, i.tipo, i.bonus, inv.qtd FROM inventario inv
        JOIN itens i ON i.id=inv.item_id WHERE inv.jogador_id=?""", (jid,)).fetchall()
    mons = c.execute("SELECT id, nome, x, y, hp FROM monstros").fetchall()
    npcs = c.execute("SELECT id, nome, x, y, tipo FROM npcs").fetchall()
    agora = time.time()
    outros_rows = c.execute("""SELECT id, nome_personagem, nome, cargo, x, y, hp, hp_max, nivel
        FROM jogador WHERE id != ? AND ultimo_visto > ? AND personagem_criado = 1""",
        (jid, agora - 15)).fetchall()
    c.close()
    info = CARGOS.get(cargo or "player", CARGOS["player"])
    lista_outros = []
    for o in outros_rows:
        info_o = CARGOS.get(o[3] or "player", CARGOS["player"])
        lista_outros.append({
            "id": o[0], "nome": o[1] or o[2], "cargo": o[3] or "player",
            "x": o[4], "y": o[5], "hp": o[6], "hp_max": o[7], "nivel": o[8],
            "cor": info_o["cor"], "badge": info_o["badge"]
        })
    return {"id": jid_, "nome": nome_pers or nome_login, "login": nome_login,
            "classe": classe, "cargo": cargo or "player",
            "cargo_nome": info["nome"], "cargo_cor": info["cor"], "cargo_badge": info["badge"],
            "hp": hp, "ouro": ouro, "x": x, "y": y,
            "xp": xp, "nivel": nivel, "hp_max": hp_max, "cor": cor,
            "arma": arma, "inv": inv, "monstros": mons, "npcs": npcs, "outros": lista_outros,
            "W": W, "H": H}

'''

start = code.find("def estado(jid):")
end = code.find("def posicao_livre")
if start == -1 or end == -1:
    print("ERRO: funcoes marcadoras nao encontradas")
    exit()

code = code[:start] + nova + code[end:]

# 3. Update ultimo_visto no api_estado
old_api = '''def api_estado():
    return jsonify(estado(session["jogador_id"]))'''
new_api = '''def api_estado():
    jid = session["jogador_id"]
    c = con()
    c.execute("UPDATE jogador SET ultimo_visto = ? WHERE id = ?", (time.time(), jid))
    c.commit()
    c.close()
    return jsonify(estado(jid))'''
if old_api in code:
    code = code.replace(old_api, new_api)
else:
    print("AVISO: api_estado nao bateu exatamente")

# 4. Update ultimo_visto no api_mover
code = code.replace(
    'c.execute("UPDATE jogador SET x=?, y=? WHERE id=?", (x, y, jid))',
    'c.execute("UPDATE jogador SET x=?, y=?, ultimo_visto=? WHERE id=?", (x, y, time.time(), jid))'
)

with open("server.py", "w") as f:
    f.write(code)

print("OK - patch aplicado")
