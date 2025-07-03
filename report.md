📊 Caprae Lead Scoring Tool – Technical Report
**Repo**: [GitHub – Lead-generation-tool](https://github.com/Ashwinxxx/Lead-generation-tool)

The goal was to create a lightweight, explainable, and efficient lead scoring tool tailored to Caprae Capital's acquisition thesis. I used a **rule-based + NLP hybrid model** where each lead is scored based on its alignment with a customizable Ideal Customer Profile (ICP). Scores are derived from structured fields (industry, revenue, EBITDA, employee count) and unstructured text (description + news articles), combining both traditional and NLP-based scoring strategies.

## 🧠 Model Selection

Instead of black-box machine learning models, I opted for a **transparent, rule-based scoring engine** enhanced by:
- **Keyword-based sentiment modeling** on `company_description`
- **News sentiment analysis** using [GNews API](https://gnews.io/)
- **Cosine scoring emulation** via semantic keyword match weights
> This method ensures full control, interpretability, and immediate usability without requiring large training datasets.
## 🧹 Data Preprocessing

- **Structured Fields**: Parsed numeric ranges for revenue, EBITDA, employee count from user-provided JSON/CSV.
- **Unstructured Text**:
  - Lowercased and cleaned company descriptions.
  - Tokenized and matched against custom positive/negative keyword lists.
  - News headlines and summaries were combined and similarly token-checked.

- **Dynamic ICP Matching**: All scoring thresholds (e.g., target revenue, role titles) are set via a Streamlit sidebar.

---

## 📈 Scoring & Performance Evaluation

- Each lead receives a **0–100 score**, broken into:
  - ✅ +20 to +25 points for revenue, EBITDA, industry fit
  - 🧠 ±15 for NLP keyword matching in description
  - 📰 ±10 for news sentiment (via GNews)
  - ⚙️ +15 for contact role match
  - 👥 +10 for employee count fit

- **Categorization Thresholds**:
  - 🌟 **High Potential**: Score ≥ 80  
  - ✅ **Medium Potential**: Score ≥ 50  
  - ❌ **Low Potential**: Score < 50

- Results are **interpretable with feedback per lead** (e.g., “⚠️ EBITDA outside target”).

---

## ✅ Rationale

I chose this approach for:
- **Clarity**: Stakeholders can understand *why* a lead scored high or low.
- **Customization**: ICP parameters are dynamic and user-controlled.
- **Speed & Cost**: Runs locally without large cloud models or long inference times.
- **Scalability**: Supports both individual and batch scoring.

This makes the tool ideal for investment research teams like Caprae Capital to screen deals quickly, transparently, and consistently.

---

