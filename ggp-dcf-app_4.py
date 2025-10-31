import streamlit as st
import pandas as pd

st.set_page_config(page_title="GGP 20-Year DCF (£m)", layout="wide")

st.title("Greatland Gold – 20-Year DCF Model (£ millions)")
st.write("DCF based on production, AISC and capex assumptions. Values converted from AUD → GBP (÷2) and shown in £m.")

# ─────────────────────────────────────────
# SIDEBAR INPUTS
# ─────────────────────────────────────────
st.sidebar.header("Key assumptions")

# Ops
production_y1 = st.sidebar.number_input("Year 1 production (oz)", 100_000, 1_000_000, 285_000, 5_000)
production_growth = st.sidebar.number_input("Production growth % (years 2–5)", 0.0, 10.0, 2.0, 0.5) / 100
gold_price_aud = st.sidebar.number_input("Gold price (A$/oz)", 2_000, 8_000, 4_800, 50)
aisc_y1 = st.sidebar.number_input("Year 1 AISC (A$/oz)", 1_500, 4_000, 2_600, 50)
aisc_improvement = st.sidebar.number_input("AISC improvement per year (A$)", 0, 500, 50, 10)

# Costs
corp_costs = st.sidebar.number_input("Corporate / overhead (A$/yr)", 0, 500_000_000, 120_000_000, 5_000_000)

# Capex profile
capex_y1 = st.sidebar.number_input("Year 1 growth capex (A$)", 0, 1_000_000_000, 368_000_000, 10_000_000)
capex_decline_to = st.sidebar.number_input("Steady-state capex (from year 6) (A$)", 0, 1_000_000_000, 150_000_000, 10_000_000)

# Finance
wacc = st.sidebar.slider("Discount rate (WACC %)", 5.0, 15.0, 10.0, 0.5) / 100
terminal_multiple = st.sidebar.slider("Terminal multiple (× final FCF)", 2.0, 8.0, 4.0, 0.5)

# Balance sheet
cash_balance = st.sidebar.number_input("Cash (A$)", 0, 2_000_000_000, 750_000_000, 25_000_000)
deferred_liability = st.sidebar.number_input("Deferred liability (A$)", 0, 1_000_000_000, 115_000_000, 5_000_000)
shares_out = st.sidebar.number_input("Shares outstanding", 1_000_000, 5_000_000_000, 670_700_000, 1_000_000)

# ─────────────────────────────────────────
# CORE 20-YEAR DCF
# ─────────────────────────────────────────
years = list(range(1, 21))
productions = []
aiscs = []
capexes = []
fcfs = []
pvs = []

for year in years:
    # production: grow to yr5, flat to yr15, then -1%/yr
    if year == 1:
        prod = production_y1
    elif year <= 5:
        prod = productions[-1] * (1 + production_growth)
    elif year <= 15:
        prod = productions[-1]
    else:
        prod = productions[-1] * 0.99
    productions.append(prod)

    # AISC: improve to yr5, then flat
    if year == 1:
        aisc = aisc_y1
    elif year <= 5:
        aisc = max(aiscs[-1] - aisc_improvement, 1_600)
    else:
        aisc = aiscs[-1]
    aiscs.append(aisc)

    # capex: high early, step down to steady from yr6
    if year == 1:
        capex = capex_y1
    elif year <= 5:
        step = (capex_y1 - capex_decline_to) / 5
        capex = max(capex_y1 - step * (year - 1), capex_decline_to)
    else:
        capex = capex_decline_to
    capexes.append(capex)

    # FCF in AUD
    margin = gold_price_aud - aisc
    operating_cf = margin * prod
    fcf = operating_cf - corp_costs - capex
    fcfs.append(fcf)

# discount FCFs and add terminal value at year 20
for i, year in enumerate(years, start=1):
    fcf = fcfs[i - 1]
    if year == 20:
        total = fcf + fcfs[-1] * terminal_multiple
    else:
        total = fcf
    pv = total / ((1 + wacc) ** year)
    pvs.append(pv)

