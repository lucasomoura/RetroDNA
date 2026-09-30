import argparse
import json
from pathlib import Path

from apps.analyzer import report as analyze
from apps.exporter import roblox
from apps.generator import generate, validate
from apps.observer import auto, sample
from packages.events import telemetry
from packages.metrics import aggregate, build_genome, extract
from packages.schema import genome


def _gen_args(p):
    p.add_argument("--theme", default="humor", choices=list(generate.THEMES))
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--minutes", type=float, default=8)
    p.add_argument("--seconds-per-room", type=float, default=None)
    p.add_argument("--out", default="out")


def _build(a, out, gn):
    m = generate.generate(gn, a.theme, a.seed, a.minutes, a.seconds_per_room)
    roblox.export(m, out / "roblox")
    v = validate.validate_map(m, gn)
    (out / "validation.json").write_text(
        json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out / "validation.md").write_text(validate.to_markdown(v), encoding="utf-8")
    print("mapa:", m["stats"])
    print(
        f"validação: {'APROVADO' if v['passed'] else 'REPROVADO'} ({v['errors']} erros, {v['warnings']} avisos)"
    )
    return v


def _genome_from(paths, game, out):
    ms = []
    for t in paths:
        frames, meta = telemetry.load_with_meta(t)
        if meta.get("source") == "oam":
            print(
                f"  {Path(t).name}: {len(frames)} amostras; confiança do jogador {meta['player_confidence']}; câmera {'ok' if meta['camera'] else 'NÃO detectada'}"
            )
            if meta["player_confidence"] < 0.15:
                print(
                    "  aviso: jogador identificado com baixa confiança (poucos movimentos ligados ao input)."
                )
        ms.append(extract(frames, meta=meta))
    m = aggregate(ms)
    (out / "metrics.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
    gn = genome.validate(build_genome(m, game))
    genome.save(gn, out / "genome.json")
    (out / "report.md").write_text(analyze.report(gn), encoding="utf-8")
    (out / "llm_prompt.md").write_text(analyze.llm_prompt(gn), encoding="utf-8")
    print(f"genome + relatório em {out} ({len(ms)} sessão(ões))")
    return gn


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="retrodna", description="Engenharia reversa de game design"
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample", help="gera telemetria sintética")
    s.add_argument("out")
    s.add_argument("--seed", type=int, default=7)
    e = sub.add_parser("extract")
    e.add_argument("telemetry", nargs="+")
    e.add_argument("--game", default="unknown")
    e.add_argument("--out", default="out")
    pl = sub.add_parser(
        "pipeline", help="sessões .jsonl -> genome -> mapa -> validação"
    )
    pl.add_argument(
        "telemetry", nargs="+", help="sessões .jsonl (telemetria direta ou trace OAM)"
    )
    pl.add_argument("--game", default="unknown")
    _gen_args(pl)
    au = sub.add_parser(
        "auto",
        help="AUTOMÁTICO: ROM -> Mesen (sem interface) -> genome -> mapa -> validação",
    )
    au.add_argument("rom")
    au.add_argument(
        "--mesen", default=None, help="caminho do executável do Mesen/MesenCE"
    )
    au.add_argument("--sessions", type=int, default=3)
    au.add_argument("--seconds", type=int, default=300)
    au.add_argument("--game", default=None)
    au.add_argument("--no-skip-title", action="store_true")
    _gen_args(au)
    pr = sub.add_parser(
        "prepare", help="gera o observador configurado para você jogar (modo manual)"
    )
    pr.add_argument(
        "--file", default="sessao1.jsonl", help="arquivo de saída da captura"
    )
    pr.add_argument("--lua", default="observer.lua")
    pr.add_argument("--mode", default="human", choices=["human", "bot"])
    pr.add_argument("--seconds", type=int, default=0)
    g = sub.add_parser("generate", help="genome.json -> mapa + validação")
    g.add_argument("genome")
    _gen_args(g)
    v = sub.add_parser("validate", help="valida map.json contra genome.json")
    v.add_argument("map")
    v.add_argument("genome")
    a = p.parse_args(argv)

    if a.cmd == "sample":
        sample.make(a.out, seed=a.seed)
        print("telemetria gerada:", a.out)
        return 0
    if a.cmd == "prepare":
        auto.prepare(
            a.lua, a.file, mode=a.mode, seconds=a.seconds, seed=1, skip_title=False
        )
        print(
            f"gerado {a.lua}. Abra o jogo no Mesen, carregue este script no Script Window (habilite I/O), jogue e depois:\n  retrodna pipeline {a.file} --game NOME"
        )
        return 0
    if a.cmd == "validate":
        map_data = json.loads(Path(a.map).read_text(encoding="utf-8"))
        res = validate.validate_map(map_data, genome.load(a.genome))
        print(validate.to_markdown(res))
        return 0 if res["passed"] else 1
    out = Path(getattr(a, "out", "out"))
    out.mkdir(parents=True, exist_ok=True)
    if a.cmd == "auto":
        mesen = auto.find_mesen(a.mesen)
        paths = []
        for i in range(1, a.sessions + 1):
            print(f"sessão {i}/{a.sessions} ({a.seconds}s de jogo, bot)...")
            paths.append(
                auto.run_session(
                    mesen,
                    a.rom,
                    out / "sessions" / f"sessao{i}.oam.jsonl",
                    a.seconds,
                    seed=i,
                    mode="bot",
                    skip_title=not a.no_skip_title,
                )
            )
        gn = _genome_from(paths, a.game or Path(a.rom).stem, out)
    elif a.cmd in ("extract", "pipeline"):
        gn = _genome_from(a.telemetry, a.game, out)
    else:
        gn = genome.load(a.genome)
    if a.cmd in ("auto", "pipeline", "generate"):
        return 0 if _build(a, out, gn)["passed"] else 1
    return 0
