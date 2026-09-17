# REINO SOMBRIO MMORPG — Contexto do Projeto

Documento pra retomar o projeto em qualquer chat novo.
Última atualização: 17/09/2026

---

## 1. O QUE É O PROJETO

MMORPG 2D online, inspirado no Curse of Aros, feito em Flask + SQLite
rodando no Termux (Android). Hospedado no Render (grátis).

- **Nome:** Reino Sombrio MMORPG
- **Estilo:** pixel art 2D top-down
- **Servidor local:** Termux + Flask + SQLite
- **Servidor nuvem:** Render (free tier, dorme a cada 15min sem acesso)
- **Uptime:** UptimeRobot (ping a cada 5min)
- **Repositório:** https://github.com/trezes-dev/Reino-sombrio
- **URL nuvem:** https://reino-sombrio.onrender.com
- **URL local:** http://127.0.0.1:5000
- **Conta admin/dev:** trezes (cargo dev, admin=1)
- **Conta de teste:** kowz (cargo player)
- **Senha admin panel:** admin123

---

## 2. STACK TÉCNICA

- **Backend:** Python 3.13 + Flask + SQLite
- **Frontend:** HTML + CSS + JavaScript puro (sem framework)
- **Banco:** SQLite (arquivo rpg.db)
- **Assets:** SVGs próprios + packs CC0 (Kenney, CraftPix)
- **Sprites do player:** LPC (Liberated Pixel Cup)
- **PWA:** manifest.json + service worker + ícone (dragão)
- **Deploy:** push no GitHub → Render faz deploy automático
- **Ferramentas:** PIL/Pillow, ImageMagick

---

## 3. ESTRUTURA DE ARQUIVOS

~/rpg/
├── server.py              (backend Flask, ~1400 linhas)
├── rpg.db                 (SQLite, banco de dados)
├── requirements.txt       (Flask + Werkzeug)
├── .gitignore
├── CONTEXTO.md            (este arquivo)
├── templates/             (login, criar_personagem, index, painel, admin)
└── static/
    ├── manifest.json, sw.js, icon-192.png, icon-512.png
    ├── sprites/
    │   ├── jogador/       (100 sprites LPC)
    │   ├── terreno/       (grama, agua, areia, pedra, terra)
    │   ├── monstros/      (goblin, esqueleto, slime)
    │   ├── itens/         (15 ícones PNG 64x64)
    │   └── npc.png / npc-mercador.png
    └── assets/            (packs originais — NÃO vai pro Git)

---

## 4. BANCO DE DADOS (tabelas)

- **contas**: id, usuario, senha_hash, jogador_id, criado_em
- **jogador**: id, nome, nome_personagem, classe, cargo, hp, hp_max, ouro, x, y, xp, nivel, cor, admin, personagem_criado, hotbar, guilda, god, dano_bonus, speed, ultimo_visto
- **itens**: id, nome, tipo, bonus
- **inventario**: id, jogador_id, item_id, qtd
- **monstros**: id, nome, x, y, hp, dano
- **npcs**: id, nome, x, y, tipo
- **loja_itens**: id, item_id, preco, regiao
- **mensagens**: id, jogador_id, canal, texto, x, y, ts, destinatario, guilda_id
- **guildas**: id, nome, lider_id, criada_em
- **guilda_membros**: guilda_id, jogador_id, cargo, entrou_em
- **amizades**: id, solicitante_id, destinatario_id, status, criada_em
- **convites_guilda**: id, guilda_id, convidado_id, criado_em
- **trocas**: id, jogador_a, jogador_b, ouro_a, ouro_b, aceito_a, aceito_b, status
- **troca_itens**: id, troca_id, jogador_id, item_id, qtd
- **mapa_tiles**: x, y, tipo (grid 200x200 = 40.000 tiles)

---

## 5. CLASSES DO JOGO

- **cavaleiro**: HP 120, arma inicial "Espada Curta" (+5)
- **mago**: HP 80, arma inicial "Cajado" (+8)
- **arqueiro**: HP 100, arma inicial "Arco Curto" (+6)

---

## 6. CARGOS

- **dev**: acesso total, admin panel, comandos god
- **admin**: moderação (banir, mutar, kickar)
- **mod**: moderação básica (chat)
- **player**: jogador comum

---

## 7. FUNCIONALIDADES IMPLEMENTADAS

### Já funcionando:
- Login e criação de personagem (3 classes)
- Movimento no mapa 200x200 com grid de tiles
- Sistema de sprites LPC (walk/idle/slash/run)
- Chat global, local e privado
- Inventário (modal com sprites PNG)
- Hotbar (5 slots, sincronizada com inventário)
- Picker de itens para hotbar
- NPC Mercador na posição (39, 22) com tipo='loja'
- Loja funcional (comprar itens, deduzir ouro, adicionar ao inventário)
- Sistema de XP e level up
- Monstros (goblin, esqueleto, slime) com respawn
- Combate básico (ataque com espada/cajado/arco)
- Guilda (criar, convidar, entrar)
- Amizades
- Trocas entre jogadores
- Painel de moderação
- PWA (instalável no celular)
- Deploy no Render + UptimeRobot

