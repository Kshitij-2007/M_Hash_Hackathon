"""CityResilience Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.criticality import analyze_criticality, compare_scenarios
from src.metrics import asset_impact_frame, calculate_metrics
from src.network import create_infrastructure_network, network_summary
from src.simulation import simulate_cascade
from src.visualization import comparison_figure, network_figure, sector_impact_figure, utilization_figure


st.set_page_config(
    page_title="CityResilience | Cascade Simulator",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --teal:#064744; --teal-deep:#033b39; --mint:#dfeae7; --paper:#f4f8f6; --ink:#073f3d; --muted:#58716f; }
    html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    .stApp {
      background:
        radial-gradient(circle at 93% 7%, rgba(94,190,177,.20), transparent 23rem),
        radial-gradient(circle at 2% 72%, rgba(15,94,88,.10), transparent 27rem),
        #e8f0ee;
      color:var(--ink);
    }
    [data-testid="stHeader"] { background:transparent; }
    .block-container { padding-top:1.3rem; padding-bottom:3.2rem; max-width:1480px; }
    [data-testid="stSidebar"] { background:#dce8e5; border-right:0; box-shadow:10px 0 35px rgba(4,55,52,.08); }
    [data-testid="stSidebar"] > div:first-child { padding-top:1.6rem; }
    [data-testid="stSidebar"] hr { border-color:rgba(4,71,68,.18); }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5 { color:#174f4c !important; }
    .brand { display:flex; align-items:center; gap:.75rem; margin-bottom:.2rem; }
    .brand-mark { width:38px; height:38px; display:grid; place-items:center; border:1px solid #0b5c57;
      border-radius:50% 50% 45% 55%; color:#eaf4f1; background:var(--teal); font-size:.72rem; font-weight:800;
      box-shadow:0 7px 14px rgba(5,70,67,.18); }
    .brand-name { color:#064744; font-size:1.12rem; letter-spacing:.14em; font-weight:800; }
    .susun-nav { min-height:54px; display:flex; align-items:center; gap:clamp(.75rem,3vw,2.8rem); padding:.45rem .65rem .45rem 1.3rem;
      border-radius:999px; color:#dbe9e6; background:var(--teal); box-shadow:0 12px 25px rgba(4,55,52,.18); margin-bottom:1rem; }
    .susun-nav .nav-brand { font-weight:850; color:white; letter-spacing:.12em; margin-right:auto; }
    .susun-nav .nav-link { font-size:.72rem; letter-spacing:.08em; white-space:nowrap; }
    .susun-nav .active { border-bottom:1px solid #e4f2ef; padding-bottom:.18rem; color:white; }
    .susun-nav .nav-avatar { background:#edf4f2; color:var(--teal); padding:.66rem 1rem; border-radius:999px;
      font-weight:800; font-size:.7rem; letter-spacing:.08em; }
    .hero { position:relative; display:grid; grid-template-columns:minmax(0,1.25fr) minmax(280px,.75fr); gap:2rem;
      align-items:center; min-height:310px; background:var(--teal); padding:2.2rem 2.35rem; border-radius:28px 78px 28px 28px;
      box-shadow:0 20px 35px rgba(4,55,52,.20); overflow:hidden; margin-bottom:1.25rem; }
    .hero:before { content:""; position:absolute; width:240px; height:240px; right:24%; bottom:-165px; border:1px solid rgba(224,240,236,.55);
      border-radius:48px 48px 0 0; }
    .hero:after { content:"+"; position:absolute; left:-14px; top:74px; display:grid; place-items:center; width:46px; height:46px;
      color:#eaf5f2; background:#0a5a55; border:7px solid #e8f0ee; border-radius:50%; font-size:1.5rem; font-weight:500; }
    .hero-copy { position:relative; z-index:1; }
    .outline-chip { display:inline-block; border:1px solid rgba(231,244,240,.72); color:#e8f3f0; border-radius:11px;
      padding:.48rem 1rem; font-size:.66rem; letter-spacing:.13em; margin-bottom:1.05rem; }
    .hero h1 { color:#eaf4f1 !important; font-family:"Arial Narrow",Impact,sans-serif; font-stretch:condensed; font-size:clamp(3.25rem,7vw,6.3rem);
      line-height:.76; letter-spacing:.01em; margin:.1rem 0 1rem; font-weight:600; }
    .hero h1 span { color:#8fd2c9; }
    .hero-copy p { color:#b9d3ce; max-width:590px; margin:0; font-size:.94rem; }
    .hero-note { position:relative; z-index:2; background:#e7efed; color:#174c49; padding:1.7rem 1.7rem 1.5rem;
      border-radius:28px 28px 28px 8px; box-shadow:13px 14px 0 rgba(3,53,50,.35); }
    .hero-note h3 { color:#0b4b48 !important; margin:0 0 .7rem; font-size:1.35rem; }
    .hero-note p { color:#456864; margin:0 0 1rem; line-height:1.45; font-size:.86rem; }
    .hero-arrow { margin-left:auto; width:44px; height:44px; display:grid; place-items:center; color:#edf5f3; background:var(--teal);
      border-radius:9px; font-size:1.5rem; box-shadow:4px 5px 0 #aac7c2; }
    [data-testid="stMetric"] { background:#f4f8f6; border:1px solid rgba(4,71,68,.12); border-radius:15px 28px 15px 15px;
      padding:1.05rem 1.15rem; min-height:112px; box-shadow:9px 11px 20px rgba(5,64,60,.12); }
    [data-testid="stMetricLabel"] { color:#5e7975; text-transform:uppercase; letter-spacing:.09em; font-size:.68rem; }
    [data-testid="stMetricValue"] { color:#064744; font-weight:800; }
    [data-testid="stTabs"] [role="tablist"] { background:var(--teal); padding:.48rem; gap:.3rem; border-radius:999px;
      box-shadow:0 10px 20px rgba(4,55,52,.16); }
    [data-testid="stTabs"] button { color:#c2d8d4; border-radius:999px; padding:.45rem 1rem; }
    [data-testid="stTabs"] button[aria-selected="true"] { color:#064744 !important; background:#e8f0ee; }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] { display:none; }
    [data-testid="stTabs"] [data-baseweb="tab-border"] { display:none; }
    [data-testid="stButton"] button { background:var(--teal) !important; color:#eef7f4 !important; border:0 !important;
      border-radius:999px !important; min-height:2.65rem; font-weight:750; letter-spacing:.04em; box-shadow:0 8px 15px rgba(4,55,52,.14); }
    [data-testid="stButton"] button:hover { background:#09605b !important; transform:translateY(-1px); }
    [data-testid="stSelectbox"] > div > div, [data-testid="stSlider"] { color:var(--ink); }
    div[data-testid="stVerticalBlockBorderWrapper"] { background:#f3f7f5; border-color:rgba(4,71,68,.16); border-radius:20px 32px 20px 20px;
      box-shadow:7px 9px 17px rgba(5,64,60,.09); }
    [data-testid="stPlotlyChart"] { border-radius:24px 46px 24px 24px; overflow:hidden; box-shadow:10px 13px 24px rgba(5,64,60,.14); }
    [data-testid="stDataFrame"] { border:1px solid rgba(4,71,68,.15); border-radius:20px; overflow:hidden; box-shadow:7px 9px 18px rgba(5,64,60,.10); }
    .section-kicker { color:#15746d; font-size:.7rem; text-transform:uppercase; letter-spacing:.16em; font-weight:800; margin-top:1.15rem; }
    .section-title { color:#064744; font-size:1.3rem; font-weight:800; margin:.12rem 0 .75rem; }
    .timeline-round { color:#0a6962; font-size:.7rem; letter-spacing:.12em; font-weight:800; text-transform:uppercase; }
    .timeline-event { color:#345e5a; padding:.18rem 0; }
    .method-note { border-left:4px solid #0b5e58; padding:1rem 1.1rem; background:#dbe9e6; color:#315d59; border-radius:0 18px 18px 0; }
    .stAlert { border-radius:18px 30px 18px 18px; }
    h1,h2,h3,h4 { color:#073f3d !important; }
    p, label, [data-testid="stCaptionContainer"] { color:#536f6b; }
    @media (max-width:900px) {
      .susun-nav .nav-link { display:none; }
      .hero { grid-template-columns:1fr; padding:1.8rem; border-radius:24px 52px 24px 24px; }
      .hero h1 { font-size:4.2rem; }
      .hero-note { max-width:520px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_base_graph():
    return create_infrastructure_network()


@st.cache_data(show_spinner=False)
def get_criticality_table() -> pd.DataFrame:
    return analyze_criticality(create_infrastructure_network())


base_graph = get_base_graph()
summary = network_summary(base_graph)
name_by_id = {node_id: data["name"] for node_id, data in base_graph.nodes(data=True)}

if "result" not in st.session_state:
    st.session_state.result = None
if "comparison" not in st.session_state:
    st.session_state.comparison = None


with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark">CR</div><div class="brand-name">CITYRESILIENCE</div></div>',
        unsafe_allow_html=True,
    )
    st.caption("Infrastructure intelligence console")
    st.divider()
    st.markdown("#### Simulation controls")
    sectors = ["All sectors"] + list(summary["sectors"])
    selected_sector = st.selectbox("Infrastructure sector", sectors)
    eligible = [
        node_id for node_id, data in base_graph.nodes(data=True)
        if selected_sector == "All sectors" or data["sector"] == selected_sector
    ]
    eligible.sort(key=lambda node_id: name_by_id[node_id])
    default_index = eligible.index("BRIDGE_A") if "BRIDGE_A" in eligible else 0
    selected_asset = st.selectbox(
        "Asset to fail", eligible, index=default_index,
        format_func=lambda node_id: name_by_id[node_id],
    )
    severity = st.slider(
        "Failure severity", min_value=0.25, max_value=1.0, value=1.0, step=0.05,
        help="Share of the failed asset's active load pushed onto connected infrastructure.",
    )
    run_simulation = st.button("SIMULATE FAILURE", type="primary", width="stretch")
    reset_network = st.button("Reset network", width="stretch")
    if run_simulation:
        with st.spinner("Propagating displaced load…"):
            st.session_state.result = simulate_cascade(base_graph, selected_asset, severity=severity)
    if reset_network:
        st.session_state.result = None
        st.session_state.comparison = None
        st.rerun()

    st.divider()
    st.markdown("##### Status legend")
    st.markdown("🟢 &nbsp; Healthy &nbsp;&nbsp; 🟠 &nbsp; Degraded &nbsp;&nbsp; 🔴 &nbsp; Failed")
    st.caption("Shapes: ⬢ Power  ·  ● Transport  ·  ◆ Water  ·  ■ Healthcare")
    st.divider()
    st.caption(f"Synthetic network · {summary['nodes']} assets · {summary['edges']} dependencies")
    st.caption("Proof of concept · Not an operational forecast")


st.markdown(
    """
    <div class="susun-nav">
      <span class="nav-brand">CITYRESILIENCE</span>
      <span class="nav-link active">NETWORK</span>
      <span class="nav-link">CASCADE</span>
      <span class="nav-link">ANALYSIS</span>
      <span class="nav-link">SCENARIOS</span>
      <span class="nav-avatar">RESILIENCE LAB</span>
    </div>
    <div class="hero">
      <div class="hero-copy">
        <div class="outline-chip">URBAN SYSTEMS / INTERDEPENDENCY MODEL</div>
        <h1>CASCADE<br><span>LAB</span></h1>
        <p>Network → Failure → Redistribution → Overload → Stabilization</p>
      </div>
      <div class="hero-note">
        <h3>When one failure becomes many.</h3>
        <p>Explore how disruption moves through transportation, power, water, and healthcare—then find where intervention matters most.</p>
        <div class="hero-arrow">→</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

