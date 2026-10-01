```text
RetroDNA/
├── apps/
│   ├── observer/
│   ├── analyzer/
│   ├── generator/
│   └── exporter/
├── packages/
│   ├── schema/
│   ├── metrics/
│   ├── events/
│   └── utils/
├── docs/
│   ├── RFC/
│   ├── genome/
│   └── architecture/
├── examples/
├── tests/
└── README.md

# RetroDNA

Learn the recipe. Build a new game.

RetroDNA é uma ferramenta de engenharia reversa de game design.

O projeto analisa jogos retrô, extrai padrões estruturais e gera um Design Genome, uma representação abstrata capaz de orientar a criação de jogos inéditos.

## Objetivo da versão 0.1

- Criar o Design Genome.
- Construir o Observer.
- Extrair métricas de gameplay.
- Gerar mapas procedurais.
- Exportar para Roblox.

## Como usar

Requer Python 3.13.

```bash
pip install -e ".[dev]"

# 1) Sem ROM: telemetria sintética -> genome -> mapa -> validação
retrodna sample a.jsonl --seed 7
retrodna sample b.jsonl --seed 11
retrodna sample c.jsonl --seed 5
retrodna pipeline a.jsonl b.jsonl c.jsonl --game Teste --theme humor --seed 3 --out out

# 2) Automático com uma ROM (o Mesen roda sem interface e um bot joga)
retrodna auto jogo.sfc --mesen /caminho/do/Mesen --sessions 3 --seconds 300 --out out

# 3) Manual: gera o observador, você joga no Mesen, depois processa
retrodna prepare --file sessao1.jsonl
retrodna pipeline sessao1.jsonl --game NomeDoJogo

pytest && ruff check .
```

Emulador: use o **MesenCE** (https://github.com/nesdev-org/MesenCE/releases). O repositório SourMesen/Mesen2
foi arquivado em 2025.

**Uma vez só, antes do primeiro uso:** no Mesen, abra as configurações, aba **Script Window**, e marque
**"Allow access to I/O and OS functions"**. Sem isso o script Lua não consegue gravar a telemetria. Essa opção é uma
configuração do Mesen; não existe opção de linha de comando para ela.

O `retrodna auto` abre o Mesen (janela visível) com a ROM e o script como argumentos, o bot joga em tempo real e o
Python fecha o Mesen quando o script termina. A saída do Mesen fica em `sessions/*.mesen.log`.
Se o Mesen abrir mas nada for gravado, o comando falha em ~45 s com o motivo provável.

Saída em `out/`: `metrics.json`, `genome.json`, `report.md` (DADO / INTERPRETAÇÃO / HIPÓTESE),
`llm_prompt.md`, `validation.md`, `roblox/`.

## Estado

| Parte | Situação |
|---|---|
| Genome v0.2 (pydantic), métricas, relatório, gerador, validador | implementado e testado |
| Conversor OAM (jogador e inimigos sem endereços de RAM) | testado com simulação; **não** com um jogo real |
| `retrodna auto` | validado pelo autor com o MesenCE 2.2.1 e um jogo real (bot joga e a telemetria é gravada); o conversor OAM ainda precisa de mais jogos |
| Exportador Roblox, plugin e scripts Luau | implementados, congelados, sem teste no Studio |

A validação do mapa confirma que o gerador cumpre as métricas do Genome; não prova que a experiência é parecida.
A fórmula de tensão e os limiares precisam de calibração com gameplay real.

## Documentação
- [RFC 0001 — Design Genome](docs/RFC/0001-design-genome.md)
- [RFC 0002 — Observer e telemetria](docs/RFC/0002-observer-events.md)
- [Arquitetura](docs/architecture/overview.md) e [plano v2.1](docs/architecture/plano-v2.1.txt)
- [JSON Schema do Genome](docs/genome/genome.schema.json)

## Legal
Nada do jogo original entra no Genome nem na saída. Não distribua ROMs.

### Sobre o bot
- **Menus:** enquanto a tela tem poucos sprites (título, seleção de personagem, password...), o bot **só aperta Start**,
  em pulsos de 8 frames a cada 2,5 s, e nunca mexe o direcional nem aperta A/B. Não depende de tempo fixo.
- **Gameplay:** quando a tela tem pelo menos `--gameplay-sprites` sprites visíveis (padrão 12) por 1 s seguido, o bot
  começa a andar/atacar **e a gravar**. Se a contagem cair abaixo disso por 6 s (game over, menu, pausa), ele volta a
  apertar Start e para de gravar. `--seconds` conta só o tempo gravado de gameplay.
- Se o gameplay não for detectado em 120 s, a sessão termina com erro explicando como ajustar.
- **Calibração (uma vez por jogo):** a cada ~2 s o script escreve `RDNA: sprites=N gameplay=...` no log
  (`<saida>.mesen.log`, ou o painel de log da janela de script do Mesen). Veja o número em cada tela:
  se os menus mostram menos sprites que o gameplay, o padrão serve. Senão, escolha um valor entre os dois, por exemplo
  `retrodna auto ... --gameplay-sprites 25`.
- Os testes com o Mesen simulado (`tests/test_auto.py`, exigem Lua instalado) cobrem: o bot chama `setInput`, só aperta
  Start nos menus, não grava menus, volta ao menu após game over e desiste se nunca detectar gameplay.
