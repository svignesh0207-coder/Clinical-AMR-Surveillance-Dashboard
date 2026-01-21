# ============================================================
# Clinical AMR Surveillance Dashboard
# FINAL v1 — Cleaned Data Only
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Clinical AMR Surveillance Dashboard",
    page_icon="🧫",
    layout="wide"
)

st.title("🧫 Clinical Antimicrobial Resistance (AMR) Surveillance Dashboard")
st.caption(
    "For antimicrobial resistance surveillance, epidemiology, "
    "research, and antimicrobial stewardship support"
)

# ------------------------------------------------------------
# SIDEBAR — DATA INPUT & DOCUMENTATION
# ------------------------------------------------------------
st.sidebar.header("📂 Data Upload")

uploaded_file = st.sidebar.file_uploader(
    "Upload CLEANED AMR Excel file (.xlsx)",
    type=["xlsx"]
)

use_sample = st.sidebar.checkbox("Use sample dataset", value=False)

@st.cache_data
def load_sample():
    return pd.read_excel("sample_amr_data.xlsx")

@st.cache_data
def load_uploaded(file):
    return pd.read_excel(file)

with st.sidebar.expander("📋 Expected Input Format"):
    st.markdown("""
**File type:** `.xlsx`  
**Each row = one isolate**

### Required metadata columns
- `SNO`
- `SAMPLE_TYPE`
- `GENDER` (M / F)
- `ESBL` (YES / NO)
- `MDR` (YES / NO)
- `MAR_INDEX` (0–1)

### Antibiotic columns
- One column per antibiotic
- Allowed values: **S, I, R**

👉 Use the **sample dataset** as a template.
""")

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
if use_sample:
    df = load_sample()
    st.sidebar.success("Using sample dataset")
elif uploaded_file:
    df = load_uploaded(uploaded_file)
    st.sidebar.success("File uploaded successfully")
else:
    st.info("Upload a cleaned AMR dataset or enable sample data.")
    st.stop()

# ------------------------------------------------------------
# STANDARDIZE COLUMNS
# ------------------------------------------------------------
df.columns = (
    df.columns.str.strip()
              .str.upper()
              .str.replace(" ", "_")
              .str.replace("/", "_")
)

required_cols = ["SNO", "SAMPLE_TYPE", "GENDER", "ESBL", "MDR", "MAR_INDEX"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"❌ Missing required columns: {missing}")
    st.stop()

antibiotic_cols = [c for c in df.columns if c not in required_cols]

allowed_vals = {"S", "I", "R"}
for col in antibiotic_cols:
    bad = set(df[col].dropna().astype(str).str.upper()) - allowed_vals
    if bad:
        st.error(f"❌ Invalid values in column `{col}`: {bad}")
        st.stop()

# Normalize metadata
df["ESBL"] = df["ESBL"].astype(str).str.upper()
df["MDR"] = df["MDR"].astype(str).str.upper()
df["GENDER"] = df["GENDER"].astype(str).str.upper()

# ------------------------------------------------------------
# ENCODE & LONG FORMAT
# ------------------------------------------------------------
sir_map = {"S": 0.0, "I": 0.5, "R": 1.0}
df_encoded = df.copy()

for col in antibiotic_cols:
    df_encoded[col] = df_encoded[col].map(sir_map)

df_long = df_encoded.melt(
    id_vars=required_cols,
    value_vars=antibiotic_cols,
    var_name="ANTIBIOTIC",
    value_name="RESISTANCE_SCORE"
)

df_long["RESISTANCE_LABEL"] = df_long["RESISTANCE_SCORE"].map(
    {0.0: "Sensitive", 0.5: "Intermediate", 1.0: "Resistant"}
)

# ------------------------------------------------------------
# SIDEBAR FILTERS
# ------------------------------------------------------------
st.sidebar.header("🔎 Filters")

gender_filter = st.sidebar.multiselect(
    "Gender",
    options=sorted(df["GENDER"].unique()),
    default=sorted(df["GENDER"].unique())
)

sample_filter = st.sidebar.multiselect(
    "Sample Type",
    options=sorted(df["SAMPLE_TYPE"].unique()),
    default=sorted(df["SAMPLE_TYPE"].unique())
)

