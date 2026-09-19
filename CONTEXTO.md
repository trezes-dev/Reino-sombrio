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