### Próximos passos:
- [ ] Botão "Vender" na loja (50% do valor)
- [ ] Travar compra sem ouro suficiente
- [ ] Equipar itens (alterar status de ataque/defesa)
- [ ] Mais NPCs (ferreiro, alquimista)
- [ ] Sistema de quests
- [ ] Mais mapas/regiões

---

## 8. SPRITES DE ITENS (mapeamento)

Os 15 ícones em static/sprites/itens/:

| Item              | Arquivo             | Tipo   | Bonus |
|-------------------|---------------------|--------|-------|
| Espada Curta      | espada-aco.png      | arma   | +5    |
| Adaga Enferrujada | adaga.png           | arma   | +2    |
| Cajado            | cajado.png          | arma   | +8    |
| Arco Curto        | arco.png            | arma   | +6    |
| Escudo de Madeira | escudo-madeira.png  | escudo | +3    |
| Espada de Veneno  | espada-veneno.png   | arma   | -     |
| Espada de Gelo    | espada-gelo.png     | arma   | -     |
| Espada de Fogo    | espada-fogo.png     | arma   | -     |
| Espada Sombria    | espada-sombria.png  | arma   | -     |
| Machado           | machado.png         | arma   | -     |
| Lança             | lanca.png           | arma   | -     |
| Adaga Mágica      | adaga-magica.png    | arma   | -     |
| Poção de Cura     | pocao-vermelha.png  | pocao  | +20   |
| Poção de Mana     | pocao-azul.png      | pocao  | +20   |
| Poção de Veneno   | pocao-verde.png     | pocao  | -     |

Mapeamento no index.html:

const SPRITE_ITEM = {
  "Espada Curta": "/static/sprites/itens/espada-aco.png",
  "Adaga Enferrujada": "/static/sprites/itens/adaga.png",
  // ... etc
};
function spriteDe(nome) { return SPRITE_ITEM[nome] || null; }

---

## 9. SISTEMA DE COMBATE

- **Ataque:** Botão de espada ⚔️ na direita (ou tecla ESPAÇO)
- **Alcance:** 1 tile de distância (adjacente)
- **Dano:** dano_bonus do item equipado + nível do jogador
- **Monstros:** têm HP, dano, XP e respawn (5 segundos após morte)
- **XP por monstro:**
  - Slime: 10 XP
  - Goblin: 25 XP
  - Esqueleto: 40 XP
- **Level up:** precisa de nivel * 100 XP para o próximo nível
- **Morte do jogador:** respawna em (44, 9) com HP cheio

---

## 10. COMANDOS DO CHAT

Digite no chat do jogo (tecla ENTER):

| Comando                | Função                  | Cargo necessário |
|------------------------|-------------------------|------------------|
| /god                   | Modo invencível         | dev              |
| /tp X Y                | Teleporta               | dev              |
| /ouro 9999             | Adiciona ouro           | dev              |
| /item nome             | Adiciona item           | dev              |
| /ban usuario           | Bane jogador            | admin            |
| /kick usuario          | Expulsa jogador         | admin            |
| /mute usuario          | Silencia no chat        | mod              |
| /guilda criar nome     | Cria guilda             | player           |
| /guilda convidar user  | Convida para guilda     | lider            |
| /amigo add usuario     | Pedido de amizade       | player           |
| /trade usuario         | Inicia troca            | player           |

---

## 11. APIs DO SERVIDOR (Flask)

Rotas principais do server.py:

POST /login                    -> autenticação
POST /criar_personagem         -> cria personagem (classe)
GET  /api/estado               -> estado completo do jogo (JSON)
POST /api/mover                -> move o jogador
POST /api/ir                   -> interage (baú, NPC, porta)
POST /api/atacar               -> ataca monstro adjacente
POST /api/chat                 -> envia mensagem no chat
POST /api/comprar              -> compra item da loja
POST /api/vender               -> vende item (a implementar)
POST /api/usar                 -> usa/equipa item
POST /api/hotbar               -> define item na hotbar
POST /api/guilda               -> ações de guilda
POST /api/amizade              -> ações de amizade
POST /api/troca                -> ações de troca
GET  /api/loja/<npc_id>        -> lista itens da loja
GET  /admin                    -> painel admin
GET  /painel                   -> painel moderação

---

## 12. DEPLOY (Render)

**Fluxo:**
1. Commit local no Termux: git add . && git commit -m "msg"
2. Push: git push origin main
3. Render detecta o push e faz deploy automático (2-3 min)
4. Se o servidor dormir (15min sem acesso), o UptimeRobot acorda

**Configuração no Render:**
- Build: pip install -r requirements.txt
- Start: gunicorn server:app --bind 0.0.0.0:$PORT

---

## 13. PROBLEMAS CONHECIDOS E SOLUÇÕES

