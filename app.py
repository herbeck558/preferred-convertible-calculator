import streamlit as st
import numpy as np
import numpy_financial as npf
import requests
import json
import re
import yfinance as yf

# Page styling configuration
st.set_page_config(page_title="Convertible Preferred Modeler", layout="wide")

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

st.title("📊 Advanced Convertible Preferred Stock Modeler")
st.markdown("Analyze structured collar conversion profiles, toggle live asset discovery feeds, and review terminal cash flows.")

# 1. CORE DEFINED PRESETS (Forces GOOGN as position zero default index)
PRESET_PROFILES = {
    "Alphabet Inc. 6.25% Series C (GOOGN)": {
        "preferred_ticker": "GOOGN", "common_ticker": "GOOGL", "par": 50.0, "coupon": 6.25,
        "lower_collar": 351.87, "upper_collar": 439.75, "max_ratio": 0.14210, "min_ratio": 0.11370, "quarters": 10
    },
    "Meta Platforms 6.50% Series A (META Pfd)": {
        "preferred_ticker": "META", "common_ticker": "META", "par": 50.0, "coupon": 6.50,
        "lower_collar": 312.50, "upper_collar": 367.10, "max_ratio": 0.16000, "min_ratio": 0.13620, "quarters": 11
    },
    "KKR & Co. 6.25% Series D (KKR.PRD)": {
        "preferred_ticker": "KKR-PD", "common_ticker": "KKR", "par": 50.0, "coupon": 6.25,
        "lower_collar": 120.77, "upper_collar": 150.97, "max_ratio": 0.41400, "min_ratio": 0.33120, "quarters": 5
    },
    "Custom (Manual Input / LLM Overwrite)": None
}

# 2. REAL-TIME SEC DISCOVERY WIDGET 
st.sidebar.header("🔍 SEC EDGAR Live Discovery")
enable_sec_lookup = st.sidebar.checkbox("Search Live SEC Database")

discovered_filing_text = ""

