# CityResilience

CityResilience is a polished hackathon proof of concept for exploring cascading
failures across a synthetic, multi-sector smart-city infrastructure network.

It demonstrates the complete loop:

`Network → Failure → Load Redistribution → Overload → Secondary Failure → Cascade → Metrics`

## What is included

- Deterministic 23-asset NetworkX graph covering transportation, power, water,
  and healthcare
- Adjustable initial failure and failure severity
- Iterative load redistribution, degraded states, secondary failures, and a
  stabilization limit
- Interactive Plotly network with load, capacity, utilization, and status
- Cascade timeline, KPI cards, utilization analysis, and sector impact chart
- Simulation-based criticality ranking across every asset
- Side-by-side comparison of two failure scenarios
- Explicit model assumptions and proof-of-concept disclaimers

The optional ML layer is intentionally excluded. There is no validated training
dataset, so the dashboard presents it only as a possible future analytical layer.

## Project structure

```text
cascading_failure/
├── app.py
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── network.py
│   ├── simulation.py
│   ├── criticality.py
│   ├── metrics.py
│   └── visualization.py
└── data/
    └── infrastructure.csv
```

## Install and run with global Python

From the project directory:

```bash
cd "/home/solomon/Desktop/Work/M#"/cascading_failure
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Streamlit will print a local URL, usually <http://localhost:8501>.

## Suggested 45-second demo

1. Start on **Live Simulation** and point out the healthy four-sector network.
2. Leave **Rivergate Bridge** selected and click **SIMULATE FAILURE**.
3. Show the red/amber cascade state, KPI cards, and propagation timeline.
4. Open **Critical Assets** and show the simulation-based ranking.
5. Open **Scenario Comparison**, compare Rivergate Bridge with Central Grid
   Substation, and show the result table and maps.

## Model logic

Each link has a dependency strength and rerouting friction. When an asset fails,
its displaced load is divided among active neighbors in proportion to:

```text
dependency strength / rerouting friction
```

An asset is degraded at 90% utilization and fails above 100%. Newly failed
assets redistribute 30% of their load during the next round, while emergency
controls shed the remainder. This damping avoids an unrealistic total collapse
caused by conserving all pressure while the graph continually loses capacity.
The process stops once no new failures occur or after eight rounds.

Loads are normalized **service-pressure units**. Cross-sector edges describe
operational dependencies; they do not imply that physical water, electrical
power, traffic, and patients use interchangeable units.

## Scope and interpretation

All infrastructure, dependencies, thresholds, and results are synthetic. The
criticality and impact scores are transparent simulation heuristics—not
probabilities, scientific validation, or predictions about a real city. This
prototype must not be used for operational planning.
