"""Tests for the system dynamics engine."""

import pytest

from policy_dynamics_sim.engine import (
    Auxiliary,
    Flow,
    ModelConfig,
    SDEngine,
    Stock,
)


def test_simple_stock_growth() -> None:
    """A single stock with constant inflow should grow linearly."""
    config = ModelConfig(
        name="simple_growth",
        description="",
        stocks=[Stock(name="inventory", initial_value=10.0)],
        flows=[Flow(name="inflow", target_stock="inventory", formula="5.0")],
        auxiliaries=[],
        time_step=1.0,
        total_time=10.0,
    )
    engine = SDEngine(config)
    history = engine.run()

    assert history["time"][0] == 0.0
    assert history["time"][-1] == 10.0
    assert history["inventory"][0] == 10.0
    assert history["inventory"][-1] == pytest.approx(60.0)


def test_stock_with_bounds() -> None:
    """Stock should respect min and max bounds."""
    config = ModelConfig(
        name="bounded",
        description="",
        stocks=[Stock(name="tank", initial_value=5.0, min_value=0.0, max_value=8.0)],
        flows=[Flow(name="fill", target_stock="tank", formula="10.0")],
        auxiliaries=[],
        time_step=1.0,
        total_time=10.0,
    )
    engine = SDEngine(config)
    history = engine.run()
    assert max(history["tank"]) <= 8.0


def test_auxiliary_resolution() -> None:
    """Auxiliaries should be computed and used in flows."""
    config = ModelConfig(
        name="aux_test",
        description="",
        stocks=[Stock(name="pop", initial_value=100.0)],
        flows=[Flow(name="births", target_stock="pop", formula="growth_rate * pop")],
        auxiliaries=[
            Auxiliary(name="growth_rate", formula="0.05"),
        ],
        time_step=1.0,
        total_time=10.0,
    )
    engine = SDEngine(config)
    history = engine.run()
    assert history["pop"][-1] > 100.0


def test_feedback_loop() -> None:
    """A negative feedback loop should stabilize the system."""
    config = ModelConfig(
        name="feedback",
        description="",
        stocks=[Stock(name="temp", initial_value=100.0)],
        flows=[
            Flow(
                name="cooling",
                source_stock="temp",
                target_stock="",
                formula="0.1 * temp",
            )
        ],
        auxiliaries=[],
        time_step=0.1,
        total_time=50.0,
    )
    engine = SDEngine(config)
    history = engine.run()
    final = history["temp"][-1]
    assert final < 100.0
    assert final >= 0.0


def test_time_vars_available() -> None:
    """The time variable should be accessible in formulas."""
    config = ModelConfig(
        name="time_var",
        description="",
        stocks=[Stock(name="x", initial_value=0.0)],
        flows=[Flow(name="f", target_stock="x", formula="time")],
        auxiliaries=[],
        time_step=1.0,
        total_time=5.0,
    )
    engine = SDEngine(config)
    history = engine.run()
    assert history["x"][1] == pytest.approx(0.0)
    assert history["x"][2] == pytest.approx(1.0)


def test_math_functions() -> None:
    """Math functions like sin, clamp should work."""
    config = ModelConfig(
        name="math_test",
        description="",
        stocks=[Stock(name="x", initial_value=0.0)],
        flows=[Flow(name="f", target_stock="x", formula="math.sin(time)")],
        auxiliaries=[],
        time_step=0.5,
        total_time=2.0,
    )
    engine = SDEngine(config)
    history = engine.run()
    assert len(history["x"]) > 0
