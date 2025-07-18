import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import skew

st.set_page_config(page_title="HosierRisk: RMS-style Florida CAT Risk Assessor", layout="centered")
st.title("❄️ TubbySnowPlow: RMS-style CAT Reinsurance Simulator")

with st.expander("📘 What Does RMS Typically Require?"):
    st.markdown("""
    RMS exposure inputs often include:
    - **Latitude / Longitude**: To geocode location and hazard risk
    - **Building, Contents, BI Value**: To simulate total exposure
    - **Occupancy, Construction, Year Built**: To inform vulnerability
    - **Limits, Deductibles, Attachment Points**: For treaty simulation
    - **Exposure Value, Event Loss Table (ELT)**: For risk layers and probabilistic modeling
    - **Standard Deviation**: Key metric for understanding volatility and risk pricing
    - **Thousands of years of simulated events** using real hazard + vulnerability data

    TubbySnowPlow mimics this by allowing:
    1. A full simulated exposure-based input
    2. A simple loss set upload
    3. Internal 10,000-year Florida-wide gamma-based loss generation
    """)

st.header("⚙️ Choose Input Method")
input_mode = st.radio("Select input type:", ["Upload RMS-style CSV", "Use built-in simulation for Florida-wide events"])

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
    st.subheader("📍 Florida-Wide Built-in Simulation")
    st.caption("Simulating 10,000 years of hurricane-related losses across all of Florida")
    losses = np.random.gamma(shape=2.0, scale=1.1e7, size=10000)

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
    payout_probability = (layer_losses > 0).sum() / len(layer_losses)
    el_ratio = (el / limit) * 100
    exposure_value = limit + attachment
    loss_cost = (el / exposure_value) * 10000
    max_loss = layer_losses.max()
    skewness = skew(layer_losses)
    p95 = np.percentile(layer_losses, 95)
    p99 = np.percentile(layer_losses, 99)

    st.header("📊 RMS-style Treaty Metrics")
    st.metric("Expected Loss (EL)", f"${el:,.2f}")
    st.metric("Suggested Premium", f"${el * 1.55:,.2f}")
    st.metric("Chance of Payout in Year", f"{payout_probability*100:.1f}%")
    st.metric("EL / Limit %", f"{el_ratio:.2f}%")
    st.metric("AAL (Annual Avg Loss)", f"${el:,.2f}")
    st.metric("Standard Deviation", f"${std_dev:,.2f}")
    st.metric("Coefficient of Variation", f"{cv:.2f}")
    st.metric("Total Exposure Value", f"${exposure_value:,.2f}")
    st.metric("Loss Cost per $100 Exposure", f"${loss_cost:.2f}")
    st.metric("Skewness", f"{skewness:.2f}")
    st.metric("Maximum Simulated Loss", f"${max_loss:,.2f}")
    st.metric("95th Percentile Loss", f"${p95:,.2f}")
    st.metric("99th Percentile Loss", f"${p99:,.2f}")

    elt_df = pd.DataFrame({'Year': np.arange(1, len(layer_losses)+1), 'Loss': layer_losses})
    st.download_button("📁 Download Event Loss Table (ELT)", elt_df.to_csv(index=False), file_name="ELT.csv")

    if st.checkbox("📈 Generate EP Curve from simulation"):
        sorted_losses = np.sort(layer_losses)[::-1]
        return_periods = [1 / ((i + 1) / len(layer_losses)) for i in range(len(layer_losses))]
        loss_1_in_200 = sorted_losses[int(len(sorted_losses) * (1 / 200))] if len(sorted_losses) >= 200 else None
        ep_curve_df = pd.DataFrame({
            'Return Period (Years)': return_periods,
            'Loss (USD)': sorted_losses
        })
        if loss_1_in_200:
            st.metric("1-in-200 Year Loss", f"${loss_1_in_200:,.2f}")
        st.line_chart(ep_curve_df.set_index("Return Period (Years)"))
else:
    st.info("Please upload a file or run a built-in simulation to begin analysis.")

st.caption("❄️ TubbySnowPlow: RMS-style insights powered by open data and custom analytics.")

