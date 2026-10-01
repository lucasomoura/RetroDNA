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
| `retrodna auto` | lançamento e observador Lua testados com um Mesen simulado (Lua 5.4 real); **ainda não validado com o Mesen real** |
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

