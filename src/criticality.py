"""Simulation-based infrastructure criticality and scenario comparison."""

from __future__ import annotations

import networkx as nx
import pandas as pd

from .metrics import calculate_metrics
from .simulation import simulate_cascade


def analyze_criticality(
    graph: nx.Graph,
    severity: float = 1.0,
    max_rounds: int = 8,
) -> pd.DataFrame:
    """Fail every asset once and rank the synthetic simulation outcomes."""
    rows = []
    for node_id, data in graph.nodes(data=True):
        result = simulate_cascade(graph, node_id, severity=severity, max_rounds=max_rounds)
        metrics = calculate_metrics(result)
        rows.append(
            {
                "Asset ID": node_id,
                "Asset": data["name"],
                "Sector": data["sector"],
                "Type": data["type"],
                "Impact Score": metrics["impact_score"],
                "Failed Assets": metrics["failed_assets"],
                "Degraded Assets": metrics["degraded_assets"],
                "Cascade Depth": metrics["cascade_depth"],
                "Affected Sectors": metrics["affected_sector_count"],
                "Excess Load": metrics["total_excess_load"],
            }
        )
    frame = pd.DataFrame(rows).sort_values(
        ["Impact Score", "Failed Assets", "Cascade Depth"], ascending=False
    ).reset_index(drop=True)
    frame.insert(0, "Rank", frame.index + 1)
    high_cutoff = max(3, round(len(frame) * 0.20))
    medium_cutoff = max(high_cutoff + 1, round(len(frame) * 0.55))
    frame["Criticality"] = [
        "High" if index < high_cutoff else "Medium" if index < medium_cutoff else "Lower"
        for index in frame.index
    ]
    return frame


def compare_scenarios(
    graph: nx.Graph,
    scenario_a: str,
    scenario_b: str,
    severity_a: float = 1.0,
    severity_b: float = 1.0,
) -> tuple[pd.DataFrame, dict[str, dict[str, object]]]:
    """Run and format two failure scenarios for side-by-side comparison."""
    results = {
        "Scenario A": simulate_cascade(graph, scenario_a, severity=severity_a),
        "Scenario B": simulate_cascade(graph, scenario_b, severity=severity_b),
    }
    metric_labels = [
        ("Failed Assets", "failed_assets"),
        ("Degraded Assets", "degraded_assets"),
        ("Affected Assets", "affected_assets"),
        ("Cascade Depth", "cascade_depth"),
        ("Affected Sectors", "affected_sector_count"),
        ("Impact Score", "impact_score"),
    ]
    summaries = {label: calculate_metrics(result) for label, result in results.items()}
    rows = []
    for display, key in metric_labels:
        values = {"Metric": display}
        for label in results:
            value = summaries[label][key]
            values[label] = round(value, 1) if isinstance(value, float) else value
        rows.append(values)
    return pd.DataFrame(rows), results
