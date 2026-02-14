# Save as: app_circular_platform_mvp.py
# Optional hero image (repo root): hero_infographic.png
# requirements.txt: streamlit, pandas, numpy, matplotlib

from __future__ import annotations
import base64
import math
from datetime import date
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# -------------------------
# Helpers
# -------------------------
def money(x: float) -> str:
    try:
        return "${:,.0f}".format(float(x))
    except Exception:
        return str(x)

def money2(x: float) -> str:
    try:
        return "${:,.2f}".format(float(x))
    except Exception:
        return str(x)

def pct(x: float) -> str:
    try:
        return "{:.2%}".format(float(x))
    except Exception:
        return str(x)

def clamp(x: float, lo: float, hi: float) -> float:
    return min(max(float(x), lo), hi)

def load_image_as_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def traffic_light(value: float, target: float, warn_band: float = 0.03) -> str:
    if value >= target:
        return "🟢"
    if value >= target - warn_band:
        return "🟡"
    return "🔴"

# -------------------------
# Page config + theme
# -------------------------
st.set_page_config(page_title="DSGE Circular Platform MVP", page_icon="♻️", layout="wide")

hero_b64 = ""
try:
    hero_b64 = load_image_as_base64("hero_infographic.png")
except Exception:
    hero_b64 = ""

