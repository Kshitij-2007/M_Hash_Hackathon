"""Plotly figures for the CityResilience dashboard."""

from __future__ import annotations

import networkx as nx
import pandas as pd
import plotly.graph_objects as go

from .metrics import asset_impact_frame, sector_impact_frame


STATUS_COLORS = {"healthy": "#21d4a7", "degraded": "#ffb547", "failed": "#ff4d6d"}
SECTOR_SYMBOLS = {
    "Power": "hexagon",
    "Transportation": "circle",
    "Water": "diamond",
    "Healthcare": "square",
}


def network_figure(graph: nx.Graph) -> go.Figure:
    """Build an interactive fixed-layout infrastructure graph."""
    figure = go.Figure()
    for source, target, edge in graph.edges(data=True):
        a, b = graph.nodes[source], graph.nodes[target]
        cross_sector = a["sector"] != b["sector"]
        figure.add_trace(
            go.Scatter(
                x=[a["x"], b["x"]], y=[a["y"], b["y"]],
                mode="lines", hoverinfo="text",
                text=[
                    f"{a['name']} ↔ {b['name']}<br>{edge['relation'].title()}<br>"
                    f"Dependency strength: {edge['dependency_strength']:.2f}"
                ] * 2,
                line={
                        "color": "rgba(190, 225, 218, 0.46)" if cross_sector else "rgba(155, 205, 196, 0.28)",
                    "width": 1.8 if cross_sector else 1.1,
                    "dash": "dot" if cross_sector else "solid",
                },
                showlegend=False,
            )
        )

    legend_shown: set[str] = set()
    for status in ("healthy", "degraded", "failed"):
        for sector in SECTOR_SYMBOLS:
            nodes = [
                (node_id, data) for node_id, data in graph.nodes(data=True)
                if data["status"] == status and data["sector"] == sector
            ]
            if not nodes:
                continue
            hover = []
            sizes = []
            for _, data in nodes:
                utilization = data["load"] / data["capacity"] * 100 if status != "failed" else 0
                hover.append(
                    f"<b>{data['name']}</b><br>{data['type']} · {sector}<br>"
                    f"Capacity: {data['capacity']:.0f}<br>Current load: {data['load']:.1f}<br>"
                    f"Utilization: {utilization:.1f}%<br>Status: {status.upper()}"
                )
                peak = max(data.get("peak_utilization", utilization / 100), 0.35)
                sizes.append(min(34, 15 + peak * 10))
            figure.add_trace(
                go.Scatter(
                    x=[data["x"] for _, data in nodes],
                    y=[data["y"] for _, data in nodes],
                    mode="markers+text",
                    text=[data["name"].replace(" ", "<br>", 1) for _, data in nodes],
                    textposition="bottom center",
                    textfont={"size": 9, "color": "#c6ddd8"},
                    hovertext=hover,
                    hoverinfo="text",
                    name=status.title(),
                    legendgroup=status,
                    showlegend=status not in legend_shown,
                    marker={
                        "size": sizes,
                        "color": STATUS_COLORS[status],
                        "symbol": SECTOR_SYMBOLS[sector],
                        "line": {"color": "#eef5ff", "width": 1.2 if status != "failed" else 2.2},
                        "opacity": 0.96,
                    },
                )
            )
            legend_shown.add(status)

    figure.update_layout(
        height=600,
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        paper_bgcolor="#064744",
        plot_bgcolor="#064744",
        hoverlabel={"bgcolor": "#e7f0ed", "font_color": "#073f3d", "bordercolor": "#9bbdb7"},
        legend={"orientation": "h", "y": 1.04, "x": 0, "font": {"color": "#d5e6e2"}},
        xaxis={"visible": False, "range": [0, 1]},
        yaxis={"visible": False, "range": [0, 1]},
        dragmode="pan",
    )
    return figure


def utilization_figure(result: dict[str, object]) -> go.Figure:
    """Compare baseline and peak utilization for the most affected assets."""
    frame = asset_impact_frame(result)
    frame = frame[frame["Affected"]].sort_values("Peak utilization", ascending=True).tail(10)
    figure = go.Figure()
    figure.add_bar(
        x=frame["Before utilization"], y=frame["Asset"], orientation="h",
        name="Baseline", marker_color="#405475",
    )
    figure.add_bar(
        x=frame["Peak utilization"], y=frame["Asset"], orientation="h",
        name="Peak", marker_color="#ff657f",
    )
    figure.add_vline(x=100, line_dash="dash", line_color="#ffb547", annotation_text="Capacity")
    figure.update_layout(
        barmode="group", height=380, margin={"l": 10, "r": 10, "t": 20, "b": 30},
        paper_bgcolor="#f4f8f6", plot_bgcolor="#f4f8f6",
        font={"color": "#315d59"}, legend={"orientation": "h", "y": 1.08},
        xaxis={"title": "Utilization (%)", "gridcolor": "rgba(32,102,96,.13)"},
        yaxis={"title": ""},
    )
    return figure


def sector_impact_figure(result: dict[str, object]) -> go.Figure:
    """Show affected asset counts by sector and status."""
    frame = sector_impact_frame(result)
    figure = go.Figure()
    for column, color in (("Affected", "#4f8cff"), ("Degraded", "#ffb547"), ("Failed", "#ff4d6d")):
        figure.add_bar(x=frame["Sector"], y=frame[column], name=column, marker_color=color)
    figure.update_layout(
        barmode="group", height=380, margin={"l": 10, "r": 10, "t": 20, "b": 30},
        paper_bgcolor="#f4f8f6", plot_bgcolor="#f4f8f6",
        font={"color": "#315d59"}, legend={"orientation": "h", "y": 1.08},
        yaxis={"title": "Assets", "dtick": 1, "gridcolor": "rgba(32,102,96,.13)"},
        xaxis={"title": ""},
    )
    return figure


def comparison_figure(comparison: pd.DataFrame) -> go.Figure:
    """Visual comparison of normalized headline scenario metrics."""
    plotted = comparison[comparison["Metric"].isin(["Failed Assets", "Degraded Assets", "Affected Assets", "Impact Score"])]
    figure = go.Figure()
    for label, color in (("Scenario A", "#4f8cff"), ("Scenario B", "#ff657f")):
        figure.add_bar(x=plotted["Metric"], y=plotted[label], name=label, marker_color=color)
    figure.update_layout(
        barmode="group", height=370, margin={"l": 10, "r": 10, "t": 20, "b": 30},
        paper_bgcolor="#f4f8f6", plot_bgcolor="#f4f8f6",
        font={"color": "#315d59"}, legend={"orientation": "h", "y": 1.08},
        yaxis={"gridcolor": "rgba(32,102,96,.13)"},
    )
    return figure
