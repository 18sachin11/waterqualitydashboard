# app.py
# Water Quality Dashboard for major ions and trace elements
# Run: streamlit run app.py

import io
import tempfile
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

st.set_page_config(
    page_title="Water Quality Dashboard | WHRC Jammu",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_NOT_AVAILABLE = "Data not available"
DEVELOPER_TEXT = "Website developed by Dr Sachchidanand Singh, Scientist B, Western Himalayan Regional Centre Jammu"
MISSING_TOKENS = {
    "", " ", "NA", "N/A", "na", "n/a", "Na", "nan", "NaN",
    "-", "--", "nil", "NIL", "None", "none", DATA_NOT_AVAILABLE,
    DATA_NOT_AVAILABLE.lower()
}

# A clean Plotly template for a softer dashboard look.
px.defaults.template = "plotly_white"
px.defaults.color_continuous_scale = "Viridis"

st.markdown(
    """
    <style>
    :root {
        --primary: #075985;
        --secondary: #0e7490;
        --accent: #14b8a6;
        --soft-bg: #f8fafc;
        --card: #ffffff;
        --text: #0f172a;
        --muted: #64748b;
        --border: #e2e8f0;
    }

    .stApp {
        background: linear-gradient(180deg, #f0f9ff 0%, #f8fafc 35%, #ffffff 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #082f49 0%, #0f766e 100%);
    }

    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] .stMultiSelect div,
    [data-testid="stSidebar"] .stTextInput div,
    [data-testid="stSidebar"] .stNumberInput div,
    [data-testid="stSidebar"] .stDataFrame div,
    [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #0f172a !important;
    }

    .hero {
        padding: 2.3rem 2rem 1.8rem 2rem;
        border-radius: 28px;
        background:
            radial-gradient(circle at top left, rgba(20,184,166,0.30), transparent 28%),
            linear-gradient(135deg, #075985 0%, #0f766e 58%, #0891b2 100%);
        color: white;
        box-shadow: 0 22px 70px rgba(8, 47, 73, 0.20);
        margin-bottom: 1.2rem;
        border: 1px solid rgba(255,255,255,0.25);
    }

    .hero h1 {
        font-size: 2.45rem;
        line-height: 1.15;
        margin: 0 0 0.7rem 0;
        font-weight: 800;
        color: #ffffff;
    }

    .hero p {
        font-size: 1.05rem;
        color: rgba(255,255,255,0.93);
        max-width: 980px;
        margin-bottom: 0.85rem;
    }

    .developer-badge {
        display: inline-block;
        padding: 0.55rem 0.85rem;
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.28);
        border-radius: 999px;
        font-weight: 650;
        color: #ffffff;
    }

    .upload-card, .info-card, .metric-card, .footer-card {
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 1.2rem 1.35rem;
        box-shadow: 0 14px 40px rgba(15, 23, 42, 0.08);
    }

    .upload-card {
        border-left: 7px solid var(--accent);
        margin-bottom: 1rem;
    }

    .upload-card h3, .info-card h4 {
        color: var(--text);
        margin-top: 0;
    }

    .upload-card p, .info-card p, .footer-card p {
        color: var(--muted);
    }

    .section-title {
        padding: 0.2rem 0 0.5rem 0;
        color: #0f172a;
        font-weight: 800;
    }

    .metric-card h4 {
        color: var(--muted);
        font-size: 0.88rem;
        margin: 0 0 0.3rem 0;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .metric-card h2 {
        color: var(--primary);
        margin: 0;
        font-size: 1.9rem;
    }

    .stButton > button {
        border-radius: 999px;
        min-height: 3rem;
        font-weight: 750;
        border: none;
        box-shadow: 0 12px 28px rgba(14, 116, 144, 0.22);
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 0.8rem 1rem;
        box-shadow: 0 10px 28px rgba(15,23,42,0.07);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 999px;
        padding: 0.55rem 1rem;
        background: #e0f2fe;
        color: #075985;
        font-weight: 700;
    }

    .stTabs [aria-selected="true"] {
        background: #0e7490 !important;
        color: white !important;
    }

    .small-note {
        color: #64748b;
        font-size: 0.92rem;
    }
    </style>
    """,
    unsafe_allow_html=True
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


def standardize_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Convert blank strings and common missing-value tokens to NaN.

    The app displays NaN as 'Data not available', but keeps the internal
    value as NaN so maps, plots, correlations and compliance checks remain valid.
    """
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c]):
            df[c] = df[c].apply(
                lambda x: np.nan
                if pd.isna(x) or str(x).strip() in MISSING_TOKENS
                else str(x).strip()
            )
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


def display_value(value):
    if pd.isna(value):
        return DATA_NOT_AVAILABLE
    return value


def make_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return a display/export copy where blank values are shown explicitly."""
    display_df = df.copy()
    for c in display_df.columns:
        display_df[c] = display_df[c].map(display_value)
    return display_df


def format_number_or_na(value, digits=3):
    if pd.isna(value):
        return DATA_NOT_AVAILABLE
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def status_from_limits(value, acceptable=None, permissible=None):
    if pd.isna(value):
        return DATA_NOT_AVAILABLE
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

            if status == DATA_NOT_AVAILABLE:
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
            DATA_NOT_AVAILABLE: no_data,
            "Exceedance Score": above * 2 + between
        })

    return pd.DataFrame(rows)


