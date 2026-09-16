code = open("server.py").read()

# 1. Fórmula de XP mais robusta (curva polinomial, estilo FF)
old_xp = "while xp >= nivel * 50:"
new_xp = "while xp >= int(100 * (nivel ** 1.5)):"
code = code.replace(old_xp, new_xp)

old_xp2 = "xp -= nivel * 50"
new_xp2 = "xp -= int(100 * (nivel ** 1.5))"
code = code.replace(old_xp2, new_xp2)

# 2. Endpoint de ataque por botão
ataque_endpoint = '''
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

'''
code = code.replace('if __name__ == "__main__":', ataque_endpoint + 'if __name__ == "__main__":')

# 3. Adicionar hp aos monstros no estado (ja existe, mas vamos confirmar formato)
# formato: [id, nome, x, y, hp] - ok

open("server.py", "w").write(code)
print("server.py patchado")
