from pathlib import Path
import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

BASE = Path(__file__).resolve().parent
SIGNALS_CSV = BASE / "sample_dataset_v3_signals.csv"
LABELS_CSV = BASE / "sample_dataset_v3_labels.csv"
METRICS_JSON = BASE / "sample_dataset_v3_metrics.json"
VIDEO_PATH = BASE / "sample_dataset_v3_event_overlay_web.mp4"

st.set_page_config(page_title="SCG Sample Dataset v3", layout="wide")

signals = pd.read_csv(SIGNALS_CSV)
labels = pd.read_csv(LABELS_CSV)
metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))

def get_label(t):
    row = labels[(labels["start_time"] <= t) & (labels["end_time"] >= t)]
    if row.empty:
        return "OUTSIDE_EVENT", 0.0
    return row.iloc[0]["label"], float(row.iloc[0]["confidence"])

def explain(label):
    mapping = {
        "APPROACH": "Vehicle maintains momentum before tunnel entry.",
        "ENTRY_PEAK": "Peak speed occurs near tunnel entry.",
        "TURNING": "Speed is suppressed by tunnel curvature and spatial compression.",
        "UPHILL_EXIT": "Speed remains suppressed after the curve due to uphill load.",
        "TRAFFIC_CONSTRAINT": "Forward traffic further limits speed recovery.",
    }
    return mapping.get(label, "Outside event.")

def chart(col, title, t_now):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=signals["time_sec"], y=signals[col], mode="lines"))
    fig.add_vline(x=t_now, line_width=2, line_dash="dash")
    for _, r in labels.iterrows():
        fig.add_vrect(x0=r["start_time"], x1=r["end_time"], opacity=0.08, line_width=0)
    fig.update_layout(title=title, height=220, margin=dict(l=20, r=20, t=35, b=20), showlegend=False)
    return fig

st.title("SCG Sample Dataset v3")
st.caption("World-class sample with human-validated event sections and video overlay labels")

with st.sidebar:
    current_t = st.slider(
        "Current time (sec)",
        float(signals["time_sec"].min()),
        float(signals["time_sec"].max()),
        float(signals["time_sec"].min()),
        0.1
    )
    st.write(metrics["event_name"])

label, conf = get_label(current_t)

left, right = st.columns([1.0, 1.1], gap="large")

with left:
    st.subheader("Labeled Event Video")
    if VIDEO_PATH.exists():
        st.video(VIDEO_PATH.read_bytes())
    else:
        st.warning("Video file not found")

    st.markdown(f"**Current phase:** `{label}`")
    st.progress(min(int(conf * 100), 100), text=f"Confidence {conf:.0%}")
    st.info(explain(label))

    row = signals.iloc[(signals["time_sec"] - current_t).abs().argmin()]
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    c1.metric("Speed", f'{row["speed_kmh"]:.1f} km/h')
    c2.metric("Throttle", f'{row["throttle_pct"]:.1f} %')
    c3.metric("Yaw Proxy", f'{row["yaw_proxy_deg_s"]:.2f} deg/s')
    c4.metric("Accel", f'{row["accel_mps2"]:.2f} m/s²')

with right:
    st.subheader("Signals")
    st.plotly_chart(chart("speed_kmh", "Speed vs Time", current_t), use_container_width=True)
    st.plotly_chart(chart("yaw_proxy_deg_s", "Yaw Proxy vs Time", current_t), use_container_width=True)
    st.plotly_chart(chart("throttle_pct", "Throttle vs Time", current_t), use_container_width=True)
    st.plotly_chart(chart("accel_mps2", "Acceleration vs Time", current_t), use_container_width=True)

st.markdown("---")
st.subheader("Phase Labels")
st.dataframe(labels, use_container_width=True)