def style_status(val):
    if val == "Above permissible":
        return "background-color: #fee2e2; color: #7f1d1d; font-weight: bold"
    if val == "Between acceptable & permissible":
        return "background-color: #fef3c7; color: #78350f"
    if val == "Acceptable":
        return "background-color: #dcfce7; color: #14532d"
    if val == DATA_NOT_AVAILABLE:
        return "background-color: #e5e7eb; color: #374151"
    return ""


def add_missing_value_note(plot_df, parameter, loc_col_use):
    missing_df = plot_df[pd.isna(plot_df[parameter])]
    if not missing_df.empty:
        with st.expander(f"Samples where {parameter} is {DATA_NOT_AVAILABLE}"):
            st.dataframe(
                missing_df[[c for c in ["Sample ID", loc_col_use] if c in missing_df.columns]],
                use_container_width=True
            )


def make_map_figure(map_df, map_param, loc_col_use):
    map_df = map_df.copy()
    map_df["_value_label"] = map_df[map_param].apply(lambda x: format_number_or_na(x, 3))
    map_df["_status"] = np.where(map_df[map_param].notna(), "Value available", DATA_NOT_AVAILABLE)

    valid_df = map_df[map_df[map_param].notna()].copy()
    missing_df = map_df[map_df[map_param].isna()].copy()

    fig = go.Figure()

    if not valid_df.empty:
        vals = valid_df[map_param].astype(float)
        abs_vals = vals.abs()
        positive = abs_vals[abs_vals > 0]
        min_positive = float(positive.min()) if not positive.empty else 1.0
        valid_df["_marker_size_value"] = abs_vals.where(abs_vals > 0, min_positive * 0.25)

        fig = px.scatter_mapbox(
            valid_df,
            lat="Latitude",
            lon="Longitude",
            color=map_param,
            size="_marker_size_value",
            size_max=24,
            hover_name=loc_col_use,
            hover_data={
                "Latitude": ":.4f",
                "Longitude": ":.4f",
                map_param: ":.3f",
                "_marker_size_value": False,
                "_value_label": False,
                "_status": False,
            },
        )

    if not missing_df.empty:
        fig.add_trace(
            go.Scattermapbox(
                lat=missing_df["Latitude"],
                lon=missing_df["Longitude"],
                mode="markers",
                marker=dict(size=14, color="lightgray", opacity=0.90),
                name=f"{map_param}: {DATA_NOT_AVAILABLE}",
                customdata=np.stack([
                    missing_df[loc_col_use].astype(str),
                    missing_df["Latitude"].round(4).astype(str),
                    missing_df["Longitude"].round(4).astype(str),
                    missing_df["_value_label"].astype(str),
                ], axis=-1),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Latitude: %{customdata[1]}<br>"
                    "Longitude: %{customdata[2]}<br>"
                    f"{map_param}: %{{customdata[3]}}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=10,
        mapbox_center={
            "lat": float(map_df["Latitude"].mean()),
            "lon": float(map_df["Longitude"].mean()),
        },
        height=640,
        title=f"Spatial distribution of {map_param}",
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        legend_title_text="Map legend",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig



def _pdf_cell(value, max_chars=42):
    """Return compact text for ReportLab table cells."""
    if pd.isna(value):
        return DATA_NOT_AVAILABLE
    txt = str(value)
    return txt if len(txt) <= max_chars else txt[: max_chars - 3] + "..."


def _pdf_table(data, col_widths=None, font_size=7.2, header_bg="#075985"):
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _save_bar_chart(df, parameter, loc_col_use, acceptable, permissible, unit, out_path):
    plot_df = df.copy()
    labels = plot_df[loc_col_use].astype(str).tolist()
    values = plot_df[parameter]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    x = np.arange(len(plot_df))
    ax.bar(x, values.fillna(0))
    if values.isna().any():
        for xi, yi, is_missing in zip(x, values.fillna(0), values.isna()):
            if is_missing:
                ax.text(xi, max(float(values.max(skipna=True) or 1) * 0.03, 0.01), "NA", ha="center", va="bottom", fontsize=8)
    if acceptable is not None:
        ax.axhline(acceptable, linestyle="--", linewidth=1, label="Acceptable limit")
    if permissible is not None and permissible != acceptable:
        ax.axhline(permissible, linestyle=":", linewidth=1, label="Permissible limit")
    ax.set_title(f"{parameter} concentration by sample")
    ax.set_ylabel(f"{parameter} ({unit})" if unit else parameter)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    if acceptable is not None or permissible is not None:
        ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_histogram(df, parameter, unit, out_path):
    values = df[parameter].dropna()
    fig, ax = plt.subplots(figsize=(7, 3.8))
    if values.empty:
        ax.text(0.5, 0.5, f"No numeric values available for {parameter}", ha="center", va="center")
        ax.set_axis_off()
    else:
        ax.hist(values, bins=min(10, max(3, len(values))))
        ax.set_title(f"Distribution of {parameter}")
        ax.set_xlabel(f"{parameter} ({unit})" if unit else parameter)
        ax.set_ylabel("Frequency")
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_spatial_chart(df, parameter, loc_col_use, out_path):
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    if "Longitude" not in df.columns or "Latitude" not in df.columns:
        ax.text(0.5, 0.5, "Longitude and Latitude columns not available", ha="center", va="center")
        ax.set_axis_off()
    else:
        map_df = df.dropna(subset=["Longitude", "Latitude"]).copy()
        if map_df.empty:
            ax.text(0.5, 0.5, "No valid coordinates available", ha="center", va="center")
            ax.set_axis_off()
        else:
            valid = map_df[map_df[parameter].notna()]
            missing = map_df[map_df[parameter].isna()]
            if not valid.empty:
                sc = ax.scatter(valid["Longitude"], valid["Latitude"], c=valid[parameter], s=90, alpha=0.85)
                fig.colorbar(sc, ax=ax, label=parameter)
            if not missing.empty:
                ax.scatter(missing["Longitude"], missing["Latitude"], marker="x", s=80, label=DATA_NOT_AVAILABLE)
            for _, row in map_df.iterrows():
                ax.annotate(str(row[loc_col_use])[:14], (row["Longitude"], row["Latitude"]), fontsize=7, xytext=(3, 3), textcoords="offset points")
            ax.set_title(f"Spatial distribution of {parameter}")
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            ax.grid(alpha=0.25)
            if not missing.empty:
                ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_correlation_heatmap(df, corr_cols, out_path):
    corr = df[corr_cols].corr(method="pearson", min_periods=2)
    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    if corr.empty or corr.isna().all().all():
        ax.text(0.5, 0.5, "Correlation matrix could not be generated", ha="center", va="center")
        ax.set_axis_off()
    else:
        im = ax.imshow(corr, vmin=-1, vmax=1)
        ax.set_xticks(np.arange(len(corr.columns)))
        ax.set_yticks(np.arange(len(corr.index)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=7)
        ax.set_yticklabels(corr.index, fontsize=7)
        for i in range(len(corr.index)):
            for j in range(len(corr.columns)):
                val = corr.iloc[i, j]
                ax.text(j, i, "NA" if pd.isna(val) else f"{val:.2f}", ha="center", va="center", fontsize=6)
        ax.set_title("Pearson correlation matrix")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _save_compliance_chart(comp_df, out_path):
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    if comp_df.empty:
        ax.text(0.5, 0.5, "Compliance summary not available", ha="center", va="center")
        ax.set_axis_off()
    else:
        x = np.arange(len(comp_df))
        above = comp_df["Above permissible"].to_numpy()
        between = comp_df["Between acceptable & permissible"].to_numpy()
        missing = comp_df[DATA_NOT_AVAILABLE].to_numpy()
        ax.bar(x, above, label="Above permissible")
        ax.bar(x, between, bottom=above, label="Between acceptable & permissible")
        ax.bar(x, missing, bottom=above + between, label=DATA_NOT_AVAILABLE)
        ax.set_xticks(x)
        ax.set_xticklabels(comp_df["Location"].astype(str), rotation=35, ha="right", fontsize=8)
        ax.set_ylabel("Number of parameters")
        ax.set_title("Compliance and missing-data count by sample")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _add_image(story, path, width=6.8 * inch):
    try:
        img = Image(path)
        ratio = img.imageHeight / float(img.imageWidth)
        img.drawWidth = width
        img.drawHeight = width * ratio
        story.append(img)
        story.append(Spacer(1, 0.12 * inch))
    except Exception:
        pass


def _parameter_explanation(df, parameter, acceptable, permissible):
    values = df[parameter].dropna()
    missing_n = int(df[parameter].isna().sum())
    if values.empty:
        return f"For {parameter}, no numeric observations are available in the selected dataset. All available locations are therefore shown as {DATA_NOT_AVAILABLE} and excluded from numeric statistics."

    mean_v = values.mean()
    min_v = values.min()
    max_v = values.max()
    status_counts = df[parameter].apply(lambda x: status_from_limits(x, acceptable, permissible)).value_counts().to_dict()
    above = int(status_counts.get("Above permissible", 0))
    between = int(status_counts.get("Between acceptable & permissible", 0))
    acceptable_count = int(status_counts.get("Acceptable", 0))
    return (
        f"For {parameter}, the observed values range from {min_v:.3f} to {max_v:.3f}, "
        f"with a mean concentration of {mean_v:.3f}. In the selected dataset, {acceptable_count} samples are within the acceptable limit, "
        f"{between} samples fall between acceptable and permissible limits, and {above} samples are above the permissible limit. "
        f"Missing observations for this parameter: {missing_n}. Missing values are not treated as zero."
    )


def generate_project_report_pdf(df, selected_params, limit_table, data_source_label, loc_col, numeric_cols):
    """Create a downloadable PDF project report from the current dashboard state."""
    if loc_col is None:
        report_df = df.copy()
        report_df["Location"] = report_df.index.astype(str)
        loc_col_use = "Location"
    else:
        report_df = df.copy()
        loc_col_use = loc_col

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=34,
        leftMargin=34,
        topMargin=34,
        bottomMargin=30,
        title="Water Quality Analysis Project Report",
        author="Dr Sachchidanand Singh",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterTitle", parent=styles["Title"], alignment=1, textColor=colors.HexColor("#075985")))
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#64748B"), leading=10))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], textColor=colors.HexColor("#0F766E"), spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", parent=styles["BodyText"], fontSize=9.5, leading=13, spaceAfter=6))

    story = []
    story.append(Paragraph("Water Quality Analysis Project Report", styles["CenterTitle"]))
    story.append(Paragraph(DEVELOPER_TEXT, styles["SmallMuted"]))
    story.append(Spacer(1, 0.16 * inch))
    story.append(
        Paragraph(
            f"Generated on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}<br/>Data source: {_pdf_cell(data_source_label, 90)}",
            styles["SmallMuted"],
        )
    )
    story.append(Spacer(1, 0.15 * inch))
    story.append(
        Paragraph(
            "This project report summarizes the uploaded water-quality dataset through data screening, missing-value assessment, "
            "parameter-wise statistics, spatial distribution plots, correlation analysis and drinking-water compliance screening. "
            f"Blank values are reported as {DATA_NOT_AVAILABLE} and are excluded from numeric calculations rather than being treated as zero.",
            styles["Body"],
        )
    )

    mapped_n = int(report_df[["Longitude", "Latitude"]].dropna().shape[0]) if {"Longitude", "Latitude"}.issubset(report_df.columns) else 0
    total_missing = int(report_df[selected_params].isna().sum().sum()) if selected_params else 0
    comp = build_compliance(report_df, selected_params, limit_table) if selected_params else pd.DataFrame()
    above_samples = int((comp["Above permissible"] > 0).sum()) if not comp.empty else 0

    kpi_data = [
        ["Indicator", "Value"],
        ["Number of samples", str(len(report_df))],
        ["Mapped samples", str(mapped_n)],
        ["Selected parameters", str(len(selected_params))],
        [f"Total {DATA_NOT_AVAILABLE} cells", str(total_missing)],
        ["Samples with at least one above-permissible parameter", str(above_samples)],
    ]
    story.append(_pdf_table(kpi_data, col_widths=[3.8 * inch, 2.1 * inch], font_size=8.2))

    story.append(Paragraph("1. Dataset overview", styles["Section"]))
    preview_cols = [c for c in ["Sample ID", loc_col_use, "Longitude", "Latitude"] if c in report_df.columns]
    if preview_cols:
        preview = make_display_df(report_df[preview_cols]).head(12)
        table_data = [preview.columns.tolist()] + [[_pdf_cell(v, 32) for v in row] for row in preview.values.tolist()]
        story.append(_pdf_table(table_data, font_size=7.0))
        story.append(Spacer(1, 0.08 * inch))
    story.append(
        Paragraph(
            "The dataset has been standardized by converting blank strings and common missing-value tokens such as NA, N/A, NIL and dashes "
            f"to missing numeric values. In all exported display tables these values are written as {DATA_NOT_AVAILABLE}.",
            styles["Body"],
        )
    )

    if selected_params:
        story.append(Paragraph("2. Parameter-wise statistical summary", styles["Section"]))
        summary_rows = [["Parameter", "Unit", "Count", "Missing", "Min", "Mean", "Median", "Max"]]
        for param in selected_params:
            values = report_df[param].dropna()
            unit_row = limit_table[limit_table["Parameter"] == param]
            unit = unit_row["Unit"].iloc[0] if not unit_row.empty else ""
            if values.empty:
                summary_rows.append([param, unit, "0", str(int(report_df[param].isna().sum())), "NA", "NA", "NA", "NA"])
            else:
                summary_rows.append([
                    param,
                    unit,
                    str(int(values.count())),
                    str(int(report_df[param].isna().sum())),
                    f"{values.min():.3f}",
                    f"{values.mean():.3f}",
                    f"{values.median():.3f}",
                    f"{values.max():.3f}",
                ])
        story.append(_pdf_table(summary_rows, font_size=6.8))
        story.append(Spacer(1, 0.12 * inch))

        missing_rows = [["Parameter", "Available", DATA_NOT_AVAILABLE, "Missing (%)"]]
        for param in selected_params:
            missing = int(report_df[param].isna().sum())
            available = int(report_df[param].notna().sum())
            pct = (missing / len(report_df) * 100) if len(report_df) else 0
            missing_rows.append([param, str(available), str(missing), f"{pct:.1f}"])
        story.append(Paragraph("Missing-data summary", styles["Heading3"]))
        story.append(_pdf_table(missing_rows, col_widths=[2.5 * inch, 1.1 * inch, 1.5 * inch, 1.1 * inch], font_size=7.2))

        with tempfile.TemporaryDirectory() as tmpdir:
            story.append(PageBreak())
            story.append(Paragraph("3. Parameter-wise visual analysis and interpretation", styles["Section"]))
            for i, param in enumerate(selected_params, 1):
                acceptable, permissible = limit_for_column(param, limit_table)
                unit_row = limit_table[limit_table["Parameter"] == param]
                unit = unit_row["Unit"].iloc[0] if not unit_row.empty else ""
                story.append(Paragraph(f"3.{i} {param}", styles["Heading3"]))
                story.append(Paragraph(_parameter_explanation(report_df, param, acceptable, permissible), styles["Body"]))

                bar_path = f"{tmpdir}/{i}_{param}_bar.png".replace("/", "/")
                hist_path = f"{tmpdir}/{i}_{param}_hist.png".replace("/", "/")
                map_path = f"{tmpdir}/{i}_{param}_spatial.png".replace("/", "/")
                _save_bar_chart(report_df, param, loc_col_use, acceptable, permissible, unit, bar_path)
                _add_image(story, bar_path, width=6.9 * inch)
                _save_histogram(report_df, param, unit, hist_path)
                _add_image(story, hist_path, width=5.9 * inch)
                _save_spatial_chart(report_df, param, loc_col_use, map_path)
                _add_image(story, map_path, width=5.9 * inch)
                if i != len(selected_params):
                    story.append(Spacer(1, 0.08 * inch))

            story.append(PageBreak())
            story.append(Paragraph("4. Correlation analysis", styles["Section"]))
            corr_cols = [c for c in selected_params if report_df[c].notna().sum() >= 2]
            if len(corr_cols) >= 2:
                corr_path = f"{tmpdir}/correlation_heatmap.png"
                _save_correlation_heatmap(report_df, corr_cols, corr_path)
                story.append(
                    Paragraph(
                        "The correlation matrix provides an exploratory view of pairwise linear relationships among parameters. "
                        "Correlations should be interpreted carefully because missing values and small sample sizes can affect stability.",
                        styles["Body"],
                    )
                )
                _add_image(story, corr_path, width=6.6 * inch)
            else:
                story.append(Paragraph("Correlation analysis requires at least two parameters with two or more numeric observations.", styles["Body"]))

            story.append(Paragraph("5. Compliance screening", styles["Section"]))
            comp = build_compliance(report_df, selected_params, limit_table).sort_values("Exceedance Score", ascending=False)
            comp_rows = [["Sample", "Location", "Acceptable", "Between", "Above", DATA_NOT_AVAILABLE, "Score"]]
            for _, row in comp.iterrows():
                comp_rows.append([
                    _pdf_cell(row.get("Sample ID", ""), 18),
                    _pdf_cell(row.get("Location", ""), 28),
                    str(int(row["Acceptable"])),
                    str(int(row["Between acceptable & permissible"])),
                    str(int(row["Above permissible"])),
                    str(int(row[DATA_NOT_AVAILABLE])),
                    str(int(row["Exceedance Score"])),
                ])
            story.append(
                Paragraph(
                    "Compliance status is calculated using the editable limit table used in the dashboard. "
                    "The exceedance score gives higher weight to above-permissible observations and is useful for prioritizing locations for detailed review.",
                    styles["Body"],
                )
            )
            story.append(_pdf_table(comp_rows, font_size=6.6))
            comp_path = f"{tmpdir}/compliance_chart.png"
            _save_compliance_chart(comp, comp_path)
            _add_image(story, comp_path, width=6.7 * inch)

            story.append(Paragraph("6. Interpretive summary", styles["Section"]))
            if not comp.empty:
                highest = comp.iloc[0]
                story.append(
                    Paragraph(
                        f"Based on the selected parameters, the highest screening priority is observed for {_pdf_cell(highest.get('Location', ''), 60)} "
                        f"with an exceedance score of {int(highest['Exceedance Score'])}. "
                        "Locations with above-permissible observations should be verified using laboratory QA/QC records, repeat sampling and relevant local hydrogeological information. "
                        f"Cells marked as {DATA_NOT_AVAILABLE} indicate that the parameter was not available and should not be interpreted as absence of contamination.",
                        styles["Body"],
                    )
                )
            story.append(
                Paragraph(
                    "This report is intended for exploratory assessment and decision support. Final conclusions should use the latest notified standards, "
                    "field observations, laboratory uncertainty information and repeat measurements wherever required.",
                    styles["Body"],
                )
            )
    else:
        story.append(Paragraph("No parameters were selected for detailed report generation.", styles["Body"]))

    def _footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(34, 18, DEVELOPER_TEXT)
        canvas.drawRightString(A4[0] - 34, 18, f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


def load_uploaded_file(uploaded_file):
    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def render_hero():
    st.markdown(
        f"""
        <div class="hero">
            <h1>💧 Water Quality Analysis & Visualization Dashboard</h1>
            <p>
            A web-based dashboard for analysing hydrochemical parameters, trace elements,
            spatial distribution, missing-data patterns and drinking-water compliance screening.
            </p>
            <span class="developer-badge">{DEVELOPER_TEXT}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_landing_cards():
    a, b, c = st.columns(3)
    with a:
        st.markdown(
            """
            <div class="info-card">
                <h4>📊 Parameter analysis</h4>
                <p>Bar charts, histograms, box plots, summary statistics and missing-value reporting.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with b:
        st.markdown(
            """
            <div class="info-card">
                <h4>🗺️ Spatial mapping</h4>
                <p>Interactive online maps using longitude and latitude. Missing values are shown as grey points.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c:
        st.markdown(
            """
            <div class="info-card">
                <h4>✅ Compliance report</h4>
                <p>Editable guideline limits, status matrix and downloadable screening summaries.</p>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_footer():
    st.markdown("---")
    st.markdown(
        f"""
        <div class="footer-card">
            <p><b>{DEVELOPER_TEXT}</b></p>
            <p class="small-note">
            Note: This dashboard is for exploratory screening and visualization. Final drinking-water
            interpretation should use the latest notified standards and laboratory QA/QC validation.
            Blank values are displayed as <b>{DATA_NOT_AVAILABLE}</b> and are not treated as zero.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


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


# -----------------------------
# Landing and upload workflow
# -----------------------------
render_hero()

st.markdown(
    f"""
    <div class="upload-card">
        <h3>Start here</h3>
        <p>
        Please upload the water-quality data file first. After uploading the file, click
        <b>Generate Report</b> to display all visualizations, maps, statistical summaries,
        correlation analysis, compliance screening and export options.
        </p>
        <p class="small-note">
        Recommended format: CSV or Excel file with columns such as Sample ID, Sample Name,
        Longitude, Latitude, Fluoride, Nitrate, Sulfate, Fe_ppb, Mn_ppb, As_ppb and Pb_ppb.
        Blank parameter values will be displayed as <b>{DATA_NOT_AVAILABLE}</b>.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

upload_col, action_col = st.columns([2.5, 1])
with upload_col:
    uploaded_file = st.file_uploader(
        "Upload data file",
        type=["csv", "xlsx"],
        label_visibility="collapsed",
        help="Upload a combined major-ion and trace-element dataset in CSV or Excel format."
    )
with action_col:
    st.write("")
    generate_clicked = st.button("🚀 Generate Report", type="primary", use_container_width=True)

with st.expander("Use sample dataset for testing", expanded=False):
    use_demo = st.checkbox(
        "Use bundled sample dataset if no file is uploaded",
        value=False,
        help="This option is useful for testing the website before uploading a new dataset."
    )

if "report_generated" not in st.session_state:
    st.session_state.report_generated = False
if "file_signature" not in st.session_state:
    st.session_state.file_signature = None

current_signature = None
if uploaded_file is not None:
    current_signature = f"{uploaded_file.name}_{uploaded_file.size}"
elif use_demo:
    current_signature = "bundled_demo_dataset"

if current_signature != st.session_state.file_signature:
    st.session_state.report_generated = False
    st.session_state.file_signature = current_signature

if generate_clicked:
    if uploaded_file is None and not use_demo:
        st.error("Please upload a CSV/XLSX data file first, then click Generate Report.")
    else:
        st.session_state.report_generated = True

if not st.session_state.report_generated:
    render_landing_cards()
    render_footer()
    st.stop()

# -----------------------------
# Load and prepare data
# -----------------------------
try:
    if uploaded_file is not None:
        raw_df = load_uploaded_file(uploaded_file)
        data_source_label = uploaded_file.name
    else:
        raw_df = load_default_data()
        data_source_label = "Bundled sample dataset"
except Exception as exc:
    st.error(f"Could not read the uploaded file: {exc}")
    st.stop()

if raw_df.empty:
    st.error("The uploaded dataset is empty. Please upload a valid water-quality dataset.")
    st.stop()

df = clean_columns(raw_df)
df = standardize_missing_values(df)
df = to_numeric_safely(df)

loc_col = get_location_column(df)
numeric_cols = get_numeric_columns(df)

st.sidebar.markdown("# 💧 Dashboard Controls")
st.sidebar.markdown(DEVELOPER_TEXT)
st.sidebar.markdown("---")
st.sidebar.success(f"Report generated for: {data_source_label}")

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
    st.caption("Values are editable. Use BIS/WHO/project-specific limits as required.")
    limit_table = st.data_editor(
        DEFAULT_LIMITS,
        num_rows="dynamic",
        use_container_width=True,
        key="limits_editor"
    )

st.markdown("<h2 class='section-title'>Generated Water Quality Report</h2>", unsafe_allow_html=True)
st.caption(
    f"Data source: {data_source_label}. Blank cells are displayed as '{DATA_NOT_AVAILABLE}' and are kept internally as missing values."
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Samples", len(df))
c2.metric("Numeric parameters", len(numeric_cols))

if "Longitude" in df.columns and "Latitude" in df.columns:
    c3.metric("Mapped samples", int(df[["Longitude", "Latitude"]].dropna().shape[0]))
else:
    c3.metric("Mapped samples", "N/A")

if selected_params:
    comp_tmp = build_compliance(df, selected_params, limit_table)
    c4.metric("Samples above permissible", int((comp_tmp["Above permissible"] > 0).sum()))
    c5.metric(DATA_NOT_AVAILABLE, int(df[selected_params].isna().sum().sum()))
else:
    c4.metric("Samples above permissible", "N/A")
    c5.metric(DATA_NOT_AVAILABLE, "N/A")

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
    st.dataframe(make_display_df(df), use_container_width=True, height=380)

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
            if plot_df[parameter].dropna().empty:
                st.info(f"No numeric values are available for {parameter}. All selected samples are marked as {DATA_NOT_AVAILABLE}.")
            else:
                fig = px.bar(
                    plot_df.sort_values(parameter, ascending=False, na_position="last"),
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
                fig.update_layout(xaxis_tickangle=-35, height=520, paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

        with col_b:
            values = plot_df[parameter].dropna()
            st.metric("Minimum", f"{values.min():.3f}" if not values.empty else DATA_NOT_AVAILABLE)
            st.metric("Mean", f"{values.mean():.3f}" if not values.empty else DATA_NOT_AVAILABLE)
            st.metric("Maximum", f"{values.max():.3f}" if not values.empty else DATA_NOT_AVAILABLE)
            st.metric(DATA_NOT_AVAILABLE, int(plot_df[parameter].isna().sum()))

            if acceptable is not None or permissible is not None:
                status_counts = plot_df[parameter].apply(
                    lambda x: status_from_limits(x, acceptable, permissible)
                ).value_counts()
                st.write("Status count")
                st.dataframe(status_counts.rename("count"), use_container_width=True)

        add_missing_value_note(plot_df, parameter, loc_col_use)

        col_h, col_box = st.columns(2)

        with col_h:
            if plot_df[parameter].dropna().empty:
                st.info(f"Histogram cannot be generated for {parameter} because all values are {DATA_NOT_AVAILABLE}.")
            else:
                fig_hist = px.histogram(
                    plot_df,
                    x=parameter,
                    nbins=10,
                    title=f"Histogram: {parameter}",
                    labels={parameter: f"{parameter} ({unit})" if unit else parameter}
                )
                fig_hist.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_hist, use_container_width=True)

        with col_box:
            if plot_df[parameter].dropna().empty:
                st.info(f"Box plot cannot be generated for {parameter} because all values are {DATA_NOT_AVAILABLE}.")
            else:
                fig_box = px.box(
                    plot_df,
                    y=parameter,
                    points="all",
                    hover_data=[loc_col_use],
                    title=f"Box plot: {parameter}",
                    labels={parameter: f"{parameter} ({unit})" if unit else parameter}
                )
                fig_box.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)")
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

        if map_df.empty:
            st.warning("No samples have valid Longitude and Latitude values.")
        else:
            if loc_col is None:
                map_df["Location"] = map_df.index.astype(str)
                loc_col_use = "Location"
            else:
                loc_col_use = loc_col

            fig_map = make_map_figure(map_df, map_param, loc_col_use)
            st.plotly_chart(fig_map, use_container_width=True)

            st.caption(
                f"Grey markers indicate samples where {map_param} is {DATA_NOT_AVAILABLE}. "
                "These locations are still mapped so every parameter can be visualized spatially."
            )

            missing_map_df = map_df[pd.isna(map_df[map_param])]
            if not missing_map_df.empty:
                with st.expander(f"Mapped samples where {map_param} is {DATA_NOT_AVAILABLE}"):
                    cols_to_show = [c for c in ["Sample ID", loc_col_use, "Latitude", "Longitude"] if c in missing_map_df.columns]
                    st.dataframe(make_display_df(missing_map_df[cols_to_show]), use_container_width=True)

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
        corr = df[corr_cols].corr(method="pearson", min_periods=2)
        fig_corr = px.imshow(
            corr,
            text_auto=".2f",
            aspect="auto",
            title="Pearson correlation matrix"
        )
        fig_corr.update_layout(height=700, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_corr, use_container_width=True)

        xcol, ycol = st.columns(2)
        with xcol:
            x_param = st.selectbox("X parameter", corr_cols, index=0)
        with ycol:
            y_param = st.selectbox("Y parameter", corr_cols, index=1 if len(corr_cols) > 1 else 0)

        scatter_df = df.dropna(subset=[x_param, y_param]).copy()
        if len(scatter_df) < 2:
            st.info(
                f"Scatter plot needs at least two samples with data for both {x_param} and {y_param}. "
                f"Missing values are shown as {DATA_NOT_AVAILABLE} in the data table."
            )
        else:
            fig_sc = px.scatter(
                scatter_df,
                x=x_param,
                y=y_param,
                trendline="ols" if len(scatter_df) >= 3 else None,
                hover_name=loc_col if loc_col else None,
                title=f"{x_param} vs {y_param}"
            )
            fig_sc.update_layout(height=500, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_sc, use_container_width=True)

with tab5:
    st.subheader("Compliance screening")
    st.caption(
        "Status is computed using the editable limit table in the sidebar. "
        "For trace elements, columns ending in _ppb are compared against ppb/µg/L limits. "
        f"Blank values are treated as {DATA_NOT_AVAILABLE}, not as zero."
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
            y=["Above permissible", "Between acceptable & permissible", DATA_NOT_AVAILABLE],
            title="Compliance and missing-data count by sample",
            labels={
                "value": "Number of parameters",
                "Location": "Location",
                "variable": "Status"
            }
        )
        fig_score.update_layout(xaxis_tickangle=-35, height=500, paper_bgcolor="rgba(0,0,0,0)")
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

    csv_numeric = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download analysis-ready dataset as CSV",
        data=csv_numeric,
        file_name="filtered_water_quality_data_numeric_missing_as_blank.csv",
        mime="text/csv"
    )

    csv_display = make_display_df(df).to_csv(index=False).encode("utf-8")
    st.download_button(
        f"Download display dataset with '{DATA_NOT_AVAILABLE}' as CSV",
        data=csv_display,
        file_name="filtered_water_quality_data_with_data_not_available.csv",
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
    st.subheader("Export complete project report as PDF")
    st.caption(
        "The PDF report includes an executive overview, data summary, missing-data assessment, "
        "parameter-wise charts, printable spatial plots, correlation heatmap, compliance screening and explanatory interpretation."
    )

    if not selected_params:
        st.info("Please select at least one parameter from the sidebar to generate the PDF project report.")
    else:
        if st.button("📄 Prepare PDF Project Report", type="primary", use_container_width=True):
            with st.spinner("Preparing the PDF project report..."):
                try:
                    st.session_state["project_report_pdf"] = generate_project_report_pdf(
                        df=df,
                        selected_params=selected_params,
                        limit_table=limit_table,
                        data_source_label=data_source_label,
                        loc_col=loc_col,
                        numeric_cols=numeric_cols,
                    )
                    st.success("PDF project report is ready. Click the download button below.")
                except Exception as exc:
                    st.error(f"Could not generate PDF report: {exc}")

        if "project_report_pdf" in st.session_state:
            st.download_button(
                "⬇️ Download Complete Project Report as PDF",
                data=st.session_state["project_report_pdf"],
                file_name="water_quality_project_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

render_footer()
