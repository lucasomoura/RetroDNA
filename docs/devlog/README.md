# Diário de desenvolvimento

Registro, em ordem, do que foi construído e do que ficou funcionando. As datas dos commits vêm do histórico do Git
(`git log`); o histórico é a fonte de verdade. Esta versão foi reconstruída depois dos fatos (retroativa).
Erros e becos sem saída ainda não são documentados aqui (decisão do autor).

## Decisões de fundação
1. **Observar em vez de decodificar a ROM.** O jogo roda num emulador e o RetroDNA lê a tabela de sprites (OAM), o input e o
   scroll; não depende de endereços de RAM por jogo nem do formato de cada console.
2. **Genome primeiro.** O Design Genome é o contrato entre observação, análise, geração e exportação ([RFC 0001](../RFC/0001-design-genome.md)).
3. **IA interpreta, não inventa números.** Todo campo tem proveniência: `measured`, `inferred`, `hypothesis` ou `unavailable`.
4. **O gerador cria tudo do zero.** Nada do jogo original (arte, nomes, mapas, música) entra no Genome nem na saída.
5. **Objetivo do projeto:** conhecimento e portfólio, código aberto (MIT), divulgação só quando estiver funcional e documentado.

## 2026-09-29 — Esqueleto e MVP
- Repositório criado (README, licença MIT, `pyproject.toml`, CI com Ruff + Pytest em Python 3.13).
- MVP do pipeline (`4a39aca`): Genome v0.2, observador OAM/auto, métricas, relatório, gerador de mapas, validador do mapa e
  exportador Roblox, com telemetria sintética (`retrodna sample`).
- Layout `apps/` + `packages/`, contratos pydantic, RFC 0001 (Genome) e RFC 0002 (Observer), JSON Schema gerado, exemplo sintético.
- **Resultado:** pipeline completo roda sem ROM e está coberto por testes no CI.

## 2026-09-30 — Observer no Mesen
- Lançamento do MesenCE por linha de comando (ROM e `.lua` como argumentos posicionais) e observador Lua que grava a OAM,
  o input e o scroll a ~10 Hz (`34f80b0`).
- **Resultado:** primeiro fluxo ponta a ponta no Windows com a ROM do ZAMN.

## 2026-10-01 — Bot jogando e telemetria gravada
- `efa6434`: o bot joga sozinho e o arquivo de saída é gerado. `10db630`: callback `inputPolled` do bot restaurado (PR #4).
- Primeira sessão real do ZAMN convertida pelo conversor OAM (confiança do jogador 0,87, câmera detectada) e transformada em
  Genome e relatório (números em [testing/README.md](../testing/README.md)).

## Em verificação (entregue em zips, ainda fora da `main` no momento desta nota)
- Detecção de menu/gameplay por contagem de sprites, com tolerância e aquecimento de 5 s; `retrodna calibrate`; `retrodna setup-mesen`.
  Testados com um Mesen simulado em Lua; **falta confirmar no Mesen real**.

## 2026-11-14 — Qualidade e honestidade dos dados
- Controle de qualidade por sessão (`quality.json`): sessões curtas, jogador mal identificado ou parado são rejeitadas, com motivo.
- Dispersão entre sessões (`dispersion`) para saber se as sessões concordam.
- Proveniência mais honesta: `combat`/`exploration` passam a `inferred` (são proxy de proximidade); o ritmo vira `unavailable`
  quando não há encontros suficientes.
- Taxas padrão movidas do Genome para o gerador; o validador marca objetivos/recompensas sem dado como `n/a` (antes comparava
  o mapa com o próprio padrão do gerador).
- `.gitignore` cobre sessões brutas (`*.oam.jsonl*`) e `*.patch`; README com o estado real; RFC 0001 atualizado.
- Testes de Lua passam a rodar de verdade em ambiente com interpretador Lua (44 → 55 testes verdes, nenhum pulado).
- Pesquisa pública sobre a ROM do ZAMN ([research/zamn-rom.md](../research/zamn-rom.md)) e brief da Fase 2 ([fase2-brief.md](../fase2-brief.md)).
