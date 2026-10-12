from __future__ import annotations
import json, os, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path('/var/www/antmux.com/public_html/brutus/public-state.json')

def get(url):
    req = Request(url, headers={'User-Agent':'BrutusPublicExporter/0.1','Cache-Control':'no-cache'})
    with urlopen(req, timeout=3) as r:
        return json.load(r)

def module_states(value):
    out = {}
    if isinstance(value, dict):
        for k,v in value.items():
            if isinstance(v, dict):
                out[k] = v.get('state') or v.get('status') or v.get('mode') or 'AVAILABLE'
            else:
                out[k] = str(v)
    return out

def snapshot():
    state = get('http://127.0.0.1:8811/api/state')
    queen = get('http://127.0.0.1:8811/api/queen').get('queen', {})
    bro = get('http://127.0.0.1:8781/api/status')
    bm = bro.get('brutomagique', {})
    pap = bro.get('papillon', {})
    sent = bro.get('sentinels', {})
    targets = sent.get('targets', []) if isinstance(sent, dict) else []
    evals = (state.get('evaluation') or {}).get('candidates') or {}
    colony = state.get('colony') or queen.get('counts') or {}
    candidates = []
    for c in queen.get('candidates', [])[-12:]:
        candidates.append({
            'candidate_id': c.get('candidate_id'),
            'title': c.get('title'),
            'classification': c.get('classification'),
            'ready_for_astra': bool(c.get('ready_for_astra')),
        })
    return {
        'schema': 'BRUTUS-PUBLIC-VITRINE-v0.1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'public_scope': 'READ_ONLY_SANITIZED',
        'brutus': {
            'schema': state.get('schema'),
            'queen_mode': state.get('queen_mode'),
            'mode': state.get('mode'),
            'live_routing': state.get('live_routing'),
            'auto_proof_promotion': state.get('auto_proof_promotion'),
            'evaluation_mode': state.get('evaluation_mode'),
            'discovery_mode': state.get('discovery_mode'),
        },
        'brotoculateur': {
            'state': bro.get('state'),
            'run_id': bro.get('run_id'),
            'processed_packets': bro.get('processed_packets'),
            'crystals': bm.get('total_crystals'),
            'levels': bm.get('emitted_by_level') or {},
            'formula_ids': bro.get('formula_ids') or [],
            'crystal_ranking': [
                {'formula_id': str(r.get('formula_id') or ''), 'level': str(r.get('level') or ''), 'count': int(r.get('count') or 0)}
                for r in (bm.get('crystal_ranking') or []) if isinstance(r, dict) and r.get('formula_id') and r.get('level')
            ],
            'worker_error': bro.get('worker_error'),
            'storage': (bm.get('storage') or {}).get('active_write_mode'),
            'papillon_enabled': bool(pap.get('enabled')),
            'papillon_hit_rate': pap.get('cache_hit_rate'),
            'papillon_ratio': pap.get('overall_logical_to_physical_ratio'),
            'papillon_mass': (bro.get('papillon_mass') or {}).get('state'),
            'sentinels_total': len(targets),
            'sentinels_survived': sum(1 for t in targets if t.get('survived')),
            'sentinel_hits': sum(int(t.get('hits') or 0) for t in targets),
        },
        'colony': {
            'observations': colony.get('observations', len(queen.get('observations', []))),
            'tasks': colony.get('tasks', len(queen.get('tasks', []))),
            'candidates': colony.get('candidates', len(queen.get('candidates', []))),
            'mailbox': colony.get('mailbox', len(queen.get('mailbox', []))),
        },
        'evaluation': {
            'total': evals.get('total', 0),
            'ready_for_astra': evals.get('ready_for_astra', 0),
            'blocked': evals.get('blocked', 0),
            'needing_prior_art': evals.get('needing_prior_art', 0),
            'needing_novelty_review': evals.get('needing_novelty_review', 0),
        },
        'candidates': candidates,
        'modules': module_states(state.get('modules')),
        'pell': state.get('pell'),
        'zel': state.get('zel'),
    }

def write(data):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',',':')), encoding='utf-8')
    os.replace(tmp, OUT)

while True:
    try:
        write(snapshot())
    except Exception as exc:
        write({'schema':'BRUTUS-PUBLIC-VITRINE-v0.1','generated_at':datetime.now(timezone.utc).isoformat(),'public_scope':'READ_ONLY_SANITIZED','error':f'{type(exc).__name__}: {exc}'})
    time.sleep(2)
