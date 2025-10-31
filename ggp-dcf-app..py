import streamlit as st
import pandas as pd

st.set_page_config(page_title="GGP Valuation Model (GBP)", layout="wide")

st.title("Greatland Gold Valuation Model (DCF, in GBP)")
st.write("Adjust gold price, production, and costs to estimate GGP’s value per share in GBP.")

# --- Sidebar inputs ---
st.sidebar.header("Key assumptions (input values)")

# Production and price
production_oz = st.sidebar.number_input("Annual production (oz)", min_value=10000, max_value=1000000, value=500000, step=5000)
gold_price_usd = st.sidebar.number_input("Gold price (USD/oz)", min_value=1000, max_value=6000, value=4000, step=50)
aisc_usd = st.sidebar.number_input("AISC (USD/oz)", min_value=500, max_value=5000, value=2000, step=50)

# FX
usd_to_gbp = st.sidebar.number_input("USD → GBP exchange rate", min_value=0.4, max_value=1.0, value=0.79, step=0.01)

# Costs
corp_costs_gbp = st.sidebar.number_input("Corporate costs (£ / year)", min_value=0, max_value=1000000000, value=90_000_000, step=5_000_000)
growth_capex_gbp = st.sidebar.number_input("Growth capex (£ / year)", min_value=0, max_value=1000000000, value=150_000_000, step=10_000_000)

# DCF parameters
years = st.sidebar.slider("Forecast years", min_value=3, max_value=15, value=5)
wacc = st.sidebar.slider("Discount rate (WACC %)", min_value=5.0, max_value=15.0, value=10.0, step=0.5) / 100
terminal_multiple = st.sidebar.slider("Terminal multiple (× FCF in final year)", min_value=1.0, max_value=8.0, value=4.0, step=0.5)

# Shares
shares_out = st.sidebar.number_input("Shares outstanding", min_value=1_000_000, max_value=5_000_000_000, value=670_750_000, step=1_000_000)

# --- Core calculations ---
gold_price_gbp = gold_price_usd * usd_to_gbp
aisc_gbp = aisc_usd * usd_to_gbp
margin_per_oz = gold_price_gbp - aisc_gbp
operating_cf = margin_per_oz * production_oz
annual_fcf = operating_cf - corp_costs_gbp - growth_capex_gbp

# Build forecast table
years_list = list(range(1, years + 1))
fcf_list = []
discounted_list = []

for t in years_list:
    fcf_t = annual_fcf
    if t == years:
        tv = annual_fcf * terminal_multiple
        fcf_t_total = fcf_t + tv
    else:
        fcf_t_total = fcf_t

    pv_t = fcf_t_total / ((1 + wacc) ** t)
    fcf_list.append(fcf_t_total)
    discounted_list.append(pv_t)

equity_value_gbp = sum(discounted_list)
value_per_share_gbp = equity_value_gbp / shares_out

# --- Display main numbers ---
col1, col2, col3 = st.columns(3)
col1.metric("Gold price (£/oz)", f"£{gold_price_gbp:,.0f}")
col2.metric("Annual FCF (£)", f"£{annual_fcf:,.0f}")
col3.metric("Equity value (£)", f"£{equity_value_gbp:,.0f}")

st.metric("Value per share", f"£{value_per_share_gbp:,.2f}")

# --- Table ---
df = pd.DataFrame({
    "Year": years_list,
    "FCF incl. TV in final year (£)": fcf_list,
    "Discounted FCF (£)": discounted_list,
})
st.subheader("Discounted cash flows (GBP)")
st.dataframe(df.style.format("£{:,.0f}", na_rep="-"))

# --- Chart ---
st.subheader("Discounted FCF profile")
st.line_chart(df.set_index("Year")["Discounted FCF (£)"])
