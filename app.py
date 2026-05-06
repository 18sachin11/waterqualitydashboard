# app.py
# Water Quality Dashboard for major ions and trace elements
# Run: streamlit run app.py

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Water Quality Dashboard",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_default_data():
    return pd.read_csv("data/wql_jammu_feb2026.csv")

def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    rename_map = {
        "Long.": "Longitude",
        "Long": "Longitude",
        "Lon": "Longitude",
        "Lat.": "Latitude",
        "Lat": "Latitude",
        "Alk": "Alkalinity",
        "phosphate": "Phosphate",
        "sulfate": "Sulfate",
        "fluoride": "Fluoride",
        "chloride": "Chloride",
        "nitrate": "Nitrate",
        "nitrite": "Nitrite",
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})
    return df

def to_numeric_safely(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    id_like = {"Sample ID", "Sample Name", "Location", "Trace Location"}
    for c in df.columns:
        if c not in id_like:
            converted = pd.to_numeric(df[c], errors="coerce")
            if converted.notna().sum() > 0 or df[c].isna().all():
                df[c] = converted
    return df

def get_numeric_columns(df: pd.DataFrame):
    return [
        c for c in df.columns
        if pd.api.types.is_numeric_dtype(df[c])
        and c not in ["Sample No", "Longitude", "Latitude"]
    ]

def get_location_column(df: pd.DataFrame):
    for c in ["Sample Name", "Location", "Trace Location"]:
        if c in df.columns:
            return c
    return None

def status_from_limits(value, acceptable=None, permissible=None):
    if pd.isna(value):
        return "No data"
    if acceptable is None and permissible is None:
        return "No limit"
    if acceptable is not None and value <= acceptable:
        return "Acceptable"
    if permissible is not None and value <= permissible:
        return "Between acceptable & permissible"
    limit = permissible if permissible is not None else acceptable
    if value > limit:
        return "Above permissible"
    return "No limit"

def limit_for_column(col, limit_table):
    row = limit_table[limit_table["Parameter"] == col]
    if row.empty:
        return None, None
    a = row["Acceptable"].iloc[0]
    p = row["Permissible"].iloc[0]
    acceptable = None if pd.isna(a) else float(a)
    permissible = None if pd.isna(p) else float(p)
    return acceptable, permissible

def build_compliance(df, selected_cols, limit_table):
    loc_col = get_location_column(df)
    rows = []
    for _, r in df.iterrows():
        sample_id = r.get("Sample ID", r.get("Sample No", ""))
        location = r.get(loc_col, "") if loc_col else ""
        above = 0
        between = 0
        acceptable_n = 0
        no_data = 0

        for col in selected_cols:
            if col not in df.columns:
                continue
            a, p = limit_for_column(col, limit_table)
            status = status_from_limits(r[col], a, p)

            if status == "No data":
                no_data += 1
            elif status == "Above permissible":
                above += 1
            elif status == "Between acceptable & permissible":
                between += 1
            elif status == "Acceptable":
                acceptable_n += 1

        rows.append({
            "Sample ID": sample_id,
            "Location": location,
            "Acceptable": acceptable_n,
            "Between acceptable & permissible": between,
            "Above permissible": above,
            "No data": no_data,
            "Exceedance Score": above * 2 + between
        })

    return pd.DataFrame(rows)

def style_status(val):
    if val == "Above permissible":
        return "background-color: #ffcccc; color: #7a0000; font-weight: bold"
    if val == "Between acceptable & permissible":
        return "background-color: #fff2cc; color: #7a5a00"
    if val == "Acceptable":
        return "background-color: #d9ead3; color: #245c24"
    return ""

# Major ions are assumed to be in mg/L.
# Trace elements are assumed to be in ppb/µg/L.
# These values are editable inside the dashboard.
DEFAULT_LIMITS = pd.DataFrame([
    ["Fluoride", "mg/L", 1.0, 1.5, "Major ions"],
    ["Chloride", "mg/L", 250.0, 1000.0, "Major ions"],
    ["Nitrate", "mg/L", 45.0, 45.0, "Major ions"],
    ["Sulfate", "mg/L", 200.0, 400.0, "Major ions"],
    ["Calcium", "mg/L", 75.0, 200.0, "Major ions"],
    ["Magnesium", "mg/L", 30.0, 100.0, "Major ions"],
    ["Alkalinity", "mg/L", 200.0, 600.0, "Major ions"],
    ["Fe_ppb", "ppb", 300.0, 300.0, "Trace elements"],
    ["Mn_ppb", "ppb", 100.0, 300.0, "Trace elements"],
    ["As_ppb", "ppb", 10.0, 50.0, "Trace elements"],
    ["Pb_ppb", "ppb", 10.0, 10.0, "Trace elements"],
    ["Cd_ppb", "ppb", 3.0, 3.0, "Trace elements"],
    ["Cr_ppb", "ppb", 50.0, 50.0, "Trace elements"],
    ["Cu_ppb", "ppb", 50.0, 1500.0, "Trace elements"],
    ["Zn_ppb", "ppb", 5000.0, 15000.0, "Trace elements"],
    ["Ni_ppb", "ppb", 20.0, 20.0, "Trace elements"],
    ["Se_ppb", "ppb", 10.0, 10.0, "Trace elements"],
], columns=["Parameter", "Unit", "Acceptable", "Permissible", "Group"])

st.sidebar.title("💧 Water Quality Dashboard")
st.sidebar.caption("Major ions + trace elements analysis")

uploaded_file = st.sidebar.file_uploader(
    "Upload combined CSV/XLSX dataset",
    type=["csv", "xlsx"],
    help="Recommended columns: Sample ID, Sample Name, Longitude, Latitude, Fluoride, Nitrate, Fe_ppb, As_ppb, etc."
)

if uploaded_file is not None:
    if uploaded_file.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
else:
    df = load_default_data()

df = clean_columns(df)
df = to_numeric_safely(df)

loc_col = get_location_column(df)
numeric_cols = get_numeric_columns(df)

with st.sidebar.expander("Filter samples", expanded=True):
    if loc_col:
        all_locations = sorted(df[loc_col].dropna().astype(str).unique().tolist())
        selected_locations = st.multiselect(
            "Select locations",
            all_locations,
            default=all_locations
        )
        df = df[df[loc_col].astype(str).isin(selected_locations)]

    default_params = [
        c for c in [
            "Fluoride", "Nitrate", "Sulfate", "Calcium", "Magnesium",
            "Fe_ppb", "Mn_ppb", "As_ppb", "Pb_ppb"
        ]
        if c in numeric_cols
    ]
    selected_params = st.multiselect(
        "Select parameters for analysis",
        numeric_cols,
        default=default_params
    )

with st.sidebar.expander("Editable standards / limits", expanded=False):
    st.caption("Values are editable. Use local BIS/WHO/project-specific limits as required.")
    limit_table = st.data_editor(
        DEFAULT_LIMITS,
        num_rows="dynamic",
        use_container_width=True,
        key="limits_editor"
    )

st.title("Water Quality Analysis & Visualization Dashboard")
st.markdown(
    "This dashboard supports exploratory analysis, spatial visualization, parameter-wise comparison, "
    "correlation analysis, and compliance screening for water-quality samples."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Samples", len(df))
c2.metric("Numeric parameters", len(numeric_cols))

if "Longitude" in df.columns and "Latitude" in df.columns:
    c3.metric("Mapped samples", int(df[["Longitude", "Latitude"]].dropna().shape[0]))
else:
    c3.metric("Mapped samples", "N/A")

if selected_params:
    comp_tmp = build_compliance(df, selected_params, limit_table)
    c4.metric("Samples above permissible", int((comp_tmp["Above permissible"] > 0).sum()))
else:
    c4.metric("Samples above permissible", "N/A")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📄 Data",
    "📊 Parameter analysis",
    "🗺️ Spatial map",
    "🔥 Correlation",
    "✅ Compliance",
    "⬇️ Export"
])

