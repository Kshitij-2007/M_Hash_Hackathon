"""Deterministic cascading-failure simulation engine."""

from __future__ import annotations

from copy import deepcopy
from typing import Iterable

import networkx as nx


FAILURE_THRESHOLD = 1.00
DEGRADED_THRESHOLD = 0.90
SECONDARY_TRANSFER_FACTOR = 0.30


def _as_failure_list(initial_failures: str | Iterable[str]) -> list[str]:
    if isinstance(initial_failures, str):
        return [initial_failures]
    return list(dict.fromkeys(initial_failures))


def _mark_failed(
    graph: nx.Graph,
    node_ids: Iterable[str],
    round_number: int,
    severity: float = 1.0,
) -> dict[str, float]:
    """Fail nodes and return the load that must be redistributed."""
    displaced: dict[str, float] = {}
    for node_id in node_ids:
        data = graph.nodes[node_id]
        if data["status"] == "failed":
            continue
        active_load = float(data["load"])
        displaced[node_id] = active_load * severity
        data["load"] = 0.0
        data["status"] = "failed"
        data["failure_round"] = round_number
        data["was_affected"] = True
    return displaced


def _redistribute(
    graph: nx.Graph, displaced: dict[str, float]
) -> tuple[list[dict[str, object]], float]:
    """Redistribute displaced pressure across each failed node's active links.

    Allocation is proportional to dependency strength and inversely proportional
    to rerouting friction. This deliberately simple local rule makes the cascade
    deterministic and easy to explain during a demo.
    """
    transfers: list[dict[str, object]] = []
    unserved = 0.0
    for source in sorted(displaced):
        amount = displaced[source]
        candidates: list[tuple[str, float]] = []
        for target in graph.neighbors(source):
            if graph.nodes[target]["status"] == "failed":
                continue
            edge = graph.edges[source, target]
            score = edge["dependency_strength"] / max(edge["weight"], 0.1)
            candidates.append((target, score))

        score_total = sum(score for _, score in candidates)
        if not candidates or score_total <= 0:
            unserved += amount
            continue

        for target, score in candidates:
            allocation = amount * score / score_total
            graph.nodes[target]["load"] += allocation
            graph.nodes[target]["was_affected"] = True
            graph.edges[source, target]["flow"] += allocation
            transfers.append(
                {"source": source, "target": target, "amount": allocation}
            )
    return transfers, unserved


def simulate_cascade(
    graph: nx.Graph,
    initial_failures: str | Iterable[str],
    severity: float = 1.0,
    max_rounds: int = 8,
    failure_threshold: float = FAILURE_THRESHOLD,
    degraded_threshold: float = DEGRADED_THRESHOLD,
) -> dict[str, object]:
    """Run a cascade until no new failures occur or ``max_rounds`` is hit.

    The input graph is never mutated. Severity controls how much of the initial
    failed asset's load is pushed into the remaining network.
    """
    if not 0.0 <= severity <= 1.0:
        raise ValueError("severity must be between 0 and 1")
    if max_rounds < 1:
        raise ValueError("max_rounds must be at least 1")

    failures = _as_failure_list(initial_failures)
    unknown = [node_id for node_id in failures if node_id not in graph]
    if unknown:
        raise KeyError(f"Unknown infrastructure asset(s): {unknown}")
    if not failures:
        raise ValueError("At least one initial failure is required")

    simulated = deepcopy(graph)
    for _, data in simulated.nodes(data=True):
        data["baseline_load"] = float(data.get("baseline_load", data["load"]))
        data["peak_utilization"] = data["load"] / data["capacity"]
        data["was_affected"] = False
        data.pop("failure_round", None)
        data["status"] = "healthy"

    pending = _mark_failed(simulated, failures, round_number=0, severity=severity)
    initial_names = [simulated.nodes[node_id]["name"] for node_id in failures]
    rounds: list[dict[str, object]] = [
        {
            "round": 0,
            "failed": failures,
            "degraded": [],
            "transfers": [],
            "unserved_load": 0.0,
            "events": [f"{name} set to FAILED" for name in initial_names],
        }
    ]
    total_unserved = 0.0
    reached_limit = False

    for round_number in range(1, max_rounds + 1):
        transfers, unserved = _redistribute(simulated, pending)
        total_unserved += unserved
        newly_failed: list[str] = []
        newly_degraded: list[str] = []

        for node_id, data in simulated.nodes(data=True):
            if data["status"] == "failed":
                continue
            utilization = data["load"] / data["capacity"]
            data["peak_utilization"] = max(data["peak_utilization"], utilization)
            old_status = data["status"]
            if utilization > failure_threshold:
                newly_failed.append(node_id)
            elif utilization >= degraded_threshold:
                data["status"] = "degraded"
                if old_status != "degraded":
                    newly_degraded.append(node_id)
            else:
                data["status"] = "healthy"

        events: list[str] = []
        if transfers:
            moved = sum(item["amount"] for item in transfers)
            receivers = len({item["target"] for item in transfers})
            events.append(f"{moved:.1f} load units redistributed to {receivers} assets")
        if unserved:
            events.append(f"{unserved:.1f} load units could not be rerouted")
        for node_id in newly_failed:
            utilization = simulated.nodes[node_id]["peak_utilization"] * 100
            events.append(f"{simulated.nodes[node_id]['name']} FAILED at {utilization:.0f}% peak utilization")
        for node_id in newly_degraded:
            utilization = simulated.nodes[node_id]["peak_utilization"] * 100
            events.append(f"{simulated.nodes[node_id]['name']} DEGRADED at {utilization:.0f}% utilization")

        rounds.append(
            {
                "round": round_number,
                "failed": list(newly_failed),
                "degraded": list(newly_degraded),
                "transfers": transfers,
                "unserved_load": unserved,
                "events": events,
            }
        )
        if not newly_failed:
            if not events:
                rounds[-1]["events"] = ["Network stabilized with no additional overloads"]
            else:
                rounds[-1]["events"].append("Network stabilized")
            break

        # Emergency controls and demand shedding absorb part of a secondary
        # failure's load. Without this damping, a connected graph conserves all
        # pressure while losing capacity and unrealistically collapses in full.
        active_failed_load = sum(simulated.nodes[node_id]["load"] for node_id in newly_failed)
        shed_load = active_failed_load * (1.0 - SECONDARY_TRANSFER_FACTOR)
        total_unserved += shed_load
        rounds[-1]["unserved_load"] += shed_load
        if shed_load:
            rounds[-1]["events"].append(f"{shed_load:.1f} load units shed by emergency controls")
        pending = _mark_failed(
            simulated,
            newly_failed,
            round_number=round_number,
            severity=SECONDARY_TRANSFER_FACTOR,
        )
    else:
        reached_limit = True

    return {
        "graph": simulated,
        "initial_failures": failures,
        "severity": severity,
        "rounds": rounds,
        "total_unserved_load": total_unserved,
        "reached_round_limit": reached_limit,
        "settings": {
            "failure_threshold": failure_threshold,
            "degraded_threshold": degraded_threshold,
            "secondary_transfer_factor": SECONDARY_TRANSFER_FACTOR,
            "max_rounds": max_rounds,
        },
    }