result = st.session_state.result
metrics = calculate_metrics(result) if result else None
cards = st.columns(4)
cards[0].metric("Cascade depth", metrics["cascade_depth"] if metrics else "—")
cards[1].metric("Affected assets", metrics["affected_assets"] if metrics else "0")
cards[2].metric("Failed assets", metrics["failed_assets"] if metrics else "0")
cards[3].metric("Impact score", f"{metrics['impact_score']:.0f}%" if metrics else "0%")

live_tab, critical_tab, compare_tab, method_tab = st.tabs(
    ["◉ LIVE SIMULATION", "◈ CRITICAL ASSETS", "⇄ SCENARIO COMPARISON", "◎ MODEL NOTES"]
)

with live_tab:
    shown_graph = result["graph"] if result else base_graph
    st.markdown('<div class="section-kicker">Network state</div>', unsafe_allow_html=True)
    title = "Post-cascade infrastructure map" if result else "Healthy infrastructure baseline"
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.plotly_chart(
        network_figure(shown_graph), width="stretch", config={"displayModeBar": False}, key="live_network"
    )

    if not result:
        st.info("Select an asset in the sidebar and click **SIMULATE FAILURE** to start the cascade.")
    else:
        left, right = st.columns([1, 1.55], gap="large")
        with left:
            st.markdown('<div class="section-kicker">Propagation log</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Cascade timeline</div>', unsafe_allow_html=True)
            for entry in result["rounds"]:
                label = "INITIAL SHOCK" if entry["round"] == 0 else f"ROUND {entry['round']}"
                with st.container(border=True):
                    st.markdown(f'<div class="timeline-round">{label}</div>', unsafe_allow_html=True)
                    for event in entry["events"]:
                        st.markdown(f'<div class="timeline-event">{event}</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="section-kicker">Impact analysis</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Load pressure and sector reach</div>', unsafe_allow_html=True)
            st.plotly_chart(
                utilization_figure(result), width="stretch", config={"displayModeBar": False}, key="utilization"
            )

        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            st.markdown("#### Affected assets by sector")
            st.plotly_chart(
                sector_impact_figure(result), width="stretch", config={"displayModeBar": False}, key="sector_impact"
            )
        with col_b:
            st.markdown("#### Operational summary")
            st.metric("Maximum overload", f"{metrics['maximum_overload']:.1f}%")
            st.metric("Unserved pressure", f"{metrics['unserved_load']:.1f} units")
            sectors_text = ", ".join(metrics["affected_sectors"]) or "None"
            st.markdown(f"**Affected sectors:** {sectors_text}")
            impact = asset_impact_frame(result)
            visible = impact[impact["Affected"]][["Asset", "Sector", "Status", "Peak utilization"]]
            st.dataframe(
                visible.sort_values("Peak utilization", ascending=False),
                hide_index=True, width="stretch",
                column_config={"Peak utilization": st.column_config.NumberColumn(format="%.1f%%")},
            )

