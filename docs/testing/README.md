# Testes

## Como rodar
```bash
pip install -e ".[dev]"
ruff check . && pytest -q
```
O CI (`.github/workflows/tests.yml`) roda Ruff e Pytest em Python 3.13. Os testes do observador Lua precisam de um interpretador
Lua 5.4 (`lua5.4` ou `lua` no PATH); sem ele aparecem como *skipped*. Para rodá-los: instale o Lua e rode `pytest -q` de novo.

## O que cada arquivo cobre
| Arquivo | Cobertura |
|---|---|
| `tests/test_genome.py`, `test_genome_contract.py` | contrato do Genome: campos, proveniência, rejeição de dados inválidos, JSON Schema e exemplo em sincronia |
| `tests/test_pipeline.py` | telemetria sintética → métricas → Genome → relatório → mapa → validação → exportação |
| `tests/test_oam.py` | conversão OAM: HUD, câmera, jogador, inimigos, contratos |
| `tests/test_auto.py` | `retrodna auto`: comando do Mesen, renderização do script e o **bot contra um Mesen simulado** (Start só nos menus, não grava menus, ignora lixo do boot, tolera oscilação, volta ao menu, desiste sem gameplay) |
| `tests/test_calibrate.py` | `retrodna calibrate` |
| `tests/test_mesen_setup.py` | `retrodna setup-mesen` (edição segura do `settings.json`) |
| `tests/test_quality.py` | controle de qualidade por sessão, dispersão, proveniência honesta, validador sem checagem circular |

## Resultados registrados
Estado em 2026-11-14 (ambiente de desenvolvimento, Python 3.13, Lua 5.4): **55 testes passando, Ruff sem avisos**.

### Teste com dado real — ZAMN, 1 sessão (`sessao1.oam.jsonl`)
Reprodução em 2026-11-14 com o pipeline atual (`retrodna extract`):

| Item | Resultado |
|---|---|
| Amostras de gameplay | 292 (~51 s) |
| Confiança do jogador / câmera | 0,87 / detectada |
| Controle de qualidade | aceita (82,1% do tempo em movimento) |
| Velocidade do jogador | 91,82 px/s |
| Inimigos ativos (média) | 2,3 |
| Encontros / combate / exploração / intervalo | 5 / 2,3 s / 8,5 s / 10,7 s |
| Arquétipos | lento 60% (0,48×), constante 25% (0,96×), rápido 15% (1,61×) |
| Indisponível (OAM não vê) | objetivos, recompensas, level design |

Leitura honesta: uma sessão de bot não representa o design do jogo. Serve para provar que a cadeia observação → Genome funciona
com dado real. Falta variabilidade (3+ sessões) e comparação entre jogos.

## Roteiro de teste manual (precisa do Mesen e da ROM)
Registre data, versão do Mesen e resultado de cada passo.
1. `retrodna setup-mesen` (Mesen fechado) → confere que `AllowIoOsAccess` ficou ligado.
2. `retrodna prepare --mode human --file D:/pasta/humano.jsonl` → carregar o `.lua` no Mesen e jogar: título → Start → seleção → Start → ~20 s de fase.
3. `retrodna calibrate D:/pasta/humano.jsonl --gameplay-from SEGUNDO` → anotar o `--gameplay-sprites` sugerido.
4. `retrodna auto ROM --mesen EXE --sessions 3 --seconds 120 --out out_zamn` → o bot sai do menu, anda e atira; 3 sessões gravadas.
5. Conferir `out_zamn/quality.json`, `genome.json` e `report.md`; guardar o resultado neste arquivo.

## Lacunas conhecidas
- Detecção de menu/gameplay por sprites ainda não confirmada no Mesen real.
- Exportador Roblox nunca testado no Studio.
- Fórmula de tensão (hipótese) sem calibração; limites do controle de qualidade são heurísticas.
- Sem experimento A/A'/B (distância entre sessões do mesmo jogo vs entre jogos).
