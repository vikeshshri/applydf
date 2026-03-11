"""Simple Streamlit frontend for applydf."""

import json
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(
    page_title="applydf | Data Studio",
    page_icon="✨",
    layout="wide",
)

API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 120


def init_state() -> None:
    if "current_data" not in st.session_state:
        st.session_state.current_data = None
    if "preview_data" not in st.session_state:
        st.session_state.preview_data = None
    if "transformation_history" not in st.session_state:
        st.session_state.transformation_history = []
    if "saved_pipelines" not in st.session_state:
        st.session_state.saved_pipelines = []
    if "last_metadata" not in st.session_state:
        st.session_state.last_metadata = None
    if "dataset_health_report" not in st.session_state:
        st.session_state.dataset_health_report = None
    if "data_quality_score" not in st.session_state:
        st.session_state.data_quality_score = None
    if "auto_pipeline" not in st.session_state:
        st.session_state.auto_pipeline = None
    if "exported_pipeline_code" not in st.session_state:
        st.session_state.exported_pipeline_code = None
    if "exported_pipeline_format" not in st.session_state:
        st.session_state.exported_pipeline_format = "python"
    if "pipeline_history" not in st.session_state:
        st.session_state.pipeline_history = []


def inject_styles() -> None:
    st.markdown("""<style>
    .hero { background: linear-gradient(135deg, #0f172a, #2563eb); color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; }
    .hero h2 { margin: 0 0 0.5rem 0; font-size: 1.5rem; }
    .hero p { margin: 0; opacity: 0.9; }
    [data-testid="stDeployButton"] { display: none !important; }
    .stAppDeployButton { display: none !important; }
    [data-testid="stFileUploader"] {
        border: 1px solid #d9dee7;
        border-radius: 12px;
        padding: 10px;
        background: #f8fafc;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    [data-testid="stFileUploaderDropzone"] {
        border: 1.5px dashed #c8d2e1;
        border-radius: 10px;
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        transition: all 0.18s ease;
        min-height: 110px;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #7aa2ff;
        background: #f4f8ff;
    }
    [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p {
        color: #334155;
        font-size: 0.84rem;
        line-height: 1.35;
    }
    [data-testid="stFileUploader"] section button {
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
        background: #ffffff !important;
        color: #0f172a !important;
        font-weight: 600 !important;
        padding: 0.35rem 0.75rem !important;
    }
    [data-testid="stFileUploader"] section button:hover {
        border-color: #94a3b8 !important;
        background: #f8fafc !important;
    }
    div[data-baseweb="select"] > div {
        border-radius: 8px;
        border: 1px solid #d5dbe5;
        background: #f8fafc;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: #b8c4d9;
        background: #f3f6fb;
    }
    .studio-note {
        margin-top: -2px;
        margin-bottom: 8px;
        color: #64748b;
        font-size: 0.86rem;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        border: none;
        color: #ffffff;
        font-weight: 600;
        border-radius: 8px;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
    }
    .analysis-widget {
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #cfe7da;
        background: linear-gradient(180deg, #f3fbf7 0%, #eaf7f1 100%);
        margin-bottom: 10px;
    }
    .analysis-head {
        display: flex;
        align-items: center;
        gap: 7px;
        color: #166534;
        font-weight: 700;
        font-size: 12px;
        margin-bottom: 8px;
    }
    .analysis-dot {
        width: 7px;
        height: 7px;
        border-radius: 999px;
        background: #16a34a;
        animation: pulse 1.1s ease-in-out infinite;
    }
    .mini-bars {
        height: 34px;
        display: flex;
        align-items: end;
        gap: 4px;
        margin-bottom: 8px;
    }
    .mini-bars span {
        width: 7px;
        border-radius: 3px 3px 1px 1px;
        background: linear-gradient(180deg, #22c55e 0%, #16a34a 100%);
        animation: bars 1.6s ease-in-out infinite;
    }
    .mini-bars span:nth-child(1) { animation-delay: 0s; }
    .mini-bars span:nth-child(2) { animation-delay: 0.15s; }
    .mini-bars span:nth-child(3) { animation-delay: 0.3s; }
    .mini-bars span:nth-child(4) { animation-delay: 0.45s; }
    .mini-bars span:nth-child(5) { animation-delay: 0.6s; }
    .mini-bars span:nth-child(6) { animation-delay: 0.75s; }
    .mini-kpis {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
        margin-bottom: 7px;
    }
    .kpi {
        background: #ffffff;
        border: 1px solid #dcf2e4;
        border-radius: 6px;
        padding: 5px 6px;
    }
    .kpi-label {
        font-size: 9px;
        color: #64748b;
        line-height: 1;
    }
    .kpi-value {
        font-size: 12px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 3px;
    }
    .kpi-value.rows::after {
        content: "1,248";
        animation: rowsCount 2.4s linear infinite;
    }
    .kpi-value.cols::after {
        content: "32";
        animation: colsCount 2.2s linear infinite;
    }
    .analysis-popup {
        height: 18px;
        border-radius: 5px;
        background: #ffffff;
        border: 1px dashed #c7e7d4;
        font-size: 10px;
        color: #166534;
        display: flex;
        align-items: center;
        padding: 0 6px;
        overflow: hidden;
    }
    .analysis-popup::after {
        content: "Scanning missing values...";
        animation: popupText 4.8s steps(1, end) infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.45; transform: scale(0.85); }
    }
    @keyframes bars {
        0%, 100% { height: 10px; opacity: 0.55; }
        50% { height: 30px; opacity: 1; }
    }
    @keyframes rowsCount {
        0% { content: "1,248"; }
        33% { content: "1,392"; }
        66% { content: "1,476"; }
        100% { content: "1,624"; }
    }
    @keyframes colsCount {
        0% { content: "32"; }
        50% { content: "36"; }
        100% { content: "40"; }
    }
    @keyframes popupText {
        0%, 24% { content: "Scanning missing values..."; }
        25%, 49% { content: "Profiling numeric columns..."; }
        50%, 74% { content: "Building feature insights..."; }
        75%, 100% { content: "Refreshing visual summary..."; }
    }
    </style>""", unsafe_allow_html=True)


