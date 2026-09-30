from packages.schema.genome import Gameplay, Genome


def test_gameplay_ratio():
    genome = Genome(
        gameplay=Gameplay(
            exploration=0.72,
            combat=0.28,
        )
    )

    assert 0 <= genome.gameplay.exploration <= 1
    assert 0 <= genome.gameplay.combat <= 1