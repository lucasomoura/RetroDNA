# RFC 0001 — Design Genome v0.2

- **Status:** Aceito (implementado em `packages/schema/genome.py`)
- **Substitui:** rascunhos v0.1 do plano (`docs/architecture/plano-v2.1.txt`, seções 9 e 17)

## Motivação
O Genome é o contrato entre observação, análise, IA, geração e exportadores. É uma representação
**independente de console e de engine** do "DNA" de design de um jogo: ritmo, tensão, densidade de
inimigos, estrutura de fases. Uma vez produzido, serve para gerar conteúdo (Roblox, Unity, Godot) ou
documentos de design.

## Regras
1. **Só métricas abstratas.** Nenhum sprite, mapa, áudio, código ou nome de fase do jogo original.
2. **Proveniência por campo** (`provenance`): `measured` | `inferred` | `hypothesis` | `unavailable`.
   IA pode interpretar `measured`; nunca altera números nem trata `hypothesis` como fato.
3. **Escalas** normalizadas 0–1 para densidades/frequências; valores absolutos em `raw`
   (a normalização perde a unidade, e o gerador precisa dela). Constantes em `normalization`.
4. **Campos sem dado ficam `null`** e marcados `unavailable`, em vez de assumirem um valor.
5. **Schema estrito** (`extra="forbid"`): campos desconhecidos são erro.

## Estrutura
```
genome_version, source{game,sessions,duration_s}, movement{player_speed_px_s},
gameplay{exploration,combat,objective_density,enemy_density,reward_frequency},
level_design{average_area_size,alternate_routes,chokepoints,open_area_frequency},
pacing{average_exploration_time_s,average_combat_duration_s,average_time_between_encounters_s},
tension{curve[8]}, enemies{archetypes[{name,speed_ratio,share}]},
raw{enemies_active_mean,objectives_per_min,rewards_per_min,encounters},
normalization{...}, provenance{"secao.campo": "measured|inferred|hypothesis|unavailable"}
```
JSON Schema gerado a partir do modelo: `docs/genome/genome.schema.json`.

## Definições

| Campo | Escala | Origem | Cálculo |
|---|---|---|---|
| movement.player_speed_px_s | px/s | measured | mediana do deslocamento por segundo do jogador |
| gameplay.combat | 0–1 | measured | fração das amostras com inimigo a < 64 px |
| gameplay.exploration | 0–1 | measured | 1 − combat |
| gameplay.enemy_density | 0–1 | measured | média de inimigos ativos / 8 |
| gameplay.objective_density | 0–1 | measured | eventos `rescue` por min / 2 |
| gameplay.reward_frequency | 0–1 | measured | eventos `item` por min / 4 |
| level_design.average_area_size | 0–1 | inferred | diagonal média da região visitada por área / 300 px |
| level_design.alternate_routes | 0–1 | inferred | (E − V + 1) / V no grafo de transições entre áreas |
| level_design.chokepoints | 0–1 | inferred | fração de áreas cuja remoção desconecta o grafo |
| level_design.open_area_frequency | 0–1 | unavailable | exige análise de vídeo (futuro) |
| tension.curve | 8 pontos, 0–1 | hypothesis | fórmula abaixo, média por segmento |
| enemies.archetypes | share 0–1 | inferred | razão de velocidade inimigo/jogador: < 0,75 `slow_chaser`; < 1,1 `steady_pursuer`; senão `fast_ambush` |

### Pacing (definições formais)
- `average_combat_duration_s`: início → fim de um encontro.
- `average_exploration_time_s`: **fim** de um encontro → **início** do próximo.
- `average_time_between_encounters_s`: início → início.
- Invariante: `between ≈ exploration + combat` (±30%), verificada em `packages/schema/validation.py`.

### Tensão (v0, experimental)
Por amostra, limitada a [0, 1]:
```
0.35·min(1, inimigos_perto/3) + 0.25·max(0, 1 − dist_mais_próximo/128)
+ 0.20·(dano nos últimos 2 s) + 0.20·min(1, tempo_no_encontro/20 s)
− 0.15·(item nos últimos 5 s) − 0.10·(nenhum inimigo a < 128 px)
```
Ainda não inclui projéteis, obstáculos, objetivos ativos nem rotas de fuga. **Calibrar com gameplay real.**

## Limitações conhecidas
- Uma sessão mede o jogador tanto quanto o design → agregar ≥ 3 sessões (`retrodna pipeline a b c`).
- Métricas de level design cobrem só as áreas visitadas; exigem o campo `area` na telemetria.
- Com o observador OAM (RFC 0002) não há eventos: risco/recompensa da tensão valem 0 e
  `objective_density`/`reward_frequency` ficam `unavailable`.

## Alternativas descartadas
- **Extrair mapas da ROM:** formato próprio por jogo, quase sempre comprimido; não generaliza e aproxima o
  projeto de reproduzir conteúdo protegido.
- **Genome plano:** mistura seções e não comporta proveniência.