st.markdown(f"""
<style>
.stApp {{
  background:
    linear-gradient(rgba(6,10,18,0.97), rgba(6,10,18,0.98)),
    url('data:image/png;base64,{hero_b64}') no-repeat top center fixed;
  background-size: cover;
}}
html, body, [class*="css"] {{
  color: #FFFFFF !important;
  font-size: 18px !important;
}}
h1 {{ font-size: 44px !important; font-weight: 900 !important; }}
h2 {{ font-size: 30px !important; font-weight: 850 !important; }}
h3 {{ font-size: 22px !important; font-weight: 800 !important; }}

.hero-card {{
  padding: 20px;
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.22);
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.40);
}}
.pill {{
  display:inline-block; padding: 7px 12px; border-radius: 999px;
  background: rgba(0,229,255,0.14);
  border: 1px solid rgba(0,229,255,0.35);
  font-weight: 900; font-size: 13px;
}}
[data-testid="stMetricValue"] {{
  font-size: 34px !important;
  font-weight: 900 !important;
  color: #00E5FF !important;
}}
[data-testid="stMetricLabel"] {{
  font-size: 17px !important;
  font-weight: 850 !important;
}}
section[data-testid="stSidebar"] {{
  background-color: rgba(10,16,30,0.98) !important;
  border-right: 1px solid rgba(255,255,255,0.10);
}}
section[data-testid="stSidebar"] * {{
  font-size: 16px !important;
  color: #FFFFFF !important;
}}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Simple simulated login
# -------------------------
st.sidebar.markdown("## Access")
mode = st.sidebar.radio("View Mode", ["Public Impact Portal", "Organization Login"], index=0)

role = "PUBLIC"
if mode == "Organization Login":
    st.sidebar.markdown("### Sign-in (MVP demo)")
    org = st.sidebar.text_input("Organization", value="DSGE 501(c)(3)")
    user = st.sidebar.text_input("User", value="admin")
    pin = st.sidebar.text_input("Access PIN (demo)", value="1234", type="password")
    if pin != "1234":
        st.sidebar.error("Invalid PIN (demo pin is 1234).")
        st.stop()
    role = st.sidebar.selectbox("Role", ["Admin", "Industrial Partner", "Corporate Sponsor", "Workforce Team"], index=0)
else:
    org = "Public"

# -------------------------
# Shared baseline inputs
# -------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("## Program Inputs (shared)")

sites = st.sidebar.number_input("Sites participating", min_value=1.0, max_value=5000.0, value=1.0, step=1.0)

lbs_per_site_month = st.sidebar.number_input("Plastic processed per site (lbs/month)", min_value=0.0, max_value=50_000_000.0, value=80_000.0, step=1000.0)

recovery_rate = st.sidebar.number_input("Recovery rate (0–1)", min_value=0.0, max_value=1.0, value=0.90, step=0.01)
yield_rate = st.sidebar.number_input("Processing yield (0–1)", min_value=0.0, max_value=1.0, value=0.92, step=0.01)
downtime_rate = st.sidebar.number_input("Downtime rate (0–1)", min_value=0.0, max_value=1.0, value=0.08, step=0.01)
scrap_rate = st.sidebar.number_input("Contamination scrap (0–1)", min_value=0.0, max_value=1.0, value=0.06, step=0.01)

sell_share = st.sidebar.number_input("Sell share of output (0–1)", min_value=0.0, max_value=1.0, value=0.50, step=0.05)

sell_price_lb = st.sidebar.number_input("Sell price ($/lb)", min_value=0.0, max_value=1000.0, value=10.0, step=0.5)
internal_value_lb = st.sidebar.number_input("Internal reuse value ($/lb)", min_value=0.0, max_value=1000.0, value=12.0, step=0.5)

disposal_avoid_lb = st.sidebar.number_input("Disposal avoided ($/lb recovered)", min_value=0.0, max_value=100.0, value=0.15, step=0.05)
carbon_value_lb = st.sidebar.number_input("Carbon/ESG value ($/lb recovered)", min_value=0.0, max_value=100.0, value=0.06, step=0.02)

op_cost_site_month = st.sidebar.number_input("Operating cost per site ($/month)", min_value=0.0, max_value=10_000_000.0, value=18_000.0, step=500.0)
capex_per_site = st.sidebar.number_input("CapEx per site (one-time $)", min_value=0.0, max_value=500_000_000.0, value=120_000.0, step=1000.0)

# Workforce assumptions (used in Admin pro forma + public)
trainees_per_site_year = st.sidebar.number_input("Trainees per site per year", min_value=0.0, max_value=5000.0, value=80.0, step=5.0)
placement_rate = st.sidebar.number_input("Placement rate (0–1)", min_value=0.0, max_value=1.0, value=0.70, step=0.05)
avg_wage_uplift = st.sidebar.number_input("Avg wage uplift ($/hr)", min_value=0.0, max_value=50.0, value=8.0, step=1.0)

# -------------------------
# Core calculations (monthly, scaled)
# -------------------------
W = lbs_per_site_month * sites
R = clamp(recovery_rate, 0.0, 1.0)
Y = clamp(yield_rate, 0.0, 1.0)
D = clamp(downtime_rate, 0.0, 1.0)
S = clamp(scrap_rate, 0.0, 1.0)

recovered = W * R
usable = recovered * (1.0 - S)
finished = usable * Y * (1.0 - D)

sold_lbs = finished * clamp(sell_share, 0.0, 1.0)
internal_lbs = finished * (1.0 - clamp(sell_share, 0.0, 1.0))

sell_rev = sold_lbs * sell_price_lb
internal_val = internal_lbs * internal_value_lb
disp_avoid = recovered * disposal_avoid_lb
carbon_val = recovered * carbon_value_lb

gross_value = sell_rev + internal_val + disp_avoid + carbon_val
op_cost = op_cost_site_month * sites
net_profit = gross_value - op_cost

capex_total = capex_per_site * sites
payback_mo = float("inf") if net_profit <= 0 else capex_total / net_profit

# KPI traffic lights (simple defaults)
target_recovery = 0.90
target_yield = 0.92
target_downtime_max = 0.08
target_scrap_max = 0.07

# Workforce outputs
trainees_total_year = trainees_per_site_year * sites
placed_total_year = trainees_total_year * placement_rate

# -------------------------
# HERO header
# -------------------------
st.markdown("""
<div class="hero-card">
  <div class="pill">Public Impact + Secure Operations • AWS-ready • DSGE 501(c)(3)</div>
  <h1 style="margin:10px 0 6px 0;">Circular Plastics → Workforce Platform (MVP)</h1>
  <div style="opacity:0.92;">
    Convert <b>80,000+ lbs/month</b> of plastics into <b>usable products</b> + <b>measurable revenue</b>,
    and reinvest net proceeds into <b>training + job placement</b>.
  </div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# Public Impact Portal
# -------------------------
if role == "PUBLIC":
    st.subheader("Public Impact Portal (Transparency)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Plastic processed (lbs/mo)", f"{W:,.0f}")
    c2.metric("Recovered (lbs/mo)", f"{recovered:,.0f}")
    c3.metric("Jobs placed (est / year)", f"{placed_total_year:,.0f}")
    c4.metric("CO₂/ESG value (proxy / mo)", money(carbon_val))

    st.markdown("### Impact story (full circle)")
    st.write("Waste diversion → processing → value creation → workforce training → job placement → community stability.")

    st.markdown("### Process health (Likely targets)")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"{traffic_light(R, target_recovery, 0.05)} Recovery rate", pct(R))
    k2.metric(f"{traffic_light(Y, target_yield, 0.05)} Yield rate", pct(Y))
    k3.metric(f"{traffic_light(1-D, 1-target_downtime_max, 0.05)} Downtime", pct(D))
    k4.metric(f"{traffic_light(1-S, 1-target_scrap_max, 0.05)} Scrap", pct(S))

    st.markdown("### What we publish (and what we don’t)")
    st.write("Public: pounds diverted, trainees served, placement outcomes, and high-level ESG impact. Private: contract pricing, margins, partner splits, and internal controls.")

