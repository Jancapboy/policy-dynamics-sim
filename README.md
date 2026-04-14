# Policy Dynamics Simulator

[![CI](https://github.com/Jancapboy/policy-dynamics-sim/actions/workflows/ci.yml/badge.svg)](https://github.com/Jancapboy/policy-dynamics-sim/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Simulate the long-tail effects and unintended consequences of policies using System Dynamics.

This project helps analysts, consultants, and policymakers model second-order effects before making decisions. Define stocks, flows, and feedback loops in YAML or JSON, run simulations, and visualize outcomes.

## 🚀 Features

- **System Dynamics Engine**: Euler integration with stocks, flows, and auxiliary variables
- **Feedback Loop Support**: Model reinforcing and balancing feedback loops
- **Policy Previsualization**: Run "what-if" scenarios before real-world rollout
- **YAML/JSON Configs**: Human-readable model definitions
- **CLI Tool**: Run simulations from the command line
- **Matplotlib Visualizations**: Export charts as PNG, SVG, or HTML

## 📦 Installation

```bash
git clone https://github.com/Jancapboy/policy-dynamics-sim.git
cd policy-dynamics-sim
pip install -e ".[dev]"
```

## 🔧 Usage

### CLI

```bash
# Run a simulation
sd-sim examples/window_tax.json

# Run and save results
sd-sim examples/carbon_neutral.yaml --output results.json --csv results.csv

# Run and generate a plot
sd-sim examples/window_tax.json --plot window_tax.png --title "Window Tax Impact"
```

### Python API

```python
from policy_dynamics_sim import load_config, SDEngine, plot_simulation, save_plot

config = load_config("examples/carbon_neutral.yaml")
engine = SDEngine(config)
history = engine.run()

fig = plot_simulation(engine)
save_plot(fig, "carbon_neutral.png")
```

## 🧪 Testing

```bash
pytest
```

## 📁 Project Structure

```
policy-dynamics-sim/
├── src/policy_dynamics_sim/   # Core engine + CLI + viz
├── tests/                     # Pytest suite
├── examples/                  # Sample models
│   ├── window_tax.json        # The classic policy fable
│   └── carbon_neutral.yaml    # Climate transition model
└── docs/                      # Documentation
```

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   YAML/JSON │ ──▶ │  SDEngine    │ ──▶ │  Matplotlib     │
│   Config    │     │  (Euler)     │     │  Visualization  │
└─────────────┘     └──────────────┘     └─────────────────┘
```

## 📝 Example: Window Tax

A classic policy fable:

1. Government taxes windows
2. Citizens brick up windows to avoid tax
3. Revenue falls, public health deteriorates

See [`examples/window_tax.json`](examples/window_tax.json).

## 🗺️ Roadmap

- [ ] Interactive web UI for model editing
- [ ] Sensitivity analysis tools
- [ ] Monte Carlo parameter exploration
- [ ] Export to Vensim / Stella formats
- [ ] Documentation site

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

Built as part of a system dynamics and policy analysis learning journey.
