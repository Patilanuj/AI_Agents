import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(
    page_title="Business Insight Summary Agent",
    layout="wide"
)

st.title("Business Insight Summary Agent")
st.caption("Upload business data and receive management-ready insights")

# ------------------------------
# Helper Functions
# ------------------------------

def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    elif file.name.endswith(".xlsx"):
        return pd.read_excel(file)
    elif file.name.endswith(".json"):
        return pd.read_json(file)
    else:
        return None


def detect_date_column(df):
    for col in df.columns:
        try:
            df[col] = pd.to_datetime(df[col])
            return col
        except:
            pass
    return None


def classify_domain(columns):
    finance_keywords = ["revenue", "sales", "profit", "margin", "cost", "expense", "ebitda"]
    marketing_keywords = ["leads", "conversion", "ctr", "cac", "traffic", "churn", "retention"]

    finance_score = sum(any(k in col.lower() for k in finance_keywords) for col in columns)
    marketing_score = sum(any(k in col.lower() for k in marketing_keywords) for col in columns)

    if finance_score >= marketing_score:
        return "Finance"
    return "Marketing"


def growth_rate(series):
    if series.iloc[0] == 0:
        return np.nan
    return (series.iloc[-1] - series.iloc[0]) / abs(series.iloc[0]) * 100


def detect_outliers(series):
    if series.std() == 0:
        return []
    z_scores = (series - series.mean()) / series.std()
    return series[abs(z_scores) > 2]


# ------------------------------
# Insight Rules
# ------------------------------

def finance_insights(df, date_col):
    insights = []

    numeric_cols = df.select_dtypes(include="number").columns

    if len(numeric_cols) == 0:
        return insights

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 2:
            continue

        growth = growth_rate(series)

        if not np.isnan(growth):
            if growth > 5:
                insights.append(f"{col.title()} increased by {growth:.1f}% over the period.")
            elif growth < -5:
                insights.append(f"{col.title()} declined by {abs(growth):.1f}% over the period.")

        outliers = detect_outliers(series)
        if len(outliers) > 0:
            insights.append(f"{col.title()} showed unusual spikes or drops, indicating volatility.")

    # Margin pressure logic
    if "revenue" in df.columns and "cost" in df.columns:
        rev_growth = growth_rate(df["revenue"])
        cost_growth = growth_rate(df["cost"])
        if cost_growth > rev_growth:
            insights.append("Costs grew faster than revenue, leading to margin pressure.")

    return insights


def marketing_insights(df, date_col):
    insights = []

    if "leads" in df.columns and "conversion" in df.columns:
        conv_rate_start = df["conversion"].iloc[0]
        conv_rate_end = df["conversion"].iloc[-1]

        if conv_rate_end < conv_rate_start:
            insights.append("Conversion rates declined, indicating funnel efficiency issues.")

    if "traffic" in df.columns:
        traffic_growth = growth_rate(df["traffic"])
        if traffic_growth > 10:
            insights.append("Website traffic increased strongly, suggesting effective acquisition efforts.")
        elif traffic_growth < -10:
            insights.append("Website traffic declined significantly, requiring channel review.")

    if "churn" in df.columns:
        churn_growth = growth_rate(df["churn"])
        if churn_growth > 5:
            insights.append("Customer churn increased, particularly among sensitive segments.")

    return insights


def rewrite_insights(insights, domain):
    if not insights:
        return "No significant patterns or changes were detected in the data."

    summary = " ".join(insights)

    if domain == "Finance":
        return (
            f"Financial performance analysis shows that {summary} "
            "Overall results indicate key areas impacting profitability and cost structure."
        )
    else:
        return (
            f"Marketing performance analysis indicates that {summary} "
            "These trends highlight opportunities to improve acquisition efficiency and retention."
        )


# ------------------------------
# UI
# ------------------------------

uploaded_file = st.file_uploader(
    "Upload CSV, Excel, or JSON file",
    type=["csv", "xlsx", "json"]
)

st.markdown("**OR paste summary data (optional)**")
text_input = st.text_area("Paste summary notes or KPIs here")

if uploaded_file:
    df = load_data(uploaded_file)
    st.subheader("Data Preview")
    st.dataframe(df.head())

    date_col = detect_date_column(df)
    domain = classify_domain(df.columns)

    st.info(f"Detected domain: {domain}")

    if st.button("Generate Insights"):
        if domain == "Finance":
            insights = finance_insights(df, date_col)
        else:
            insights = marketing_insights(df, date_col)

        final_output = rewrite_insights(insights, domain)

        st.subheader("Management Insight Summary")
        st.success(final_output)

elif text_input:
    st.subheader("Management Insight Summary")
    st.success(
        "Based on the provided summary, performance trends indicate notable changes. "
        "Key drivers should be reviewed to assess sustainability and corrective actions."
    )