if enable_sec_lookup:
    user_email = st.sidebar.text_input(
        "Your Email (Required by SEC Rules)", 
        placeholder="analyst@example.com",
        help="The SEC requires automated tools to provide an identity header to avoid throttling."
    )
    search_ticker = st.sidebar.text_input("Filter by Core Ticker (e.g. META, GOOGL)", value="").strip().upper()
    
    if st.sidebar.button("📡 Search SEC Registry") and user_email:
        with st.sidebar.spinner("Querying SEC EDGAR Engine..."):
            try:
                sec_search_url = "https://sec.gov"
                query_string = '"mandatory convertible preferred stock"'
                if search_ticker:
                    query_string += f" AND {search_ticker}"
                
                payload = {
                    "q": query_string,
                    "dateRange": "all",
                    "startdt": "2023-01-01",
                    "forms": ["424B5", "424B2", "8-K"]
                }
                
                headers = {"User-Agent": f"ConvertibleModeler/1.0 ({user_email})"}
                response = requests.post(sec_search_url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    hits = response.json().get("hits", {}).get("hits", [])
                    if hits:
                        st.sidebar.success(f"Discovered {len(hits)} matching SEC filings!")
                        
                        filing_options = {}
                        for item in hits:
                            source = item.get("_source", {})
                            doc_title = f"{source.get('display_names', ['Unknown Filer'])} ({source.get('form', 'Filing')}) - {source.get('file_date', '')}"
                            
                            accession_num = source.get("adsh", "").replace("-", "")
                            doc_name = source.get("primary_doc_name", "")
                            cik = source.get("cik", "").zfill(10)
                            full_url = f"https://sec.gov{cik}/{accession_num}/{doc_name}"
                            filing_options[doc_title] = full_url
                        
                        selected_doc = st.sidebar.selectbox("Select a filing to pull text for the AI parser:", list(filing_options.keys()))
                        target_url = filing_options[selected_doc]
                        st.sidebar.markdown(f"🔗 [Open Original SEC Document]({target_url})")
                        
                        with st.spinner("Slicing document text structure..."):
                            doc_response = requests.get(target_url, headers=headers, timeout=10)
                            raw_html = doc_response.text
                            
                            match_idx = raw_html.lower().find("conversion rate")
                            if match_idx == -1:
                                match_idx = raw_html.lower().find("preferred stock")
                                
                            start_p = max(0, match_idx - 500)
                            sliced_text = raw_html[start_p:start_p+4000]
                            discovered_filing_text = re.sub('<[^<]+?>', '', sliced_text)
                            st.sidebar.caption("✅ Text snippet successfully captured. Ready to run the AI Extractor below.")
                    else:
                        st.sidebar.warning("No matching convertible registrations found for this filter criteria.")
                else:
                    st.sidebar.error(f"SEC Portal Error Connection Code: {response.status_code}")
            except Exception as e:
                st.sidebar.error(f"Discovery Connectivity Interruption: {str(e)}")

# Define active preset selection window 
selected_preset = st.selectbox("📂 Select a Known Preferred Asset Profile:", list(PRESET_PROFILES.keys()), index=0)

# Default profile initialization
defaults = {
    "ticker": "GOOGN", "market_price": 41.25, "common_price": 180.00, "par": 50.0, "coupon": 6.25,
    "lower_collar": 351.87, "upper_collar": 439.75, "max_ratio": 0.14210, "min_ratio": 0.11370, "quarters": 10
}

# Execute dynamic background price parsing sequence
if PRESET_PROFILES[selected_preset]:
    cfg = PRESET_PROFILES[selected_preset]
    defaults["ticker"] = cfg["preferred_ticker"]
    defaults["par"] = cfg["par"]
    defaults["coupon"] = cfg["coupon"]
    defaults["lower_collar"] = cfg["lower_collar"]
    defaults["upper_collar"] = cfg["upper_collar"]
    defaults["max_ratio"] = cfg["max_ratio"]
    defaults["min_ratio"] = cfg["min_ratio"]
    defaults["quarters"] = cfg["quarters"]
    
    with st.spinner(f"Updating market data for {cfg['preferred_ticker']} / {cfg['common_ticker']}..."):
        try:
            pref_stock = yf.Ticker(cfg["preferred_ticker"])
            common_stock = yf.Ticker(cfg["common_ticker"])
            defaults["market_price"] = round(float(pref_stock.history(period="1d")["Close"].iloc[-1]), 2)
            defaults["common_price"] = round(float(common_stock.history(period="1d")["Close"].iloc[-1]), 2)
            st.toast("Updated active equity quote metrics!", icon="📈")
        except Exception:
            defaults["market_price"] = 41.25 if cfg["preferred_ticker"] == "GOOGN" else 50.0
            defaults["common_price"] = 180.00

# 3. SECURE EXTRACTION BLOCK
st.sidebar.markdown("---")
st.sidebar.header("🤖 AI Parameter Extractor")
use_llm = st.sidebar.checkbox("Enable AI Text Parsing Engine")

if use_llm:
    try: 
        hf_token = st.secrets["HF_TOKEN"]
    except KeyError: 
        hf_token = None
    
    input_text_payload = discovered_filing_text if discovered_filing_text else ""
    prospectus_text = st.sidebar.text_area("Prospectus Input Clipboard Frame:", value=input_text_payload, height=150)
    
    if st.sidebar.button("🤖 Run AI Extractor") and hf_token:
        with st.sidebar.spinner("Processing extracted financial payload..."):
            try:
                API_URL = "https://huggingface.co"
                headers = {"Authorization": f"Bearer {hf_token}"}
                system_instruction = (
                    "You are a precise financial parser. You must output ONLY valid raw JSON data matching this exact template layout. "
                    "Do not wrap it in markdown code blocks. Template: "
                    '{"ticker": "XYZ", "market_price": 50.0, "par": 50.0, "coupon": 6.25, "lower_collar": 100.0, "upper_collar": 150.0, '
                    '"max_ratio": 0.1421, "min_ratio": 0.1137, "quarters": 10}'
                )
                payload = {
                    "inputs": f"<s>[INST] {system_instruction}\n\nParse this text:\n{prospectus_text} [/INST]",
                    "parameters": {"return_full_text": False, "max_new_tokens": 500, "temperature": 0.1}
                }
                response = requests.post(API_URL, headers=headers, json=payload)
                raw_text = response.json()['generated_text'] if isinstance(response.json(), list) else response.json().get('generated_text', '')
                json_match = re.search(r'{.*}', raw_text, re.DOTALL)
                if json_match:
                    defaults.update(json.loads(json_match.group(0)))
                    st.sidebar.success("Structural overrides parsed successfully!")
            except Exception as e:
                st.sidebar.error(f"AI Extraction Failure: {str(e)}")

# 4. AUDITABLE PARAMETER WORKSPACE OVERRIDES
st.header("⚙️ Step 1: Asset Structural Parameters Audit")
col1, col2, col3, col4 = st.columns(4)
with col1:
    ticker = st.text_input("Asset Ticker Symbol", value=defaults["ticker"])
    mkt_prc = st.number_input("Preferred Cost Basis ($/Share)", value=float(defaults["market_price"]), step=0.25)
with col2:
    par = st.number_input("Liquidation Par Value ($)", value=float(defaults["par"]), step=1.0)
    coupon = st.number_input("Annual Coupon Rate (%)", value=float(defaults["coupon"]), step=0.05)
with col3:
    lower_c = st.number_input("Lower Price Collar ($)", value=float(defaults["lower_collar"]), step=1.0)
    upper_c = st.number_input("Upper Price Collar ($)", value=float(defaults["upper_collar"]), step=1.0)
with col4:
    max_r = st.number_input("Maximum Conversion Ratio", value=float(defaults["max_ratio"]), format="%.5f")
    min_r = st.number_input("Minimum Conversion Ratio", value=float(defaults["min_ratio"]), format="%.5f")
    quarters_left = st.number_input("Remaining Distribution Quarters", value=int(defaults.get("quarters", 10)), step=1)

# Advanced Valuation Core Mathematics
quarterly_div = (par * (coupon / 100)) / 4
total_dividends = quarterly_div * quarters_left
net_cost_basis = mkt_prc - total_dividends
net_breakeven_common_price = round(float(net_cost_basis / max_r), 2) if max_r > 0 else 0.0

# 5. MATURITY TARGET CONTROLLER
st.header("📈 Step 2: Set Maturity Projection Target")
slider_label = (
    f"Hypothetical Equity Price at Maturity ($) "
    f" | [ LIVE TODAY: ${defaults['common_price']:.2f} ] "
    f" | [ NET BREAK-EVEN FLOOR: ${net_breakeven_common_price:.2f} ]"
)
target_stock_price = st.slider(slider_label, min_value=float(lower_c * 0.4), max_value=float(upper_c * 1.6), value=float(defaults["common_price"]), step=1.0)

# Helper engine function to evaluate zones across any specific price input
def get_payout_for_price(p):
    if p <= lower_c:
        ratio = max_r
        zone = "Below Floor (Max Ratio)"
    elif p >= upper_c:
        ratio = min_r
        zone = "Above Cap (Min Ratio)"
    else:
        ratio = par / p
        zone = "Inside Collar (Variable)"
        
    stock_val = ratio * p
    total_val = stock_val + total_dividends
    
    # Internal Rate of Return Matrix setup
    c_flows = [-mkt_prc] + [quarterly_div] * (quarters_left - 1) + [quarterly_div + stock_val]
    irr_v = npf.irr(c_flows)
    ann_irr = ((1 + irr_v) ** 4) - 1 if irr_v is not None else 0.0
    return ratio, stock_val, total_val, ann_irr, zone

settlement_ratio, terminal_stock_value, total_val, annualized_irr, scenario_desc = get_payout_for_price(target_stock_price)
cagr = (total_val / mkt_prc) ** (1 / (quarters_left / 4)) - 1 if mkt_prc > 0 else 0.0

# Render Dashboard Metrics Display Cards
res1, res2, res3 = st.columns(3)
res1.metric("Compounded Cash Flow IRR (Annual)", f"{annualized_irr*100:.2f}%") 
res2.metric("Simple Yield CAGR", f"{cagr*100:.2f}%")
res3.metric("Total Absolute Holding Return", f"{((total_val / mkt_prc) - 1)*100:.1f}%" if mkt_prc > 0 else "0.0%")
st.info(f"**Current Pricing Zone Status:** {scenario_desc}")

# 6. CHARTING CANVAS INTERFACES
if HAS_PLOTLY:
    st.subheader("📊 Total Return Curve Profile at Maturity (Stock Value + Income)")
    stock_prices = np.linspace(lower_c * 0.4, upper_c * 1.6, 200)
    total_payouts = []
    for p in stock_prices:
        _, _, t_pay, _, _ = get_payout_for_price(p)
        total_payouts.append(t_pay)
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stock_prices, y=total_payouts, mode='lines', name='Total Value Curve Profile', line=dict(color='#2ca02c', width=3)))
    fig.add_trace(go.Scatter(x=[stock_prices[0], stock_prices[-1]], y=[mkt_prc, mkt_prc], mode='lines', name='Net Preferred Cost Basis Floor', line=dict(color='red', dash='dash')))
    fig.add_vline(x=defaults["common_price"], line_width=1.5, line_dash="dot", line_color="blue", annotation_text=" Live Price Intercept")
    fig.add_vline(x=net_breakeven_common_price, line_width=1.5, line_dash="dot", line_color="purple", annotation_text=" True Break-Even Floor")
    
    fig.add_trace(go.Scatter(x=[target_stock_price], y=[total_val], mode='markers', name='Your Simulated Target Point', marker=dict(size=12, color='orange')))
    fig.update_layout(xaxis_title="Underlying Common Stock Price at Maturity ($)", yaxis_title="Total Realized Value (Stock + Dividends) ($)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# 7. ADDED SCENARIO MATRIX BLOCK
st.header("📋 Step 3: Multi-Price Scenario Matrix Analysis")
st.markdown("Review mathematical step returns automatically running parallel market prices concurrently.")

matrix_prices = [
    round(defaults["common_price"] * 0.7, 2),  # Down 30%
    round(defaults["common_price"] * 0.85, 2), # Down 15%
    round(defaults["common_price"], 2),        # Flat / Live Price
    round(lower_c, 2),                         # Exact Floor Collar Wall
    round(upper_c, 2),                         # Exact Cap Collar Wall
    round(defaults["common_price"] * 1.15, 2), # Up 15%
    round(defaults["common_price"] * 1.3, 2)   # Up 30%
]

# De-duplicate, sort, and clean the matrix array
matrix_prices = sorted(list(set(matrix_prices)))

matrix_rows = []
for mp in matrix_prices:
    rat, s_val, t_val, a_irr, z_desc = get_payout_for_price(mp)
    abs_ret = ((t_val / mkt_prc) - 1) * 100 if mkt_prc > 0 else 0.0
    matrix_rows.append({
        "Hypothetical Stock Price ($)": f"${mp:,.2f}",
        "Pricing Zone Description": z_desc,
        "Resulting Conversion Ratio": f"{rat:.5f}",
        "Final Settled Stock Value ($)": f"${s_val:,.2f}",
        "Total Return Value (Stock + Divs) ($)": f"${t_val:,.2f}",
        "Absolute Return (%)": f"{abs_ret:+.2f}%",
        "Annualized Cash Flow IRR (%)": f"{a_irr * 100:+.2f}%"
    })

st.table(matrix_rows)
