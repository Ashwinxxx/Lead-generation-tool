import streamlit as st
import pandas as pd
import json
import requests
from time import sleep

# ---- Streamlit App Config ----
st.set_page_config(page_title="Caprae Lead Scorer", layout="wide", page_icon="📊")

# ---- Custom CSS for Light Theme Look ----
def local_css():
    st.markdown("""
        <style>
        body {
            background-color: #f8f9fa;
            color: #333333;
        }
        h1, h2, h3, h4 {
            color: #003366;
        }
        .stButton>button {
            background-color: #003366;
            color: white;
            border-radius: 6px;
        }
        .stMetric {
            background-color: #ffffff;
            padding: 8px;
            border-radius: 8px;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

local_css()

# ---- API Configuration ----
GNEWS_API_KEY = "ec527836565a28003689db598195abb1"
NEWS_API_ENDPOINT = "https://gnews.io/api/v4/search"

POSITIVE_KEYWORDS = ["growth", "expansion", "profit", "acquisition", "partnership", "innovative", "successful", "revenue increase", "market leader", "strong performance"]
NEGATIVE_KEYWORDS = ["lawsuit", "bankruptcy", "decline", "loss", "layoffs", "struggling", "investigation", "scandal", "debt", "restructuring"]

def get_company_news_sentiment(company_name: str) -> int:
    sentiment_score = 0
    if not GNEWS_API_KEY or GNEWS_API_KEY == "YOUR_GNEWS_API_KEY":
        return 0
    try:
        params = {'q': company_name, 'lang': 'en', 'max': 5, 'apikey': GNEWS_API_KEY}
        response = requests.get(NEWS_API_ENDPOINT, params=params, timeout=5)
        response.raise_for_status()
        articles = response.json().get('articles', [])
        for article in articles:
            content = (article.get('title', '') + " " + article.get('description', '')).lower()
            sentiment_score += sum(1 for keyword in POSITIVE_KEYWORDS if keyword in content)
            sentiment_score -= sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in content)
    except requests.exceptions.RequestException:
        return 0
    return sentiment_score

def score_lead(lead_data: dict, icp_params: dict) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    target_industries = [i.strip().lower() for i in icp_params.get('industries', '').split(',') if i.strip()]
    min_revenue = icp_params.get('min_revenue', 0)
    max_revenue = icp_params.get('max_revenue', float('inf'))
    min_ebitda = icp_params.get('min_ebitda', 0)
    max_ebitda = icp_params.get('max_ebitda', float('inf'))
    pos_keywords = [k.strip().lower() for k in icp_params.get('positive_keywords_desc', '').split(',') if k.strip()]
    neg_keywords = [k.strip().lower() for k in icp_params.get('negative_keywords_desc', '').split(',') if k.strip()]
    target_roles = [r.strip().lower() for r in icp_params.get('contact_roles', '').split(',') if r.strip()]
    min_emp = icp_params.get('min_employees', 0)
    max_emp = icp_params.get('max_employees', float('inf'))

    industry = lead_data.get('industry', '').lower()
    if target_industries and any(ti in industry for ti in target_industries):
        score += 20
        reasons.append(f"✅ Industry Fit: {lead_data.get('industry')}")
    elif target_industries:
        score -= 5
        reasons.append(f"⚠️ Industry Mismatch: {lead_data.get('industry')}")

    revenue = lead_data.get('revenue_usd')
    if revenue is not None:
        if min_revenue <= revenue <= max_revenue:
            score += 25
            reasons.append(f"✅ Revenue (${revenue:,.0f}) within target")
        else:
            score -= 10
            reasons.append(f"⚠️ Revenue (${revenue:,.0f}) outside target")
    else:
        reasons.append("❌ Revenue data missing")

    ebitda = lead_data.get('ebitda_usd')
    if ebitda is not None:
        if min_ebitda <= ebitda <= max_ebitda:
            score += 25
            reasons.append(f"✅ EBITDA (${ebitda:,.0f}) within target")
        else:
            score -= 10
            reasons.append(f"⚠️ EBITDA (${ebitda:,.0f}) outside target")
    else:
        reasons.append("❌ EBITDA data missing")

    description = lead_data.get('company_description', '').lower()
    desc_score = sum(5 for keyword in pos_keywords if keyword in description) - sum(5 for keyword in neg_keywords if keyword in description)
    score += min(max(desc_score, -15), 15)

    contact_title = lead_data.get('contact_title', '').lower()
    if target_roles and any(role in contact_title for role in target_roles):
        score += 15
        reasons.append(f"✅ Contact Role: {lead_data.get('contact_title')}")
    else:
        reasons.append(f"⚠️ Contact Role: {lead_data.get('contact_title')} not target")

    emp_count = lead_data.get('employee_count')
    if emp_count is not None:
        if min_emp <= emp_count <= max_emp:
            score += 10
            reasons.append(f"✅ Employee Count: {emp_count}")
        else:
            reasons.append(f"⚠️ Employee Count: {emp_count} outside target")
    else:
        reasons.append("❌ Employee count missing")

    news_score = get_company_news_sentiment(lead_data.get('company_name', ''))
    if news_score != 0:
        score += max(min(news_score * 2, 10), -10)
        reasons.append(f"📰 News Sentiment Impact: {news_score}")
    else:
        reasons.append("📰 No significant news sentiment")

    # --- Final Category ---
    if score >= 80:
        category = "🌟 HIGH POTENTIAL LEAD"
    elif score >= 50:
        category = "✅ MEDIUM POTENTIAL LEAD"
    else:
        category = "❌ LOW POTENTIAL LEAD"

    reasons.insert(0, f"Lead Category: {category} | Total Score: {score}")
    return score, reasons

# ---- Sidebar: ICP Config ----
st.sidebar.title("🎯 Ideal Customer Profile (ICP)")

icp = {
    'industries': st.sidebar.text_input("Target Industries", "manufacturing, services, healthcare"),
    'min_revenue': st.sidebar.number_input("Min Revenue ($)", 0, step=100000, value=1000000),
    'max_revenue': st.sidebar.number_input("Max Revenue ($)", 0, step=100000, value=10000000),
    'min_ebitda': st.sidebar.number_input("Min EBITDA ($)", 0, step=50000, value=500000),
    'max_ebitda': st.sidebar.number_input("Max EBITDA ($)", 0, step=50000, value=2000000),
    'positive_keywords_desc': st.sidebar.text_input("Positive Desc Keywords", "owner-operated, recurring revenue"),
    'negative_keywords_desc': st.sidebar.text_input("Negative Desc Keywords", "startup, pre-revenue"),
    'contact_roles': st.sidebar.text_input("Target Contact Roles", "founder, ceo, owner"),
    'min_employees': st.sidebar.number_input("Min Employees", 0, value=10),
    'max_employees': st.sidebar.number_input("Max Employees", 0, value=100)
}

# ---- Main Page ----
st.title("📈 Caprae Capital Lead Scorer")
st.markdown("Score potential acquisition targets based on your custom ICP settings.")

input_mode = st.radio("Choose Input Method", ["Single Lead (Form)", "Multiple Leads (JSON)"])
leads_to_score = []

if input_mode == "Single Lead (Form)":
    st.subheader("📝 Enter Lead Details")
    col1, col2 = st.columns(2)
    with col1:
        cname = st.text_input("Company Name", "Precision Machining Solutions")
        industry = st.text_input("Industry", "Specialty Manufacturing")
        revenue = st.number_input("Revenue ($)", 0, step=100000, value=6800000)
        ebitda = st.number_input("EBITDA ($)", 0, step=50000, value=1100000)
        employees = st.number_input("Employee Count", 0, value=35)
    with col2:
        contact_name = st.text_input("Contact Name", "Robert Johnson")
        contact_title = st.text_input("Contact Title", "Founder & CEO")
        location = st.text_input("Location", "Dallas, TX")
        description = st.text_area("Company Description", "An owner-operated CNC machining firm with strong recurring revenue.")

    leads_to_score.append({
        "company_name": cname,
        "industry": industry,
        "revenue_usd": revenue,
        "ebitda_usd": ebitda,
        "employee_count": employees,
        "company_description": description,
        "contact_name": contact_name,
        "contact_title": contact_title,
        "location": location
    })

else:
    st.subheader("📥 Paste JSON Array of Leads")
    sample_json = json.dumps([
        {
            "company_name": "Precision Machining Solutions",
            "industry": "Specialty Manufacturing",
            "revenue_usd": 6800000,
            "ebitda_usd": 1100000,
            "employee_count": 35,
            "company_description": "Owner-operated, strong recurring revenue from aerospace clients.",
            "contact_name": "Robert Johnson",
            "contact_title": "Founder & CEO",
            "location": "Dallas, TX"
        },
        {
            "company_name": "Eco-Tech Startup",
            "industry": "Environmental Tech",
            "revenue_usd": 300000,
            "ebitda_usd": -50000,
            "employee_count": 8,
            "company_description": "Pre-revenue startup using AI for waste management.",
            "contact_name": "Sarah Chen",
            "contact_title": "Co-Founder",
            "location": "San Francisco, CA"
        }
    ], indent=2)
    user_json = st.text_area("Paste JSON leads here:", sample_json, height=300)
    try:
        leads_to_score = json.loads(user_json)
    except:
        st.error("❌ Invalid JSON format!")

if st.button("🚀 Score Leads"):
    if leads_to_score:
        st.success(f"Scoring {len(leads_to_score)} leads...")
        progress = st.progress(0)
        final_data = []

        for i, lead in enumerate(leads_to_score):
            score, feedback = score_lead(lead, icp)
            st.markdown(f"### 📍 Lead: {lead.get('company_name', 'N/A')}")
            st.metric(label="Total Score", value=score)
            for line in feedback:
                st.write(f"- {line}")
            st.markdown("---")
            final_data.append({
                "Company": lead.get('company_name'),
                "Score": score,
                "Summary": feedback[0],
                "Industry": lead.get('industry'),
                "Revenue": lead.get('revenue_usd'),
                "EBITDA": lead.get('ebitda_usd'),
                "Employees": lead.get('employee_count'),
                "Contact": lead.get('contact_title')
            })
            progress.progress((i+1)/len(leads_to_score))
            sleep(0.1)
        progress.empty()

        st.subheader("📊 Summary Table")
        df = pd.DataFrame(final_data)
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Results as CSV", data=csv, file_name="lead_scoring_results.csv", mime='text/csv')
    else:
        st.warning("Please input at least one valid lead.")

st.markdown("---")
st.info("Built by Caprae Capital | SaaSquatch Lead Scoring Demo | Enhanced UI 🌐")