with tab1:
    st.subheader("Dataset preview")
    st.dataframe(df, use_container_width=True, height=380)

    st.subheader("Summary statistics")
    if numeric_cols:
        summary = df[numeric_cols].describe().T
        summary["missing_count"] = df[numeric_cols].isna().sum()
        summary["missing_%"] = (df[numeric_cols].isna().mean() * 100).round(1)
        st.dataframe(summary.round(3), use_container_width=True)
    else:
        st.warning("No numeric columns detected.")

with tab2:
    st.subheader("Parameter-wise analysis")
    if not selected_params:
        st.info("Select one or more parameters from the sidebar.")
    else:
        parameter = st.selectbox("Choose parameter", selected_params)
        plot_df = df.copy()
        if loc_col is None:
            plot_df["Location"] = plot_df.index.astype(str)
            loc_col_use = "Location"
        else:
            loc_col_use = loc_col

        acceptable, permissible = limit_for_column(parameter, limit_table)
        unit_row = limit_table[limit_table["Parameter"] == parameter]
        unit = unit_row["Unit"].iloc[0] if not unit_row.empty else ""

        col_a, col_b = st.columns([2, 1])

        with col_a:
            fig = px.bar(
                plot_df.sort_values(parameter, ascending=False),
                x=loc_col_use,
                y=parameter,
                text=parameter,
                title=f"{parameter} concentration by sample",
                labels={
                    parameter: f"{parameter} ({unit})" if unit else parameter,
                    loc_col_use: "Location"
                }
            )
            fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            if acceptable is not None:
                fig.add_hline(y=acceptable, line_dash="dash", annotation_text="Acceptable limit")
            if permissible is not None and permissible != acceptable:
                fig.add_hline(y=permissible, line_dash="dot", annotation_text="Permissible limit")
            fig.update_layout(xaxis_tickangle=-35, height=520)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            values = plot_df[parameter].dropna()
            st.metric("Minimum", f"{values.min():.3f}" if not values.empty else "N/A")
            st.metric("Mean", f"{values.mean():.3f}" if not values.empty else "N/A")
            st.metric("Maximum", f"{values.max():.3f}" if not values.empty else "N/A")

            if acceptable is not None or permissible is not None:
                status_counts = plot_df[parameter].apply(
                    lambda x: status_from_limits(x, acceptable, permissible)
                ).value_counts()
                st.write("Status count")
                st.dataframe(status_counts.rename("count"), use_container_width=True)

        col_h, col_box = st.columns(2)

        with col_h:
            fig_hist = px.histogram(
                plot_df,
                x=parameter,
                nbins=10,
                title=f"Histogram: {parameter}",
                labels={parameter: f"{parameter} ({unit})" if unit else parameter}
            )
            fig_hist.update_layout(height=420)
            st.plotly_chart(fig_hist, use_container_width=True)

        with col_box:
            fig_box = px.box(
                plot_df,
                y=parameter,
                points="all",
                hover_data=[loc_col_use],
                title=f"Box plot: {parameter}",
                labels={parameter: f"{parameter} ({unit})" if unit else parameter}
            )
            fig_box.update_layout(height=420)
            st.plotly_chart(fig_box, use_container_width=True)