enterprise_value_aud = sum(pvs)
equity_value_aud = enterprise_value_aud + cash_balance - deferred_liability
value_per_share_aud = equity_value_aud / shares_out

# ─────────────────────────────────────────
# AUD → GBP (÷2) and to £m
# ─────────────────────────────────────────
def aud_to_gbp_m(x: float) -> float:
    # AUD → GBP ≈ ÷2, then ÷1,000,000 → £m
    return x / 2_000_000

ev_gbp_m = aud_to_gbp_m(enterprise_value_aud)
eq_gbp_m = aud_to_gbp_m(equity_value_aud)
fcf_gbp_m = [aud_to_gbp_m(f) for f in fcfs]
pv_gbp_m = [aud_to_gbp_m(p) for p in pvs]
vps_gbp = value_per_share_aud / 2  # AUD/share → GBP/share

# ─────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Enterprise value", f"£ {ev_gbp_m:,.0f} m")
col2.metric("Equity value", f"£ {eq_gbp_m:,.0f} m")
col3.metric("Value per share", f"£ {vps_gbp:,.2f}")

st.subheader("20-Year Cash-Flow Forecast (£ m)")
df = pd.DataFrame({
    "Year": years,
    "Production (oz)": [round(x) for x in productions],
    "AISC (A$/oz)": [round(x) for x in aiscs],
    "Capex (£ m)": [round(aud_to_gbp_m(x), 1) for x in capexes],
    "FCF (£ m)": [round(x, 1) for x in fcf_gbp_m],
    "Discounted FCF (£ m)": [round(x, 1) for x in pv_gbp_m],
})
st.dataframe(df)

st.subheader("Discounted FCF profile (20 yrs, £ m)")
st.line_chart(df.set_index("Year")["Discounted FCF (£ m)"])

# ─────────────────────────────────────────
# SENSITIVITY (no styling → works without matplotlib)
# ─────────────────────────────────────────
st.subheader("Valuation sensitivity – value per share (£)")

prod_options = [250_000, 300_000, 350_000, 400_000, 450_000, 500_000]
gold_options = [4_200, 4_500, 4_800, 5_200, 5_500, 6_000]

sens_rows = []
for gold_assump in gold_options:
    row = {"Gold (A$/oz)": gold_assump}
    for prod_assump in prod_options:
        # build alt 20-yr production for this combo
        alt_prods = []
        for year in years:
            if year == 1:
                alt_prods.append(prod_assump)
            elif year <= 5:
                alt_prods.append(alt_prods[-1] * (1 + production_growth))
            elif year <= 15:
                alt_prods.append(alt_prods[-1])
            else:
                alt_prods.append(alt_prods[-1] * 0.99)

        # reuse aiscs and capexes from main run
        alt_fcfs = []
        for i, year in enumerate(years):
            margin_tmp = gold_assump - aiscs[i]
            op_cf_tmp = margin_tmp * alt_prods[i]
            fcf_tmp = op_cf_tmp - corp_costs - capexes[i]
            alt_fcfs.append(fcf_tmp)

        # discount
        alt_pvs = []
        for i, year in enumerate(years, start=1):
            fcf_tmp = alt_fcfs[i - 1]
            total_tmp = fcf_tmp + (alt_fcfs[-1] * terminal_multiple if year == 20 else 0)
            pv_tmp = total_tmp / ((1 + wacc) ** year)
            alt_pvs.append(pv_tmp)

        ev_tmp_aud = sum(alt_pvs)
        eq_tmp_aud = ev_tmp_aud + cash_balance - deferred_liability
        vps_tmp_aud = eq_tmp_aud / shares_out
        vps_tmp_gbp = vps_tmp_aud / 2

        row[f"{prod_assump//1000}k oz"] = round(vps_tmp_gbp, 2)
    sens_rows.append(row)

sens_df = pd.DataFrame(sens_rows)
st.dataframe(sens_df)

st.caption(
    "Use the table above to see when the DCF gets close to £6/share. "
    "High production (450–500k oz) + high gold (A$5,500–6,000) + lower WACC in the sidebar pushes values up."
)
