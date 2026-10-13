from __future__ import annotations

import os
from types import SimpleNamespace

from brotoculateur.c3_library import C3Library37
from brotoculateur.c4_novelty import C4Novelty
from brotoculateur.c5_rarity import C5StructuralRarity
from brotoculateur.c6_provenance import C6Provenance
from brotoculateur.c7_router import C7ShadowRouter
from brotoculateur.dashboard import build_default_registry
from brotoculateur.engine import TracePacket
from brotoculateur.orchestrator import ExperimentRunner, ExperimentSpec
from brotoculateur.t1_family import T1FamilyClassifier


def test_taxonomy() -> None:
    c = T1FamilyClassifier()
    cases = [
        ((), 'ROOT', False),
        (('PLUS1',), 'ARITHMETIC_EXPANSION', False),
        (('DIGIT_SUM',), 'REDUCTION', False),
        (('PELL_Q',), 'PELL', False),
        (('FACTOR_GAP_LOW_666',), 'FACTOR_GAP', False),
        (('CRYSTAL_REINJECT:X',), 'CRYSTAL_REINJECTION', False),
        (('CRYSTAL_REINJECT:X','DIGIT_SUM','PELL_Q'), 'PELL', True),
        (('MYSTERY',), 'OTHER', False),
    ]
    for chain, family, mixed in cases:
        info = c.classify(SimpleNamespace(formula_chain=chain))
        assert info['family'] == family, (chain, info)
        assert bool(info['mixed_lineage']) is mixed, (chain, info)
    print('T1_TAXONOMY=PASS')


def build_shared():
    return (
        C3Library37(),
        C4Novelty(),
        C5StructuralRarity(),
        C6Provenance(),
        C7ShadowRouter(),
        T1FamilyClassifier(),
    )


def new_runner(shared):
    c3,c4,c5,c6,c7,t1=shared
    spec=ExperimentSpec(duration_seconds=3600,checkpoint_seconds=300,max_depth=4,max_active_branches=128,max_packets=20000)
    return ExperimentRunner(
        build_default_registry(), spec,
        c3_library=c3,c4_novelty=c4,c5_rarity=c5,c6_provenance=c6,c7_router=c7,t1_family=t1,
    )


def test_chain_and_rollover() -> None:
    os.environ['BROTO_ZSTAMP_ENABLED']='1'
    os.environ['BROTO_ZSTAMP_PERCENT']='100'
    for name in ('BROTO_C2_ENABLED','BROTO_C3_ENABLED','BROTO_C4_ENABLED','BROTO_C5_ENABLED','BROTO_C6_ENABLED','BROTO_C7_ENABLED','BROTO_T1_ENABLED'):
        os.environ[name]='1'
    shared=build_shared()
    r1=new_runner(shared)
    r1.seed([TracePacket(343),TracePacket(73),TracePacket(47)])
    for _ in range(24):
        if not r1.step(): break
    n=int(r1.c2_status()['fingerprints'])
    assert n>3, n
    assert n==int(r1.c3_status()['observations'])==int(r1.c4_status()['observations'])==int(r1.c5_status()['observations'])==int(r1.c6_status()['observations'])==int(r1.c7_status()['observations'])==int(r1.t1_status()['observations'])
    s=r1.t1_status()
    assert sum(int(v) for v in s['family_counts'].values())==n
    assert s['authority']=='SHADOW_ONLY'
    assert s['scientific_taxonomy_claim'] is False
    assert s['controls_routing'] is False
    assert s['actual_routes_applied']==0
    assert s['compute_skips']==0
    assert s['value_mutated'] is False
    assert s['proof_promotion'] is False
    before=n
    r2=new_runner(shared)
    r2.seed([TracePacket(343)])
    after=int(r2.t1_status()['observations'])
    assert after==before+1,(before,after)
    print('T1_CHAIN=PASS', n, s['family_counts'])
    print('T1_ROLLOVER=PASS', before, after)


def test_route_cross_table() -> None:
    t=T1FamilyClassifier()
    p=SimpleNamespace(formula_chain=('PELL_Q',),z_id='Z-demo')
    t.observe(p,'C2-'+'a'*64,c7_route='NOVELTY_REVIEW')
    st=t.status()
    assert st['route_family_counts']['NOVELTY_REVIEW']['PELL']==1
    print('T1_ROUTE_CROSS_TABLE=PASS')


if __name__=='__main__':
    test_taxonomy()
    test_route_cross_table()
    test_chain_and_rollover()
    print('T1_FAMILY=PASS')
