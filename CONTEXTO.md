# REINO SOMBRIO MMORPG — Contexto do Projeto
Última atualização: 19/09/2026 (tarde)

## 1. O QUE É O PROJETO
MMORPG 2D online, inspirado no Curse of Aros, feito em Flask + SQLite
rodando no Termux (Android).

- Nome: Reino Sombrio MMORPG
- Estilo: pixel art 2D top-down
- Servidor local: Termux + Flask + SQLite
- URL local: http://127.0.0.1:5000
- URL rede: http://192.168.18.28:5000
- Repositório: https://github.com/trezes-dev/Reino-sombrio
- Conta admin/dev: trezes
- Conta teste: kowz
- Senha admin panel: admin123

## 2. STACK TÉCNICA
- Backend: Python 3.13 + Flask + SQLite (WAL mode)
- Frontend: HTML + CSS + JavaScript puro
- Sprites: LPC (jogador), CraftPix (slimes)
- Ferramentas: PIL/Pillow

## 3. ESTADO ATUAL DO MAPA
- Tamanho: 200x200 (40.000 tiles)
- Estrutura: 4 quadrantes + Lobby central + cruz de caminhos
  - Q1 Sup Esq: grama_escura (Floresta Escura)
  - Q2 Sup Dir: grama_floresta (Floresta Normal)
  - Q3 Inf Esq: areia_deserto (Deserto)
  - Q4 Inf Dir: pedra_ruinas (Ruinas)
  - Centro: grama_lobby (Lobby 30x30)
  - Cruz: terra_caminho (6 tiles largura)
- Gerador: ~/rpg/gerar_mapa_cruz.py

## 4. VARIAVEIS SINCRONIZADAS (CRITICO)
### server.py:
W_MAP = 200
H_MAP = 200
VIEW = 41
METADE = 20

### index.html:
const W_MAP = 200;
const H_MAP = 200;
const VIEW = 41;
const METADE = 20;
const TILE_PX = 40;

## 5. NPCs (no Lobby)
| Nome | X | Y | Tipo |
|------|---|---|------|
| Mercador | 97 | 95 | loja |
| Ferreiro | 95 | 100 | ferreiro |
| Alquimista | 105 | 100 | alquimista |

## 6. MONSTROS (3 Slimes coloridos)
| Nome | X | Y | HP | Dano | Bioma |
|------|---|---|-----|------|-------|
| Slime Verde | 150 | 50 | 30 | 3 | Floresta Normal |
| Slime Azul | 50 | 50 | 60 | 6 | Floresta Escura |
| Slime Vermelho | 150 | 150 | 100 | 12 | Ruinas |

### Sprites dos slimes:
- Original: slime.png (384x256, spritesheet 6 frames x 4 direcoes)
- Coloridos gerados com rotacao HSV via Python (slime_verde/azul/vermelho.png)
- CSS usa background-size:384px 256px + animation:monstroIdle 1s steps(6) infinite

## 7. TILES DE CHAO (static/sprites/terreno/chao/)
grama_lobby.png, grama_normal.png, grama_escura.png,
areia_deserto.png, pedra_ruinas.png, terra_caminho.png

## 8. CLASSES CSS IMPORTANTES
.tile.grama_lobby -> grama_lobby.png
.tile.grama_floresta -> grama_normal.png
.tile.grama_escura -> grama_escura.png
.tile.areia_deserto -> areia_deserto.png
.tile.pedra_ruinas -> pedra_ruinas.png
.tile.terra_caminho -> terra_caminho.png

## 9. APIs DO SERVIDOR
POST /login
POST /criar_personagem
GET  /api/estado
GET  /api/mover/<dir> (cima, baixo, esq, dir)
POST /api/atacar
POST /api/chat
POST /api/comprar, /api/vender
GET  /api/loja/<npc_id>
GET  /api/objetos
GET  /minimapa.png (imagem 200x200)
GET  /api/mapa_completo (JSON todos os tiles)

## 10. BUGS CORRIGIDOS EM 19/09
1. W_MAP/H_MAP estavam 50, mudados para 200
2. VIEW sincronizado entre server e client (41)
3. Funcao bloqueia() consulta banco (nao cache)
4. SQLite com WAL mode + timeout
5. UPDATE unico no /api/mover (x,y,hp,ouro)
6. Slimes coloridos (rotacao HSV)

## 11. PENDENCIAS / PROXIMOS PASSOS
- [ ] Testar visualmente Slime Verde e Slime Azul
- [ ] Colisao completa (nao atravessar arvores)
- [ ] Chao de pedra lisa nas Ruinas (atual e tijolo)
- [ ] Sistema de drops
- [ ] Chat (testar envio)
- [ ] Melhorar visual do mapa

