import json

# ============ PATCH SERVER.PY ============
code = open("server.py").read()

old = '''    linha = c.execute("""SELECT id, nome, nome_personagem, classe, cargo, hp, ouro, x, y, xp, nivel, hp_max, cor
        FROM jogador WHERE id=?""", (jid,)).fetchone()'''
new = '''    linha = c.execute("""SELECT id, nome, nome_personagem, classe, cargo, hp, ouro, x, y, xp, nivel, hp_max, cor, COALESCE(hotbar,'[]')
        FROM jogador WHERE id=?""", (jid,)).fetchone()'''
if old in code:
    code = code.replace(old, new)
    print("OK1: SELECT atualizado")
else:
    print("AVISO1: SELECT nao bateu")

old = '''    (jid_, nome_login, nome_pers, classe, cargo, hp, ouro, x, y, xp, nivel, hp_max, cor) = linha'''
new = '''    (jid_, nome_login, nome_pers, classe, cargo, hp, ouro, x, y, xp, nivel, hp_max, cor, hotbar_str) = linha
    try:
        hotbar_ids = json.loads(hotbar_str or "[]")
    except:
        hotbar_ids = []'''
if old in code:
    code = code.replace(old, new)
    print("OK2: unpack atualizado")
else:
    print("AVISO2: unpack nao bateu")

old = '''"arma": arma, "inv": inv, "monstros": mons, "npcs": npcs, "outros": lista_outros,'''
new = '''"arma": arma, "inv": inv, "monstros": mons, "npcs": npcs, "outros": lista_outros, "hotbar": hotbar_ids,'''
if old in code:
    code = code.replace(old, new)
    print("OK3: retorno atualizado")
else:
    print("AVISO3: retorno nao bateu")

if "import json" not in code:
    code = "import json\n" + code
    print("OK4: import json adicionado")

# Adicionar campo id na query do inventario
old_inv = '''    inv = c.execute("""SELECT i.nome, i.tipo, i.bonus, inv.qtd FROM inventario inv
        JOIN itens i ON i.id=inv.item_id WHERE inv.jogador_id=?""", (jid,)).fetchall()'''
new_inv = '''    inv = c.execute("""SELECT i.nome, i.tipo, i.bonus, inv.qtd, i.id FROM inventario inv
        JOIN itens i ON i.id=inv.item_id WHERE inv.jogador_id=?""", (jid,)).fetchall()'''
if old_inv in code:
    code = code.replace(old_inv, new_inv)
    print("OK5: inventario com id")
else:
    print("AVISO5: query do inventario nao bateu")

endpoint = '''
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

'''
if "api_hotbar_salvar" not in code:
    code = code.replace('if __name__ == "__main__":', endpoint + 'if __name__ == "__main__":')
    print("OK6: endpoint hotbar adicionado")

open("server.py", "w").write(code)
print("server.py salvo")