df = df[df["GENDER"].isin(gender_filter) & df["SAMPLE_TYPE"].isin(sample_filter)]
df_encoded = df_encoded.loc[df.index]
df_long = df_long[df_long["SNO"].isin(df["SNO"])]

# ------------------------------------------------------------
# TABS
# ------------------------------------------------------------
tabs = st.tabs([
    "📊 Overview",
    "💊 Antibiotic Resistance",
    "🦠 MDR & ESBL",
    "⚠️ MAR Index & Risk",
    "🔗 Co-Resistance",
    "🧬 MDR Profiles",
    "🧪 ESBL vs Non-ESBL",
    "📐 MDR Structure",
    "📝 AMR Summary",
    "⬇️ Downloads"
])

# ============================================================
# TAB 1 — OVERVIEW
# ============================================================
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Isolates", df.shape[0])
    c2.metric("MDR (%)", f"{(df['MDR']=='YES').mean()*100:.1f}%")
    c3.metric("ESBL (%)", f"{(df['ESBL']=='YES').mean()*100:.1f}%")

    st.info(
        "This overview summarizes the overall antimicrobial resistance burden "
        "within the dataset."
    )

# ============================================================
# TAB 2 — ANTIBIOTIC RESISTANCE
# ============================================================
with tabs[1]:
    summary = (
        df_long.groupby(["ANTIBIOTIC", "RESISTANCE_LABEL"])
               .size()
               .reset_index(name="COUNT")
    )
    summary["PERCENT"] = summary.groupby("ANTIBIOTIC")["COUNT"].transform(
        lambda x: x / x.sum() * 100
    )

    fig = px.bar(
        summary,
        x="ANTIBIOTIC",
        y="PERCENT",
        color="RESISTANCE_LABEL",
        title="Antibiotic-wise Resistance Distribution (%)",
        color_discrete_map={
            "Resistant": "#d62728",
            "Intermediate": "#ff7f0e",
            "Sensitive": "#2ca02c"
        }
    )
    fig.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 3 — MDR & ESBL
