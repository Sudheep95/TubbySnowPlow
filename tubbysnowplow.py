import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="HosierRisk: RMS-style Florida CAT Risk Assessor", layout="centered")
st.title("❄️ TubbySnowPlow: RMS-style CAT Reinsurance Simulator")

with st.expander("📘 What Does RMS Typically Require?"):
    st.markdown("""
    RMS exposure inputs often include:
    - **Latitude / Longitude**: To geocode location and hazard risk
    - **Building, Contents, BI Value**: To simulate total exposure
    - **Occupancy, Construction, Year Built**: To inform vulnerability
    - **Limits, Deductibles, Attachment Points**: For treaty simulation
    - **1000s of years of simulated events** using real hazard + vulnerability data

    TubbySnowPlow mimics this by allowing:
    1. A full simulated exposure-based input
    2. A simple loss set upload
    3. Internal 10,000-year gamma-based loss generation
    """)

st.header("⚙️ Choose Input Method")
input_mode = st.radio("Select input type:", ["Upload RMS-style CSV", "Use built-in simulation"])

losses = None
if input_mode == "Upload RMS-style CSV":
    uploaded_file = st.file_uploader("Upload CSV with simulated annual losses (one value per year)", type=["csv"])
    if uploaded_file:
        try:
            data = pd.read_csv(uploaded_file, header=None)
            losses = data.iloc[:, 0].dropna().values
        except Exception as e:
            st.error(f"Failed to process file: {e}")
else:
    st.subheader("📍 Built-in Simulation Parameters")
    zone = st.selectbox("Select Florida Zone:", [
        "South Florida (Zone A)", "Central Florida (Zone B)", "North Florida (Zone C)"
    ])
    zone_loss_map = {
        "South Florida (Zone A)": np.random.gamma(shape=2.2, scale=1.2e7, size=10000),
        "Central Florida (Zone B)": np.random.gamma(shape=1.8, scale=1.0e7, size=10000),
        "North Florida (Zone C)": np.random.gamma(shape=1.5, scale=8.0e6, size=10000),
    }
    losses = zone_loss_map[zone]

if losses is not None:
    st.header("📝 Treaty Submission")
    limit = st.number_input("Limit (USD)", value=50000000, step=1000000)
    attachment = st.number_input("Attachment Point (USD)", value=20000000, step=1000000)
    deductible = st.number_input("Deductible (USD, applied before attachment)", value=0, step=100000)

    gross_losses = np.maximum(losses - deductible, 0)
    layer_losses = np.clip(gross_losses - attachment, 0, limit)
    el = layer_losses.mean()
    std_dev = layer_losses.std()
    cv = std_dev / el if el != 0 else np.nan

    sorted_losses = np.sort(layer_losses)[::-1]
    return_periods = [1 / ((i + 1) / len(layer_losses)) for i in range(len(layer_losses))]
    loss_1_in_200 = sorted_losses[int(len(sorted_losses) * (1 / 200))] if len(sorted_losses) >= 200 else None

    suggested_premium = el * 1.55
    payout_probability = (layer_losses > 0).sum() / len(layer_losses)
    el_ratio = (el / limit) * 100

    ep_curve_df = pd.DataFrame({
        'Return Period (Years)': return_periods,
        'Loss (USD)': sorted_losses
    })

    st.header("📊 RMS-style Treaty Metrics")
    st.metric("Expected Loss (EL)", f"${el:,.2f}")
    st.metric("Suggested Premium", f"${suggested_premium:,.2f}")
    st.metric("Chance of Payout in Year", f"{payout_probability*100:.1f}%")
    st.metric("EL / Limit %", f"{el_ratio:.2f}%")
    st.metric("AAL (Annual Avg Loss)", f"${el:,.2f}")
    st.metric("Standard Deviation", f"${std_dev:,.2f}")
    st.metric("Coefficient of Variation", f"{cv:.2f}")
    if loss_1_in_200:
        st.metric("1-in-200 Year Loss", f"${loss_1_in_200:,.2f}")
    else:
        st.warning("1-in-200 loss not available (need ≥ 200 years)")

    st.header("📈 EP Curve Visualization")
    st.line_chart(ep_curve_df.set_index("Return Period (Years)"))

    if input_mode == "Use built-in simulation" and zone == "South Florida (Zone A)":
        st.warning("⚠️ High-risk zone: historically severe storms")

    st.header("📈 Historical Comparison (2023–2024 Events)")
    history_df = pd.DataFrame({
        "Event": ["Hurricane Ian (2022)", "Hurricane Michael (2018)"],
        "Avg Claims Paid (USD)": [1.095e8, 1.84e8],
        "Zone Impacted": ["South", "Central"]
    })
    st.dataframe(history_df, use_container_width=True)
else:
    st.info("Please upload a file or run a built-in simulation to begin analysis.")

st.caption("❄️ TubbySnowPlow: RMS-style insights powered by open data and custom analytics.")
