# Backlog e definição de pronto da v1.0

## Feito em 2026-11-14
- Proveniência honesta (`combat`/`exploration` inferred; ritmo `unavailable` sem encontros).
- Controle de qualidade por sessão e dispersão entre sessões.
- Taxas padrão no gerador; validador `n/a` sem dado.
- `.gitignore` para sessões brutas; README e RFC 0001 atualizados.

## Depende do autor (Mesen e ROM na sua máquina)
1. Aplicar este pacote, rodar os testes e abrir PR.
2. Calibrar o bot: sessão humana + `retrodna calibrate --gameplay-from N`.
3. `retrodna auto ... --sessions 3` e enviar `quality.json`, `genome.json`, `report.md` e o `.jsonl.log`.
4. Testar o exportador no Roblox Studio (ou manter como experimental).

## Depois
5. Experimento A/A'/B (3 sessões de A, 3 de A', 3 de B): só afirmar que o Genome distingue jogos se dist(A,B) ≫ dist(A,A').
6. Job de CI com demo sem ROM e tag `v0.1.0`.
7. Fase 2 (ver `fase2-brief.md`) e, se valer a pena, leitura de RAM por busca de memória.

## Definição de pronto v1.0 (rascunho, aguarda confirmação)
- Demo sem ROM no CI. - `auto` captura 3 sessões do ZAMN sem intervenção.
- Pelo menos 1 Genome real com QC e proveniência honesta. - Suíte verde + roteiro de teste manual registrado.
- README, RFCs, devlog, plano e resultados atualizados. - Sem ROM/sessões no repositório; licença e aviso legal.
