# Fase 2 — Brief: um sucessor espiritual, com identidade própria

Status: **ideia**, depois da v1.0. Nada aqui está implementado.

## Visão
Um jogo cooperativo de sobrevivência com a premissa: **sobreviventes espalhados pelo mapa, zumbis que podem capturá-los, e o
jogador os resgata.** A ideia (mecânica) vem do que o RetroDNA observou; tudo o mais é original.

## O que é referência e o que é original
| Item | Uso |
|---|---|
| Premissa e loop de resgate | referência (ideia de mecânica) |
| Ritmo, tensão, densidade de inimigos | medidos pelo RetroDNA (Genome) e usados como régua |
| Estilo visual e música | **referência de clima**; arte e composição 100% novas |
| Nome, personagens, fases, textos | **originais**, nada do ZAMN |
| Fases e dificuldade | criadas pelo gerador, validadas contra o Genome |

## Loop central (rascunho)
1. Sobreviventes aparecem em pontos do mapa. 2. Zumbis tentam capturá-los (relógio de pressão por sobrevivente).
3. O jogador explora, enfrenta zumbis e leva os sobreviventes à saída. 4. Fases maiores: mais sobreviventes, mais ameaças, mais rotas.

## Modo arena por ondas (inspirado em jogos pixel art do Roblox)
Variante com ondas e chefes. Exige medir "ritmo por onda" no Genome (intervalo entre chefes, densidade por onda).

## O que falta no RetroDNA para isso
- Objetivo "resgate" e "captura" no Genome e no validador (hoje `unavailable`).
- Exportador Roblox testado no Studio (hoje experimental, nunca aberto no Studio).
- Curva de dificuldade entre fases (hoje o Genome descreve uma sessão, não uma campanha).
- Arte, som e música originais.

## Critérios de sucesso do protótipo
- Gera N fases, e todas passam no validador. - Dificuldade cresce de forma monótona entre fases.
- Jogável no Studio por uma pessoa por 10 minutos sem erro. - Nenhum asset ou nome do ZAMN no resultado.

## Riscos
- Parecer clone: manter identidade própria. - Escopo: um jogo de cada vez, só generalizar se o primeiro funcionar.
- Conteúdo anual é um compromisso de manutenção: tratar como possibilidade, não promessa.
