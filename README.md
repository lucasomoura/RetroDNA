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
```

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

# 2) Automático com uma ROM (abre o Mesen com a ROM e um bot joga em tempo real)
retrodna auto jogo.sfc --mesen /caminho/do/Mesen --sessions 3 --seconds 300 --out out

# 3) Manual: gera o observador, você joga no Mesen, depois processa
retrodna prepare --file sessao1.jsonl
retrodna pipeline sessao1.jsonl --game NomeDoJogo

pytest && ruff check .
```

Emulador: use o **MesenCE** (https://github.com/nesdev-org/MesenCE/releases). O repositório SourMesen/Mesen2
foi arquivado em 2025.

**Uma vez só, antes do primeiro uso:** o script Lua precisa de acesso a I/O para gravar a telemetria. Essa opção
é do Mesen (não existe opção de linha de comando) e fica na janela **Debugger Settings**, aba **Script Window**,
seção **Restrictions**: "Allow access to I/O and OS functions". Para ligá-la sem procurar no menu, **feche o Mesen** e rode:

```bash
retrodna setup-mesen            # procura o settings.json; use --settings CAMINHO se não achar
```
Ele só edita o arquivo se encontrar `Debug.ScriptWindow` e guarda um backup `settings.json.bak`.

O `retrodna auto` abre o Mesen (janela visível) com a ROM e o script como argumentos, o bot joga em tempo real e o
Python fecha o Mesen quando o script termina. O log do script fica em `sessions/*.jsonl.log` e a saída do Mesen em `sessions/*.mesen.log`.
Se o Mesen abrir mas nada for gravado, o comando falha em ~45 s com o motivo provável.

Saída em `out/`: `metrics.json`, `genome.json`, `report.md` (DADO / INTERPRETAÇÃO / HIPÓTESE),
`llm_prompt.md`, `validation.md`, `roblox/`.

## Estado

| Parte | Situação |
|---|---|
| Genome v0.2 (pydantic), métricas, relatório, gerador, validador | implementado e testado (CI) |
| Conversor OAM (jogador e inimigos sem endereços de RAM) | testado com simulação **e** com 1 sessão real do ZAMN (confiança do jogador 0,87); precisa de mais sessões e de outros jogos |
| `retrodna auto` | com o MesenCE 2.2.1 e um jogo real, o bot jogou e a telemetria foi gravada (confirmado pelo autor); a detecção de menu/gameplay por contagem de sprites ainda **não** foi confirmada no Mesen real |
| Controle de qualidade por sessão (`quality.json`) | implementado e testado; limites são heurísticas iniciais |
| Dispersão entre sessões (`dispersion` no Genome) | implementada e testada; só existe com 2+ sessões |
| Exportador Roblox, plugin e scripts Luau | implementados, congelados, **sem teste no Studio** (experimental) |

A validação do mapa confirma que o gerador cumpre as métricas do Genome; não prova que a experiência é parecida.
Objetivos e recompensas só são validados quando o Genome os mediu; sem o dado, a checagem aparece como `n/a`.
A fórmula de tensão e os limiares precisam de calibração com gameplay real.

A validação do mapa confirma que o gerador cumpre as métricas do Genome; não prova que a experiência é parecida.
A fórmula de tensão e os limiares precisam de calibração com gameplay real.

## Documentação
- [RFC 0001 — Design Genome](docs/RFC/0001-design-genome.md)
- [RFC 0002 — Observer e telemetria](docs/RFC/0002-observer-events.md)
- [Arquitetura](docs/architecture/overview.md) e [plano v2.1](docs/architecture/plano-v2.1.txt)
- [JSON Schema do Genome](docs/genome/genome.schema.json)
- [Lições do desenvolvimento com IA](docs/lessons-ai.md)
- [Diário de desenvolvimento](docs/devlog/README.md) e [testes](docs/testing/README.md)
- [Backlog e definição de pronto da v1.0](docs/backlog.md)
- [Pesquisa sobre a ROM do ZAMN](docs/research/zamn-rom.md) e [brief da Fase 2](docs/fase2-brief.md)

## Legal
Nada do jogo original entra no Genome nem na saída. Não distribua ROMs.

### Sobre o bot
- **Menus:** enquanto a tela tem poucos sprites (título, seleção, password...), o bot **só aperta Start**, em pulsos de
  8 frames a cada 5 s, e nunca mexe o direcional nem aperta A/B. Não depende de tempo fixo.
- **Gameplay:** entra quando pelo menos 8 das últimas 10 leituras (1 s) têm `--gameplay-sprites` sprites visíveis (padrão 8)
  e só volta ao menu após 15 s seguidos abaixo do limite. Ignora os primeiros 5 s (a OAM do boot tem lixo).
  Só grava em gameplay; `--seconds` conta só o tempo gravado.
- Se o gameplay não for detectado em 120 s, a sessão termina com erro explicando como ajustar.
- **Por que há tolerância:** no ZAMN, 20% das amostras de gameplay real ficam abaixo de 12 sprites; um limite rígido fazia o bot
  "perder" o jogo e bater Start, o que **pausa/despausa** o jogo.
- O script grava seu próprio log em `<saida>.log` (linhas `sprites=N gameplay=...` a cada ~2 s). O stdout do Mesen
  (`<saida>.mesen.log`) só traz o cabeçalho da ROM.

### Calibrar o limite de sprites para um jogo novo
1. `retrodna prepare --mode human --file D:/pasta/humano.jsonl` e carregue o script no Mesen.
2. Jogue você mesmo: título → Start → seleção → Start → ~20 s de fase. Anote em que segundo o gameplay começou.
3. `retrodna calibrate D:/pasta/humano.jsonl` mostra a contagem de sprites ao longo do tempo;
   depois `retrodna calibrate D:/pasta/humano.jsonl --gameplay-from 45` sugere o `--gameplay-sprites` (ou avisa que
   menus e jogo não são separáveis por contagem de sprites).

### Testes do bot
Os testes com o Mesen simulado (`tests/test_auto.py`, exigem Lua instalado) cobrem: o bot chama `setInput`, só aperta Start
nos menus, não grava menus, ignora o lixo do boot, tolera gameplay oscilante sem pausar, volta ao menu após game over e
desiste se nunca detectar gameplay.
