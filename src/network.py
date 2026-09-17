"""Create the deterministic synthetic smart-city infrastructure graph."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pandas as pd


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "infrastructure.csv"

# Each undirected edge is a resilience/dependency link. dependency_strength
# controls how much displaced pressure a neighbor receives; weight is rerouting
# friction. Loads are normalized service-pressure units across all sectors.
EDGE_DATA = [
    ("PWR_PLANT", "SUB_N", 190, 80, 1.00, 1.0, "power supply"),
    ("PWR_PLANT", "SUB_C", 190, 98, 1.00, 1.0, "power supply"),
    ("PWR_PLANT", "SUB_S", 150, 70, 0.90, 1.2, "power supply"),
    ("SUB_N", "SUB_C", 90, 38, 0.75, 1.3, "grid redundancy"),
    ("SUB_C", "SUB_S", 85, 34, 0.72, 1.3, "grid redundancy"),
    ("SUB_C", "DIST_E", 100, 62, 0.95, 1.0, "power distribution"),
    ("SUB_C", "DIST_W", 95, 57, 0.95, 1.0, "power distribution"),
    ("SUB_N", "DIST_E", 75, 31, 0.72, 1.4, "backup supply"),
    ("SUB_S", "DIST_W", 70, 29, 0.70, 1.4, "backup supply"),
    ("HW_N", "BRIDGE_A", 165, 104, 0.88, 1.0, "primary route"),
    ("HW_N", "ROAD_E", 125, 68, 0.65, 1.4, "alternate route"),
    ("BRIDGE_A", "INT_C", 140, 96, 1.00, 1.0, "primary route"),
    ("BRIDGE_A", "ROAD_W", 110, 61, 0.90, 1.1, "alternate route"),
    ("BRIDGE_B", "INT_C", 120, 68, 0.82, 1.1, "primary route"),
    ("BRIDGE_B", "ROAD_E", 105, 57, 0.78, 1.1, "alternate route"),
    ("ROAD_E", "INT_C", 115, 72, 0.92, 1.0, "arterial route"),
    ("ROAD_W", "INT_C", 110, 70, 0.95, 1.0, "arterial route"),
    ("INT_C", "TRANSIT", 100, 59, 0.85, 1.0, "mobility link"),
    ("ROAD_E", "TRANSIT", 80, 42, 0.55, 1.5, "alternate route"),
    ("WTR_PLANT", "PUMP_N", 135, 60, 1.00, 1.0, "water supply"),
    ("WTR_PLANT", "PUMP_S", 130, 56, 1.00, 1.0, "water supply"),
    ("PUMP_N", "PUMP_S", 65, 20, 0.55, 1.5, "pump redundancy"),
    ("PUMP_N", "WATER_E", 90, 54, 0.95, 1.0, "water distribution"),
    ("PUMP_N", "WATER_W", 78, 42, 0.72, 1.3, "backup main"),
    ("PUMP_S", "WATER_W", 88, 50, 0.95, 1.0, "water distribution"),
    ("PUMP_S", "WATER_E", 76, 39, 0.70, 1.3, "backup main"),
    ("HOSP_C", "HOSP_E", 72, 27, 0.78, 1.1, "patient diversion"),
    ("HOSP_C", "HOSP_W", 70, 26, 0.78, 1.1, "patient diversion"),
    ("HOSP_C", "EMERG", 75, 36, 0.90, 1.0, "emergency referral"),
    ("HOSP_E", "EMERG", 58, 22, 0.65, 1.3, "patient diversion"),
    ("HOSP_W", "TRANSIT", 55, 19, 0.50, 1.5, "access route"),
    ("EMERG", "CLINIC_S", 48, 18, 0.60, 1.4, "care referral"),
    ("DIST_E", "HOSP_E", 85, 52, 0.92, 1.0, "electricity dependency"),
    ("DIST_W", "HOSP_W", 82, 48, 0.92, 1.0, "electricity dependency"),
    ("SUB_C", "HOSP_C", 105, 66, 1.00, 1.0, "critical power dependency"),
    ("SUB_S", "WTR_PLANT", 100, 68, 0.94, 1.0, "treatment power dependency"),
    ("SUB_N", "PUMP_N", 80, 45, 0.82, 1.1, "pump power dependency"),
    ("DIST_W", "PUMP_S", 72, 39, 0.78, 1.2, "pump power dependency"),
    ("WATER_E", "HOSP_E", 75, 49, 0.88, 1.0, "clinical water dependency"),
    ("WATER_W", "HOSP_W", 72, 46, 0.88, 1.0, "clinical water dependency"),
    ("WATER_E", "HOSP_C", 82, 51, 0.82, 1.1, "clinical water dependency"),
    ("BRIDGE_A", "HOSP_C", 90, 54, 0.72, 1.1, "emergency access"),
    ("ROAD_E", "HOSP_E", 82, 47, 0.72, 1.1, "hospital access"),
    ("ROAD_W", "HOSP_W", 78, 44, 0.72, 1.1, "hospital access"),
    ("INT_C", "EMERG", 88, 51, 0.82, 1.0, "emergency access"),
    ("TRANSIT", "CLINIC_S", 62, 29, 0.58, 1.3, "clinic access"),
]


def load_infrastructure(path: Path | str = DATA_PATH) -> pd.DataFrame:
    """Load and validate the synthetic node catalogue."""
    frame = pd.read_csv(path)
    required = {"id", "name", "sector", "type", "capacity", "load", "demand", "status", "x", "y"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Infrastructure data is missing columns: {sorted(missing)}")
    if frame["id"].duplicated().any():
        raise ValueError("Infrastructure IDs must be unique")
    if (frame[["capacity", "load", "demand"]].astype(float) < 0).any().any():
        raise ValueError("Capacity, load, and demand must be non-negative")
    return frame


def create_infrastructure_network(path: Path | str = DATA_PATH) -> nx.Graph:
    """Return a fresh deterministic 23-node, four-sector graph."""
    graph = nx.Graph(name="Synthetic City Infrastructure")
    for row in load_infrastructure(path).to_dict("records"):
        node_id = row.pop("id")
        for key in ("capacity", "load", "demand", "x", "y"):
            row[key] = float(row[key])
        row["baseline_load"] = row["load"]
        row["peak_utilization"] = row["load"] / row["capacity"]
        row["was_affected"] = False
        graph.add_node(node_id, **row)

    for source, target, capacity, flow, strength, weight, relation in EDGE_DATA:
        if source not in graph or target not in graph:
            raise ValueError(f"Edge references an unknown node: {source}--{target}")
        graph.add_edge(
            source, target, capacity=float(capacity), flow=float(flow),
            baseline_flow=float(flow), dependency_strength=float(strength),
            weight=float(weight), relation=relation,
        )
    return graph


def network_summary(graph: nx.Graph) -> dict[str, object]:
    """Return compact facts used by validation and the dashboard."""
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "sectors": sorted({data["sector"] for _, data in graph.nodes(data=True)}),
        "connected": nx.is_connected(graph),
        "total_capacity": sum(data["capacity"] for _, data in graph.nodes(data=True)),
        "total_load": sum(data["load"] for _, data in graph.nodes(data=True)),
    }
