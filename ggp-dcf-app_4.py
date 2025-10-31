import streamlit as st
import pandas as pd

st.set_page_config(page_title="GGP 10-Year DCF (£ millions)", layout="wide")

st.title("Greatland Gold – 10-Year DCF Model (£ Millions)")
st.write("All values converted from AUD to GBP (A$ ÷ 2) and shown in £ millions.")

# ── Sidebar inputs ──────────────────────────────────────────────
st.sidebar.header("Key assumptions")

production_y1 = st.sidebar.number_input("Year 1 production (oz)", 100000, 1000000, 285000, 5000)
production_growth = st.sidebar.number_input("Annual production growth % (Yrs 2–5)", 0.0, 10.0, 2.0, 0.5) / 100
gold_price_aud = st.sidebar.number_input("Gold price (A$/oz)", 2000, 8000, 4800, 50)
aisc_y1 = st.sidebar.number_input("Year 1 AISC (A$/oz)", 1500, 4000, 2600, 50)
aisc_improvement = st.sidebar.number_input("AISC improvement per yr (A$)", 0, 500, 50, 10)

corp_costs = st.sidebar.number_input("Corporate / overhead (A$/yr)", 0, 500_000_000, 120_000_000, 5_000_000)
capex_y1 = st.sidebar.number_input("Year 1 growth capex (A$)", 0, 1_000_000_000, 368_000_000, 10_000_000)
capex_decline_to = st.sidebar.number_input("Steady-state capex from Yr 5 (A$)", 0, 1_000_000_000, 150_000_000, 10_000_000)

wacc = st.sidebar.slider("Discount rate (WACC %)", 5.0, 15.0, 10.0, 0.5) / 100
terminal_multiple = st.sidebar.slider("Terminal multiple (× final FCF)", 2.0, 8.0, 4.0, 0.5)

cash_balance = st.sidebar.number_input("Cash (A$)", 0, 2_000_000_000, 750_000_000, 25_000_000)
deferred_liability = st.sidebar.number_input("Deferred liability (A$)", 0, 1_000_000_000, 115_000_000, 5_000_000)
shares_out = st.sidebar.number_input("Shares outstanding", 1_000_000, 5_000_000_000, 670_700_000, 1_000_000)

# ── Core model ─────────────────────────────────────────────────
years = list(range(1, 11))
productions, aiscs, capexes, fcfs, pvs = [], [], [], [], []

for year in years:
    if year == 1:
        prod, aisc, capex = production_y1, aisc_y1, capex_y1
    else:
        prod = productions[-1] * (1 + production_growth) if year <= 5 else productions[-1]
        aisc = max(aiscs[-1] - aisc_improvement, 1600) if year <= 5 else aiscs[-1]
        if year <= 4:
            gap = capexes[0] - capex_decline_to
            capex = capexes[-1] - 0.33 * gap if gap > 0 else capex_decline_to
            capex = max(capex, capex_decline_to)
        else:
            capex = capex_decline_to
    productions.append(prod); aiscs.append(aisc); capexes.append(capex)

    margin = gold_price_aud - aisc
    operating_cf = margin * prod
    fcf = operating_cf - corp_costs - capex
    fcfs.append(fcf)

for i, year in enumerate(years, start=1):
    fcf = fcfs[i - 1]
    total = fcf + (fcfs[-1] * terminal_multiple if year == 10 else 0)
    pv = total / ((1 + wacc) ** year)
    pvs.append(pv)

enterprise_value_aud = sum(pvs)
equity_value_aud = enterprise_value_aud + cash_balance - deferred_liability
value_per_share_aud = equity_value_aud / shares_out

# ── Convert to £ millions (A$ ÷ 2 ÷ 1,000,000) ─────────────────
def aud_to_gbp_m(x): 
    return x / 2_000_000  # A$ ÷ 2 ÷ 1,000,000 → £ millions

ev_gbp_m = aud_to_gbp_m(enterprise_value_aud)
eq_gbp_m = aud_to_gbp_m(equity_value_aud)
fcf_gbp_m = [aud_to_gbp_m(f) for f in fcfs]
pv_gbp_m = [aud_to_gbp_m(p) for p in pvs]
vps_gbp = value_per_share_aud / 2  # A$ ÷ 2 → £ per share

# ── Display results ─────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Enterprise value", f"£ {ev_gbp_m:,.0f} m")
col2.metric("Equity value", f"£ {eq_gbp_m:,.0f} m")
col3.metric("Value per share", f"£ {vps_gbp:,.2f}")

st.subheader("10-Year Cash-Flow Forecast (£ millions)")
df = pd.DataFrame({
    "Year": years,
    "Production (oz)": [round(x) for x in productions],
    "AISC (A$/oz)": [round(x) for x in aiscs],
    "Capex (£ m)": [round(aud_to_gbp_m(x), 1) for x in capexes],
    "FCF (£ m)": [round(x, 1) for x in fcf_gbp_m],
    "Discounted FCF (£ m)": [round(x, 1) for x in pv_gbp_m],
})
st.dataframe(df)

st.subheader("Discounted FCF Profile (£ m)")
st.line_chart(df.set_index("Year")["Discounted FCF (£ m)"])

st.caption("All figures converted from AUD → GBP (÷2) and displayed in £ millions.")

