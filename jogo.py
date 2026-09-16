import random, sqlite3

con = sqlite3.connect("rpg.db")
nome, hp, ouro = con.execute("SELECT nome, hp, ouro FROM jogador").fetchone()
print(f"Bem-vindo, {nome}!")

def salvar():
    con.execute("UPDATE jogador SET hp=?, ouro=? WHERE nome=?", (hp, ouro, nome))
    con.commit()

def inventario():
    print("--- Inventario ---")
    itens = con.execute("SELECT i.nome, i.tipo, i.bonus, inv.qtd FROM inventario inv JOIN itens i ON i.id=inv.item_id WHERE inv.jogador=?", (nome,)).fetchall()
    for n, t, b, q in itens:
        print(f"  {n} [{t}] +{b}  x{q}")

def usar_pocao():
    global hp
    linha2 = con.execute("SELECT inv.id, inv.qtd, i.nome, i.bonus FROM inventario inv JOIN itens i ON i.id=inv.item_id WHERE inv.jogador=? AND i.tipo=? AND inv.qtd > 0 LIMIT 1", (nome, "pocao")).fetchone()
    if not linha2:
        print("Sem pocao no inventario")
        return
    inv_id, qtd, n, b = linha2
    hp = min(100, hp + b)
    print(f"Usou {n}. +{b} HP")
    if qtd - 1 <= 0:
        con.execute("DELETE FROM inventario WHERE id=?", (inv_id,))
    else:
        con.execute("UPDATE inventario SET qtd=? WHERE id=?", (qtd-1, inv_id))
    con.commit()
    salvar()

while hp > 0:
    print(f"--- {nome} | HP {hp} | Ouro {ouro} ---")
    print("1 - Explorar")
    print("2 - Descansar")
    print("3 - Inventario")
    print("4 - Usar pocao")
    print("5 - Sair")
    op = input("> ")
    if op == "1":
        dano = random.randint(5, 20)
        ganho = random.randint(5, 15)
        hp -= dano
        ouro += ganho
        print(f"Goblin! -{dano} HP, +{ganho} ouro")
        salvar()
    elif op == "2":
        hp = min(100, hp + 5)
        print("Descansou. +5 HP")
        salvar()
    elif op == "3":
        inventario()
    elif op == "4":
        usar_pocao()
    elif op == "5":
        salvar()
        print("Ate logo!")
        break
    else:
        print("Invalido")

con.close()