with tab3:
    st.subheader("Spatial visualization")

    if "Longitude" not in df.columns or "Latitude" not in df.columns:
        st.warning("Longitude and Latitude columns are required for map visualization.")
    elif not selected_params:
        st.info("Select at least one parameter from the sidebar.")
    else:
        map_param = st.selectbox("Parameter for map colour/size", selected_params, key="map_param")
        map_df = df.dropna(subset=["Longitude", "Latitude"]).copy()

        if loc_col is None:
            map_df["Location"] = map_df.index.astype(str)
            loc_col_use = "Location"
        else:
            loc_col_use = loc_col

        fig_map = px.scatter_mapbox(
            map_df,
            lat="Latitude",
            lon="Longitude",
            color=map_param,
            size=map_param,
            size_max=22,
            hover_name=loc_col_use,
            hover_data={
                "Latitude": ":.4f",
                "Longitude": ":.4f",
                map_param: ":.3f"
            },
            zoom=10,
            height=620,
            title=f"Spatial distribution of {map_param}",
            mapbox_style="open-street-map"
        )
        st.plotly_chart(fig_map, use_container_width=True)

        st.caption("Tip: use the lasso/box tools in the Plotly toolbar to inspect clusters interactively.")

with tab4:
    st.subheader("Correlation analysis")
    corr_cols = st.multiselect(
        "Select parameters for correlation matrix",
        numeric_cols,
        default=selected_params if selected_params else numeric_cols[:8]
    )

    if len(corr_cols) < 2:
        st.info("Select at least two numeric parameters.")
    else:
        corr = df[corr_cols].corr(method="pearson")
        fig_corr = px.imshow(
            corr,
            text_auto=".2f",
            aspect="auto",
            title="Pearson correlation matrix"
        )
        fig_corr.update_layout(height=700)
        st.plotly_chart(fig_corr, use_container_width=True)

        xcol, ycol = st.columns(2)
        with xcol:
            x_param = st.selectbox("X parameter", corr_cols, index=0)
        with ycol:
            y_param = st.selectbox("Y parameter", corr_cols, index=1 if len(corr_cols) > 1 else 0)

        fig_sc = px.scatter(
            df,
            x=x_param,
            y=y_param,
            trendline="ols",
            hover_name=loc_col if loc_col else None,
            title=f"{x_param} vs {y_param}"
        )
        fig_sc.update_layout(height=500)
        st.plotly_chart(fig_sc, use_container_width=True)