## 12. COMANDOS UTEIS

### Reiniciar servidor:
pkill -9 -f server.py && sleep 2 && cd ~/rpg && python3 server.py

### Acessar banco:
sqlite3 ~/rpg/rpg.db

### Ver monstros:
sqlite3 ~/rpg/rpg.db "SELECT nome, x, y FROM monstros;"

### Backup:
pkill -9 -f server.py && sleep 2
tar -czf ~/rpg_backup_$(date +%Y%m%d_%H%M).tar.gz -C ~ --exclude='rpg/static/assets' --exclude='rpg/static/sprites/terreno/*/ASEPRITE' --exclude='rpg/static/sprites/terreno/*/PSD' --exclude='rpg/static/sprites/terreno/*/__MACOSX' --exclude='rpg_backup_*' rpg
cd ~/rpg && python3 server.py &

### Git push:
cd ~/rpg && git add . && git commit -m "msg" && git push origin main

## 13. COMO RETOMAR EM CHAT NOVO
1. No Termux: cat ~/rpg/CONTEXTO.md | termux-clipboard-set
2. No chat da IA: colar + "Baseado nesse contexto, vamos continuar o Reino Sombrio"

## 14. Sessao 19/09/2026 (tarde) - Resumo
- Reset total do mapa (apagamos todos os packs antigos)
- Restaurado: chao/, jogador/, monstros/, itens/, npcs
- Mapa novo 200x200: 4 quadrantes + Lobby + cruz de caminhos
- 3 NPCs posicionados no Lobby
- 3 Slimes coloridos (verde, azul, vermelho)
- Slime Vermelho confirmado visualmente funcionando
- Viewport sincronizado (VIEW=41, METADE=20)
- Pendente: testar slimes verde/azul, colisao, drops

## 15. OBSERVACOES IMPORTANTES
- .gitignore ignora static/assets/
- Service Worker precisa ser Unregister no Chrome ao atualizar
- image-rendering: pixelated no CSS
- Backup do rpg.db antes de mudancas grandes
- Conta trezes = dev total
- Conta kowz = testes

FIM DO DOCUMENTO

---

## 16. PENDÊNCIA PRINCIPAL - MUROS DO REINO

### Status atual:
Os muros do Reino estão FUNCIONAIS mas com visual feio (criados por código Python).
Não ficaram parecidos com o estilo do Curse of Aros.

### Preview aprovado (referência visual):
http://127.0.0.1:5000/static/sprites/lobby/muros/_preview_ok.png

Esse preview mostra o muro que o usuário APROVOU (topo claro + linha preta + frente escura com tijolos pretos bem definidos).
O problema é que essa arte precisa ser aplicada corretamente no jogo.

### O que fazer amanhã:
1. Analisar o `_preview_ok.png` que já está salvo
2. Aplicar essa arte nos muros (CSS ou sprite)
3. Testar a física (topo na frente/trás, só grossura nas laterais)
4. Se não funcionar, considerar contratar pixel artist no Fiverr (R$30-50)

### Arquivos importantes:
- `~/rpg/static/sprites/lobby/muros/muro_frente.png` (muro de frente/trás)
- `~/rpg/static/sprites/lobby/muros/muro_lateral.png` (muro lateral - só grossura)
- `~/rpg/static/sprites/lobby/muros/_preview_ok.png` (preview aprovado)
- Backup de segurança: `~/rpg_BACKUP_LIMPEZA_20260920_0049.tar.gz`

### Banco de dados - tipos de muro:
- `muro_castelo` / `muro_topo` → muro de frente/trás
- `muro_vertical` → muro lateral
- `muro_canto` → canto

### Problemas conhecidos:
- Muro fica com listras pretas quando dois tiles ficam lado a lado
- Colisão funciona (não atravessa)
- Z-index funciona (personagem atrás do muro)
- Portões funcionam (4 aberturas: Norte, Sul, Leste, Oeste)

### Contexto visual:
O usuário quer estilo Curse of Aros:
- Topo claro mostrando GROSSURA do muro (visto de cima)
- Linha preta separadora
- Frente escura com tijolos visíveis

---

**FIM DA SEÇÃO DE PENDÊNCIAS**

### Sessão 20/09/2026 (tarde) - Teleporte no mapa
- Clique/toque no mapa grande teleporta (só dev)
- Usa onclick + ontouchstart direto no HTML (funciona no celular)
- Sem confirmação, sem mensagem pra player comum
- Função tpMapa() no index.html

---

### Sessão 20/09/2026 (tarde/noite) - Teleporte no mapa + limpeza

**Funcionalidades:**
- Teleporte pelo mapa grande (só dev): clique/toque → teleporta direto
- Usa `onclick` + `ontouchstart` direto no HTML (funciona no celular)
- Função `tpMapa(e)` no index.html
- Sem confirmação, sem mensagem pra player comum