def api_call(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    expect_json: bool = True,
):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, params=params, timeout=REQUEST_TIMEOUT)
            else:
                response = requests.post(url, json=json_data, params=params, timeout=REQUEST_TIMEOUT)
        elif method == "DELETE":
            response = requests.delete(url, params=params, timeout=REQUEST_TIMEOUT)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json() if expect_json else response.content
    except requests.exceptions.ConnectionError:
        st.error("Backend is not reachable. Start FastAPI on http://localhost:8000.")
    except requests.exceptions.HTTPError as exc:
        detail = str(exc)
        try:
            detail = response.json().get("detail", detail)
        except Exception:
            pass
        st.error(f"Request failed: {detail}")
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
    return None


def get_data_preview() -> Optional[Dict[str, Any]]:
    response = api_call("/preview")
    return response if isinstance(response, dict) and "shape" in response else None


def get_visual_compare_data(limit: int = 1000) -> Optional[Dict[str, Any]]:
    response = api_call("/visual-compare", params={"limit": limit})
    return response if isinstance(response, dict) and response.get("success") else None


def get_dataset_health() -> Optional[Dict[str, Any]]:
    response = api_call("/dataset-health")
    return response if isinstance(response, dict) and response.get("success") else None


def generate_auto_pipeline_plan() -> Optional[Dict[str, Any]]:
    response = api_call("/auto-pipeline", method="POST")
    return response if isinstance(response, dict) and response.get("success") else None


def auto_clean_dataset() -> Optional[Dict[str, Any]]:
    response = api_call("/auto-clean", method="POST")
    return response if isinstance(response, dict) and response.get("success") else None


def export_pipeline_code(export_format: str) -> Optional[Dict[str, Any]]:
    response = api_call("/pipeline/export-code", params={"format": export_format})
    return response if isinstance(response, dict) and response.get("success") else None


def get_pipeline_history(limit: int = 50) -> Optional[Dict[str, Any]]:
    response = api_call("/pipeline-history", params={"limit": limit})
    return response if isinstance(response, dict) and response.get("success") else None