# -------------------------
# Organization Dashboards (login)
# -------------------------
else:
    st.subheader(f"Organization Dashboard — Role: {role}")

    # Top executive metrics (safe internal)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gross value ($/mo)", money(gross_value))
    m2.metric("Net profit ($/mo)", money(net_profit))
    m3.metric("CapEx total", money(capex_total))
    m4.metric("Payback", "∞" if not math.isfinite(payback_mo) else f"{payback_mo:.1f} mo")

    # Tabs per role
    tabs = st.tabs(["Overview", "Material Flow", "Workforce", "Finance (Admin)", "Exports"])

    # -------- Overview --------
    with tabs[0]:
        st.markdown("### What this is")
        st.write("An internal decision dashboard: throughput + quality + value + workforce outcomes. Designed for partner governance and audit-ready reporting.")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric(f"{traffic_light(R, target_recovery, 0.05)} Recovery", pct(R))
        k2.metric(f"{traffic_light(Y, target_yield, 0.05)} Yield", pct(Y))
        k3.metric(f"{traffic_light(1-D, 1-target_downtime_max, 0.05)} Downtime", pct(D))
        k4.metric(f"{traffic_light(1-S, 1-target_scrap_max, 0.05)} Scrap", pct(S))

        st.markdown("### Narrative for stakeholders")
        st.write("We quantify plastics processing and reinvest net proceeds into training cohorts that lead to reliable job placement—tracked as measurable outcomes.")

    # -------- Material Flow --------
    with tabs[1]:
        st.markdown("### Monthly material flow (scaled)")
        flow = pd.DataFrame([{
            "Incoming lbs": W,
            "Recovered lbs": recovered,
            "Usable lbs": usable,
            "Finished lbs": finished,
            "Sold lbs": sold_lbs,
            "Internal lbs": internal_lbs
        }]).T.reset_index()
        flow.columns = ["Stage", "Lbs/month"]
        st.dataframe(flow, use_container_width=True)

        fig = plt.figure()
        plt.bar(flow["Stage"], flow["Lbs/month"])
        plt.xticks(rotation=20, ha="right")
        plt.ylabel("lbs / month")
        st.pyplot(fig)

    # -------- Workforce --------
    with tabs[2]:
        st.markdown("### Workforce pipeline (annualized)")
        w1, w2, w3 = st.columns(3)
        w1.metric("Trainees / year", f"{trainees_total_year:,.0f}")
        w2.metric("Placement rate", pct(placement_rate))
        w3.metric("Jobs placed / year", f"{placed_total_year:,.0f}")

        st.markdown("### Wage uplift story (proxy)")
        st.write(f"Average wage uplift assumption: **{money2(avg_wage_uplift)}/hour** per placement (edit in sidebar).")

    # -------- Finance (Admin) + 5-year Pro Forma --------
    with tabs[3]:
        if role != "Admin":
            st.info("Finance / Pro Forma is visible to Admin only in this MVP.")
        else:
            st.markdown("## Admin Finance + 5-Year Pro Forma (Embedded)")

            st.markdown("### Pro forma inputs")
            years = st.slider("Years", min_value=3, max_value=5, value=5, step=1)

            # Growth assumptions
            growth_sites = st.number_input("Site growth per year (%)", min_value=0.0, max_value=300.0, value=25.0, step=5.0) / 100.0
            growth_lbs = st.number_input("Throughput efficiency gain per year (%)", min_value=0.0, max_value=100.0, value=5.0, step=1.0) / 100.0
            growth_price = st.number_input("Value per lb improvement per year (%)", min_value=-50.0, max_value=100.0, value=2.0, step=1.0) / 100.0
            growth_cost = st.number_input("Op cost inflation per year (%)", min_value=-50.0, max_value=100.0, value=3.0, step=1.0) / 100.0

            # Program allocation (nonprofit funding)
            reinvest_rate = st.number_input("Net proceeds reinvested into workforce (%)", min_value=0.0, max_value=100.0, value=30.0, step=5.0) / 100.0

            # Build Year 0 baseline "value per recovered lb" proxy
            # Using current scenario components / recovered lbs
            value_per_recovered_lb = 0.0 if recovered <= 0 else gross_value / recovered
            op_cost_per_site = op_cost_site_month * 12.0
            capex_per_site_local = capex_per_site

            # Pro forma table
            rows = []
            sites_y = float(sites)
            lbs_site_y = float(lbs_per_site_month)
            vpr = float(value_per_recovered_lb)
            op_cost_site_y = float(op_cost_per_site)

            for y in range(1, years + 1):
                if y > 1:
                    sites_y *= (1.0 + growth_sites)
                    lbs_site_y *= (1.0 + growth_lbs)
                    vpr *= (1.0 + growth_price)
                    op_cost_site_y *= (1.0 + growth_cost)

                W_y = sites_y * lbs_site_y * 12.0
                recovered_y = W_y * R
                gross_y = recovered_y * vpr
                op_y = sites_y * op_cost_site_y
                net_y = gross_y - op_y

                capex_y = sites_y * capex_per_site_local if y == 1 else (sites_y - (sites_y / (1.0 + growth_sites))) * capex_per_site_local
                capex_y = max(capex_y, 0.0)

                workforce_reinvest_y = max(net_y, 0.0) * reinvest_rate

                rows.append({
                    "Year": y,
                    "Sites": sites_y,
                    "Annual incoming lbs": W_y,
                    "Annual recovered lbs": recovered_y,
                    "Gross value": gross_y,
                    "Operating cost": op_y,
                    "Net proceeds": net_y,
                    "CapEx (new sites)": capex_y,
                    "Workforce reinvest": workforce_reinvest_y
                })

            pf = pd.DataFrame(rows)
            # Add cumulative
            pf["Cumulative net proceeds"] = pf["Net proceeds"].cumsum()
            pf["Cumulative workforce reinvest"] = pf["Workforce reinvest"].cumsum()

            # Display with formatting-friendly columns
            show = pf.copy()
            for col in ["Gross value", "Operating cost", "Net proceeds", "CapEx (new sites)", "Workforce reinvest",
                        "Cumulative net proceeds", "Cumulative workforce reinvest"]:
                show[col] = show[col].apply(lambda x: float(x))
            st.dataframe(show, use_container_width=True)

            # Charts
            st.markdown("### Pro forma visuals")
            fig1 = plt.figure()
            plt.plot(pf["Year"], pf["Net proceeds"], marker="o")
            plt.ylabel("Net proceeds ($/year)")
            plt.xlabel("Year")
            st.pyplot(fig1)

            fig2 = plt.figure()
            plt.plot(pf["Year"], pf["Workforce reinvest"], marker="o")
            plt.ylabel("Workforce reinvest ($/year)")
            plt.xlabel("Year")
            st.pyplot(fig2)

            # Quick readout
            st.success(
                f"By Year {years}: "
                f"Sites ≈ {pf.iloc[-1]['Sites']:.1f} • "
                f"Annual recovered ≈ {pf.iloc[-1]['Annual recovered lbs']:,.0f} lbs • "
                f"Cumulative net proceeds ≈ {money(pf.iloc[-1]['Cumulative net proceeds'])} • "
                f"Cumulative workforce reinvest ≈ {money(pf.iloc[-1]['Cumulative workforce reinvest'])}"
            )

            st.markdown("### Definitions (Admin)")
            st.write(
                "Value per recovered lb is derived from current inputs (sell revenue + internal value + disposal avoided + ESG value) "
                "divided by recovered lbs. Pro forma applies growth assumptions to sites, throughput, value per lb, and costs."
            )

            st.download_button(
                "Download Pro Forma CSV",
                data=pf.to_csv(index=False),
                file_name="pro_forma_5yr.csv",
                mime="text/csv"
            )

    # -------- Exports --------
    with tabs[4]:
        snapshot = pd.DataFrame([{
            "date": str(date.today()),
            "sites": sites,
            "incoming_lbs_month": W,
            "recovered_lbs_month": recovered,
            "finished_lbs_month": finished,
            "gross_value_month": gross_value,
            "op_cost_month": op_cost,
            "net_profit_month": net_profit,
            "capex_total": capex_total,
            "payback_months": payback_mo if math.isfinite(payback_mo) else np.nan,
            "trainees_per_year": trainees_total_year,
            "placement_rate": placement_rate,
            "jobs_placed_per_year": placed_total_year
        }])

        st.download_button(
            "Download Current Snapshot (CSV)",
            data=snapshot.to_csv(index=False),
            file_name="snapshot_current.csv",
            mime="text/csv"
        )

        st.write("Tip: Use this snapshot for sponsor reports, partner updates, and grant attachments.")
