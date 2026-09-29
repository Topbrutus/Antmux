from __future__ import annotations

import copy

from app.noyau_runtime import NoyauEngine, NoyauServerAdapter


def run() -> None:
    engine = NoyauEngine()

    closed = engine.step()
    assert engine.held_input == 0.0
    assert closed.basin1.inflow == 0.0
    assert closed.basin1.outflow == 0.0
    assert all(value == 0.0 for value in closed.node_signals.values())

    engine.set_held_input(0.10)
    opened = engine.step()
    assert engine.held_input == 0.10
    assert opened.basin1.inflow > 0.0
    assert max(opened.node_signals.values()) > 0.0

    checkpoint = engine.to_checkpoint()
    restored = NoyauEngine.from_checkpoint(copy.deepcopy(checkpoint))
    assert restored.held_input == 0.10

    adapter = NoyauServerAdapter(engine=restored)
    payload = adapter.visual_payload()
    assert payload["control"]["mode"] == "HELD"
    assert payload["control"]["held_input"] == 0.10
    assert payload["control"]["held_percent"] == 10.0

    adapter.set_held_input(0.05)
    assert restored.held_input == 0.05

    for invalid in (-0.01, 1.01, float("inf")):
        try:
            restored.set_held_input(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid held input accepted: {invalid!r}")

    print("PASS noyau held input 0% -> 10% -> checkpoint -> 5%")


if __name__ == "__main__":
    run()