# ============================================================
with tabs[2]:
    fig = px.pie(
        df["MDR"].value_counts().reset_index(),
        names="MDR",
        values="count",
        hole=0.4,
        title="MDR Prevalence"
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 4 — MAR INDEX
# ============================================================
with tabs[3]:
    fig = px.histogram(
        df,
        x="MAR_INDEX",
        nbins=20,
        title="Distribution of MAR Index"
    )
    fig.add_vline(x=0.2, line_dash="dash", line_color="red")
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 5 — CO-RESISTANCE
# ============================================================
with tabs[4]:
    corr = df_encoded[antibiotic_cols].eq(1.0).astype(int).corr()

    fig = px.imshow(
        corr,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Antibiotic Co-Resistance Heatmap"
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 6 — MDR PROFILES
# ============================================================
with tabs[5]:
    def profile(row):
        return ",".join([abx for abx in antibiotic_cols if row[abx] == 1.0])

    df_profiles = df_encoded.copy()
    df_profiles["PROFILE"] = df_profiles.apply(profile, axis=1)

    top_profiles = (
        df_profiles[df["MDR"] == "YES"]
        .groupby("PROFILE")
        .size()
        .reset_index(name="COUNT")
        .sort_values("COUNT", ascending=False)
        .head(10)
    )

    st.dataframe(top_profiles, use_container_width=True)

# ============================================================
# TAB 7 — ESBL vs NON-ESBL
# ============================================================
with tabs[6]:
    df_esbl = df_long.copy()
    df_esbl["IS_RESISTANT"] = (df_esbl["RESISTANCE_SCORE"] == 1.0).astype(int)

    esbl_summary = (
        df_esbl.groupby(["ANTIBIOTIC", "ESBL"])["IS_RESISTANT"]
        .mean().reset_index()
    )
    esbl_summary["PERCENT_RESISTANT"] = esbl_summary["IS_RESISTANT"] * 100

    fig = px.bar(
        esbl_summary,
        x="ANTIBIOTIC",
        y="PERCENT_RESISTANT",
        color="ESBL",
        barmode="group",
        title="ESBL vs Non-ESBL Resistance Comparison",
        labels={"PERCENT_RESISTANT": "% Resistant"}
    )
    fig.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 8 — MDR STRUCTURE
# ============================================================
with tabs[7]:
    df_mdr_long = df_long[df_long["MDR"] == "YES"].copy()
    df_mdr_long["IS_RESISTANT"] = (df_mdr_long["RESISTANCE_SCORE"] == 1.0).astype(int)

    mdr_drivers = (
        df_mdr_long.groupby("ANTIBIOTIC")["IS_RESISTANT"]
        .mean().reset_index()
    )
    mdr_drivers["PERCENT_RESISTANT"] = mdr_drivers["IS_RESISTANT"] * 100
    mdr_drivers = mdr_drivers.sort_values("PERCENT_RESISTANT", ascending=False)

    fig = px.bar(
        mdr_drivers,
        x="ANTIBIOTIC",
        y="PERCENT_RESISTANT",
        title="Antibiotics Driving MDR"
    )
    fig.update_layout(xaxis_tickangle=-45, yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 9 — AUTO SUMMARY (STEP 5D)
# ============================================================
with tabs[8]:
    total = df.shape[0]
    mdr_pct = (df["MDR"] == "YES").mean() * 100
    esbl_pct = (df["ESBL"] == "YES").mean() * 100
    high_mar = (df["MAR_INDEX"] > 0.2).mean() * 100
    median_mar = df["MAR_INDEX"].median()

    top_abx = (
        df_long[df_long["RESISTANCE_SCORE"] == 1.0]
        .groupby("ANTIBIOTIC")
        .size()
        .sort_values(ascending=False)
        .head(3)
        .index.tolist()
    )

    summary_text = f"""
A total of **{total} clinical isolates** were analyzed.

- **MDR prevalence:** {mdr_pct:.1f}%
- **ESBL prevalence:** {esbl_pct:.1f}%
- **Median MAR index:** {median_mar:.2f}
- **High-risk isolates (MAR > 0.2):** {high_mar:.1f}%

The antibiotics with the highest resistance burden were:
**{', '.join(top_abx)}**.
"""
    st.markdown(summary_text)

# ============================================================
# TAB 10 — DOWNLOADS
# ============================================================
with tabs[9]:
    st.markdown("### 📥 Data Tables")

    st.download_button(
        "Download cleaned dataset (wide)",
        df.to_csv(index=False),
        "amr_cleaned_wide.csv",
        "text/csv"
    )

    st.download_button(
        "Download long-format dataset",
        df_long.to_csv(index=False),
        "amr_long_format.csv",
        "text/csv"
    )

    res_summary = (
        df_long.groupby(["ANTIBIOTIC", "RESISTANCE_LABEL"])
        .size().unstack(fill_value=0)
    )
    res_summary_pct = (res_summary.div(res_summary.sum(axis=1), axis=0) * 100).round(2)

    st.download_button(
        "Download antibiotic resistance summary (%)",
        res_summary_pct.to_csv(),
        "antibiotic_resistance_summary.csv",
        "text/csv"
    )

    st.download_button(
        "Download MDR profiles",
        top_profiles.to_csv(index=False),
        "mdr_profiles.csv",
        "text/csv"
    )

    high_risk = df[df["MAR_INDEX"] > 0.2]
    st.download_button(
        "Download high-risk isolates (MAR > 0.2)",
        high_risk.to_csv(index=False),
        "high_risk_isolates.csv",
        "text/csv"
    )

    st.markdown("### 📝 Reports")

    st.download_button(
        "Download AMR summary (TXT)",
        summary_text,
        "amr_summary.txt",
        "text/plain"
    )

# ------------------------------------------------------------
# DISCLAIMER & FOOTER
# ------------------------------------------------------------
st.markdown(
    "---\n"
    "**Disclaimer:** This dashboard is intended for surveillance, research, "
    "and antimicrobial stewardship support only. "
    "It is not intended for diagnostic or treatment decision-making.\n\n"
    "**Developed by:** Vignesh S  \n"
    "**With guidance from:** Dr. <Name>, PhD"
)