with tab5:
    st.subheader("Compliance screening")
    st.caption(
        "Status is computed using the editable limit table in the sidebar. "
        "For trace elements, columns ending in _ppb are compared against ppb/µg/L limits."
    )

    if not selected_params:
        st.info("Select parameters from the sidebar.")
    else:
        comp = build_compliance(df, selected_params, limit_table)
        comp = comp.sort_values("Exceedance Score", ascending=False)
        st.dataframe(comp, use_container_width=True)

        fig_score = px.bar(
            comp,
            x="Location",
            y=["Above permissible", "Between acceptable & permissible"],
            title="Compliance exceedance count by sample",
            labels={
                "value": "Number of parameters",
                "Location": "Location",
                "variable": "Status"
            }
        )
        fig_score.update_layout(xaxis_tickangle=-35, height=500)
        st.plotly_chart(fig_score, use_container_width=True)

        status_matrix = pd.DataFrame()
        if loc_col:
            status_matrix["Location"] = df[loc_col].values
        else:
            status_matrix["Location"] = df.index.astype(str)

        for col in selected_params:
            a, p = limit_for_column(col, limit_table)
            status_matrix[col] = df[col].apply(lambda x: status_from_limits(x, a, p))

        st.subheader("Parameter status matrix")
        st.dataframe(
            status_matrix.style.map(style_status, subset=selected_params),
            use_container_width=True,
            height=380
        )

with tab6:
    st.subheader("Export processed outputs")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered dataset as CSV",
        data=csv,
        file_name="filtered_water_quality_data.csv",
        mime="text/csv"
    )

    if selected_params:
        comp = build_compliance(df, selected_params, limit_table)
        comp_csv = comp.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download compliance summary as CSV",
            data=comp_csv,
            file_name="water_quality_compliance_summary.csv",
            mime="text/csv"
        )

    limits_csv = limit_table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download edited limits table as CSV",
        data=limits_csv,
        file_name="water_quality_limits.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption(
    "Note: This dashboard is for exploratory screening and visualization. "
    "Final drinking-water interpretation should use the latest notified standards and laboratory QA/QC validation."
)
