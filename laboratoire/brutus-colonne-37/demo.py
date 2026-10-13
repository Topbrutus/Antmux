from __future__ import annotations

import json
from brutus37 import Brutus37Engine

# Deliberately only uses values explicitly established in the current design discussion.
# The complete 45-number plaque should be loaded from its authoritative list, not guessed.
SEEDS = [111, 222, 333, 444, 555, 666, 777, 888, 999, 11611]


def main() -> None:
    engine = Brutus37Engine()
    rows = []
    for seed in SEEDS:
        out = engine.process(seed, path=f"seed/{seed}")
        rows.append({
            "seed": seed,
            "divisible_37": seed % 37 == 0,
            "quotient_37": seed // 37,
            "mod_37": seed % 37,
            "z_id": out["z_stamp"]["z_id"],
            "z_route37": out["z_stamp"]["route37"],
            "bucket37": out["record"]["bucket37"],
            "papillon144": out["route"]["route144"],
            "sequence": out["sequence"],
        })

    # Simulate a large repeated dust pile while retaining one canonical Z identity.
    for i in range(245_000):
        engine.process(777, formula_id="DUST_DEMO", path=f"ant/{i % 37}")

    dust = engine.library.get(777, "DUST_DEMO")
    report = {
        "seed_probe": rows,
        "dust_demo": {
            "observations": dust.count if dust else 0,
            "canonical_records": 1 if dust else 0,
            "z_id": dust.z_id if dust else None,
            "independent_paths": dust.independent_paths if dust else 0,
            "provenance_count": len(dust.provenance_digests) if dust else 0,
            "replay_budget": dust.replay_budget if dust else 0,
        },
        "engine": engine.status(),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
