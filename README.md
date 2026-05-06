# Water Quality Dashboard

This Streamlit dashboard analyzes major ions and trace elements in water-quality samples.

## Features

- Upload CSV/XLSX data
- View sample-wise and parameter-wise statistics
- Plot bar charts, histograms and box plots
- Visualize sample points on an online OpenStreetMap basemap
- Generate correlation heatmap and scatter trendline
- Compare selected parameters with editable water-quality limits
- Export filtered data and compliance summaries

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy online on Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload `app.py`, `requirements.txt`, and the `data/` folder.
3. Go to Streamlit Community Cloud and deploy the repository.
4. Set `app.py` as the main file path.

## Data format

The default sample dataset is stored in:

```text
data/wql_jammu_feb2026.csv
```

Recommended key columns:

- Sample ID
- Sample Name
- Longitude
- Latitude
- Major ions in mg/L: Fluoride, Chloride, Nitrate, Sulfate, Sodium, Potassium, Calcium, Magnesium, Alkalinity
- Trace elements in ppb/µg/L: Fe_ppb, Mn_ppb, As_ppb, Pb_ppb, Cd_ppb, Cr_ppb, Cu_ppb, Zn_ppb, Ni_ppb, Se_ppb

The limit table inside the app is editable.