**Mudanças no mapa:**
- Muros REMOVIDOS do banco (lobby ficou só grama + caminhos + NPCs)
- Backup do banco: `rpg.db.bak_lobby_20260920_1641`

**Pendências (o que NÃO foi feito):**
- [ ] Reconstruir muros do lobby usando editor (Tiled, Tiled Map Editor 2D, ou similar)
- [ ] Sprites dos muros: `_preview_ok.png` aprovado (frente + lateral)
- [ ] Testar slimes verde e azul (o vermelho tá OK)
- [ ] Sistema de drops de itens
- [ ] Colisão com árvores/objetos
- [ ] Pedra lisa nas Ruínas (atual é tijolo)
- [ ] Chat (testar envio)

**Arquivos importantes:**
- `~/rpg/static/sprites/lobby/muros/_preview_ok.png` (referência aprovada)
- `~/rpg/gerar_muro_externo.py` (script pra adicionar muros externos)
- `~/rpg/rpg.db.bak_lobby_20260920_1641` (backup do banco bom)

**Observações:**
- Os sprites `muro_frente.png` e `muro_lateral.png` foram extraídos do `_preview_ok.png`
- Bug do CSS duplicado de muros foi resolvido (limpeza)
- Teleporte só funciona pra cargo `dev`

---

## 21. RELATÓRIO SESSÃO 20/09/2026 (noite) - TRAVAMENTO

**Status: JOGO TRAVANDO**

**Feito nesta sessão:**
- Mapa 200x200 completo (4 biomas + 2 anéis + cruz + fonte)
- Anel 1 (lobby): x=88-112 | Anel 2 (NPCs): x=76-124
- 4 biomas FORA do anel 2 (sem cruz separando)
- 12 slimes spawnados longe do lobby
- bloqueia() simplificada (só água + muros)
- tile_em() usando MAPA_CACHE recarregado no boot
- Minimapa com cores corretas
- CSS slimes coloridos

**PROBLEMA:**
- CPU do server.py 16-20% sem ninguém conectado
- Tela azul 3-5s ao entrar
- Não consegue andar (trava no lugar)
- Cada toque demora 10-15s pra mover 1 tile
- /api/estado demora pra responder

**HIPÓTESES:**
1. ia_monstros em loop pesado
2. estado() abre conexão SQLite por tile (225 conexões/request)
3. /api/estado manda 40000 tiles (deveria mandar só 15x15 = 225)
4. Render do cliente pesado
5. SQLite WAL travando por concorrência

**COMANDOS DEBUG:**
ps aux | grep server.py | grep -v grep
tail -50 /tmp/srv.log
ls /proc/$(pgrep -f server.py)/fd/ | grep -c socket

**BACKUPS:**
server.py.bak_ia, server.py.bak_cpu2, server.py.bak_calma
templates/index.html.bak_calma

**TAREFAS AMANHÃ (prioridade):**
1. [URGENTE] Resolver travamento:
   - ps aux sem cliente: se CPU > 5%, tem thread rodando
   - Se ia_monstros: reescrever com 1 conexão só, sleep 5s
   - Se estado(): mandar só viewport 15x15 (não 40000)
2. [URGENTE] Otimizar /api/estado (viewport em vez de mapa todo)
3. [MÉDIO] Slime verde invisível (CSS com blocos quebrados)
4. [MÉDIO] Verificar bloqueia() (MAPA_CACHE recarregado?)
5. [BAIXO] Polling cliente: testar 5s (já tá em 3s)

**ANOTAÇÕES TÉCNICAS:**
- Anel 1 (lobby): x=88-112, y=88-112
- Anel 2 (NPCs): x=76-124, y=76-124
- Portões: 3 tiles em (99-101, 76/124) e (76/124, 99-101)
- Cruz de caminhos DENTRO dos anéis
- Tiles: grama_lobby, grama_normal, grama_escura, areia_deserto, pedra_ruinas, terra_caminho
- Muros: muro_topo, muro_vertical, muro2_topo, muro2_vertical
- Sprites anel 1: muro_frente.png / muro_lateral.png
- Sprites anel 2: muro2_frente.png / muro2_vertical.png

## 22. PRÓXIMA SESSÃO - PONTO DE PARTIDA

**Estado ao dormir:**
- Servidor rodando com CPU ~16%
- Jogo travando
- ia_monstros removida do código
- Commit: b58898e

**Primeiro comando ao acordar:**
ps aux | grep server.py | grep -v grep

**Se CPU > 5% sem ninguém:** thread rodando
**Solução prioritária:** otimizar /api/estado pra mandar só 15x15 ao redor do jogador
