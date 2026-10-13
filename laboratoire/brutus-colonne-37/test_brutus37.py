from brutus37 import (
    BRUTUS_CONSTANT_TEXT,
    Z_STAMP_SCHEMA,
    Brutus37Engine,
    BrutusCortex,
    Spine33,
)


def test_architecture_37():
    engine = Brutus37Engine()
    status = engine.status()
    assert status["posts"] == 37
    assert status["vertebrae"] == 33
    assert len(status["organs"]) == 4
    assert len(Spine33.NAMES) == 33
    assert status["organs"][0] == "BRUTUS_CORTEX_PINEALE"


def test_brutus_constant_exact_text():
    assert BRUTUS_CONSTANT_TEXT == "5.58545864083284007"


def test_cortex_is_between_c1_and_c2():
    engine = Brutus37Engine()
    out = engine.process(111, path="seed/111")
    assert out["sequence"] == [
        "C1_ENTREE",
        "BRUTUS_CORTEX_PINEALE",
        "Z_STAMP",
        "C2_EMPREINTE",
    ]
    assert out["z_stamp"]["schema"] == Z_STAMP_SCHEMA
    assert out["z_stamp"]["z_id"].startswith("Z-")
    assert len(out["c2_fingerprint"]) == 64
    assert out["constant_applied"] is False


def test_same_matter_same_z_different_provenance():
    engine = Brutus37Engine()
    a = engine.process(777, path="ant/A")
    b = engine.process(777, path="ant/B")
    assert a["z_stamp"]["z_id"] == b["z_stamp"]["z_id"]
    assert a["z_stamp"]["provenance_digest"] != b["z_stamp"]["provenance_digest"]
    assert b["cache_hit"] is True
    rec = engine.library.get(777, "SEED")
    assert rec is not None
    assert rec.count == 2
    assert rec.independent_paths == 2
    assert len(rec.provenance_digests) == 2


def test_different_matter_gets_different_z():
    cortex = BrutusCortex()
    a = cortex.stamp(111, formula_id="SEED", level="L1", path="a")
    b = cortex.stamp(222, formula_id="SEED", level="L1", path="a")
    c = cortex.stamp(111, formula_id="OTHER", level="L1", path="a")
    assert a.z_id != b.z_id
    assert a.z_id != c.z_id


def test_parent_lineage_is_preserved_without_changing_canonical_z():
    cortex = BrutusCortex()
    a = cortex.stamp(333, formula_id="SEED", level="L1", path="a", parent_z="Z-PARENT-A")
    b = cortex.stamp(333, formula_id="SEED", level="L1", path="b", parent_z="Z-PARENT-B")
    assert a.z_id == b.z_id
    assert a.parent_z != b.parent_z
    assert a.provenance_digest != b.provenance_digest


def test_37_family_is_detected_without_mutating_value():
    engine = Brutus37Engine()
    out = engine.process(111, path="seed/111")
    assert out["value"] == 111
    # The Z seal happens before the rest of the 33-instrument evaluation.
    assert out["z_stamp"]["normalized_value"] == 111
    assert out["constant_applied"] is False

    out999 = engine.process(999, path="seed/999")
    assert out999["value"] == 999
    assert 999 % 37 == 0
    assert 999 // 37 == 27


def test_fast_library_collapses_dust():
    engine = Brutus37Engine()
    first = engine.process(777, path="route/A")
    evals = engine.vertebra_evaluations
    for i in range(1, 1001):
        engine.process(777, path=f"route/{i % 5}")
    rec = engine.library.get(777, "SEED")
    assert rec is not None
    assert rec.count == 1001
    assert rec.independent_paths == 6
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


def test_245k_dust_becomes_one_canonical_record_with_37_provenances():
    engine = Brutus37Engine()
    total = 245_000
    first_z = None
    for i in range(total):
        out = engine.process(1234567, formula_id="DUST", path=f"ant/{i % 37}")
        first_z = first_z or out["z_stamp"]["z_id"]
        assert out["z_stamp"]["z_id"] == first_z
    rec = engine.library.get(1234567, "DUST")
    assert rec is not None
    assert rec.count == total
    assert rec.independent_paths == 37
    assert len(rec.provenance_digests) == 37
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
        assert 0 <= out["z_stamp"]["route37"] < 37
