"""Visualization utilities for simulation results."""

from __future__ import annotations

from typing import Any, List, Optional

from policy_dynamics_sim.engine import SDEngine


def _get_plt():
    """Import matplotlib with a helpful error message."""
    try:
        import matplotlib.pyplot as plt

        return plt
    except ImportError as exc:
        raise ImportError(
            "Matplotlib is required for plotting. "
            "Install with: pip install 'policy-dynamics-sim[plot]' or "
            f"ensure your system supports matplotlib. Original error: {exc}"
        ) from exc


def plot_simulation(
    engine: SDEngine,
    title: str = "Simulation Results",
    stocks: Optional[List[str]] = None,
) -> Any:
    """Create a plot of simulation results.

    Returns a matplotlib Figure or plotly Figure depending on backend.
    """
    stock_names = stocks or [s.name for s in engine.config.stocks]
    time_data = engine.history["time"]

    if len(time_data) == 0:
        raise ValueError("No simulation data to plot")

    # Default to matplotlib for static images
    plt = _get_plt()

    fig, ax = plt.subplots(figsize=(10, 6))
    for name in stock_names:
        if name not in engine.history:
            raise ValueError(f"Stock '{name}' not found in simulation history")
        ax.plot(time_data, engine.history[name], label=name, linewidth=2)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("Value", fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_with_flows(engine: SDEngine, title: str = "Simulation Results") -> Any:
    """Create a multi-panel plot showing stocks, flows, and auxiliaries."""
    plt = _get_plt()

    time_data = engine.history["time"]
    n_panels = 0
    has_stocks = len(engine.config.stocks) > 0
    has_flows = len(engine.config.flows) > 0
    has_aux = len(engine.config.auxiliaries) > 0
    n_panels = sum([has_stocks, has_flows, has_aux])

    if n_panels == 0:
        raise ValueError("No data to plot")

    fig, axes = plt.subplots(n_panels, 1, figsize=(10, 4 * n_panels), sharex=True)
    if n_panels == 1:
        axes = [axes]

    idx = 0
    if has_stocks:
        ax = axes[idx]
        for stock in engine.config.stocks:
            ax.plot(time_data, engine.history[stock.name], label=stock.name, lw=2)
        ax.set_ylabel("Stocks")
        ax.legend()
        ax.grid(True, alpha=0.3)
        idx += 1

    if has_flows:
        ax = axes[idx]
        for flow in engine.config.flows:
            ax.plot(time_data, engine.flow_history[flow.name], label=flow.name, lw=2)
        ax.set_ylabel("Flows")
        ax.legend()
        ax.grid(True, alpha=0.3)
        idx += 1

    if has_aux:
        ax = axes[idx]
        for aux in engine.config.auxiliaries:
            ax.plot(time_data, engine.aux_history[aux.name], label=aux.name, lw=2)
        ax.set_ylabel("Auxiliaries")
        ax.legend()
        ax.grid(True, alpha=0.3)
        idx += 1

    axes[-1].set_xlabel("Time")
    fig.suptitle(title, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    return fig


def save_plot(fig: Any, path: str) -> None:
    """Save a plot figure to disk."""
    if path.endswith(".html"):
        try:
            import plotly.graph_objects as go

            if isinstance(fig, go.Figure):
                fig.write_html(path)
                return
        except ImportError:
            pass
        raise ValueError("HTML output requires plotly. " "Install with: pip install plotly")
    fig.savefig(path, dpi=150)
