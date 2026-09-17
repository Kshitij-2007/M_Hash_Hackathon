"""Impact, cascade, and utilization metrics for simulation results."""

from __future__ import annotations

import pandas as pd


def calculate_metrics(result: dict[str, object]) -> dict[str, object]:
    """Summarize one cascade result with transparent heuristic metrics."""
    graph = result["graph"]
    failed = [node for node, data in graph.nodes(data=True) if data["status"] == "failed"]
    degraded = [node for node, data in graph.nodes(data=True) if data["status"] == "degraded"]
    affected = [node for node, data in graph.nodes(data=True) if data.get("was_affected")]
    affected_sectors = sorted({graph.nodes[node]["sector"] for node in affected})

    secondary_rounds = [
        entry["round"] for entry in result["rounds"]
        if entry["round"] > 0 and entry["failed"]
    ]
    cascade_depth = max(secondary_rounds, default=0)
    max_peak = max(data.get("peak_utilization", 0.0) for _, data in graph.nodes(data=True))
    total_baseline = sum(data["baseline_load"] for _, data in graph.nodes(data=True))
    failed_service = sum(graph.nodes[node]["baseline_load"] for node in failed)
    service_loss_ratio = min(
        1.0,
        (failed_service + float(result["total_unserved_load"])) / max(total_baseline, 1.0),
    )
    asset_impact = (len(failed) + 0.45 * len(degraded)) / graph.number_of_nodes()
    breadth = len(affected_sectors) / max(len({d["sector"] for _, d in graph.nodes(data=True)}), 1)
    depth_factor = min(cascade_depth / 5.0, 1.0)
    impact_score = min(
        100.0,
        100.0 * (0.35 * asset_impact + 0.30 * service_loss_ratio + 0.20 * breadth + 0.15 * depth_factor),
    )
    excess_load = sum(
        max(0.0, data.get("peak_utilization", 0.0) - 1.0) * data["capacity"]
        for _, data in graph.nodes(data=True)
    )
    return {
        "cascade_depth": cascade_depth,
        "affected_assets": len(affected),
        "failed_assets": len(failed),
        "degraded_assets": len(degraded),
        "affected_sectors": affected_sectors,
        "affected_sector_count": len(affected_sectors),
        "maximum_overload": max(0.0, (max_peak - 1.0) * 100.0),
        "total_excess_load": excess_load,
        "unserved_load": float(result["total_unserved_load"]),
        "impact_score": impact_score,
    }


def asset_impact_frame(result: dict[str, object]) -> pd.DataFrame:
    """Return node-level before/after utilization for tables and charts."""
    graph = result["graph"]
    rows = []
    for node_id, data in graph.nodes(data=True):
        before = data["baseline_load"] / data["capacity"] * 100
        after = data["load"] / data["capacity"] * 100 if data["status"] != "failed" else 0.0
        rows.append(
            {
                "Asset ID": node_id,
                "Asset": data["name"],
                "Sector": data["sector"],
                "Status": data["status"].title(),
                "Before utilization": before,
                "After utilization": after,
                "Peak utilization": data["peak_utilization"] * 100,
                "Load change": data["load"] - data["baseline_load"],
                "Affected": bool(data.get("was_affected")),
            }
        )
    return pd.DataFrame(rows)


def sector_impact_frame(result: dict[str, object]) -> pd.DataFrame:
    """Aggregate affected, degraded, and failed assets by sector."""
    graph = result["graph"]
    rows = []
    for sector in sorted({data["sector"] for _, data in graph.nodes(data=True)}):
        items = [data for _, data in graph.nodes(data=True) if data["sector"] == sector]
        rows.append(
            {
                "Sector": sector,
                "Affected": sum(bool(data.get("was_affected")) for data in items),
                "Degraded": sum(data["status"] == "degraded" for data in items),
                "Failed": sum(data["status"] == "failed" for data in items),
            }
        )
    return pd.DataFrame(rows)
