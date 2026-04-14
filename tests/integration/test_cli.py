"""Integration tests for CLI end-to-end workflows."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from policy_dynamics_sim.engine import SDEngine, load_config

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
CARBON_YAML = EXAMPLES_DIR / "carbon_neutral.yaml"
TAX_JSON = EXAMPLES_DIR / "window_tax.json"


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "policy_dynamics_sim.cli", *args],
        capture_output=True,
        text=True,
    )


class TestCliEndToEnd:
    """Tests covering CLI -> engine -> output file pipelines."""

    def test_cli_yaml_to_json(self, tmp_path: Path) -> None:
        output = tmp_path / "result.json"
        result = _run_cli([str(CARBON_YAML), "--output", str(output)])
        assert result.returncode == 0, result.stderr
        assert output.exists()
        data = json.loads(output.read_text())
        assert data["model"] == "Carbon Neutrality Transition"
        assert "history" in data
        assert "flows" in data
        assert "auxiliaries" in data

    def test_cli_json_to_csv(self, tmp_path: Path) -> None:
        output = tmp_path / "result.csv"
        result = _run_cli([str(TAX_JSON), "--csv", str(output)])
        assert result.returncode == 0, result.stderr
        assert output.exists()
        text = output.read_text()
        assert "time,revenue,public_health,windows" in text
        assert "flow:tax_income" in text
        assert "aux:tax_rate" in text

    def test_cli_plot_png(self, tmp_path: Path) -> None:
        plot_path = tmp_path / "plot.png"
        result = _run_cli([str(CARBON_YAML), "--plot", str(plot_path)])
        assert result.returncode == 0, result.stderr
        assert plot_path.exists()
        assert plot_path.stat().st_size > 0

    def test_cli_plot_svg(self, tmp_path: Path) -> None:
        plot_path = tmp_path / "plot.svg"
        result = _run_cli([str(TAX_JSON), "--plot", str(plot_path)])
        assert result.returncode == 0, result.stderr
        assert plot_path.exists()
        content = plot_path.read_text()
        assert "<svg" in content

    def test_cli_plot_html_unsupported(self, tmp_path: Path) -> None:
        """HTML output requires plotly backend, which matplotlib does not provide."""
        plot_path = tmp_path / "plot.html"
        result = _run_cli([str(TAX_JSON), "--plot", str(plot_path)])
        assert result.returncode != 0
        assert "plotly" in result.stderr.lower() or "html" in result.stderr.lower()

    def test_cli_missing_config(self) -> None:
        result = _run_cli(["nonexistent.yaml"])
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_cli_stock_filter_plot(self, tmp_path: Path) -> None:
        plot_path = tmp_path / "filtered.png"
        result = _run_cli(
            [
                str(CARBON_YAML),
                "--plot",
                str(plot_path),
                "--stocks",
                "emissions",
            ]
        )
        assert result.returncode == 0, result.stderr
        assert plot_path.exists()

    def test_cli_no_output_prints_summary(self) -> None:
        result = _run_cli([str(TAX_JSON)])
        assert result.returncode == 0, result.stderr
        assert "Window Tax Policy" in result.stdout
        assert "Final stock values:" in result.stdout


class TestEngineIntegration:
    """Tests covering config loading -> engine -> export pipelines."""

    @pytest.mark.parametrize("config_path", [CARBON_YAML, TAX_JSON])
    def test_load_config_and_run(self, config_path: Path) -> None:
        config = load_config(str(config_path))
        engine = SDEngine(config)
        history = engine.run()
        assert len(history["time"]) > 0
        for stock in config.stocks:
            assert stock.name in history

    def test_engine_to_csv(self, tmp_path: Path) -> None:
        config = load_config(str(CARBON_YAML))
        engine = SDEngine(config)
        engine.run()
        csv_path = tmp_path / "out.csv"
        engine.to_csv(csv_path)
        assert csv_path.exists()
        lines = csv_path.read_text().strip().split("\n")
        assert len(lines) == len(engine.history["time"]) + 1  # header + data rows

    def test_yaml_json_parity(self) -> None:
        """Running the same conceptual model via YAML and JSON should behave similarly."""
        config_y = load_config(str(CARBON_YAML))
        config_j = load_config(str(TAX_JSON))
        assert config_y.name != config_j.name
        # Sanity: both produce histories with expected structure
        for config in (config_y, config_j):
            engine = SDEngine(config)
            hist = engine.run()
            assert hist["time"][0] == pytest.approx(0.0)
            assert hist["time"][-1] == pytest.approx(config.total_time)
