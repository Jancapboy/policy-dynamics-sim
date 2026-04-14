"""Command-line interface for policy dynamics simulation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from policy_dynamics_sim.engine import SDEngine, load_config
from policy_dynamics_sim.visualizer import plot_simulation, save_plot


def main() -> None:
    parser = argparse.ArgumentParser(description="Policy and System Dynamics Simulator")
    parser.add_argument("config", type=str, help="Path to model config (YAML or JSON)")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output JSON file for simulation results",
    )
    parser.add_argument(
        "--csv",
        "-c",
        type=str,
        default=None,
        help="Output CSV file for simulation results",
    )
    parser.add_argument(
        "--plot",
        "-p",
        type=str,
        default=None,
        help="Output plot image file (PNG/SVG/HTML)",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        default=None,
        help="Plot title (defaults to model name)",
    )
    parser.add_argument(
        "--stocks",
        type=str,
        default=None,
        help="Comma-separated list of stocks to plot (default: all)",
    )

    args = parser.parse_args()

    if not Path(args.config).exists():
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    config = load_config(args.config)
    engine = SDEngine(config)
    history = engine.run()

    result = {
        "model": config.name,
        "description": config.description,
        "time_step": config.time_step,
        "total_time": config.total_time,
        "history": history,
        "flows": engine.flow_history,
        "auxiliaries": engine.aux_history,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"Results written to {args.output}")

    if args.csv:
        engine.to_csv(Path(args.csv))
        print(f"CSV written to {args.csv}")

    if args.plot:
        stocks_to_plot = None
        if args.stocks:
            stocks_to_plot = [s.strip() for s in args.stocks.split(",")]
        fig = plot_simulation(
            engine,
            title=args.title or config.name,
            stocks=stocks_to_plot,
        )
        save_plot(fig, args.plot)
        print(f"Plot saved to {args.plot}")

    if not args.output and not args.plot and not args.csv:
        print(f"Model: {config.name}")
        print(f"Description: {config.description}")
        print(f"Time step: {config.time_step}, Total time: {config.total_time}")
        print(f"Steps simulated: {len(history['time'])}")
        print("\nFinal stock values:")
        for stock in config.stocks:
            final = history[stock.name][-1]
            print(f"  {stock.name}: {final:.4f} {stock.unit}")


if __name__ == "__main__":
    main()
