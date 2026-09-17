"""Dependency-light smoke tests; run with ``python3 test_prototype.py``."""

from src.criticality import analyze_criticality, compare_scenarios
from src.metrics import calculate_metrics
from src.network import create_infrastructure_network, network_summary
from src.simulation import simulate_cascade


def main() -> None:
    graph = create_infrastructure_network()
    summary = network_summary(graph)
    assert summary["nodes"] == 23
    assert summary["edges"] == 46
    assert summary["connected"] is True
    assert summary["sectors"] == ["Healthcare", "Power", "Transportation", "Water"]

    bridge = simulate_cascade(graph, "BRIDGE_A")
    substation = simulate_cascade(graph, "SUB_C")
    bridge_metrics = calculate_metrics(bridge)
    substation_metrics = calculate_metrics(substation)
    assert "BRIDGE_A" in bridge["initial_failures"]
    assert bridge_metrics["failed_assets"] >= 1
    assert bridge_metrics["affected_assets"] >= bridge_metrics["failed_assets"]
    assert 0 <= bridge_metrics["impact_score"] <= 100
    assert substation_metrics["affected_sector_count"] >= 1

    ranking = analyze_criticality(graph)
    assert len(ranking) == graph.number_of_nodes()
    assert ranking["Rank"].tolist() == list(range(1, graph.number_of_nodes() + 1))

    comparison, results = compare_scenarios(graph, "BRIDGE_A", "SUB_C")
    assert len(comparison) == 6
    assert set(results) == {"Scenario A", "Scenario B"}
    print("All CityResilience smoke tests passed.")
    print("Bridge metrics:", bridge_metrics)
    print("Substation metrics:", substation_metrics)


if __name__ == "__main__":
    main()
