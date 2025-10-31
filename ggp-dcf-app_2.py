import streamlit as st
import pandas as pd

st.set_page_config(page_title="GGP 10-Year DCF", layout="wide")

st.title("Greatland Gold – 10-Year DCF Model")
st.write("Updated for 10-year horizon and A$750m cash balance.")

# ------------- SIDEBAR INPUTS -------------
st.sidebar.header("Key assumptions")

# Core operating assumptions (from 2025 report baseline)
production_y1 = st.sidebar.number_input(
    "Year 1 production (oz)", min_value=100000, max_value=1000000, value=285000, step=5000
)
production_growth = st.sidebar.number_input(
    "Annual production growth (%) for years 2–5", min_value=0.0, max_value=10.0, value=2.0, step=0.5
) / 100.0

gold_price_aud = st.sidebar.number_input(
    "Gold price (A$/oz)", min_value=2000, max_value=8000, value=4800, step=50
)

aisc_y1 = st.sidebar.number_input(
    "Year 1 AISC (A$/oz)", min_value=1500, max_value=4000, value=2600, step=50
)
aisc_improvement = st.sidebar.number_input(
    "AISC improvement per year (A$)", min_value=0, max_value=500, value=50, step=10
)

corp_costs = st.sidebar.number_input(
    "Corporate/overhead (A$ per year)", min_value=0, max_value=500_000_000, value=120_000_000, step=5_000_000
)

# Capex profile – we make Y1 high, then decline to steady state
capex_y1 = st.sidebar.number_input(
    "Year 1 growth/development capex (A$)", min_value=0, max_value=1_000_000_000, value=368_000_000, step=10_000_000
)
capex_decline_to = st.sidebar.number_input(
    "Steady-state capex from Year 5 (A$)", min_value=0, max_value=1_000_000_000, value=150_000_000, step=10_000_000
)

# Financial assumptions
wacc = st.sidebar.slider("Discount rate (WACC %)", min_value=5.0, max_value=15.0, value=10.0, step=0.5) / 100.0
terminal_multiple = st.sidebar.slider("Terminal multiple (× final-year FCF)", min_value=2.0, max_value=8.0, value=4.0, step=0.5)

# Balance sheet
cash_balance = st.sidebar.number_input(
    "Cash on hand (A$)", min_value=0, max_value=2_000_000_000, value=750_000_000, step=25_000_000
)
deferred_liability = st.sidebar.number_input(
    "Deferred / other liability to subtract (A$)", min_value=0, max_value=1_000_000_000, value=115_000_000, step=5_000_000
)

# Capital structure
shares_out = st.sidebar.number_input(
    "Shares outstanding", min_value=1_000_000, max_value=5_000_000_000, value=670_700_000, step=1_000_000
)

# FX for display
aud_to_gbp = st.sidebar.number_input(
    "AUD → GBP (for display only)", min_value=0.3, max_value=1.0, value=0.52, step=0.01
)

# ------------- CORE MODEL -------------
years = list(range(1, 11))  # 10-year DCF
productions = []
aiscs = []
capexes = []
fcfs = []
pvs = []

prod = production_y1
aisc = aisc_y1
capex = capex_y1

for year in years:
    # production path
    if year == 1:
        prod = production_y1
    elif year <= 5:
        # grow for the first five years
        prod = productions[-1] * (1 + production_growth)
    else:
        # flat after year 5
        prod = productions[-1]

    productions.append(prod)

    # AISC path
    if year == 1:
        aisc = aisc_y1
    elif year <= 5:
        aisc = max(aiscs[-1] - aisc_improvement, 1600)  # floor to avoid negative
    else:
        aisc = aiscs[-1]  # flat
    aiscs.append(aisc)

    # capex path
    if year == 1:
        capex = capex_y1
    elif year <= 4:
        # linearly move toward steady-state
        # e.g. 368 -> ... -> 150
        # simple approach: drop 25% of the gap each year for years 2-4
        gap = capexes[0] - capex_decline_to
        capex = capexes[-1] - 0.33 * gap if gap > 0 else capex_decline_to
        if capex < capex_decline_to:
            capex = capex_decline_to
    else:
        capex = capex_decline_to
    capexes.append(capex)

    # operating cash flow
    margin_per_oz = gold_price_aud - aisc
    operating_cf = margin_per_oz * prod
    fcf = operating_cf - corp_costs - capex
    fcfs.append(fcf)

# Discount FCFs and add terminal value
for i, year in enumerate(years, start=1):
    fcf = fcfs[i - 1]
    if year == 10:
        tv = fcfs[-1] * terminal_multiple
        total_in_year = fcf + tv
    else:
        total_in_year = fcf

    pv = total_in_year / ((1 + wacc) ** year)
    pvs.append(pv)

enterprise_value = sum(pvs)

# Equity value = EV + cash – deferred
equity_value = enterprise_value + cash_balance - deferred_liability
value_per_share_aud = equity_value / shares_out
value_per_share_gbp = value_per_share_aud * aud_to_gbp

# ------------- DISPLAY -------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Enterprise value (A$)", f"{enterprise_value:,.0f}")
col2.metric("Equity value (A$)", f"{equity_value:,.0f}")
col3.metric("Value per share (A$)", f"{value_per_share_aud:,.2f}")
col4.metric("Value per share (GBP)", f"£{value_per_share_gbp:,.2f}")

st.subheader("10-Year cash-flow forecast")

df = pd.DataFrame({
    "Year": years,
    "Production (oz)": [round(x) for x in productions],
    "Gold price (A$/oz)": [gold_price_aud for _ in years],
    "AISC (A$/oz)": [round(x) for x in aiscs],
    "Growth/Dev Capex (A$)": [round(x) for x in capexes],
    "FCF (A$)": [round(x) for x in fcfs],
    "Discounted FCF (A$)": [round(x) for x in pvs],
})
st.dataframe(df.style.format("{:,.0f}"))

st.subheader("Discounted FCF profile")
st.line_chart(df.set_index("Year")["Discounted FCF (A$)"])

st.caption(
    "Defaults based on FY25 report: 285koz Y1, A$2,600/oz AISC, A$368m capex in Y1, "
    "A$750m cash, A$115m deferred liability, 670.7m shares."
)