def backend_health() -> bool:
    response = api_call("/")
    return bool(response and response.get("name"))


def get_text_column_candidates(preview: Dict[str, Any]) -> list[str]:
    dtypes = preview.get("data_types", {})
    return [name for name, dtype in dtypes.items() if "object" in str(dtype).lower() or "string" in str(dtype).lower()]


def get_numeric_column_candidates(preview: Dict[str, Any]) -> list[str]:
    dtypes = preview.get("data_types", {})
    numeric_aliases = ["int", "float", "double", "number"]
    return [
        name
        for name, dtype in dtypes.items()
        if any(alias in str(dtype).lower() for alias in numeric_aliases)
    ]


def render_hero() -> None:
    st.markdown(
        """<div class="hero"><h2>applydf · Data Transformation Studio</h2>
        <p>Upload, transform, visualize, and export data.</p></div>""",
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.subheader("Workspace")
        is_online = backend_health()
        if is_online:
            st.markdown(
                '''
                <div class="analysis-widget">
                    <div class="analysis-head"><span class="analysis-dot"></span><span>Data Analyzing</span></div>
                    <div class="mini-bars">
                        <span></span><span></span><span></span><span></span><span></span><span></span>
                    </div>
                    <div class="mini-kpis">
                        <div class="kpi">
                            <div class="kpi-label">Rows scanned</div>
                            <div class="kpi-value rows"></div>
                        </div>
                        <div class="kpi">
                            <div class="kpi-label">Signals</div>
                            <div class="kpi-value cols"></div>
                        </div>
                    </div>
                    <div class="analysis-popup"></div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
        else:
            st.error("Backend: Offline")

        st.markdown("**Upload Dataset**")
        st.caption("Choose a file and click Upload to start.")

        uploaded_file = st.file_uploader("Upload file", type=["csv", "xlsx", "xls", "json", "parquet"])

        if uploaded_file is not None and st.button("Upload & Parse", use_container_width=True, type="primary"):
            with st.spinner("Processing..."):
                files = {"file": (uploaded_file.name, uploaded_file)}
                response = api_call("/upload", method="POST", files=files)
                if response and response.get("success"):
                    st.session_state.current_data = response
                    st.session_state.preview_data = get_data_preview()
                    st.session_state.dataset_health_report = response.get("dataset_health_report")
                    st.session_state.data_quality_score = response.get("data_quality_score")
                    st.session_state.auto_pipeline = response.get("auto_pipeline")
                    st.success(f"{uploaded_file.name} loaded")

        st.divider()
        st.subheader("Dataset Actions")

        if st.session_state.current_data:
            shape = st.session_state.current_data.get("shape", [0, 0])
            st.caption(f"Rows: {shape[0]} | Columns: {shape[1]}")

            if st.button("Refresh Preview", use_container_width=True):
                st.session_state.preview_data = get_data_preview()
                health = get_dataset_health()
                if health:
                    st.session_state.dataset_health_report = health.get("dataset_health_report")
                    st.session_state.data_quality_score = health.get("data_quality_score")
                    st.session_state.auto_pipeline = health.get("auto_pipeline")
                st.rerun()

            if st.button("Reset Session", use_container_width=True):
                api_call("/reset", method="POST")
                st.session_state.current_data = None
                st.session_state.preview_data = None
                st.session_state.transformation_history = []
                st.session_state.last_metadata = None
                st.session_state.dataset_health_report = None
                st.session_state.data_quality_score = None
                st.session_state.auto_pipeline = None
                st.session_state.exported_pipeline_code = None
                st.session_state.pipeline_history = []
                st.rerun()

        st.divider()
        st.subheader("Pipelines")

        if st.button("Refresh Saved Pipelines", use_container_width=True):
            response = api_call("/pipelines")
            if response and response.get("success"):
                st.session_state.saved_pipelines = response.get("pipelines", [])

        if st.session_state.transformation_history:
            name = st.text_input("Pipeline name", placeholder="my-pipeline")
            desc = st.text_area("Description", placeholder="Notes")
            if st.button("Save Pipeline", use_container_width=True):
                if not name.strip():
                    st.warning("Name required.")
                else:
                    response = api_call(
                        "/save-pipeline",
                        method="POST",
                        params={"pipeline_name": name.strip(), "description": desc.strip()},
                    )
                    if response and response.get("success"):
                        st.success(response.get("message", "Saved"))


def render_preview(preview: Dict[str, Any]) -> None:
    total_missing = int(sum(preview.get("missing_values", {}).values()))
    shape = preview.get("shape", [0, 0])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows", f"{shape[0]:,}")
    m2.metric("Columns", f"{shape[1]:,}")
    m3.metric("Missing", f"{total_missing:,}")
    m4.metric("Transforms", len(st.session_state.transformation_history))

    tab_data, tab_types, tab_missing, tab_stats, tab_visual = st.tabs(
        ["Data", "Types", "Missing", "Stats", "Visuals"]
    )

    with tab_data:
        st.dataframe(pd.DataFrame(preview.get("preview_data", [])), use_container_width=True)

    with tab_types:
        dtype_df = pd.DataFrame(list(preview.get("data_types", {}).items()), columns=["Column", "Type"])
        st.dataframe(dtype_df, use_container_width=True)

    with tab_missing:
        missing_df = pd.DataFrame(list(preview.get("missing_values", {}).items()), columns=["Column", "Missing Count"])
        if not missing_df.empty and shape[0] > 0:
            missing_df["Missing %"] = (missing_df["Missing Count"] / shape[0] * 100).round(2)
        st.dataframe(missing_df, use_container_width=True)
        if not missing_df.empty and missing_df["Missing Count"].sum() > 0:
            fig = px.bar(missing_df.sort_values("Missing %", ascending=False), x="Column", y="Missing %", title="Missing Values")
            st.plotly_chart(fig, use_container_width=True)

    with tab_stats:
        stats = preview.get("statistics", {})
        if stats:
            stats_rows = []
            for name, values in stats.items():
                row = {"Column": name}
                row.update(values)
                stats_rows.append(row)
            st.dataframe(pd.DataFrame(stats_rows), use_container_width=True)
        else:
            st.info("No numeric data")

    with tab_visual:
        compare = get_visual_compare_data(limit=1500)
        if not compare:
            st.info("Upload and transform data to see visuals.")
            return

        before_df = pd.DataFrame(compare.get("before_data", []))
        after_df = pd.DataFrame(compare.get("after_data", []))
        common_numeric_cols = compare.get("common_numeric_columns", [])

        if before_df.empty or after_df.empty:
            st.info("Not enough data.")
            return

        if not common_numeric_cols:
            st.warning("No common numeric columns available for visual comparison.")
            return

        st.markdown("**Before vs After Comparison**")
        visual_type = st.selectbox("Visualization", ["Distribution", "Box", "Scatter", "Reciprocal", "Squared"], key="vis_type")

        if visual_type == "Scatter":
            if len(common_numeric_cols) >= 2:
                x_col = st.selectbox("X-axis", common_numeric_cols, key="x")
                y_col = st.selectbox("Y-axis", [c for c in common_numeric_cols if c != x_col], key="y")
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(px.scatter(before_df, x=x_col, y=y_col, title="Before"), use_container_width=True)
                with col2:
                    st.plotly_chart(px.scatter(after_df, x=x_col, y=y_col, title="After"), use_container_width=True)
            else:
                st.warning("Need 2+ numeric columns")
                return
        else:
            selected_column = st.selectbox("Column", common_numeric_cols, key="col")
            col1, col2 = st.columns(2)
            with col1:
                before_series = pd.to_numeric(before_df[selected_column], errors="coerce").dropna()
                if visual_type == "Distribution":
                    fig = px.histogram(x=before_series, nbins=30, title="Before")
                elif visual_type == "Box":
                    fig = px.box(y=before_series, title="Before")
                elif visual_type == "Reciprocal":
                    d = pd.to_numeric(before_df[selected_column], errors="coerce")
                    d = 1.0 / d.replace(0, np.nan)
                    fig = px.histogram(d.dropna(), nbins=30, title="Before (Reciprocal)")
                else:
                    d = pd.to_numeric(before_df[selected_column], errors="coerce") ** 2
                    fig = px.histogram(d.dropna(), nbins=30, title="Before (Squared)")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                after_series = pd.to_numeric(after_df[selected_column], errors="coerce").dropna()
                if visual_type == "Distribution":
                    fig = px.histogram(x=after_series, nbins=30, title="After")
                elif visual_type == "Box":
                    fig = px.box(y=after_series, title="After")
                elif visual_type == "Reciprocal":
                    d = pd.to_numeric(after_df[selected_column], errors="coerce")
                    d = 1.0 / d.replace(0, np.nan)
                    fig = px.histogram(d.dropna(), nbins=30, title="After (Reciprocal)")
                else:
                    d = pd.to_numeric(after_df[selected_column], errors="coerce") ** 2
                    fig = px.histogram(d.dropna(), nbins=30, title="After (Squared)")
                st.plotly_chart(fig, use_container_width=True)


def render_parameter_inputs(method: str, preview: Dict[str, Any]) -> tuple[Dict[str, Any], Optional[str]]:
    params: Dict[str, Any] = {}
    text_column: Optional[str] = None
    text_cols = get_text_column_candidates(preview)
    numeric_cols = get_numeric_column_candidates(preview)

    if method in ["PCA", "SVD"]:
        max_components = len(numeric_cols) if numeric_cols else 10
        upper = min(10, max_components)
        if upper <= 1:
            params["n_components"] = st.number_input("n_components", min_value=1, max_value=max_components, value=1)
        else:
            lower = min(1, upper - 1)
            default = min(2, upper)
            params["n_components"] = st.slider("n_components", lower, upper, default)

    elif method == "t-SNE":
        c1, c2 = st.columns(2)
        with c1:
            params["n_components"] = st.radio("Dimensions", [2, 3], horizontal=True)
            params["perplexity"] = st.slider("Perplexity", 5, 50, 30)
        with c2:
            params["learning_rate"] = st.slider("Learning Rate", 10, 1000, 200, step=10)
            params["n_iter"] = st.slider("Iterations", 250, 2000, 1000, step=50)

    elif method == "UMAP":
        c1, c2 = st.columns(2)
        with c1:
            params["n_components"] = st.radio("Dimensions", [2, 3], horizontal=True)
            params["n_neighbors"] = st.slider("n_neighbors", 5, 50, 15)
        with c2:
            params["min_dist"] = st.slider("min_dist", 0.0, 1.0, 0.1, step=0.01)

    elif method == "Min-Max Normalization":
        c1, c2 = st.columns(2)
        with c1:
            min_val = st.number_input("Range min", value=0.0)
        with c2:
            max_val = st.number_input("Range max", value=1.0)
        params["feature_range"] = [min_val, max_val]

    elif method == "Quantile Transformation":
        c1, c2 = st.columns(2)
        with c1:
            params["n_quantiles"] = st.slider("n_quantiles", 10, 1000, 100)
        with c2:
            params["output_distribution"] = st.selectbox("Output distribution", ["uniform", "normal"])

    elif method == "Log/Power Transforms":
        c1, c2 = st.columns(2)
        with c1:
            params["method"] = st.selectbox("Method", ["log", "log10", "log2", "power"])
        with c2:
            if params["method"] == "power":
                params["power"] = st.number_input("Power", value=2.0)

    elif method == "Binning/Discretization":
        c1, c2 = st.columns(2)
        with c1:
            params["n_bins"] = st.slider("n_bins", 2, 20, 5)
        with c2:
            params["strategy"] = st.selectbox("Strategy", ["quantile", "uniform", "kmeans"])

    elif method == "K-Means Clustering":
        c1, c2 = st.columns(2)
        with c1:
            params["n_clusters"] = st.slider("n_clusters", 2, 20, 3)
        with c2:
            params["max_iter"] = st.slider("max_iter", 100, 1000, 300, step=50)

    elif method == "Correlation Feature Filter":
        params["threshold"] = st.slider("correlation_threshold", 0.70, 0.99, 0.95, step=0.01)

    elif method == "Variance Threshold Feature Selection":
        params["threshold"] = st.number_input("variance_threshold", min_value=0.0, value=0.0, step=0.01)

    elif method in [
        "TF-IDF",
        "N-gram Analysis",
        "Word2Vec",
        "Transformer Embeddings",
        "Text Normalization",
        "Sentiment Analysis (VADER)",
        "Topic Modeling (LDA)",
    ]:
        if text_cols:
            text_column = st.selectbox("Text column", text_cols)
        else:
            st.warning("No text-like columns detected. Upload data with object/string columns.")

        if method == "TF-IDF":
            params["max_features"] = st.slider("max_features", 10, 500, 100)
        elif method == "N-gram Analysis":
            c1, c2 = st.columns(2)
            with c1:
                min_n = st.slider("min_n", 1, 5, 1)
                max_n = st.slider("max_n", min_n, 5, max(min_n, 2))
            with c2:
                params["max_features"] = st.slider("max_features", 10, 500, 100)
            params["ngram_range"] = [min_n, max_n]
        elif method == "Word2Vec":
            c1, c2, c3 = st.columns(3)
            with c1:
                params["vector_size"] = st.slider("vector_size", 50, 300, 100, step=10)
            with c2:
                params["window"] = st.slider("window", 2, 10, 5)
            with c3:
                params["min_count"] = st.slider("min_count", 1, 5, 2)
        elif method == "Transformer Embeddings":
            params["model_name"] = st.selectbox(
                "Model",
                [
                    "sentence-transformers/all-MiniLM-L6-v2",
                    "sentence-transformers/all-mpnet-base-v2",
                    "sentence-transformers/paraphrase-MiniLM-L6-v2",
                ],
            )
            params["max_length"] = st.slider("max_length", 64, 512, 128)
        elif method == "Text Normalization":
            c1, c2, c3 = st.columns(3)
            with c1:
                params["lowercase"] = st.checkbox("lowercase", value=True)
            with c2:
                params["remove_special"] = st.checkbox("remove_special", value=True)
            with c3:
                params["lemmatize"] = st.checkbox("lemmatize", value=True)
        elif method == "Topic Modeling (LDA)":
            c1, c2 = st.columns(2)
            with c1:
                params["n_topics"] = st.slider("n_topics", 2, 20, 5)
            with c2:
                params["max_features"] = st.slider("max_features", 100, 5000, 1000, step=100)

    elif method == "Simple Missing Value Imputation":
        params["strategy"] = st.selectbox("strategy", ["median", "mean", "most_frequent"])

    elif method == "Isolation Forest Outlier Detection":
        c1, c2 = st.columns(2)
        with c1:
            params["contamination"] = st.slider("contamination", 0.01, 0.50, 0.10, step=0.01)
        with c2:
            params["remove_outliers"] = st.checkbox("remove_outliers", value=True)

    elif method == "KNN Imputation":
        params["n_neighbors"] = st.slider("n_neighbors", 1, 20, 5)

    elif method == "IQR Outlier Treatment":
        c1, c2 = st.columns(2)
        with c1:
            params["factor"] = st.slider("iqr_factor", 1.0, 3.0, 1.5, step=0.1)
        with c2:
            params["action"] = st.selectbox("action", ["cap", "remove"])

    elif method == "Winsorization":
        c1, c2 = st.columns(2)
        with c1:
            params["lower_quantile"] = st.slider("lower_quantile", 0.0, 0.20, 0.01, step=0.01)
        with c2:
            params["upper_quantile"] = st.slider("upper_quantile", 0.80, 1.0, 0.99, step=0.01)

    elif method == "Deduplication":
        params["keep"] = st.selectbox("keep", ["first", "last"])

    return params, text_column


def render_intelligence_panel() -> None:
    st.subheader("Intelligent Data Preparation")

    health_report = st.session_state.dataset_health_report
    quality_score = st.session_state.data_quality_score
    auto_pipeline = st.session_state.auto_pipeline

    if not health_report or not quality_score:
        health = get_dataset_health()
        if health:
            health_report = health.get("dataset_health_report")
            quality_score = health.get("data_quality_score")
            auto_pipeline = health.get("auto_pipeline")
            st.session_state.dataset_health_report = health_report
            st.session_state.data_quality_score = quality_score
            st.session_state.auto_pipeline = auto_pipeline

    if not health_report or not quality_score:
        st.info("Dataset diagnosis is not available yet.")
        return

    score_value = quality_score.get("score", 0)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    c1.metric("Data Quality Score", f"{score_value} / 100")
    c2.metric("Issues Detected", len(health_report.get("issues_detected", [])))
    c3.metric("Suggested Fixes", len(health_report.get("suggested_fixes", [])))
    c4.metric("Processing Engine", health_report.get("processing_engine", "pandas"))

    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("Auto Clean Dataset", type="primary", use_container_width=True):
            with st.spinner("Auto cleaning dataset..."):
                result = auto_clean_dataset()
                if result:
                    st.session_state.preview_data = get_data_preview()
                    st.session_state.dataset_health_report = result.get("after_report")
                    st.session_state.data_quality_score = result.get("after_score")
                    st.session_state.auto_pipeline = result.get("pipeline")

                    before_score = result.get("before_score", {}).get("score", 0)
                    after_score = result.get("after_score", {}).get("score", 0)
                    improvement = round(after_score - before_score, 2)
                    st.success(f"Auto clean completed. Score improved by {improvement} points.")
                    st.rerun()

    with btn2:
        if st.button("Regenerate Auto Pipeline", use_container_width=True):
            result = generate_auto_pipeline_plan()
            if result:
                st.session_state.auto_pipeline = result.get("pipeline")
                st.success("Auto pipeline generated.")
                st.rerun()

    with st.expander("Dataset Health Report", expanded=True):
        st.markdown("**Dataset Summary**")
        st.json(
            {
                "rows": health_report.get("rows"),
                "columns": health_report.get("columns"),
                "duplicates": health_report.get("duplicates"),
                "numeric_columns": health_report.get("numeric_columns", []),
                "categorical_columns": health_report.get("categorical_columns", []),
                "skewed_features": health_report.get("skewed_features", []),
                "correlated_features": health_report.get("correlated_features", []),
                "outliers_detected": health_report.get("outliers_detected", False),
                "class_imbalance": health_report.get("class_imbalance", {}),
            }
        )

        st.markdown("**Issues Detected**")
        issues = health_report.get("issues_detected", [])
        if issues:
            for issue in issues:
                st.write(f"- {issue}")
        else:
            st.write("- No major issues detected")

        st.markdown("**Suggested Fixes**")
        fixes = health_report.get("suggested_fixes", [])
        if fixes:
            for fix in fixes:
                st.write(f"- {fix}")
        else:
            st.write("- No fixes suggested")

    with st.expander("Automatic Pipeline Generation", expanded=True):
        pipeline = auto_pipeline or {"confidence": 0.0, "steps": []}
        st.write(f"Confidence: {pipeline.get('confidence', 0.0)}")
        steps = pipeline.get("steps", [])
        if not steps:
            st.info("No automatic steps suggested yet.")
        else:
            for idx, step in enumerate(steps, start=1):
                st.write(f"{idx}. {step.get('step')} - {step.get('reason')}")

    with st.expander("Export Pipeline As Code", expanded=False):
        selected_format = st.selectbox("Export format", ["python", "sklearn", "pyspark"], key="pipeline_export_format")
        if st.button("Generate Pipeline Code", use_container_width=True):
            export_result = export_pipeline_code(selected_format)
            if export_result:
                export_payload = export_result.get("export", {})
                st.session_state.exported_pipeline_code = export_payload.get("code", "")
                st.session_state.exported_pipeline_format = export_payload.get("format", selected_format)
                history = get_pipeline_history(limit=25)
                if history:
                    st.session_state.pipeline_history = history.get("history", [])

        code_block = st.session_state.exported_pipeline_code
        if code_block:
            fmt = st.session_state.exported_pipeline_format
            st.code(code_block, language="python")
            st.download_button(
                f"Download {fmt} pipeline code",
                data=code_block,
                file_name=f"applydf_pipeline_{fmt}.py",
                mime="text/plain",
                use_container_width=True,
            )

    with st.expander("Pipeline Export History", expanded=False):
        if not st.session_state.pipeline_history:
            history = get_pipeline_history(limit=25)
            if history:
                st.session_state.pipeline_history = history.get("history", [])

        if st.session_state.pipeline_history:
            st.dataframe(pd.DataFrame(st.session_state.pipeline_history), use_container_width=True)
        else:
            st.info("No pipeline history yet.")


def render_transform_panel(preview: Dict[str, Any]) -> None:
    response = api_call("/categories")
    categories = response.get("categories", {}) if response else {}
    if not categories:
        st.warning("No categories")
        return

    st.subheader("Transformation Studio")
    st.markdown('<div class="studio-note">Choose category and method, then run the transformation.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        selected_category = st.selectbox("Category", list(categories.keys()))
        selected_method = st.selectbox("Method", categories[selected_category])
    with c2:
        st.markdown("<div style='height: 66px;'></div>", unsafe_allow_html=True)
        run = st.button(f"Run {selected_method}", type="primary", use_container_width=True)

    params, text_column = render_parameter_inputs(selected_method, preview)

    if run:
        with st.spinner(f"Processing..."):
            payload = {
                "transformation_type": selected_method,
                "parameters": params,
                "text_column": text_column,
            }
            result = api_call("/transform", method="POST", json_data=payload)
            if result and result.get("success"):
                st.session_state.transformation_history.append({"type": selected_method, "parameters": params})
                st.session_state.last_metadata = result.get("metadata")
                st.session_state.preview_data = get_data_preview()
                st.success(result.get("message", "Done"))
                st.rerun()

    if st.session_state.last_metadata:
        with st.expander("Last Result"):
            st.json(st.session_state.last_metadata)


def render_export_panel() -> None:
    st.subheader("Export")
    c1, c2, c3 = st.columns(3)

    with c1:
        csv_data = api_call("/download/csv", expect_json=False)
        if csv_data:
            st.download_button("Download CSV", data=csv_data, file_name="data.csv", mime="text/csv", use_container_width=True)

    with c2:
        excel_data = api_call("/download/excel", expect_json=False)
        if excel_data:
            st.download_button("Download Excel", data=excel_data, file_name="data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    with c3:
        parquet_data = api_call("/download/parquet", expect_json=False)
        if parquet_data:
            st.download_button("Download Parquet", data=parquet_data, file_name="data.parquet", mime="application/octet-stream", use_container_width=True)


def render_history_panel() -> None:
    st.subheader("Pipeline History")
    if not st.session_state.transformation_history:
        st.info("No transformations yet")
        return

    history_df = pd.DataFrame(st.session_state.transformation_history)
    history_df.index = history_df.index + 1
    history_df.index.name = "Step"
    history_df["parameters"] = history_df["parameters"].apply(lambda x: json.dumps(x, default=str))
    st.dataframe(history_df, use_container_width=True)


def render_empty_state() -> None:
    st.info("Upload a dataset from the sidebar to begin.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div><b>Input</b><br/>CSV, Excel, JSON, Parquet</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div><b>Transform</b><br/>30+ algorithms</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div><b>Export</b><br/>CSV, Excel, Parquet</div>', unsafe_allow_html=True)


def main() -> None:
    init_state()
    inject_styles()
    render_hero()
    render_sidebar()

    if not st.session_state.current_data:
        render_empty_state()
        return

    preview = st.session_state.preview_data or get_data_preview()
    if not preview:
        st.error("Could not load dataset")
        return

    st.subheader("Dataset Overview")
    render_preview(preview)
    st.divider()
    render_intelligence_panel()
    st.divider()
    render_transform_panel(preview)
    st.divider()
    render_export_panel()
    st.divider()
    render_history_panel()


if __name__ == "__main__":
    main()