with critical_tab:
    st.markdown('<div class="section-kicker">Simulation-based screening</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Simulated Criticality Analysis</div>', unsafe_allow_html=True)
    st.caption(
        "Each asset is failed once at 100% severity. Rankings compare synthetic cascade outcomes; "
        "they are not scientifically validated risk scores."
    )
    with st.spinner("Running one failure simulation per asset…"):
        criticality = get_criticality_table()
    top = criticality.iloc[0]
    top_cols = st.columns(3)
    top_cols[0].metric("Highest-impact asset", top["Asset"])
    top_cols[1].metric("Simulated impact", f"{top['Impact Score']:.1f}%")
    top_cols[2].metric("Failures triggered", int(top["Failed Assets"]))
    st.dataframe(
        criticality, hide_index=True, width="stretch", height=610,
        column_config={
            "Impact Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100),
            "Excess Load": st.column_config.NumberColumn(format="%.1f"),
        },
    )

with compare_tab:
    st.markdown('<div class="section-kicker">Alternative futures</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Two-scenario comparison</div>', unsafe_allow_html=True)
    compare_left, compare_right = st.columns(2)
    all_nodes = sorted(name_by_id, key=name_by_id.get)
    with compare_left:
        scenario_a = st.selectbox(
            "Scenario A failure", all_nodes, index=all_nodes.index("BRIDGE_A"),
            format_func=lambda node_id: name_by_id[node_id], key="scenario_a",
        )
    with compare_right:
        scenario_b = st.selectbox(
            "Scenario B failure", all_nodes, index=all_nodes.index("SUB_C"),
            format_func=lambda node_id: name_by_id[node_id], key="scenario_b",
        )
    if st.button("COMPARE SCENARIOS", type="primary", width="stretch"):
        with st.spinner("Running both cascade scenarios…"):
            comparison, scenario_results = compare_scenarios(base_graph, scenario_a, scenario_b)
            st.session_state.comparison = {
                "table": comparison,
                "results": scenario_results,
                "asset_a": scenario_a,
                "asset_b": scenario_b,
            }

    if st.session_state.comparison:
        saved = st.session_state.comparison
        comparison = saved["table"]
        scenario_results = saved["results"]
        st.markdown(
            f"**Scenario A:** {name_by_id[saved['asset_a']]} &nbsp;&nbsp; · &nbsp;&nbsp; "
            f"**Scenario B:** {name_by_id[saved['asset_b']]}"
        )
        c1, c2 = st.columns([0.9, 1.4], gap="large")
        with c1:
            st.dataframe(comparison, hide_index=True, width="stretch")
        with c2:
            st.plotly_chart(
                comparison_figure(comparison), width="stretch", config={"displayModeBar": False}, key="comparison_bars"
            )
        map_a, map_b = st.columns(2)
        with map_a:
            st.markdown("##### Scenario A network")
            st.plotly_chart(
                network_figure(scenario_results["Scenario A"]["graph"]),
                width="stretch", config={"displayModeBar": False}, key="scenario_a_network",
            )
        with map_b:
            st.markdown("##### Scenario B network")
            st.plotly_chart(
                network_figure(scenario_results["Scenario B"]["graph"]),
                width="stretch", config={"displayModeBar": False}, key="scenario_b_network",
            )
    else:
        st.info("Choose two initial failures and run the comparison.")

