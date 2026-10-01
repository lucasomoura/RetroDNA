# RFC 0002 — Observer e telemetria

- **Status:** Aceito (implementado em `apps/observer/` e `packages/events/`)

## Ideia
O Observer **mede o jogo rodando** em um emulador; não decodifica a ROM. Isso funciona para qualquer jogo
e evita extrair conteúdo protegido. A saída é um arquivo JSONL de telemetria que o resto do pipeline consome.

## Duas fontes de telemetria (detectadas automaticamente)

### 1. OAM (padrão, sem endereços de RAM)
`apps/observer/templates/retrodna_observer.lua` grava, ~10 Hz, a tabela de sprites (OAM), o input e o scroll do PPU:
```json
{"meta": {"source": "oam", "mode": "bot"}}
{"f": 60, "in": "right,y", "oam": "<1088 hex>", "sc": {"...hscroll": 12}}
```
`packages/events/oam.py` converte isso em quadros `{t, px, py, enemies}`:
1. Descarta sprites de HUD (parados e sem trocar de tile).
2. Agrupa sprites próximos em objetos e soma o scroll da câmera para obter coordenadas de mundo.
3. Liga objetos entre amostras (rastros) e escolhe o **jogador** pela correlação do movimento e da
   animação com o input; rastros fragmentados do jogador são unidos pela assinatura de tiles.
4. Demais objetos móveis viram **inimigos**.

Limites: sem eventos (dano, item, objetivo); jogadores sem animação ou câmera sem scroll baixam a
confiança (reportada em `player_confidence`); jogos com Mode 7 ou efeitos que reutilizam o OAM enganam o rastreador.

### 2. Telemetria direta (RAM ou simulada)
```json
{"t": 12.3, "px": 100.0, "py": 40.0, "enemies": [{"id": 3, "x": 150.0, "y": 60.0}],
 "area": "2_1", "event": "damage"}
```
`event` ∈ `damage | kill | rescue | item`; `area` habilita as métricas de level design.
Modelos pydantic em `packages/schema/events.py`. `apps/observer/templates/mesen_ram_capture.lua` é um
exemplo que exige mapear endereços de RAM por jogo; `retrodna sample` gera telemetria sintética.

## Modos
- `retrodna auto jogo.sfc --mesen <caminho>`: abre o MesenCE (`--runner gui`, padrão) com a ROM e o script
  como **argumentos posicionais**; um **bot** se move de forma pseudoaleatória, tenta passar da tela de título
  e ataca. O script grava `<saida>.done` ao terminar e o Python fecha o Mesen. `--runner testrunner` usa o
  modo `--testRunner`, que no MesenCE 2.2.1 inicia a interface e não executou o script nos testes feitos.
- O MesenCE só aceita `--doNotSaveSettings`, `--enableStdout`, `--fullscreen`, `--loadLastSession`,
  `--recordMovie`, `--testRunner` e `--update` (conferido no binário). **Não existem** `--luaScript` nem
  `--allowLuaScriptIO`: o acesso a I/O é a opção "Allow access to I/O and OS functions" do Mesen.
- `retrodna prepare`: gera o script configurado para **você** jogar (modo `human`) no Script Window.

## Riscos
- O bot é um explorador ingênuo: pode não sair de menus nem chegar a áreas avançadas. O relatório mostra a
  duração e a confiança; sessões humanas são o caminho de referência.
- A API de scripts (nomes de eventos, `setInput`, `memType`) foi conferida na documentação embutida do MesenCE
  2.2.1 e o observador roda contra uma API simulada (`tests/fixtures/mock_emu.lua`); falta validar com o
  Mesen real e um jogo.
