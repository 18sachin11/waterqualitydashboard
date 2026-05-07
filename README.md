# Water Quality Analysis & Visualization Dashboard

A beautified Streamlit dashboard for analysing major ions and trace elements in water-quality samples.

**Website developed by Dr Sachchidanand Singh, Scientist B, Western Himalayan Regional Centre Jammu.**

## New workflow

1. Open the website.
2. Upload the water-quality data file in CSV or Excel format.
3. Click **Generate Report**.
4. The dashboard displays the full report with data preview, parameter-wise plots, spatial maps, correlation analysis, compliance screening, export options and a complete PDF project report.

A bundled sample dataset is included only for testing/demo purposes.

## Missing-value handling

Blank cells and common missing-value entries such as `NA`, `N/A`, `-`, `--`, and `NIL` are treated internally as missing numeric values. In the dashboard they are displayed as:

```text
Data not available
```

This approach allows maps and charts to work safely:

- numeric values are used for statistics, plots and compliance screening;
- missing values are **not** treated as zero;
- map markers are still generated for missing values using grey points and hover labels showing `Data not available`;
- export options include both an analysis-ready CSV and a display-ready CSV with `Data not available` filled in.

## Files

```text
app.py
requirements.txt
data/wql_jammu_feb2026.csv
README.md
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy online

1. Create a GitHub repository.
2. Upload `app.py`, `requirements.txt`, `README.md`, and the `data` folder.
3. Open Streamlit Community Cloud.
4. Select the GitHub repository.
5. Set the main file path as `app.py`.
6. Deploy the app.

## Recommended input columns

The app works best with columns like:

```text
Sample ID, Sample Name, Longitude, Latitude, Fluoride, Chloride, Nitrate, Sulfate, Calcium, Magnesium, Alkalinity, Fe_ppb, Mn_ppb, As_ppb, Pb_ppb
```

Longitude and Latitude are required for spatial visualization.


## PDF project report export

The final **Export** tab includes a **Prepare PDF Project Report** button. The generated PDF contains:

- project title and developer credit;
- dataset overview and sample-location preview;
- missing-data assessment where blank values are shown as `Data not available`;
- parameter-wise statistics;
- static bar charts, histograms and printable coordinate-based spatial plots;
- Pearson correlation heatmap;
- compliance screening table and chart;
- short explanatory interpretation for each selected parameter.

This PDF is intended as a project-style screening report and should be interpreted along with laboratory QA/QC records and the latest official water-quality standards.
