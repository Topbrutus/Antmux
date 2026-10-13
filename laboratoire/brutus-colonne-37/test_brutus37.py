from brutus37 import BRUTUS_CONSTANT_TEXT, Brutus37Engine, Spine33


def test_architecture_37():
    engine = Brutus37Engine()
    status = engine.status()
    assert status["posts"] == 37
    assert status["vertebrae"] == 33
    assert len(status["organs"]) == 4
    assert len(Spine33.NAMES) == 33


def test_brutus_constant_exact_text():
    assert BRUTUS_CONSTANT_TEXT == "5.58545864083284007"


def test_37_family_is_detected_without_mutating_value():
    engine = Brutus37Engine()
    out = engine.process(111, path="seed/111")
    measurements = {row["instrument"]: row["measurement"] for row in out["vertebrae"]}
    assert out["value"] == 111
    assert measurements["DIVISIBLE_37"] is True
    assert measurements["QUOTIENT_37"] == 3
    assert out["constant_applied"] is False

    out999 = engine.process(999, path="seed/999")
    m999 = {row["instrument"]: row["measurement"] for row in out999["vertebrae"]}
    assert m999["DIVISIBLE_37"] is True
    assert m999["QUOTIENT_37"] == 27


def test_fast_library_collapses_dust():
    engine = Brutus37Engine()
    first = engine.process(777, path="route/A")
    evals = engine.vertebra_evaluations
    for i in range(1, 1001):
        engine.process(777, path=f"route/{i % 5}")
    rec = engine.library.get(777, "SEED")
    assert rec is not None
    assert rec.count == 1001
    assert rec.independent_paths == 6  # route/A plus route/0..4
    assert engine.library.unique_crystals == 1
    assert engine.library.dust_collapsed == 1000
    assert engine.vertebra_evaluations == evals
    assert first["cache_hit"] is False


def test_rarity_hierarchy():
    engine = Brutus37Engine()
    expected = {1: 8, 2: 8, 3: 6, 4: 6, 5: 4, 8: 4, 9: 2, 16: 2, 17: 1, 32: 1}
    for count in range(1, 33):
        engine.process(4242, path=f"p/{count}")
        rec = engine.library.get(4242, "SEED")
        if count in expected:
            assert rec.replay_budget == expected[count]


def test_245k_dust_becomes_one_canonical_record():
    engine = Brutus37Engine()
    total = 245_000
    for i in range(total):
        engine.process(1234567, formula_id="DUST", path=f"ant/{i % 37}")
    rec = engine.library.get(1234567, "DUST")
    assert rec is not None
    assert rec.count == total
    assert rec.independent_paths == 37
    assert engine.library.unique_crystals == 1
    assert engine.library.dust_collapsed == total - 1
    assert engine.vertebra_evaluations == 33


def test_37_lanes_are_bounded():
    engine = Brutus37Engine()
    for n in range(1, 1000):
        out = engine.process(n, path=f"n/{n}")
        assert 0 <= out["record"]["bucket37"] < 37
        assert 0 <= out["route"]["lane37"] < 37
        assert 0 <= out["route"]["route144"] < 144
