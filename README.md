# 🧫 Clinical AMR Surveillance Dashboard

A Streamlit-based interactive dashboard for analyzing antimicrobial resistance (AMR)
patterns from **cleaned clinical antibiogram datasets**.

This application is designed for **AMR surveillance, epidemiology, research,
and antimicrobial stewardship support**.

---

## 🚀 Features

- Antibiotic-wise resistance distribution (S / I / R)
- Multidrug resistance (MDR) prevalence
- ESBL burden overview
- MAR index–based risk stratification
- Co-resistance heatmaps
- Dominant MDR resistance profiles
- Interactive filtering (gender, sample type)
- Downloadable processed datasets

---

## 📂 Expected Input Format

The application accepts **only cleaned Excel files (`.xlsx`)**.

### Each row represents **one clinical isolate**

### Required metadata columns
| Column name | Description |
|-----------|-------------|
| `SNO` | Isolate / sample ID |
| `SAMPLE_TYPE` | Sample source (e.g., URINE, BLOOD) |
| `GENDER` | M / F |
| `ESBL` | YES / NO |
| `MDR` | YES / NO |
| `MAR_INDEX` | Numeric (0–1) |

### Antibiotic columns
- One column per antibiotic
- Allowed values:  
  - `S` = Sensitive  
  - `I` = Intermediate (includes SDD)  
  - `R` = Resistant  

👉 **Use `sample_amr_data.xlsx` as a template.**

---

