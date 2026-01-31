# ============================================================
# Clinical AMR Surveillance Dashboard
# FINAL POLISHED VERSION — Professional light gray theme, chart downloads, all features
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

# ------------------------------------------------------------
# PAGE CONFIG + PROFESSIONAL THEME
# ------------------------------------------------------------
st.set_page_config(
    page_title="Clinical AMR Surveillance Dashboard",
    page_icon="🧫",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/amr-dashboard',  # Update with your repo
        'Report a bug': "mailto:your.email@example.com",
        'About': "Clinical AMR Surveillance Dashboard v1.1 — Research & Stewardship Tool"
    }
)

# Professional light gray theme
st.markdown("""
    <style>
    .stApp {
        background-color: #f5f6f5;          /* Clean light gray – professional & calm */
    }
    section[data-testid="stSidebar"] {
        background-color: #e9ecef;          /* Slightly darker gray sidebar for contrast */
        border-right: 1px solid #dee2e6;
    }
    .stButton>button {
        background-color: #007BFF;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        transition: background-color 0.2s;
    }
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Segoe UI', sans-serif;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #ffffff;
        border-radius: 8px;
        padding: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stTab"] {
        font-size: 16px;
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 6px;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #007BFF;
        color: white;
    }
    .stMetric {
        background-color: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    hr {
        border-color: #dee2e6;
        margin: 2rem 0;
    }
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🧫 Clinical Antimicrobial Resistance (AMR) Surveillance Dashboard")
st.caption("For antimicrobial resistance surveillance, research, and stewardship support")

# ------------------------------------------------------------
# SIDEBAR — INPUT & DOCUMENTATION
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

with st.sidebar.expander("📋 Expected Input Format", expanded=False):
    st.markdown("""
**File type:** `.xlsx` (Excel)  
**Each row = one isolate**

### Required metadata columns
- `SNO`
- `SAMPLE_TYPE`
- `GENDER` (M / F)
- `ESBL` (YES / NO)
- `MDR` (YES / NO)
- `MAR_INDEX` (numeric, 0–1)

### Antibiotic columns
- One column per antibiotic
- Allowed values: **S**, **I**, **R**

Use the checkbox above to test with sample data.
    """)

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
if use_sample:
    with st.sidebar.spinner("Loading sample dataset..."):
        df = load_sample()
    st.sidebar.success("Using sample dataset")
elif uploaded_file:
    with st.sidebar.spinner("Loading uploaded file..."):
        df = load_uploaded(uploaded_file)
    st.sidebar.success("File uploaded successfully")
else:
    st.info("Upload a cleaned AMR dataset or enable sample data.")
    st.stop()

# ------------------------------------------------------------
# STANDARDIZE COLUMN NAMES
# ------------------------------------------------------------
df.columns = (
    df.columns.str.strip()
              .str.upper()
              .str.replace(" ", "_")
              .str.replace("/", "_")
)

# ------------------------------------------------------------
# VALIDATION (STRICT)
# ------------------------------------------------------------
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

# Apply filters with spinner
with st.spinner("Applying filters..."):
    df = df[df["GENDER"].isin(gender_filter) & df["SAMPLE_TYPE"].isin(sample_filter)]
    df_encoded = df_encoded.loc[df.index]
    df_long = df_long[df_long["SNO"].isin(df["SNO"])]

# ------------------------------------------------------------
# TABS (7 tabs — all features included)
# ------------------------------------------------------------
tabs = st.tabs([
    "📊 Overview",
    "💊 Antibiotic Resistance",
    "🦠 MDR & ESBL",
    "⚠️ MAR Index & Risk",
    "🔗 Co-Resistance",
    "🧬 MDR Profiles",
    "⬇️ Download"
])

# Helper to convert Plotly fig to PNG bytes
def fig_to_png(fig):
    img_bytes = io.BytesIO()
    fig.write_image(img_bytes, format="png", scale=2)
    img_bytes.seek(0)
    return img_bytes

# ============================================================
# TAB 1 — OVERVIEW
# ============================================================
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Isolates", df.shape[0])
    c2.metric("MDR (%)", f"{(df['MDR']=='YES').mean()*100:.1f}%")
    c3.metric("ESBL (%)", f"{(df['ESBL']=='YES').mean()*100:.1f}%")

    st.info(
        "This overview summarizes the antimicrobial resistance burden in the dataset. "
        "A high MDR or ESBL prevalence indicates limited treatment options "
        "and the need for enhanced stewardship."
    )

# ============================================================
# TAB 2 — ANTIBIOTIC RESISTANCE
# ============================================================
with tabs[1]:
    with st.spinner("Generating resistance distribution..."):
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
            },
            text_auto=".1f"
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            yaxis_range=[0, 100],
            xaxis_title="Antibiotic",
            yaxis_title="Resistance (%)",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns([3, 1])
        with col2:
            st.download_button(
                "⬇️ Download Chart (PNG)",
                fig_to_png(fig),
                "antibiotic_resistance_distribution.png",
                "image/png"
            )

    st.info(
        "Antibiotics with high resistance proportions may be unsuitable "
        "for empirical therapy in this population."
    )

# ============================================================
# TAB 3 — MDR & ESBL
# ============================================================
with tabs[2]:
    with st.spinner("Generating MDR pie chart..."):
        fig = px.pie(
            df["MDR"].value_counts().reset_index(),
            names="MDR",
            values="count",
            hole=0.4,
            title="MDR Prevalence",
            color_discrete_sequence=["#2ca02c", "#d62728"]
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

        st.download_button(
            "⬇️ Download Chart (PNG)",
            fig_to_png(fig),
            "mdr_prevalence.png",
            "image/png"
        )

    st.info(
        "MDR prevalence reflects the proportion of isolates resistant "
        "to multiple antibiotic classes."
    )

# ============================================================
# TAB 4 — MAR INDEX & RISK
# ============================================================
with tabs[3]:
    with st.spinner("Generating MAR index histogram..."):
        fig = px.histogram(
            df,
            x="MAR_INDEX",
            nbins=20,
            title="Distribution of MAR Index",
            color_discrete_sequence=["#17becf"]
        )
        fig.add_vline(x=0.2, line_dash="dash", line_color="red", annotation_text="High Risk >0.2")
        fig.update_layout(xaxis_title="MAR Index", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

        st.download_button(
            "⬇️ Download Chart (PNG)",
            fig_to_png(fig),
            "mar_index_distribution.png",
            "image/png"
        )

    st.info(
        "MAR index values above 0.2 indicate high-risk isolates "
        "with substantial antibiotic exposure."
    )

# ============================================================
# TAB 5 — CO-RESISTANCE
# ============================================================
with tabs[4]:
    with st.spinner("Calculating co-resistance matrix..."):
        corr = df_encoded[antibiotic_cols].eq(1.0).astype(int).corr()
        fig = px.imshow(
            corr,
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Antibiotic Co-Resistance Heatmap",
            text_auto=".2f"
        )
        fig.update_layout(coloraxis_showscale=True)
        st.plotly_chart(fig, use_container_width=True)

        st.download_button(
            "⬇️ Download Chart (PNG)",
            fig_to_png(fig),
            "co_resistance_heatmap.png",
            "image/png"
        )

    st.info(
        "Strong co-resistance suggests antibiotics that frequently fail together, "
        "limiting combination therapy options."
    )

# ============================================================
# TAB 6 — MDR PROFILES
# ============================================================
with tabs[5]:
    with st.spinner("Generating MDR resistance profiles..."):
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

    st.info(
        "These dominant MDR profiles represent common resistance architectures "
        "observed among multidrug-resistant isolates."
    )

# ============================================================
# TAB 7 — DOWNLOAD
# ============================================================
with tabs[6]:
    st.subheader("Export Data")
    st.download_button(
        "Download Cleaned Dataset (Wide format)",
        df.to_csv(index=False).encode('utf-8'),
        "amr_cleaned_wide.csv",
        "text/csv"
    )
    st.download_button(
        "Download Long-format Dataset",
        df_long.to_csv(index=False).encode('utf-8'),
        "amr_long_format.csv",
        "text/csv"
    )
    st.info("Downloaded files can be used for reporting, statistical analysis, or further visualization.")

# ------------------------------------------------------------
# FOOTER & DISCLAIMER
# ------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6c757d; font-size: 0.9em; padding: 2rem 0;'>
    Clinical AMR Surveillance Dashboard v1.1 | Built for research & antimicrobial stewardship<br>
    <strong>Disclaimer:</strong> This tool is for surveillance, research, and educational use only. 
    Results should be interpreted by qualified professionals. Not for direct clinical decision-making.
    </div>
    """,
    unsafe_allow_html=True
)
