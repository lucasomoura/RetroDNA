# Lições do desenvolvimento com IA

O RetroDNA foi construído quase todo por IA, com um humano decidindo direção e testando no próprio computador.
Aqui ficam as práticas que funcionaram (os erros ainda não são documentados, por decisão do autor).

## O que funcionou
- **Contrato primeiro.** O Genome com proveniência por campo (`measured`, `inferred`, `hypothesis`, `unavailable`) impede que a IA
  apresente chute como medida. Quando o dado não existe, o campo fica `null` e `unavailable`.
- **Testes sem o ambiente real.** O Mesen foi simulado em Lua, e a telemetria, em Python. Isso permite validar a lógica no CI,
  sem ROM e sem emulador. A simulação não substitui o teste real, e a documentação diz o que falta confirmar.
- **Dado real como juiz.** Os números de uma sessão real do ZAMN (confiança 0,87, 5 encontros, arquétipos) ancoram o que se afirma.
- **Entregas pequenas e reproduzíveis.** Zips só com os arquivos alterados, e depois PRs, com Ruff e Pytest antes de cada entrega.
- **Verificar o estado antes de agir.** Ler `git log`, `git status` e o repositório de novo, em vez de confiar na memória da conversa
  (a `main` real estava atrás do que o histórico sugeria).
- **Decisões registradas.** Devlog, backlog e arquivos de histórico permitem retomar o trabalho depois de uma pausa longa.
- **Honestidade sobre os limites.** O README diz o que está testado, o que é simulação e o que é hipótese.
- **Escopo limitado por pergunta de design.** Antes de investir (por exemplo, em extrair a ROM), listar quais perguntas aquilo responderia.

## Como pedir bem à IA neste projeto
- Dizer o objetivo (portfólio, sem pressa, código aberto) e as convenções (Git Bash, um passo por vez).
- Colar logs e arquivos reais; a IA não deve supor o que o Mesen fez.
- Pedir que cada afirmação diga se é medida, inferida, hipótese ou indisponível.
