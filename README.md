# VDC — Velocity Dollar Currency | Genesis Supply (Proof-of-Motion)

**The first thermodynamically capped digital asset backed exclusively by human mechanical work.  
All supply derived from lifetime Apple Health energy expenditure (2017–2025).**

---

## 🧬 Genesis Supply (Brandon — 2017‒2025)

- **Total Genesis Supply:** `5,238.6952936057 VDC`  
- **Total Joules Burned:** `5,514,416,099 J`  
- **Total Active Energy:** `1,317,977.08 kcal`  
- **Emission Rate:** `0.95 × 10⁻⁶ VDC per Joule` (fixed forever)

---

## 🛰 Sensor Record Summary

- **GPX Workouts Parsed:** `732`  
- **Total Tracked Distance:** `1,942.96 km`  
- **Peak Recorded Speed:** `112.94 m/s` (406.6 km/h)  
- **VFS-01 Anomalies Detected:** `3,114`  
- **Dataset Size:** `3.2 GB export.xml` streamed with zero dependencies  
- **Parser Runtime:** ~9 minutes on a 2014 MacBook Air  

Results produced with the included **single-file extractor** (`vdc_extract.py`).  
Reproducible on any machine with Python 3.8+.

---

## 📂 What This Repo Contains

- `vdc_extract.py` – Zero-dependency lifetime Apple Health extractor  
- `vdc.py` – VDC Moonshot Mint Engine v3.1 (thermodynamically enforced issuance)  
- `vdc_lifetime_summary.json` – Machine-readable Genesis data  
- `vdc_velocity_report.csv` – Per-GPX velocity + anomaly report  
- `vdc_summary.txt` – Human-readable Genesis summary  
- `export_snippet.xml` – Optional (first/last 300 lines only; anonymized)

---

## 🔗 Verification Pipeline

1. **Run extractor**
   ```bash
   python3 vdc_extract.py

joules = kcal * 4184
vdc = joules * 0.00000095

