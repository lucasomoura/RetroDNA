# Arquitetura

```
ROM ──(emulador)──> Observer ──> telemetria.jsonl ──> events ──> metrics ──> Design Genome
                                                                      │
                                     analyzer (relatório) <───────────┤
                                     generator (mapa novo) <──────────┘ ──> validador ──> exporter (Roblox)
```

| Pasta | Responsabilidade |
|---|---|
| `apps/observer` | roda o emulador, bot/observador Lua, telemetria sintética |
| `apps/analyzer` | relatório DADO / INTERPRETAÇÃO / HIPÓTESE e prompt para LLM |
| `apps/generator` | gerador procedural guiado pelo Genome + validador do mapa |
| `apps/exporter` | JSON + scripts Luau + plugin do Roblox Studio (congelado até haver jogo real) |
| `packages/schema` | contratos pydantic: Genome, telemetria, regras de consistência |
| `packages/events` | telemetria → quadros (inclui a conversão OAM) |
| `packages/metrics` | quadros → métricas → Genome |
| `packages/utils` | estatística compartilhada |

## Princípios
1. Genome primeiro: é o contrato entre as fases.
2. A IA interpreta; números vêm do extrator.
3. O gerador cria tudo do zero; nada do jogo original entra no Genome nem na saída.
4. O validador mede o mapa gerado e compara com o Genome. Ele prova que o gerador cumpre as métricas,
   **não** que a experiência é parecida (isso exige playtest).
5. Exportadores são substituíveis (Roblox hoje; Unity/Godot depois).

Plano original completo (limpo): `plano-v2.1.txt`.

## Legal
Mecânicas e ritmo não são protegidos por direito autoral; mapas, sprites e sons são. Não distribua ROMs
(o `.gitignore` bloqueia extensões comuns). Consulte um jurídico antes de publicar. O Roblox modera IP de terceiros.