with method_tab:
    st.markdown('<div class="section-kicker">Transparent by design</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">How the prototype works</div>', unsafe_allow_html=True)
    st.markdown(
        """
        1. The selected asset is marked failed and its active load is displaced.
        2. Load is divided among connected, active assets using dependency strength and rerouting friction.
        3. Assets at or above **90% utilization** are degraded; assets above **100%** fail.
        4. Newly failed assets displace 30% of their load in the next round; emergency shedding absorbs the rest.
        5. The loop stops when no new failures appear or after eight rounds.
        """
    )
    st.markdown(
        '<div class="method-note"><b>Interpretation:</b> “load” is a normalized service-pressure unit. '
        'Cross-sector links describe operational dependency pressure, not literal transfer of traffic, water, or electricity. '
        'All assets and results are synthetic and intended only for demonstrating the cascade-analysis workflow.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Impact score")
    st.write(
        "The score is a transparent heuristic combining affected/failed assets, baseline service associated with "
        "failed assets, affected-sector breadth, and cascade depth. It is not a probability or validated forecast."
    )
    st.markdown("#### Future analytical layer")
    st.write(
        "A future ML layer could train on batches of these simulated scenarios to screen for vulnerable assets or "
        "estimate cascade severity. It is intentionally not included because no validated training data or model exists."
    )