| Problema                  | Causa                    | Solução                          |
|---------------------------|--------------------------|----------------------------------|
| Sprites desatualizados    | Service Worker antigo    | Chrome -> limpar dados / Unregister SW |
| "Servidor ocupado"        | Chat da IA (não é o jogo)| Aguardar / reabrir o chat        |
| Render dorme              | Free tier                | UptimeRobot ping a cada 5min     |
| Sprites borrados          | Falta image-rendering    | Adicionar image-rendering: pixelated |
| Banco travado             | SQLite lock              | Reiniciar servidor               |
| Personagem não aparece    | Sprite faltando          | Verificar static/sprites/jogador/|

---

## 14. ASSETS E PACKS USADOS

**Kenney (CC0):**
- tiny-dungeon -> tiles, poções, ferramentas
- tiny-town -> casas, árvores, decoração
- tiny-battle -> armas, escudos, personagens
- roguelike-* -> tiles extras

**CraftPix (CC0/free):**
- weapons -> espadas, machados, cajados
- slime-mobs -> slimes
- ruins -> ruínas do cenário
- bushes/rocks -> decoração

**LPC (Liberated Pixel Cup):**
- lpc-male -> sprites do jogador (100 frames)

**Sites úteis:**
- kenney.nl/assets
- craftpix.net
- opengameart.org

---

## 15. PRÓXIMAS TAREFAS (backlog)

### Curto prazo (2 semanas):
1. [ ] Botão "Vender" na loja (50% do valor)
2. [ ] Bloquear compra sem ouro suficiente
3. [ ] Sistema de equipar itens (mudar dano_bonus)
4. [ ] Corrigir bug da hotbar (quantidade duplicada)
5. [ ] Salvar estado completo no banco

### Médio prazo (1-2 meses):
6. [ ] NPC Ferreiro (vende armas melhores)
7. [ ] NPC Alquimista (vende poções raras)
8. [ ] Sistema de quests (matar X monstros, entregar item)
9. [ ] Mais regiões no mapa (floresta, deserto, caverna)
10. [ ] Bosses com loot especial

### Longo prazo:
11. [ ] PvP entre jogadores
12. [ ] Leilão/market global
13. [ ] Sistema de pets
14. [ ] Eventos sazonais
15. [ ] App nativo (Capacitor ou Tauri)

---

## 16. ESTRUTURA DO INDEX.HTML

O index.html (~1200 linhas) contém:

- Canvas do jogo (renderização principal)
- HUD superior: nome, HP, ouro, botões (perfil, inventário, chat, config)
- Mini-mapa no canto superior direito
- Controles virtuais: joystick (esquerda), botões de ação (direita)
- Hotbar na parte inferior (5 slots)
- Modais (overlays):
  - modal-inventario -> grade de itens
  - modal-loja -> loja do NPC
  - modal-picker -> escolher item para hotbar
  - modal-item -> detalhes do item selecionado
  - modal-chat -> chat expandido
  - modal-guilda, modal-amizade, modal-troca

Funções JS principais:
- spriteDe(nome) -> retorna URL do sprite
- emojiDe(nome) -> fallback de emoji
- acaoInteragir() -> botão de mãozinha (chama /api/ir)
- abrirLoja(npcId, npcNome) -> abre modal da loja
- carregarItensLoja(npcId) -> busca itens da loja
- comprarItem(itemId) -> chama /api/comprar
- renderizarInventario() -> atualiza grade
- renderizarHotbar() -> atualiza slots

---

## 17. COMANDOS ÚTEIS (Termux)

# Reiniciar servidor
pkill -9 -f server.py && sleep 2 && cd ~/rpg && python3 server.py

# Acessar banco
sqlite3 ~/rpg/rpg.db

# Backup do banco
cp ~/rpg/rpg.db ~/rpg/rpg.db.bak

# Git
cd ~/rpg
git add .
git commit -m "mensagem"
git push origin main

# Copiar CONTEXTO.md para área de transferência (uso diário)
cat ~/rpg/CONTEXTO.md | termux-clipboard-set

---

## 18. COMO RETOMAR EM UM CHAT NOVO

1. No Termux, rode:
   cat ~/rpg/CONTEXTO.md | termux-clipboard-set

2. No chat da IA, cole o conteúdo e adicione:
   "Baseado nesse contexto, vamos continuar o Reino Sombrio"

3. A IA vai entender todo o projeto e pode ajudar a continuar

---

## 19. OBSERVAÇÕES IMPORTANTES

- O .gitignore ignora static/assets/ (packs grandes não vão pro Git)
- O Render dorme a cada 15min sem acesso -> UptimeRobot resolve
- Service Worker (sw.js) precisa ser "Unregister" no Chrome ao atualizar
- image-rendering: pixelated no CSS mantém sprites nítidos
- Backup do rpg.db antes de mudanças grandes no banco
- Conta trezes tem poder total (dev)
- Conta kowz é para testes sem risco

---

**FIM DO DOCUMENTO - Bom trabalho no Reino Sombrio!**
