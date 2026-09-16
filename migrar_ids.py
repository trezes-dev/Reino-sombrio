import sqlite3

con = sqlite3.connect("rpg.db")
con.isolation_level = None
c = con.cursor()

c.execute("DROP TABLE IF EXISTS jogador_novo")
c.execute("DROP TABLE IF EXISTS jogador_final")

cols = [r[1] for r in c.execute("PRAGMA table_info(jogador)").fetchall()]
if "id" not in cols:
    print("migrando jogador...")
    c.execute("""
        CREATE TABLE jogador_final (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            hp INT, ouro INT, x INT, y INT,
            xp INT, nivel INT, hp_max INT, cor TEXT, admin INT
        )
    """)
    c.execute("""
        INSERT INTO jogador_final (nome, hp, ouro, x, y, xp, nivel, hp_max, cor, admin)
        SELECT nome, hp, ouro, x, y, xp, nivel, hp_max, cor, admin FROM jogador
    """)
    c.execute("DROP TABLE jogador")
    c.execute("ALTER TABLE jogador_final RENAME TO jogador")
    print("  jogador agora tem id")
else:
    print("jogador ja tem id")

c.execute("DROP TABLE IF EXISTS contas")
c.execute("""
    CREATE TABLE contas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        jogador_id INT,
        criado_em REAL DEFAULT (strftime('%s','now'))
    )
""")
row = c.execute("SELECT id, nome FROM jogador WHERE nome='heroi'").fetchone()
if row:
    c.execute("INSERT INTO contas (usuario, senha_hash, jogador_id) VALUES (?, 'migrar', ?)",
              (row[1], row[0]))
    print("  conta do heroi criada com jogador_id=" + str(row[0]))

cols = [r[1] for r in c.execute("PRAGMA table_info(inventario)").fetchall()]
if "jogador_id" not in cols:
    print("migrando inventario...")
    c.execute("DROP TABLE IF EXISTS inventario_final")
    c.execute("""
        CREATE TABLE inventario_final (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jogador_id INT NOT NULL,
            item_id INT NOT NULL,
            qtd INT NOT NULL
        )
    """)
    c.execute("""
        INSERT INTO inventario_final (jogador_id, item_id, qtd)
        SELECT j.id, i.item_id, i.qtd
        FROM inventario i JOIN jogador j ON j.nome = i.jogador
    """)
    c.execute("DROP TABLE inventario")
    c.execute("ALTER TABLE inventario_final RENAME TO inventario")
    print("  inventario usa jogador_id")
else:
    print("inventario ja usa jogador_id")

print("OK - migracao concluida")
con.close()
