code = open("server.py").read()

# Trocar "guerreiro" por "cavaleiro" no dicionário CLASSES
old = '''    "guerreiro": {"nome": "Guerreiro", "hp_max": 120, "arma": "Espada Curta", "cor": "#ff5566",
                  "descricao": "Tanque resistente. Comeca com Espada Curta (+5).", "emoji": "⚔️"},'''
new = '''    "cavaleiro": {"nome": "Cavaleiro", "hp_max": 120, "arma": "Espada Curta", "cor": "#ff5566",
                  "descricao": "Tanque resistente. Comeca com Espada Curta (+5).", "emoji": "⚔️"},'''
if old in code:
    code = code.replace(old, new)
    print("OK: dict CLASSES atualizado")
else:
    print("AVISO: dict CLASSES nao bateu (talvez ja foi trocado)")

# Trocar referência no INSERT de criação de personagem novo
code = code.replace("'guerreiro', 'player'", "'cavaleiro', 'player'")

open("server.py", "w").write(code)
print("server.py salvo")
