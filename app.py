import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="SCG Sample Dataset Demo", layout="wide")

st.title("SCG Sample Dataset Demo")
st.caption("Human-validated driving event demo for tunnel entry, turning, and uphill exit")

labels = pd.DataFrame([
    {"start_time": 0.0, "end_time": 5.0, "label": "APPROACH", "confidence": 0.93},
    {"start_time": 5.0, "end_time": 8.0, "label": "ENTRY_PEAK", "confidence": 0.91},
    {"start_time": 8.0, "end_time": 15.0, "label": "TURNING", "confidence": 0.95},
    {"start_time": 15.0, "end_time": 21.0, "label": "UPHILL_EXIT", "confidence": 0.92},
])

signals = pd.DataFrame({
    "time_sec": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
    "speed_kmh": [44, 44, 45, 46, 46, 46, 46, 47, 47, 46, 47, 47, 46, 46, 46, 46, 46, 46, 45.5, 56.0, 53.1, 57.9],
    "yaw_proxy_deg_s": [0, 0, 0, 0, 0, 0, 0, 0, 0.5, 0.5, -0.5, -0.5, 0, 0, 0, 0, -0.5, -0.5, 0.5, 0, -1.0, -0.2],
    "throttle_pct": [22.0, 22.0, 21.0, 19.5, 19.5, 16.5, 17.8, 17.8, 17.5, 17.5, 18.8, 18.8, 14.5, 14.5, 18.5, 15.2, 15.2, 19.4, 19.4, 14.4, 16.0, 16.5],
    "accel_mps2": [0.0, 0.0, 0.2, 0.4, 0.0, 0.0, 0.0, 0.3, 0.0, -0.4, 0.5, 0.0, -0.3, 0.0, 0.0, 0.0, -0.2, -0.2, 0.3, -0.8, -0.5, 0.4],
})

def get_label(t: float):
    row = labels[(labels["start_time"] <= t) & (labels["end_time"] >= t)]
    if row.empty:
        return "OUTSIDE_EVENT", 0.0
    return row.iloc[0]["label"], float(row.iloc[0]["confidence"])

def explain(label: str):
    mapping = {
        "APPROACH": "Vehicle maintains momentum before tunnel entry.",
        "ENTRY_PEAK": "Peak speed occurs near tunnel entry.",
        "TURNING": "Vehicle enters tunnel curve and speed is slightly suppressed by curvature.",
        "UPHILL_EXIT": "Vehicle exits the tunnel and speed response is affected by uphill load.",
        "OUTSIDE_EVENT": "No labeled event at the selected time.",
    }
    return mapping.get(label, "No description available.")

def chart(col: str, title: str, t_now: float):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=signals["time_sec"], y=signals[col], mode="lines", name=col))
    fig.add_vline(x=t_now, line_width=2, line_dash="dash")
    for _, r in labels.iterrows():
        fig.add_vrect(x0=r["start_time"], x1=r["end_time"], opacity=0.08, line_width=0)
    fig.update_layout(
        title=title,
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )
    return fig

with st.sidebar:
    st.header("Control")
    current_t = st.slider(
        "Current time (sec)",
        min_value=float(signals["time_sec"].min()),
        max_value=float(signals["time_sec"].max()),
        value=float(signals["time_sec"].min()),
        step=0.1,
    )

label, conf = get_label(current_t)
row = signals.iloc[(signals["time_sec"] - current_t).abs().argmin()]

left, right = st.columns([1.0, 1.1], gap="large")

with left:
    st.subheader("Event Summary")
    st.markdown(f"**Current phase:** `{label}`")
    st.progress(min(int(conf * 100), 100), text=f"Confidence {conf:.0%}")
    st.info(explain(label))

    st.subheader("Selected point")
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    c1.metric("Speed", f'{row["speed_kmh"]:.1f} km/h')
    c2.metric("Throttle", f'{row["throttle_pct"]:.1f} %')
    c3.metric("Yaw Proxy", f'{row["yaw_proxy_deg_s"]:.2f} deg/s')
    c4.metric("Acceleration", f'{row["accel_mps2"]:.2f} m/s²')

    st.subheader("Phase Labels")
    st.dataframe(labels, use_container_width=True, hide_index=True)

with right:
    st.subheader("Signals")
    st.plotly_chart(chart("speed_kmh", "Speed vs Time", current_t), use_container_width=True)
    st.plotly_chart(chart("yaw_proxy_deg_s", "Yaw Proxy vs Time", current_t), use_container_width=True)
    st.plotly_chart(chart("throttle_pct", "Throttle vs Time", current_t), use_container_width=True)
    st.plotly_chart(chart("accel_mps2", "Acceleration vs Time", current_t), use_container_width=True)

st.markdown("---")
st.subheader("Human-validated interpretation")
st.write(
    """
This demo reflects a manually interpreted event sequence:
approach to tunnel entry, peak speed near entry, turning inside the tunnel,
and uphill exit with constrained speed recovery.
"""
)