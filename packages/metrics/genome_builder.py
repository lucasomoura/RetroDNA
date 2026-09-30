"""Métricas medidas -> Design Genome v0.2 (RFC 0001)."""

from packages.schema.genome import NORMALIZATION, PROVENANCE_KEYS, VERSION


def _n(value: float | None, ref: float) -> float | None:
    return None if value is None else round(min(1.0, value / ref), 3)


def build_genome(m: dict, game: str = "unknown") -> dict:
    n = NORMALIZATION
    g = {
        "genome_version": VERSION,
        "source": {
            "game": game,
            "sessions": m.get("sessions", 1),
            "duration_s": m["duration_s"],
        },
        "movement": {"player_speed_px_s": m["player_speed"]},
        "gameplay": {
            "exploration": round(1 - m["combat_ratio"], 3),
            "combat": m["combat_ratio"],
            "objective_density": _n(m["objectives_per_min"], n["objectives_per_min"]),
            "enemy_density": _n(m["enemies_active_mean"], n["enemies_active_max"]),
            "reward_frequency": _n(m["rewards_per_min"], n["rewards_per_min"]),
        },
        "level_design": {
            "average_area_size": m["average_area_size"],
            "alternate_routes": m["alternate_routes"],
            "chokepoints": m["chokepoints"],
            "open_area_frequency": None,
        },
        "pacing": {
            "average_exploration_time_s": m["exploration_time_s"],
            "average_combat_duration_s": m["combat_duration_s"],
            "average_time_between_encounters_s": m["encounter_interval_s"],
        },
        "tension": {"curve": m["tension_curve"]},
        "enemies": {"archetypes": m["enemy_archetypes"]},
        "raw": {
            "enemies_active_mean": m["enemies_active_mean"],
            "objectives_per_min": m["objectives_per_min"],
            "rewards_per_min": m["rewards_per_min"],
            "encounters": m["encounters"],
        },
        "normalization": n,
    }
    prov = dict(PROVENANCE_KEYS)
    for key in prov:
        section, name = key.split(".")
        if name not in ("curve", "archetypes") and g[section].get(name) is None:
            prov[key] = "unavailable"
    g["provenance"] = prov
    return g
