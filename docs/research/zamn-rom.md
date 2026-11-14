# Pesquisa: o que se sabe publicamente sobre a ROM do ZAMN

Pesquisa feita em 2026-11-14 com busca web. Objetivo: saber se extrair dados de estrutura da ROM
(fases, tabelas de inimigos, regras de resgate) é viável antes de investir nisso.

## O que encontrei
- A página do jogo no Data Crystal lista subpáginas de **ROM map** e **RAM map**, e a seção de utilitários está vazia.
  Os endereços dessas subpáginas **não pude ler**: o site bloqueia leitura automática (`robots`). Não sei quão completas são.
- A página de curiosidades (TCRF) documenta só pontos isolados: crédito do driver de som em `0x88007`, itens não usados
  (banana, poção cinza, lata de tinta, poção amarela), um bônus incompleto em `0x14CC5`, paleta de inverno em `0xF9271`,
  música não usada em `0xF9292`, sons em `0x54C3`. Nada sobre formato de fases, posição de inimigos ou vítimas.
- Há um projeto de fãs que refez as 55 fases ("Dr. Tongue's Revenge"), o que sugere reconstrução manual, não extração
  automática. Não confirmei como foi feito.
- Não encontrei extrator público de fases do ZAMN nem documentação do formato (compressão, tilemap, tabelas de spawn).

## Conclusão provisória
Extrair a estrutura das fases seria **engenharia reversa do zero**, com risco real de não chegar a lugar nenhum.
O que a documentação pública cobre (curiosidades pontuais) não responde às perguntas de design.

## Perguntas de design que a ROM poderia responder (só estas importam)
1. Quantos inimigos, itens e vítimas por fase e como isso cresce.
2. Atributos dos inimigos (vida, velocidade, dano) e das armas (alcance, cadência, munição).
3. Regra de captura: tempo, distância e consequência de um vizinho capturado.

## Alternativas mais baratas para as mesmas perguntas
- Observar mais sessões (já temos) e ampliar o observador para ler RAM em pontos específicos, **só depois** de achar os
  endereços por busca de memória no depurador do Mesen (valor muda quando o evento acontece).
- Contar na prática (vídeos e partidas) para calibrar números aproximados, marcando-os `inferred`.

## Limites legais (não sou advogado)
Estudar a ROM que você possui, para uso pessoal, é diferente de publicar arte, mapas, sons ou os arquivos extraídos.
Números e regras abstratas podem virar Genome; assets e layouts não entram no repositório nem no jogo novo.

## Fontes
- [Data Crystal — Zombies Ate My Neighbors](https://datacrystal.tcrf.net/wiki/Zombies_Ate_My_Neighbors)
- [TCRF — Zombies Ate My Neighbors (SNES)](https://new.tcrf.net/Zombies_Ate_My_Neighbors_(SNES))
- [Indie Retro News — Dr. Tongue's Revenge (55 fases refeitas)](https://www.indieretronews.com/2017/06/zombies-ate-my-neighbors-dr-tongues.html)
