"""System Dynamics Simulation Engine.

Core concepts:
- Stocks: accumulations (state variables)
- Flows: rates of change
- Auxiliaries: intermediate calculations
- Feedback loops: causal connections
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class Stock:
    name: str
    initial_value: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ""


@dataclass
class Flow:
    name: str
    target_stock: str  # stock to add to
    source_stock: Optional[str] = None  # stock to subtract from
    formula: str = ""  # mathematical expression as string
    unit: str = ""


@dataclass
class Auxiliary:
    name: str
    formula: str = ""
    unit: str = ""


@dataclass
class ModelConfig:
    name: str
    description: str
    stocks: List[Stock]
    flows: List[Flow]
    auxiliaries: List[Auxiliary]
    time_step: float = 0.25
    total_time: float = 100.0


class SDEngine:
    """System Dynamics simulation engine using Euler integration."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config
        self.time = 0.0
        self.stocks: Dict[str, float] = {}
        self.history: Dict[str, List[float]] = {"time": []}
        self.aux_history: Dict[str, List[float]] = {}
        self.flow_history: Dict[str, List[float]] = {}
        self._init_stocks()

    def _init_stocks(self) -> None:
        for stock in self.config.stocks:
            self.stocks[stock.name] = stock.initial_value
            self.history[stock.name] = []
        for aux in self.config.auxiliaries:
            self.aux_history[aux.name] = []
        for flow in self.config.flows:
            self.flow_history[flow.name] = []

    def _build_namespace(self) -> dict:
        """Build the evaluation namespace for formulas."""
        ns = {
            "time": self.time,
            "math": math,
            "abs": abs,
            "max": max,
            "min": min,
            "clamp": lambda v, lo, hi: max(lo, min(hi, v)),
        }
        ns.update(self.stocks)
        return ns

    def _eval_formula(self, formula: str, namespace: dict) -> float:
        """Safely evaluate a formula string."""
        try:
            return float(eval(formula, {"__builtins__": {}}, namespace))
        except Exception as e:
            raise ValueError(f"Error evaluating formula '{formula}': {e}")

    def _compute_auxiliaries(self) -> Dict[str, float]:
        """Compute all auxiliary variables."""
        ns = self._build_namespace()
        aux_values: Dict[str, float] = {}
        unresolved = list(self.config.auxiliaries)
        max_passes = 10
        for _ in range(max_passes):
            if not unresolved:
                break
            still_unresolved: List[Auxiliary] = []
            for aux in unresolved:
                try:
                    val = self._eval_formula(aux.formula, ns)
                    aux_values[aux.name] = val
                    ns[aux.name] = val
                except (NameError, ValueError):
                    still_unresolved.append(aux)
            unresolved = still_unresolved
        if unresolved:
            raise ValueError(f"Could not resolve auxiliaries: {[a.name for a in unresolved]}")
        return aux_values

    def _compute_flows(self) -> Dict[str, float]:
        """Compute all flow rates."""
        ns = self._build_namespace()
        ns.update(self._compute_auxiliaries())
        flow_values: Dict[str, float] = {}
        for flow in self.config.flows:
            flow_values[flow.name] = self._eval_formula(flow.formula, ns)
        return flow_values

    def step(self) -> None:
        """Advance simulation by one time step."""
        flow_values = self._compute_flows()
        aux_values = self._compute_auxiliaries()
        delta = {stock.name: 0.0 for stock in self.config.stocks}
        for flow in self.config.flows:
            rate = flow_values[flow.name]
            if flow.target_stock:
                delta[flow.target_stock] += rate * self.config.time_step
            if flow.source_stock:
                delta[flow.source_stock] -= rate * self.config.time_step

        for stock in self.config.stocks:
            new_val = self.stocks[stock.name] + delta[stock.name]
            if stock.min_value is not None:
                new_val = max(stock.min_value, new_val)
            if stock.max_value is not None:
                new_val = min(stock.max_value, new_val)
            self.stocks[stock.name] = new_val

        self.time += self.config.time_step
        self._record_history(flow_values, aux_values)

    def _record_history(self, flow_values: Dict[str, float], aux_values: Dict[str, float]) -> None:
        self.history["time"].append(self.time)
        for stock in self.config.stocks:
            self.history[stock.name].append(self.stocks[stock.name])
        for name, val in flow_values.items():
            self.flow_history[name].append(val)
        for name, val in aux_values.items():
            self.aux_history[name].append(val)

    def run(self) -> Dict[str, List[float]]:
        """Run the full simulation."""
        steps = int(self.config.total_time / self.config.time_step)
        self._record_history(
            {f.name: 0.0 for f in self.config.flows},
            {a.name: 0.0 for a in self.config.auxiliaries},
        )
        for _ in range(steps):
            self.step()
        return self.history

    def to_csv(self, path: Path) -> None:
        """Export simulation results to CSV."""
        rows = []
        n = len(self.history["time"])
        headers = ["time"] + [s.name for s in self.config.stocks]
        headers += [f"flow:{f.name}" for f in self.config.flows]
        headers += [f"aux:{a.name}" for a in self.config.auxiliaries]
        for i in range(n):
            row = {"time": self.history["time"][i]}
            for stock in self.config.stocks:
                row[stock.name] = self.history[stock.name][i]
            for flow in self.config.flows:
                row[f"flow:{flow.name}"] = self.flow_history[flow.name][i]
            for aux in self.config.auxiliaries:
                row[f"aux:{aux.name}"] = self.aux_history[aux.name][i]
            rows.append(row)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)


def load_config(path: str) -> ModelConfig:
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith(".yaml") or path.endswith(".yml"):
            data = yaml.safe_load(f)
        else:
            data = json.load(f)

    stocks = [Stock(**s) for s in data.get("stocks", [])]
    flows = [Flow(**f) for f in data.get("flows", [])]
    auxiliaries = [Auxiliary(**a) for a in data.get("auxiliaries", [])]

    return ModelConfig(
        name=data["name"],
        description=data.get("description", ""),
        stocks=stocks,
        flows=flows,
        auxiliaries=auxiliaries,
        time_step=data.get("time_step", 0.25),
        total_time=data.get("total_time", 100.0),
    )
