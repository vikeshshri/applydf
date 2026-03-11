"""
Enhanced Frontend for applydf with Collaborative Features
Multi-page Streamlit application
"""

import json
import os
from typing import Any, Dict, Optional, List
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="ApplyDF Nexus | Collaborative Data Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 120
SCREEN_MODES = ["System", "Dark", "Light"]

SESSION_DEFAULTS: Dict[str, Any] = {
    "current_user": None,
    "current_data": None,
    "preview_data": None,
    "transformation_history": [],
    "last_metadata": None,
    "dataset_health_report": None,
    "data_quality_score": None,
    "auto_pipeline": None,
    "current_page": "Data Studio",
    "last_registered_dataset_id": None,
    "last_report": None,
    "last_cleaning_result": None,
    "exported_pipeline_code": "",
    "exported_pipeline_format": "python",
    "pipeline_history": [],
    "screen_mode": "System",
    "selected_transform_code": "",
    "selected_transform_name": "",
}


def init_state():
    """Initialize session state variables."""
    for key, default_value in SESSION_DEFAULTS.items():
        # Copy mutable defaults so each key owns its own session object.
        if key not in st.session_state:
            st.session_state[key] = default_value.copy() if isinstance(default_value, list) else default_value


def inject_styles():
    """Inject custom CSS that respects Streamlit's theme system."""
    st.markdown("""
    <style>
    :root {
        --landing-card-color: #eef4fb;
        --applydf-blue: #2f6fa3;
        --applydf-blue-dark: #255a86;
        --applydf-blue-soft: #eaf2f8;
        --panel-border: #dbe6ef;
        --panel-bg: #f9fbfd;
        --text-main: #1f344d;
        --text-soft: #5f7388;
    }

    [data-testid="stDeployButton"],
    .stAppDeployButton,
    [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
    }

    html, body, [class*="css"], .stApp {
        font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif !important;
        color: var(--text-main);
        line-height: 1.45;
    }

    h1, h2, h3 {
        letter-spacing: -0.2px;
    }

    p, li, label {
        color: #4f6479;
    }

    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 8% 2%, rgba(47, 111, 163, 0.06), rgba(47, 111, 163, 0) 30%), #f5f8fb;
    }

    .block-container {
        max-width: 1240px;
        padding-top: 1.1rem;
        padding-bottom: 1.5rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f2f6fa 0%, #edf3f8 100%);
        border-right: 1px solid #d6e1eb;
    }

    [data-testid="stSidebar"] hr {
        border-color: #d5e0ea;
    }

    .stButton > button {
        border-radius: 10px !important;
        border: 1px solid #c7d8e6 !important;
        background: #ffffff !important;
        color: #244461 !important;
        font-weight: 600 !important;
        transition: all 0.16s ease;
    }

    .stButton > button * {
        color: inherit !important;
    }

    .stButton > button:hover {
        border-color: #95b4cc !important;
        box-shadow: 0 4px 10px rgba(37, 90, 134, 0.14);
    }

    .stButton button[kind="primary"],
    [data-testid="baseButton-primary"] {
        background: linear-gradient(120deg, var(--applydf-blue), var(--applydf-blue-dark)) !important;
        color: #ffffff !important;
        border: 1px solid var(--applydf-blue) !important;
        box-shadow: 0 6px 14px rgba(47, 111, 163, 0.22);
    }

    .stButton button[kind="primary"] *,
    [data-testid="baseButton-primary"] * {
        color: #ffffff !important;
    }

    .stButton button[kind="primary"]:hover,
    [data-testid="baseButton-primary"]:hover {
        background: linear-gradient(120deg, var(--applydf-blue-dark), #1f4f78) !important;
        border-color: #1f4f78 !important;
    }

    [data-testid="stFileUploader"] {
        border: 1px solid #d2deea;
        border-radius: 12px;
        background: #f8fbfe;
        padding: 0.15rem;
    }

    [data-testid="stFileUploaderDropzone"] {
        border: 1px dashed #9cb6cd !important;
        border-radius: 10px !important;
        background: linear-gradient(140deg, #f8fbff, #f2f7fb) !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    [data-baseweb="select"] > div {
        border-radius: 10px !important;
        border: 1px solid #cddaea !important;
        background: #ffffff !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stNumberInput input:focus {
        border-color: var(--applydf-blue) !important;
        box-shadow: 0 0 0 2px rgba(47, 111, 163, 0.12) !important;
    }

    [data-baseweb="tag"] {
        background: #eef4fb !important;
        border: 1px solid #cfe0ef !important;
        color: #2a4e71 !important;
    }

    [data-baseweb="tab-list"] {
        background: #ffffff;
        border: 1px solid var(--panel-border);
        border-radius: 10px;
        padding: 0.22rem;
        border-bottom: 1px solid var(--panel-border);
        margin-bottom: 0.25rem;
    }

    [data-baseweb="tab-panel"] {
        background: #ffffff;
        border: 1px solid var(--panel-border);
        border-radius: 12px;
        padding: 0.6rem;
    }

    [data-baseweb="tab"] {
        color: var(--text-soft) !important;
        font-weight: 600 !important;
    }

    [aria-selected="true"][data-baseweb="tab"] {
        color: var(--applydf-blue) !important;
        border-bottom: 2px solid var(--applydf-blue) !important;
    }

    [data-testid="stDataFrame"],
    [data-testid="stMetric"],
    [data-testid="stExpander"],
    [data-testid="stAlert"] {
        border: 1px solid var(--panel-border);
        border-radius: 12px;
        background: #ffffff;
    }

    [data-testid="stMetric"] {
        padding: 0.5rem;
    }

    .studio-status-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.6rem;
        margin: 0.5rem 0 0.9rem 0;
    }

    .studio-status-card {
        background: var(--panel-bg);
        border: 1px solid var(--panel-border);
        border-radius: 12px;
        padding: 0.65rem 0.72rem;
        position: relative;
        overflow: hidden;
    }

    .studio-status-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, var(--applydf-blue), #49a0df);
    }

    .studio-status-label {
        margin: 0;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        color: var(--text-soft);
        font-weight: 700;
    }

    .studio-status-value {
        margin: 0.2rem 0 0 0;
        font-size: 0.92rem;
        color: var(--text-main);
        font-weight: 700;
    }

    .studio-section-heading {
        margin: 0.2rem 0 0.35rem 0;
        color: var(--text-main);
        font-size: 1.25rem;
        font-weight: 800;
    }

    .studio-section-subtext {
        margin: 0 0 0.7rem 0;
        color: var(--text-soft);
        font-size: 0.9rem;
    }

    @media (max-width: 900px) {
        .studio-status-strip {
            grid-template-columns: 1fr;
        }
    }

    .brand-wrap {
        margin-bottom: 0.4rem;
        line-height: 1;
    }
    .brand-applydf {
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #2f6fa3;
        text-transform: uppercase;
    }
    .brand-subtitle {
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 1px;
        color: #2f6fa3;
        margin-top: 3px;
        text-transform: uppercase;
    }

    .analysis-widget {
        background: linear-gradient(135deg, rgba(230, 247, 236, 0.9) 0%, rgba(215, 240, 225, 0.82) 100%);
        border: 1.5px solid rgba(34, 197, 94, 0.26);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 18px;
        box-shadow: 0 6px 18px rgba(22, 163, 74, 0.12);
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
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(34, 197, 94, 0.24);
        border-radius: 6px;
        padding: 5px 6px;
    }
    .kpi-label {
        font-size: 9px;
        color: #4b7a60;
        line-height: 1;
    }
    .kpi-value {
        font-size: 12px;
        font-weight: 700;
        color: #166534;
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
        border: 1px dashed rgba(34, 197, 94, 0.42);
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
        0% { content: "Scanning missing values..."; }
        20% { content: "Detecting outliers..."; }
        40% { content: "Analyzing correlations..."; }
        60% { content: "Checking data types..."; }
        80% { content: "Computing statistics..."; }
        100% { content: "Scanning missing values..."; }
    }

    .hero {
        background: linear-gradient(120deg, #1f2937 0%, #374151 100%);
        color: white;
        padding: 1.7rem;
        border-radius: 12px;
        margin-bottom: 1.05rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.14);
    }
    .hero h1 {
        margin: 0 0 0.5rem 0;
        color: white !important;
    }
    .hero p {
        margin: 0;
        color: white !important;
    }

    .onboarding-shell {
        margin-top: 0.35rem;
        margin-bottom: 1rem;
    }
    .onboarding-hero {
        background: var(--landing-card-color);
        border: 1px solid #d0ddec;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        box-shadow: none;
        margin-bottom: 0.9rem;
    }
    .onboarding-badge {
        display: inline-block;
        border-radius: 999px;
        background: #e9f3ff;
        border: 1px solid #bfd8f0;
        color: #215a91;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.3px;
        padding: 0.18rem 0.55rem;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
    }
    .onboarding-title {
        margin: 0;
        color: #1e3a5f;
        font-size: 1.35rem;
        font-weight: 800;
    }
    .onboarding-text {
        margin: 0.38rem 0 0 0;
        color: #4a647f;
        font-size: 0.93rem;
        line-height: 1.45;
    }
    .onboarding-feature {
        background: var(--landing-card-color);
        border: 1px solid #d0ddec;
        border-radius: 12px;
        padding: 0.8rem;
        box-shadow: none;
        height: 100%;
    }
    .onboarding-feature-title {
        margin: 0 0 0.32rem 0;
        font-size: 0.93rem;
        color: #1f3f66;
        font-weight: 700;
    }
    .onboarding-feature-text {
        margin: 0;
        font-size: 0.83rem;
        color: #5a7188;
        line-height: 1.35;
    }
    .onboarding-section-title {
        margin-top: 0.9rem;
        margin-bottom: 0.45rem;
        color: #1f3f66;
        font-size: 1.02rem;
        font-weight: 700;
    }
    .process-card {
        background: var(--landing-card-color);
        border: 1px solid #d0ddec;
        border-radius: 11px;
        padding: 0.72rem;
    }
    .process-step {
        width: 22px;
        height: 22px;
        border-radius: 999px;
        display: inline-grid;
        place-items: center;
        color: #ffffff;
        background: #2f6fa3;
        font-size: 0.74rem;
        font-weight: 700;
        margin-bottom: 0.38rem;
    }
    .process-title {
        margin: 0 0 0.24rem 0;
        color: #1f3f66;
        font-size: 0.88rem;
        font-weight: 700;
    }
    .process-text {
        margin: 0;
        color: #5a7188;
        font-size: 0.8rem;
        line-height: 1.35;
    }

    .page-intro-strip {
        background: #f2f7fc;
        border: 1px solid #d8e4f0;
        border-radius: 10px;
        padding: 0.62rem 0.75rem;
        margin-bottom: 0.85rem;
    }

    .page-intro-title {
        margin: 0;
        font-size: 0.78rem;
        color: #2f6fa3;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-weight: 700;
    }

    .page-intro-text {
        margin: 0.2rem 0 0 0;
        color: #4f6479;
        font-size: 0.88rem;
    }

    /* Dark mode when Streamlit theme is explicitly toggled */
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) {
        --landing-card-color: #1f2a37;
        --panel-border: #2c3d50;
        --panel-bg: #16222f;
        --text-main: #e5edf5;
        --text-soft: #a8bdd1;
    }

    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 8% 2%, rgba(73, 160, 223, 0.12), rgba(73, 160, 223, 0) 30%), #0f1722 !important;
    }

    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111c29 0%, #0f1722 100%) !important;
        border-right: 1px solid #233347 !important;
    }

    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) p,
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) li,
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) label {
        color: var(--text-soft) !important;
    }

    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) [data-baseweb="tab-list"],
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) [data-baseweb="tab-panel"],
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) [data-testid="stDataFrame"],
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) [data-testid="stMetric"],
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) [data-testid="stExpander"],
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) [data-testid="stAlert"],
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) .studio-status-card,
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) .onboarding-hero,
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) .onboarding-feature,
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) .process-card,
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) .page-intro-strip {
        background: #162230 !important;
        border-color: #2d4257 !important;
        color: var(--text-main) !important;
    }

    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) .stButton > button {
        background: #1a2a3a !important;
        border-color: #385470 !important;
        color: #d7e6f4 !important;
    }

    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) .stButton > button * {
        color: inherit !important;
    }

    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) .stButton button[kind="primary"],
    :is(html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"], [data-theme="dark"], html[data-base-theme="dark"], body[data-base-theme="dark"], .stApp[data-base-theme="dark"], [data-base-theme="dark"]) [data-testid="baseButton-primary"] {
        background: linear-gradient(120deg, #2f6fa3, #255a86) !important;
        color: #ffffff !important;
        border-color: #2f6fa3 !important;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --landing-card-color: #1f2a37;
            --panel-border: #2c3d50;
            --panel-bg: #16222f;
            --text-main: #e5edf5;
            --text-soft: #a8bdd1;
        }

        html, body, [class*="css"], .stApp {
            color: var(--text-main) !important;
        }

        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at 8% 2%, rgba(73, 160, 223, 0.12), rgba(73, 160, 223, 0) 30%), #0f1722 !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #111c29 0%, #0f1722 100%) !important;
            border-right: 1px solid #233347 !important;
        }

        [data-testid="stSidebar"] hr {
            border-color: #233347 !important;
        }

        p, li, label {
            color: var(--text-soft) !important;
        }

        .hero {
            background: linear-gradient(120deg, #0f2740 0%, #173a5d 100%) !important;
            border: 1px solid #26496e !important;
        }

        [data-testid="stFileUploader"] {
            background: #131f2c !important;
            border-color: #2b3d51 !important;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: linear-gradient(140deg, #162332, #1a2939) !important;
            border-color: #35516e !important;
        }

        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        [data-baseweb="select"] > div {
            background: #162230 !important;
            border-color: #31465c !important;
            color: #d7e4f0 !important;
        }

        [data-baseweb="tab-list"],
        [data-baseweb="tab-panel"],
        [data-testid="stDataFrame"],
        [data-testid="stMetric"],
        [data-testid="stExpander"],
        [data-testid="stAlert"],
        .studio-status-card,
        .onboarding-hero,
        .onboarding-feature,
        .process-card,
        .page-intro-strip {
            background: #162230 !important;
            border-color: #2d4257 !important;
            color: var(--text-main) !important;
        }

        .studio-status-label,
        .onboarding-feature-text,
        .process-text,
        .page-intro-text,
        .studio-section-subtext {
            color: var(--text-soft) !important;
        }

        .onboarding-title,
        .onboarding-feature-title,
        .process-title,
        .studio-section-heading,
        .page-intro-title {
            color: #dbe9f5 !important;
        }

        .stButton > button {
            background: #1a2a3a !important;
            border-color: #385470 !important;
            color: #d7e6f4 !important;
        }

        .stButton button[kind="primary"],
        [data-testid="baseButton-primary"] {
            background: linear-gradient(120deg, #2f6fa3, #255a86) !important;
            color: #ffffff !important;
            border-color: #2f6fa3 !important;
        }
    }

    </style>
    """, unsafe_allow_html=True)


def inject_screen_mode_override():
    """Force full-screen light/dark mode similar to IDE themes."""
    mode = st.session_state.get("screen_mode", "System")

    if mode == "Dark":
        st.markdown(
            """
            <style>
            html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main, [data-testid="stAppViewBlockContainer"] {
                background: #0f1722 !important;
                color: #e5edf5 !important;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #111c29 0%, #0f1722 100%) !important;
                border-right: 1px solid #233347 !important;
            }

            p, li, label, h1, h2, h3, h4, h5, h6 {
                color: #d7e4f0 !important;
            }

            [data-testid="stFileUploader"],
            [data-testid="stFileUploaderDropzone"],
            [data-baseweb="tab-list"],
            [data-baseweb="tab-panel"],
            [data-testid="stDataFrame"],
            [data-testid="stMetric"],
            [data-testid="stExpander"],
            [data-testid="stAlert"],
            .studio-status-card,
            .onboarding-hero,
            .onboarding-feature,
            .process-card,
            .page-intro-strip,
            .stMarkdown {
                background: #162230 !important;
                border-color: #2d4257 !important;
                color: #e5edf5 !important;
            }

            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input,
            [data-baseweb="select"] > div {
                background: #162230 !important;
                border-color: #31465c !important;
                color: #d7e4f0 !important;
            }

            .stButton > button {
                background: #1a2a3a !important;
                border-color: #385470 !important;
                color: #d7e6f4 !important;
            }

            .stButton button[kind="primary"],
            [data-testid="baseButton-primary"] {
                background: linear-gradient(120deg, #2f6fa3, #255a86) !important;
                color: #ffffff !important;
                border-color: #2f6fa3 !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    elif mode == "Light":
        st.markdown(
            """
            <style>
            html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main, [data-testid="stAppViewBlockContainer"] {
                background: #f5f8fb !important;
                color: #1f344d !important;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #f2f6fa 0%, #edf3f8 100%) !important;
                border-right: 1px solid #d6e1eb !important;
            }

            p, li, label, h1, h2, h3, h4, h5, h6 {
                color: #1f344d !important;
            }

            [data-testid="stFileUploader"],
            [data-testid="stFileUploaderDropzone"],
            [data-baseweb="tab-list"],
            [data-baseweb="tab-panel"],
            [data-testid="stDataFrame"],
            [data-testid="stMetric"],
            [data-testid="stExpander"],
            [data-testid="stAlert"],
            .studio-status-card,
            .onboarding-hero,
            .onboarding-feature,
            .process-card,
            .page-intro-strip,
            .stMarkdown {
                background: #ffffff !important;
                border-color: #dbe6ef !important;
                color: #1f344d !important;
            }

            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input,
            [data-baseweb="select"] > div {
                background: #ffffff !important;
                border-color: #cddaea !important;
                color: #1f344d !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


# ==================== API HELPER FUNCTIONS ====================

def get_current_user():
    """Get or create current user session."""
    if st.session_state.current_user is None:
        try:
            response = requests.get(f"{API_BASE_URL}/auth/demo-login", timeout=10)
            if response.status_code == 200:
                data = response.json()
                st.session_state.current_user = data
                return data
        except Exception:
            pass
    return st.session_state.current_user


def connect_data_source(source_type: str, config: Dict[str, Any]):
    """Connect to external data source."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/connect-source",
            json={"source_type": source_type, "config": config},
            timeout=REQUEST_TIMEOUT
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


def register_dataset(dataset_name: str, description: str, visibility: str):
    """Register current dataset."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/datasets/register",
            json={
                "dataset_name": dataset_name,
                "description": description,
                "visibility": visibility
            },
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


def list_public_datasets():
    """List all public datasets."""
    try:
        response = requests.get(f"{API_BASE_URL}/datasets/public", timeout=30)
        return response.json()
    except Exception as e:
        return {"success": False, "datasets": []}


def get_user_datasets():
    """Get user's datasets."""
    try:
        response = requests.get(f"{API_BASE_URL}/workspace/datasets", timeout=30)
        return response.json()
    except Exception as e:
        return {"success": False, "datasets": []}


def get_workspace_reports():
    """Get reports in current user's workspace."""
    try:
        response = requests.get(f"{API_BASE_URL}/workspace/reports", timeout=30)
        return response.json()
    except Exception:
        return {"success": False, "reports": []}


def get_workspace_pipelines():
    """Get pipelines in current user's workspace."""
    try:
        response = requests.get(f"{API_BASE_URL}/workspace/pipelines", timeout=30)
        return response.json()
    except Exception:
        return {"success": False, "pipelines": []}


def load_dataset(dataset_id: str):
    """Load a registered dataset."""
    try:
        response = requests.get(f"{API_BASE_URL}/datasets/{dataset_id}/load", timeout=60)
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


def generate_report(report_name: str, description: str = ""):
    """Generate dataset report."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/reports/generate",
            json={"report_name": report_name, "description": description},
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


def create_share_link(resource_type: str, resource_id: int, is_public: bool = True):
    """Create share link."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/share/create",
            json={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "access_level": "viewer",
                "is_public_link": is_public
            },
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


# ==================== PAGE: SIDEBAR ====================

def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        st.markdown(
            '''
            <div class="brand-wrap">
                <div class="brand-applydf">ApplyDF</div>
                <div class="brand-subtitle">Nexus</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        # User info
        user = get_current_user()
        if user and user.get("success", True):
            st.markdown(f"**{user.get('username', 'Guest')}**")

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
            st.markdown("---")
        
        # Navigation
        st.markdown("### Screen")
        st.selectbox("Mode", SCREEN_MODES, key="screen_mode")
        st.markdown("---")

        pages = {
            "Data Studio": "Data Studio",
            "Data Sources": "Data Sources",
            "Workspace": "Workspace",
            "Public Datasets": "Public Datasets",
            "Reports": "Reports"
        }
        
        for label, page in pages.items():
            if st.button(label, use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        **ApplyDF Nexus** is a collaborative data transformation platform.
        
        - Connect multiple data sources
        - Auto-clean datasets
        - Generate reports
        - Share publicly
        - Team workspace
        """)


# ==================== PAGE: DATA SOURCES ====================

def page_data_sources():
    """Data source connection page."""
    st.markdown('<div class="hero"><h1>Connect Data Sources</h1><p>Import data from databases, cloud storage, and APIs</p></div>', unsafe_allow_html=True)
    st.markdown(
        '''
        <div class="page-intro-strip">
            <p class="page-intro-title">Enterprise Ingestion</p>
            <p class="page-intro-text">Connect trusted sources, validate schema, and prepare clean inputs for downstream ML pipelines.</p>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    
    source_type = st.selectbox(
        "Select Data Source",
        ["CSV URL", "PostgreSQL", "MySQL", "AWS S3", "Google Sheets", "SQLite", "API (JSON)"]
    )
    
    st.markdown("---")
    
    if source_type == "CSV URL":
        url = st.text_input("CSV URL", placeholder="https://example.com/data.csv")
        
        if st.button("Connect", type="primary"):
            if url:
                with st.spinner("Loading data..."):
                    result = connect_data_source("csv_url", {"url": url})
                    if result.get("success"):
                        st.success(f"✅ Connected! Loaded {result['shape'][0]} rows, {result['shape'][1]} columns")
                        st.dataframe(pd.DataFrame(result['preview']))
                    else:
                        st.error(f"❌ {result.get('message', 'Connection failed')}")
    
    elif source_type == "PostgreSQL":
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("Host", "localhost")
            database = st.text_input("Database")
            table_name = st.text_input("Table Name")
        with col2:
            port = st.number_input("Port", value=5432)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
        
        if st.button("Connect", type="primary"):
            if all([host, database, username, password, table_name]):
                config = {
                    "host": host,
                    "port": port,
                    "database": database,
                    "username": username,
                    "password": password,
                    "table_name": table_name
                }
                with st.spinner("Connecting to PostgreSQL..."):
                    result = connect_data_source("postgres", config)
                    if result.get("success"):
                        st.success(f"✅ Connected! Loaded {result['shape'][0]} rows")
                    else:
                        st.error(f"❌ {result.get('message')}")
    
    elif source_type == "MySQL":
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("Host", "localhost")
            database = st.text_input("Database")
            table_name = st.text_input("Table Name")
        with col2:
            port = st.number_input("Port", value=3306)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
        
        if st.button("Connect", type="primary"):
            if all([host, database, username, password, table_name]):
                config = {
                    "host": host,
                    "port": port,
                    "database": database,
                    "username": username,
                    "password": password,
                    "table_name": table_name
                }
                with st.spinner("Connecting to MySQL..."):
                    result = connect_data_source("mysql", config)
                    if result.get("success"):
                        st.success(f"✅ Connected! Loaded {result['shape'][0]} rows")
                    else:
                        st.error(f"❌ {result.get('message')}")
    
    elif source_type == "AWS S3":
        bucket = st.text_input("Bucket Name")
        file_key = st.text_input("File Key/Path")
        col1, col2 = st.columns(2)
        with col1:
            access_key = st.text_input("AWS Access Key ID", type="password")
            region = st.text_input("Region", "us-east-1")
        with col2:
            secret_key = st.text_input("AWS Secret Access Key", type="password")
            file_format = st.selectbox("File Format", ["csv", "parquet", "excel", "json"])
        
        if st.button("Connect", type="primary"):
            if all([bucket, file_key]):
                config = {
                    "bucket_name": bucket,
                    "file_key": file_key,
                    "aws_access_key_id": access_key if access_key else None,
                    "aws_secret_access_key": secret_key if secret_key else None,
                    "region_name": region,
                    "file_format": file_format
                }
                with st.spinner("Loading from S3..."):
                    result = connect_data_source("s3", config)
                    if result.get("success"):
                        st.success(f"✅ Loaded! {result['shape'][0]} rows")
                    else:
                        st.error(f"❌ {result.get('message')}")
    
    elif source_type == "Google Sheets":
        sheet_url = st.text_input("Google Sheets URL")
        api_key = st.text_input("Google API Key (optional)", type="password")
        credentials_path = st.text_input("Service Account JSON Path (optional)")
        
        if st.button("Connect", type="primary"):
            if sheet_url:
                config = {"sheet_url": sheet_url}
                if api_key:
                    config["api_key"] = api_key
                if credentials_path:
                    config["credentials_json"] = credentials_path
                with st.spinner("Loading from Google Sheets..."):
                    result = connect_data_source("google_sheets", config)
                    if result.get("success"):
                        st.success(f"✅ Loaded! {result['shape'][0]} rows")
                    else:
                        st.error(f"❌ {result.get('message')}")

    elif source_type == "SQLite":
        db_path = st.text_input("SQLite Database Path", placeholder="C:/path/to/database.db")
        table_name = st.text_input("Table Name (optional)")
        query = st.text_area("SQL Query (optional)", placeholder="SELECT * FROM my_table LIMIT 1000")

        if st.button("Connect", type="primary"):
            if db_path and (table_name or query):
                config = {
                    "database_path": db_path,
                    "table_name": table_name if table_name else None,
                    "query": query if query else None,
                }
                with st.spinner("Loading from SQLite..."):
                    result = connect_data_source("sqlite", config)
                    if result.get("success"):
                        st.success(f"✅ Loaded! {result['shape'][0]} rows")
                    else:
                        st.error(f"❌ {result.get('message')}")
            else:
                st.warning("Please provide database path and either table name or query")

    elif source_type == "API (JSON)":
        url = st.text_input("API URL", placeholder="https://api.example.com/data")
        method = st.selectbox("HTTP Method", ["GET", "POST"])
        headers_text = st.text_area("Headers (JSON, optional)", placeholder='{"Authorization": "Bearer ..."}')
        params_text = st.text_area("Query Params (JSON, optional)", placeholder='{"limit": 100}')
        json_path = st.text_input("JSON Path (optional)", placeholder="data.items")

        if st.button("Connect", type="primary"):
            if url:
                try:
                    headers = json.loads(headers_text) if headers_text.strip() else None
                    params = json.loads(params_text) if params_text.strip() else None
                except Exception:
                    st.error("Headers/Params must be valid JSON")
                    return

                config = {
                    "url": url,
                    "method": method,
                    "headers": headers,
                    "params": params,
                    "json_path": json_path if json_path else None,
                }
                with st.spinner("Loading from API..."):
                    result = connect_data_source("api", config)
                    if result.get("success"):
                        st.success(f"✅ Loaded! {result['shape'][0]} rows")
                        st.dataframe(pd.DataFrame(result.get("preview", [])), use_container_width=True)
                    else:
                        st.error(f"❌ {result.get('message')}")
            else:
                st.warning("Please provide API URL")


# ==================== PAGE: WORKSPACE ====================

def page_workspace():
    """User workspace page."""
    st.markdown('<div class="hero"><h1>My Workspace</h1><p>Manage your datasets and shared resources</p></div>', unsafe_allow_html=True)
    st.markdown(
        '''
        <div class="page-intro-strip">
            <p class="page-intro-title">Team Collaboration</p>
            <p class="page-intro-text">Manage reusable datasets, share validated pipelines, and track quality outcomes across teams.</p>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    
    tabs = st.tabs(["My Datasets", "Shared With Me", "Reports", "Pipelines", "Register Dataset"])
    
    with tabs[0]:
        st.subheader("My Datasets")
        result = get_user_datasets()
        
        if result.get("success") and result.get("datasets"):
            for dataset in result["datasets"]:
                with st.expander(f"{dataset['dataset_name']} ({dataset['visibility']})"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Rows", dataset['row_count'])
                    col2.metric("Columns", dataset['column_count'])
                    col3.metric("Quality Score", f"{dataset['data_quality_score']:.1f}/100" if dataset['data_quality_score'] else "N/A")
                    
                    if st.button(f"Load Dataset", key=f"load_{dataset['dataset_id']}"):
                        with st.spinner("Loading..."):
                            load_result = load_dataset(dataset['dataset_id'])
                            if load_result.get("success"):
                                st.success("✅ Dataset loaded!")
                                st.rerun()
                            else:
                                st.error("Failed to load dataset")
        else:
            st.info("No datasets registered yet. Upload and register a dataset to get started!")
    
    with tabs[1]:
        st.subheader("Shared With Me")
        try:
            response = requests.get(f"{API_BASE_URL}/workspace/shared", timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("shares"):
                    for share in data["shares"]:
                        st.markdown(f"- **{share['resource_type']}** (ID: {share['resource_id']}) - {share['access_level']}")
                else:
                    st.info("No resources shared with you yet")
        except Exception:
            st.info("Loading...")
    
    with tabs[2]:
        st.subheader("My Reports")
        reports = get_workspace_reports()
        if reports.get("success") and reports.get("reports"):
            for report in reports["reports"]:
                with st.expander(f"{report.get('report_name', 'Report')} ({report.get('report_id', '')})"):
                    st.write(report.get("description", "No description"))
                    st.write(f"Created: {report.get('created_at', 'N/A')}")
                    st.write(f"Quality Score: {report.get('data_quality_score', 0)}")
        else:
            st.info("No reports in workspace yet")

    with tabs[3]:
        st.subheader("My Pipelines")
        pipelines = get_workspace_pipelines()
        if pipelines.get("success") and pipelines.get("pipelines"):
            for pipeline in pipelines["pipelines"]:
                with st.expander(f"{pipeline.get('pipeline_name', 'Pipeline')} ({pipeline.get('pipeline_id', '')})"):
                    st.write(pipeline.get("description", "No description"))
                    st.write(f"Visibility: {pipeline.get('visibility', 'private')}")
                    for idx, step in enumerate(pipeline.get("pipeline_steps", []) or [], start=1):
                        if isinstance(step, dict):
                            st.write(f"{idx}. {step.get('step', 'step')} - {step.get('reason', '')}")
                        else:
                            st.write(f"{idx}. {step}")
        else:
            st.info("No pipelines in workspace yet")

    with tabs[4]:
        st.subheader("Register Current Dataset")
        st.markdown("Save the currently loaded dataset to your workspace")
        
        dataset_name = st.text_input("Dataset Name")
        description = st.text_area("Description (optional)")
        visibility = st.selectbox("Visibility", ["Private", "Public", "Shared"])
        
        if st.button("Register Dataset", type="primary"):
            if dataset_name:
                with st.spinner("Registering..."):
                    result = register_dataset(dataset_name, description, visibility.lower())
                    if result.get("success"):
                        st.success(f"✅ Dataset registered! ID: {result['dataset_id']}")
                        st.session_state.last_registered_dataset_id = result['dataset_id']
                    else:
                        st.error(f"❌ {result.get('message')}")
            else:
                st.warning("Please provide a dataset name")


# ==================== PAGE: PUBLIC DATASETS ====================

def page_public_datasets():
    """Public datasets exploration page."""
    st.markdown('<div class="hero"><h1>Public Datasets</h1><p>Explore and clone public datasets from the community</p></div>', unsafe_allow_html=True)
    
    result = list_public_datasets()
    
    if result.get("success") and result.get("datasets"):
        st.markdown(f"**{result['count']} public datasets available**")
        
        for dataset in result["datasets"]:
            with st.expander(f"{dataset['dataset_name']}"):
                if dataset.get('description'):
                    st.markdown(dataset['description'])

                columns_info = dataset.get("columns_info", {})
                sample_values = columns_info.get("sample_values", []) if isinstance(columns_info, dict) else []
                if sample_values:
                    st.markdown("**Dataset Preview**")
                    st.dataframe(pd.DataFrame(sample_values), use_container_width=True)
                if isinstance(columns_info, dict) and columns_info.get("types"):
                    st.markdown("**Column Summary**")
                    st.dataframe(
                        pd.DataFrame(list(columns_info.get("types", {}).items()), columns=["Column", "Type"]),
                        use_container_width=True,
                    )
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Rows", dataset['row_count'])
                col2.metric("Columns", dataset['column_count'])
                col3.metric("Quality", f"{dataset['data_quality_score']:.0f}/100" if dataset['data_quality_score'] else "N/A")
                col4.metric("Pipeline", "✅" if dataset['pipeline_applied'] else "❌")
                
                cols = st.columns([2, 2, 3])
                
                if cols[0].button("Load Dataset", key=f"public_load_{dataset['dataset_id']}"):
                    with st.spinner("Loading..."):
                        load_result = load_dataset(dataset['dataset_id'])
                        if load_result.get("success"):
                            st.success("✅ Loaded!")
                        else:
                            st.error("Failed to load")

                if cols[2].button("Download Dataset", key=f"public_download_{dataset['dataset_id']}"):
                    with st.spinner("Preparing download..."):
                        load_result = load_dataset(dataset['dataset_id'])
                        if load_result.get("success"):
                            try:
                                dl = requests.get(f"{API_BASE_URL}/download/csv", timeout=60)
                                if dl.status_code == 200:
                                    st.download_button(
                                        "Download CSV",
                                        data=dl.content,
                                        file_name=f"{dataset['dataset_name']}.csv",
                                        mime="text/csv",
                                        key=f"public_download_btn_{dataset['dataset_id']}",
                                        use_container_width=True,
                                    )
                                else:
                                    st.error("Failed to generate download")
                            except Exception:
                                st.error("Failed to download dataset")
                        else:
                            st.error("Failed to load dataset")
                
                if cols[1].button("Clone Pipeline", key=f"clone_{dataset['dataset_id']}"):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/datasets/{dataset['dataset_id']}/clone-pipeline",
                            timeout=30
                        )
                        if response.status_code == 200:
                            st.success("✅ Pipeline cloned!")
                        else:
                            st.error("No pipeline available")
                    except Exception:
                        st.error("Failed to clone")
    else:
        st.info("No public datasets available yet. Be the first to share one!")


# ==================== PAGE: REPORTS ====================

def page_reports():
    """Reports generation and viewing page."""
    st.markdown('<div class="hero"><h1>Dataset Reports</h1><p>Generate comprehensive analysis reports</p></div>', unsafe_allow_html=True)
    st.markdown(
        '''
        <div class="page-intro-strip">
            <p class="page-intro-title">Audit and Governance</p>
            <p class="page-intro-text">Generate traceable before/after evidence for model-readiness reviews, compliance, and stakeholder reporting.</p>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    
    tabs = st.tabs(["Generate Report", "View Last Report"])
    
    with tabs[0]:
        st.subheader("Generate New Report")
        
        report_name = st.text_input("Report Name", "Dataset Analysis Report")
        description = st.text_area("Description", "Comprehensive analysis of the dataset")
        
        if st.button("Generate Report", type="primary"):
            with st.spinner("Generating report..."):
                result = generate_report(report_name, description)
                if result.get("success"):
                    st.success(f"✅ Report generated! ID: {result['report_id']}")
                    st.session_state.last_report = result['report']
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('message')}")
    
    with tabs[1]:
        if st.session_state.last_report:
            report = st.session_state.last_report
            
            st.markdown(f"## {report['report_name']}")
            st.markdown(f"*{report.get('description', '')}*")
            st.markdown(f"Generated: {report['created_at']}")

            report_id = report.get("report_id")
            if report_id:
                download_url = f"{API_BASE_URL}/reports/{report_id}/download"
                try:
                    dl = requests.get(download_url, timeout=60)
                    if dl.status_code == 200:
                        st.download_button(
                            "Download Cleaned Dataset",
                            data=dl.content,
                            file_name=f"report_{report_id}_cleaned.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )
                except Exception:
                    pass
            
            # Dataset Summary
            st.markdown("### Dataset Summary")
            summary = report['dataset_summary']
            col1, col2, col3 = st.columns(3)
            col1.metric("Rows", summary['shape']['rows'])
            col2.metric("Columns", summary['shape']['columns'])
            col3.metric("Quality Score", f"{report.get('data_quality_score', 0):.1f}/100")
            
            # Missing Values
            if summary.get('missing_values'):
                st.markdown("### ❓ Missing Values")
                missing_data = summary['missing_values']
                if missing_data['total_missing'] > 0:
                    st.warning(f"Total missing values: {missing_data['total_missing']}")
                else:
                    st.success("No missing values!")
            
            # Visualizations
            if report.get('visualizations'):
                st.markdown("### 📈 Visualizations")
                for viz in report['visualizations'][:5]:  # Show first 5
                    st.markdown(f"**{viz['title']}**")
                    try:
                        fig = go.Figure(json.loads(viz['config']))
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        st.info("Visualization not available")
            
            # Before/After Comparison
            if report.get('before_after_comparison'):
                st.markdown("### 🔄 Before vs After")
                comp = report['before_after_comparison']
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Before**")
                    st.metric("Rows", comp['shape']['before']['rows'])
                    st.metric("Missing", comp['missing_values']['before'])
                with col2:
                    st.markdown("**After**")
                    st.metric("Rows", comp['shape']['after']['rows'])
                    st.metric("Missing", comp['missing_values']['after'])
        else:
            st.info("No report generated yet. Generate one from the first tab!")


# ==================== PAGE: DATA STUDIO ====================

def studio_api_call(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    expect_json: bool = True,
):
    """Shared API client for transformation studio."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
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
    except requests.exceptions.HTTPError:
        try:
            detail = response.json().get("detail", "Request failed")
        except Exception:
            detail = "Request failed"
        st.error(detail)
    except Exception as exc:
        st.error(str(exc))
    return None


def studio_get_preview() -> Optional[Dict[str, Any]]:
    response = studio_api_call("/preview")
    return response if isinstance(response, dict) and "shape" in response else None


def studio_get_visual_compare_data(limit: int = 1000) -> Optional[Dict[str, Any]]:
    response = studio_api_call("/visual-compare", params={"limit": limit})
    return response if isinstance(response, dict) and response.get("success") else None


def studio_get_dataset_health() -> Optional[Dict[str, Any]]:
    response = studio_api_call("/dataset-health")
    return response if isinstance(response, dict) and response.get("success") else None


def studio_generate_auto_pipeline() -> Optional[Dict[str, Any]]:
    response = studio_api_call("/auto-pipeline", method="POST")
    return response if isinstance(response, dict) and response.get("success") else None


def studio_auto_clean() -> Optional[Dict[str, Any]]:
    response = studio_api_call("/auto-clean", method="POST")
    return response if isinstance(response, dict) and response.get("success") else None


def studio_export_pipeline_code(export_format: str) -> Optional[Dict[str, Any]]:
    response = studio_api_call("/pipeline/export-code", params={"format": export_format})
    return response if isinstance(response, dict) and response.get("success") else None


def studio_get_pipeline_history(limit: int = 25) -> Optional[Dict[str, Any]]:
    response = studio_api_call("/pipeline-history", params={"limit": limit})
    return response if isinstance(response, dict) and response.get("success") else None


def studio_build_selected_transform_code(method: str, params: Dict[str, Any], text_column: Optional[str]) -> str:
    """Build standalone Python code for the currently selected transform."""
    payload = {
        "transformation_type": method,
        "parameters": params,
        "text_column": text_column,
    }
    payload_json = json.dumps(payload, indent=4)

    return f'''"""Generated by ApplyDF Nexus: single transformation export."""

import json
import requests

API_BASE_URL = "http://localhost:8000"

payload = json.loads({payload_json!r})

response = requests.post(
    f"{{API_BASE_URL}}/transform",
    json=payload,
    timeout=120,
)
response.raise_for_status()
result = response.json()

print("Success:", result.get("success"))
print("Message:", result.get("message"))
print("Metadata:", result.get("metadata"))
'''


def studio_get_text_columns(preview: Dict[str, Any]) -> List[str]:
    dtypes = preview.get("data_types", {})
    return [name for name, dtype in dtypes.items() if "object" in str(dtype).lower() or "string" in str(dtype).lower()]


def studio_get_numeric_columns(preview: Dict[str, Any]) -> List[str]:
    dtypes = preview.get("data_types", {})
    aliases = ["int", "float", "double", "number"]
    return [name for name, dtype in dtypes.items() if any(alias in str(dtype).lower() for alias in aliases)]


def studio_render_preview(preview: Dict[str, Any]) -> None:
    shape = preview.get("shape", [0, 0])
    missing_total = int(sum(preview.get("missing_values", {}).values()))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows", f"{shape[0]:,}")
    m2.metric("Columns", f"{shape[1]:,}")
    m3.metric("Missing", f"{missing_total:,}")
    m4.metric("Transforms", len(st.session_state.transformation_history))

    tab_data, tab_types, tab_missing, tab_stats, tab_visual = st.tabs(["Data", "Types", "Missing", "Stats", "Visuals"])

    with tab_data:
        preview_df = pd.DataFrame(preview.get("preview_data", []))
        if preview_df.empty:
            st.info("No preview rows available.")
        else:
            c1, c2 = st.columns([2, 1])
            with c1:
                search_query = st.text_input("Search rows", key="studio_data_search", placeholder="Type to filter rows")
            with c2:
                only_missing = st.checkbox("Only rows with missing values", key="studio_only_missing")

            selectable_columns = preview_df.columns.tolist()
            selected_columns = st.multiselect(
                "Visible columns",
                options=selectable_columns,
                default=selectable_columns,
                key="studio_visible_columns",
            )

            sort_c1, sort_c2 = st.columns([2, 1])
            with sort_c1:
                sort_col = st.selectbox("Sort by", options=["(none)"] + selectable_columns, key="studio_sort_col")
            with sort_c2:
                sort_desc = st.checkbox("Descending", key="studio_sort_desc")

            filtered = preview_df.copy()
            if selected_columns:
                filtered = filtered[selected_columns]

            if search_query:
                mask = filtered.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False)).any(axis=1)
                filtered = filtered[mask]

            if only_missing:
                missing_mask = filtered.isna().any(axis=1) | (filtered.astype(str).eq("").any(axis=1))
                filtered = filtered[missing_mask]

            if sort_col != "(none)" and sort_col in filtered.columns:
                filtered = filtered.sort_values(by=sort_col, ascending=not sort_desc)

            styled = filtered.style.apply(
                lambda col: [
                    "background-color: #fff3cd; color: #7a5b00" if (pd.isna(v) or str(v).strip() == "") else ""
                    for v in col
                ]
            )
            st.dataframe(styled, use_container_width=True)

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
            rows = []
            for name, values in stats.items():
                row = {"Column": name}
                row.update(values)
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("No numeric data")

    with tab_visual:
        compare = studio_get_visual_compare_data(limit=1500)
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

        vis_type = st.selectbox("Visualization", ["Distribution", "Box", "Scatter", "Reciprocal", "Squared"], key="studio_vis_type")
        
        if vis_type == "Scatter":
            if len(common_numeric_cols) >= 2:
                x_col = st.selectbox("X-axis", common_numeric_cols, key="studio_x_col")
                y_col = st.selectbox("Y-axis", [c for c in common_numeric_cols if c != x_col], key="studio_y_col")
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(px.scatter(before_df, x=x_col, y=y_col, title="Before"), use_container_width=True)
                with c2:
                    st.plotly_chart(px.scatter(after_df, x=x_col, y=y_col, title="After"), use_container_width=True)
            else:
                st.warning("Need at least 2 numeric columns for scatter plot")
                return
        else:
            selected = st.selectbox("Column", common_numeric_cols, key="studio_compare_col")
            c1, c2 = st.columns(2)
            with c1:
                series = pd.to_numeric(before_df[selected], errors="coerce")
                if vis_type == "Distribution":
                    fig = px.histogram(x=series.dropna(), nbins=30, title="Before")
                elif vis_type == "Box":
                    fig = px.box(y=series.dropna(), title="Before")
                elif vis_type == "Reciprocal":
                    transformed = 1.0 / series.replace(0, pd.NA)
                    fig = px.histogram(transformed.dropna(), nbins=30, title="Before (Reciprocal)")
                else:  # Squared
                    transformed = series ** 2
                    fig = px.histogram(transformed.dropna(), nbins=30, title="Before (Squared)")
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                series = pd.to_numeric(after_df[selected], errors="coerce")
                if vis_type == "Distribution":
                    fig = px.histogram(x=series.dropna(), nbins=30, title="After")
                elif vis_type == "Box":
                    fig = px.box(y=series.dropna(), title="After")
                elif vis_type == "Reciprocal":
                    transformed = 1.0 / series.replace(0, pd.NA)
                    fig = px.histogram(transformed.dropna(), nbins=30, title="After (Reciprocal)")
                else:  # Squared
                    transformed = series ** 2
                    fig = px.histogram(transformed.dropna(), nbins=30, title="After (Squared)")
                st.plotly_chart(fig, use_container_width=True)


def studio_render_parameter_inputs(method: str, preview: Dict[str, Any]) -> tuple[Dict[str, Any], Optional[str]]:
    params: Dict[str, Any] = {}
    text_column: Optional[str] = None
    text_cols = studio_get_text_columns(preview)
    numeric_cols = studio_get_numeric_columns(preview)

    if method in ["PCA", "SVD"]:
        max_components = len(numeric_cols) if numeric_cols else 10
        upper = min(10, max_components)
        params["n_components"] = st.slider("n_components", 1, max(1, upper), min(2, max(1, upper)), key="studio_n_components")
    elif method == "t-SNE":
        params["n_components"] = st.radio("Dimensions", [2, 3], horizontal=True, key="studio_tsne_dims")
        params["perplexity"] = st.slider("Perplexity", 5, 50, 30, key="studio_tsne_perp")
        params["learning_rate"] = st.slider("Learning Rate", 10, 1000, 200, step=10, key="studio_tsne_lr")
        params["n_iter"] = st.slider("Iterations", 250, 2000, 1000, step=50, key="studio_tsne_iter")
    elif method == "UMAP":
        params["n_components"] = st.radio("Dimensions", [2, 3], horizontal=True, key="studio_umap_dims")
        params["n_neighbors"] = st.slider("n_neighbors", 5, 50, 15, key="studio_umap_neighbors")
        params["min_dist"] = st.slider("min_dist", 0.0, 1.0, 0.1, step=0.01, key="studio_umap_min_dist")
    elif method == "Min-Max Normalization":
        min_val = st.number_input("Range min", value=0.0, key="studio_mm_min")
        max_val = st.number_input("Range max", value=1.0, key="studio_mm_max")
        params["feature_range"] = [min_val, max_val]
    elif method == "Quantile Transformation":
        params["n_quantiles"] = st.slider("n_quantiles", 10, 1000, 100, key="studio_quantiles")
        params["output_distribution"] = st.selectbox("Output distribution", ["uniform", "normal"], key="studio_quantile_output")
    elif method == "Log/Power Transforms":
        params["method"] = st.selectbox("Method", ["log", "log10", "log2", "power"], key="studio_log_method")
        if params["method"] == "power":
            params["power"] = st.number_input("Power", value=2.0, key="studio_power")
    elif method == "K-Means Clustering":
        params["n_clusters"] = st.slider("n_clusters", 2, 20, 3, key="studio_kmeans_clusters")
        params["max_iter"] = st.slider("max_iter", 100, 1000, 300, step=50, key="studio_kmeans_iter")
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
            text_column = st.selectbox("Text column", text_cols, key="studio_text_col")
        else:
            st.warning("No text-like columns detected.")

        if method == "TF-IDF":
            params["max_features"] = st.slider("max_features", 10, 500, 100, key="studio_tfidf_max")
        elif method == "N-gram Analysis":
            min_n = st.slider("min_n", 1, 5, 1, key="studio_ngram_min")
            max_n = st.slider("max_n", min_n, 5, max(min_n, 2), key="studio_ngram_max")
            params["max_features"] = st.slider("max_features", 10, 500, 100, key="studio_ngram_features")
            params["ngram_range"] = [min_n, max_n]
        elif method == "Word2Vec":
            params["vector_size"] = st.slider("vector_size", 50, 300, 100, step=10, key="studio_w2v_size")
            params["window"] = st.slider("window", 2, 10, 5, key="studio_w2v_window")
            params["min_count"] = st.slider("min_count", 1, 5, 2, key="studio_w2v_min_count")
        elif method == "Transformer Embeddings":
            params["model_name"] = st.selectbox("Model", ["sentence-transformers/all-MiniLM-L6-v2", "sentence-transformers/all-mpnet-base-v2", "sentence-transformers/paraphrase-MiniLM-L6-v2"], key="studio_transformer_model")
            params["max_length"] = st.slider("max_length", 64, 512, 128, key="studio_transformer_max_length")
        elif method == "Text Normalization":
            params["lowercase"] = st.checkbox("lowercase", value=True, key="studio_text_lowercase")
            params["remove_special"] = st.checkbox("remove_special", value=True, key="studio_text_remove_special")
            params["lemmatize"] = st.checkbox("lemmatize", value=True, key="studio_text_lemmatize")
        elif method == "Topic Modeling (LDA)":
            params["n_topics"] = st.slider("n_topics", 2, 20, 5, key="studio_lda_topics")
            params["max_features"] = st.slider("max_features", 100, 5000, 1000, step=100, key="studio_lda_features")
    elif method == "Simple Missing Value Imputation":
        params["strategy"] = st.selectbox("strategy", ["median", "mean", "most_frequent"], key="studio_impute_strategy")
    elif method == "Isolation Forest Outlier Detection":
        params["contamination"] = st.slider("contamination", 0.01, 0.50, 0.10, step=0.01, key="studio_iso_contam")
        params["remove_outliers"] = st.checkbox("remove_outliers", value=True, key="studio_iso_remove")
    elif method == "KNN Imputation":
        params["n_neighbors"] = st.slider("n_neighbors", 1, 20, 5, key="studio_knn_neighbors")

    return params, text_column


def studio_render_intelligence_panel() -> None:
    st.subheader("Intelligent Data Preparation")

    health_report = st.session_state.dataset_health_report
    quality_score = st.session_state.data_quality_score
    auto_pipeline = st.session_state.auto_pipeline

    if not health_report or not quality_score:
        health = studio_get_dataset_health()
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

    score_value = quality_score.get("score", 0) if isinstance(quality_score, dict) else quality_score
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    c1.metric("Data Quality Score", f"{score_value} / 100")
    c2.metric("Issues Detected", len(health_report.get("issues_detected", [])))
    c3.metric("Suggested Fixes", len(health_report.get("suggested_fixes", [])))
    c4.metric("Processing Engine", health_report.get("processing_engine", "pandas"))

    with st.expander("Dataset Health Report", expanded=True):
        summary = health_report.get("dataset_summary", {})
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Rows", summary.get("rows", health_report.get("rows", 0)))
        s2.metric("Columns", summary.get("columns", health_report.get("columns", 0)))
        s3.metric("Duplicates", summary.get("duplicates", health_report.get("duplicates", 0)))
        s4.metric("Outlier Rows", summary.get("outlier_rows", health_report.get("outlier_rows", 0)))

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

        st.markdown("**Class Imbalance**")
        imbalance = health_report.get("class_imbalance", {})
        if imbalance.get("detected"):
            st.write(f"Label column: {imbalance.get('label_column', 'N/A')}")
            st.write(f"Imbalance ratio: {imbalance.get('imbalance_ratio', 'N/A')}")
            st.write(f"Imbalanced: {imbalance.get('is_imbalanced', False)}")
        else:
            st.write("No classification label detected")

    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("Auto Clean Dataset", type="primary", use_container_width=True, key="studio_auto_clean"):
            with st.spinner("Auto cleaning dataset..."):
                result = studio_auto_clean()
                if result:
                    st.session_state.preview_data = studio_get_preview()
                    st.session_state.dataset_health_report = result.get("after_report")
                    st.session_state.data_quality_score = result.get("after_score")
                    st.session_state.auto_pipeline = result.get("pipeline")
                    st.session_state.last_cleaning_result = {
                        "before_score": result.get("before_score"),
                        "after_score": result.get("after_score"),
                        "steps_applied": result.get("steps_applied", []),
                        "before_shape": result.get("before_report", {}).get("dataset_summary", {}).get("columns", 0),
                        "after_shape": result.get("after_report", {}).get("dataset_summary", {}).get("columns", 0),
                    }
                    st.success("Auto clean completed.")
                    st.rerun()

    with btn2:
        if st.button("Regenerate Auto Pipeline", use_container_width=True, key="studio_regen_pipeline"):
            result = studio_generate_auto_pipeline()
            if result:
                st.session_state.auto_pipeline = result.get("pipeline")
                st.success("Auto pipeline generated.")
                st.rerun()

    with st.expander("Automatic Pipeline", expanded=True):
        pipeline = auto_pipeline or {"confidence": 0.0, "steps": []}
        st.write(f"Confidence: {pipeline.get('confidence', 0.0)}")
        for idx, step in enumerate(pipeline.get("steps", []), start=1):
            st.write(f"{idx}. {step.get('step')} - {step.get('reason')}")

    with st.expander("Export Pipeline As Code", expanded=False):
        selected_format = st.selectbox(
            "Export format",
            ["python", "sklearn", "pyspark"],
            key="studio_pipeline_export_format",
        )
        if st.button("Generate Pipeline Code", use_container_width=True, key="studio_generate_pipeline_code"):
            export_result = studio_export_pipeline_code(selected_format)
            if export_result:
                export_payload = export_result.get("export", {})
                st.session_state.exported_pipeline_code = export_payload.get("code", "")
                st.session_state.exported_pipeline_format = export_payload.get("format", selected_format)
                history = studio_get_pipeline_history(limit=25)
                if history:
                    st.session_state.pipeline_history = history.get("history", [])

        if st.session_state.exported_pipeline_code:
            fmt = st.session_state.exported_pipeline_format
            st.code(st.session_state.exported_pipeline_code, language="python")
            st.download_button(
                f"Download {fmt} pipeline code",
                data=st.session_state.exported_pipeline_code,
                file_name=f"applydf_pipeline_{fmt}.py",
                mime="text/plain",
                use_container_width=True,
            )

    with st.expander("Pipeline Export History", expanded=False):
        if not st.session_state.pipeline_history:
            history = studio_get_pipeline_history(limit=25)
            if history:
                st.session_state.pipeline_history = history.get("history", [])

        if st.session_state.pipeline_history:
            st.dataframe(pd.DataFrame(st.session_state.pipeline_history), use_container_width=True)
        else:
            st.info("No pipeline history yet.")

    if st.session_state.last_cleaning_result:
        clean = st.session_state.last_cleaning_result
        before_score = clean.get("before_score", {})
        after_score = clean.get("after_score", {})
        before_value = before_score.get("score", 0) if isinstance(before_score, dict) else before_score
        after_value = after_score.get("score", 0) if isinstance(after_score, dict) else after_score
        st.markdown("**Latest Auto Clean Improvement**")
        c1, c2 = st.columns(2)
        c1.metric("Before", f"{before_value} / 100")
        c2.metric("After", f"{after_value} / 100", delta=round(after_value - before_value, 2))
        if clean.get("steps_applied"):
            st.write("Steps Applied: " + ", ".join(clean.get("steps_applied", [])))


def studio_render_transform_panel(preview: Dict[str, Any]) -> None:
    response = studio_api_call("/categories")
    categories = response.get("categories", {}) if response else {}
    if not categories:
        st.warning("No transformation categories returned by backend.")
        return

    st.subheader("Transformation Studio")
    
    # Display current quality score
    quality_score = st.session_state.data_quality_score
    if quality_score:
        score_value = quality_score.get("score", 0) if isinstance(quality_score, dict) else quality_score
        st.info(f"📊 Current Data Quality Score: **{score_value:.1f}/100** (updates after each transformation)")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        selected_category = st.selectbox("Category", list(categories.keys()), key="studio_category")
        selected_method = st.selectbox("Method", categories[selected_category], key="studio_method")
    with c2:
        st.markdown("<div style='height: 66px;'></div>", unsafe_allow_html=True)
        run = st.button(f"Run {selected_method}", type="primary", use_container_width=True, key="studio_run_transform")

    params, text_column = studio_render_parameter_inputs(selected_method, preview)

    with st.expander("Export Selected Transform As Code", expanded=False):
        st.caption("Export code for only the currently selected method and parameter values.")
        if st.button("Generate Code For Selected Method", use_container_width=True, key="studio_export_selected_method"):
            st.session_state.selected_transform_code = studio_build_selected_transform_code(selected_method, params, text_column)
            st.session_state.selected_transform_name = selected_method

        if st.session_state.selected_transform_code:
            export_name = st.session_state.selected_transform_name or "selected_transform"
            safe_name = export_name.lower().replace(" ", "_").replace("/", "_")
            st.code(st.session_state.selected_transform_code, language="python")
            st.download_button(
                "Download Selected Method Code",
                data=st.session_state.selected_transform_code,
                file_name=f"applydf_{safe_name}.py",
                mime="text/plain",
                use_container_width=True,
                key="studio_download_selected_method_code",
            )

    if run:
        payload = {
            "transformation_type": selected_method,
            "parameters": params,
            "text_column": text_column,
        }
        with st.spinner("Applying transformation..."):
            result = studio_api_call("/transform", method="POST", json_data=payload)
            if result and result.get("success"):
                st.session_state.transformation_history.append({"type": selected_method, "parameters": params})
                st.session_state.last_metadata = result.get("metadata")
                st.session_state.preview_data = studio_get_preview()
                
                # Recalculate quality score after transformation
                health = studio_get_dataset_health()
                if health:
                    new_quality_score = health.get("data_quality_score")
                    old_quality_score = st.session_state.data_quality_score
                    st.session_state.data_quality_score = new_quality_score
                    st.session_state.dataset_health_report = health.get("dataset_health_report")
                    
                    # Show quality score change
                    old_score_value = old_quality_score.get("score", 0) if isinstance(old_quality_score, dict) else (old_quality_score if old_quality_score else 0)
                    new_score_value = new_quality_score.get("score", 0) if isinstance(new_quality_score, dict) else new_quality_score
                    score_change = new_score_value - old_score_value
                    
                    if score_change > 0:
                        st.success(f"✅ {result.get('message', 'Transformation applied')} | Quality Score: {old_score_value:.1f} → {new_score_value:.1f} (+{score_change:.1f})")
                    elif score_change < 0:
                        st.warning(f"⚠️ {result.get('message', 'Transformation applied')} | Quality Score: {old_score_value:.1f} → {new_score_value:.1f} ({score_change:.1f})")
                    else:
                        st.success(f"{result.get('message', 'Transformation applied')} | Quality Score: {new_score_value:.1f}/100")
                else:
                    st.success(result.get("message", "Transformation applied"))
                
                st.rerun()

    if st.session_state.last_metadata:
        with st.expander("Last Result Metadata"):
            st.json(st.session_state.last_metadata)


def studio_render_export_panel() -> None:
    st.subheader("Export")
    c1, c2, c3 = st.columns(3)

    with c1:
        csv_data = studio_api_call("/download/csv", expect_json=False)
        if csv_data:
            st.download_button("Download CSV", data=csv_data, file_name="data.csv", mime="text/csv", use_container_width=True)

    with c2:
        excel_data = studio_api_call("/download/excel", expect_json=False)
        if excel_data:
            st.download_button("Download Excel", data=excel_data, file_name="data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    with c3:
        parquet_data = studio_api_call("/download/parquet", expect_json=False)
        if parquet_data:
            st.download_button("Download Parquet", data=parquet_data, file_name="data.parquet", mime="application/octet-stream", use_container_width=True)


def studio_render_history_panel() -> None:
    st.subheader("Pipeline History")
    if not st.session_state.transformation_history:
        st.info("No transformations yet")
        return

    history_df = pd.DataFrame(st.session_state.transformation_history)
    history_df.index = history_df.index + 1
    history_df.index.name = "Step"
    history_df["parameters"] = history_df["parameters"].apply(lambda x: json.dumps(x, default=str))
    st.dataframe(history_df, use_container_width=True)


def page_data_studio():
    """Full transformation studio merged into collaborative app."""
    st.markdown('<div class="hero"><h1>Data Studio</h1><p>Upload, transform, visualize, and export data</p></div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Dataset", type=["csv", "xlsx", "xls", "json", "parquet"], key="studio_uploader")
    c_upload, c_refresh, c_reset = st.columns(3)

    with c_upload:
        if uploaded_file is not None and st.button("Upload & Parse", use_container_width=True, type="primary", key="studio_upload_btn"):
            with st.spinner("Uploading and parsing dataset..."):
                files = {"file": (uploaded_file.name, uploaded_file)}
                response = studio_api_call("/upload", method="POST", files=files)
                if response and response.get("success"):
                    st.session_state.current_data = response
                    st.session_state.preview_data = studio_get_preview()
                    st.session_state.dataset_health_report = response.get("dataset_health_report")
                    st.session_state.data_quality_score = response.get("data_quality_score")
                    st.session_state.auto_pipeline = response.get("auto_pipeline")
                    st.success(f"Loaded {uploaded_file.name}")
                    st.rerun()

    with c_refresh:
        if st.button("Refresh Preview", use_container_width=True, key="studio_refresh_btn"):
            st.session_state.preview_data = studio_get_preview()
            health = studio_get_dataset_health()
            if health:
                st.session_state.dataset_health_report = health.get("dataset_health_report")
                st.session_state.data_quality_score = health.get("data_quality_score")
                st.session_state.auto_pipeline = health.get("auto_pipeline")
            st.rerun()

    with c_reset:
        if st.button("Reset Session", use_container_width=True, key="studio_reset_btn"):
            studio_api_call("/reset", method="POST")
            st.session_state.current_data = None
            st.session_state.preview_data = None
            st.session_state.transformation_history = []
            st.session_state.last_metadata = None
            st.session_state.dataset_health_report = None
            st.session_state.data_quality_score = None
            st.session_state.auto_pipeline = None
            st.rerun()

    if not st.session_state.current_data:
        st.markdown(
            '''
            <div class="onboarding-shell">
                <div class="onboarding-hero">
                    <div class="onboarding-badge">Smart Data Preparation</div>
                    <h3 class="onboarding-title">Welcome to ApplyDF Nexus</h3>
                    <p class="onboarding-text">
                        Transform raw files into ML-ready datasets with guided quality checks, automated cleaning,
                        and reproducible transformation pipelines.
                    </p>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        f1, f2, f3 = st.columns(3)
        with f1:
            st.markdown(
                '''
                <div class="onboarding-feature">
                    <h4 class="onboarding-feature-title">Diagnose Data Quality</h4>
                    <p class="onboarding-feature-text">Detect missing values, duplicates, outliers, and type inconsistencies before training.</p>
                </div>
                ''',
                unsafe_allow_html=True,
            )
        with f2:
            st.markdown(
                '''
                <div class="onboarding-feature">
                    <h4 class="onboarding-feature-title">Apply Smart Transformations</h4>
                    <p class="onboarding-feature-text">Run auto-clean workflows and targeted transforms while tracking quality score impact.</p>
                </div>
                ''',
                unsafe_allow_html=True,
            )
        with f3:
            st.markdown(
                '''
                <div class="onboarding-feature">
                    <h4 class="onboarding-feature-title">Export and Collaborate</h4>
                    <p class="onboarding-feature-text">Export cleaned datasets, publish reports, and share reusable pipelines with your team.</p>
                </div>
                ''',
                unsafe_allow_html=True,
            )

        st.markdown('<h4 class="onboarding-section-title">How it works</h4>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                '''
                <div class="process-card">
                    <span class="process-step">1</span>
                    <h5 class="process-title">Upload</h5>
                    <p class="process-text">Add CSV, Excel, JSON, or Parquet using the uploader above.</p>
                </div>
                ''',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                '''
                <div class="process-card">
                    <span class="process-step">2</span>
                    <h5 class="process-title">Improve</h5>
                    <p class="process-text">Review quality insights and apply auto-clean or manual transformations.</p>
                </div>
                ''',
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                '''
                <div class="process-card">
                    <span class="process-step">3</span>
                    <h5 class="process-title">Deliver</h5>
                    <p class="process-text">Download clean outputs or publish them to workspace and reports.</p>
                </div>
                ''',
                unsafe_allow_html=True,
            )

        st.markdown("### Quick navigation")
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("Go to Data Sources", use_container_width=True, key="landing_go_sources"):
                st.session_state.current_page = "Data Sources"
                st.rerun()
        with a2:
            if st.button("Open Public Datasets", use_container_width=True, key="landing_go_public"):
                st.session_state.current_page = "Public Datasets"
                st.rerun()
        with a3:
            if st.button("View Workspace", use_container_width=True, key="landing_go_workspace"):
                st.session_state.current_page = "Workspace"
                st.rerun()

        return

    preview = st.session_state.preview_data or studio_get_preview()
    if not preview:
        st.error("Could not load dataset preview")
        return

    rows = preview.get("shape", [0, 0])[0]
    cols = preview.get("shape", [0, 0])[1]
    missing_total = int(sum(preview.get("missing_values", {}).values()))
    quality_score = st.session_state.data_quality_score
    score_value = quality_score.get("score", 0) if isinstance(quality_score, dict) else (quality_score or 0)

    st.markdown(
        f'''
        <div class="studio-status-strip">
            <div class="studio-status-card">
                <p class="studio-status-label">ML Readiness</p>
                <p class="studio-status-value">Quality Score: {score_value}/100</p>
            </div>
            <div class="studio-status-card">
                <p class="studio-status-label">Dataset Health</p>
                <p class="studio-status-value">{rows:,} rows · {cols:,} columns · {missing_total:,} missing</p>
            </div>
            <div class="studio-status-card">
                <p class="studio-status-label">Pipeline Safety</p>
                <p class="studio-status-value">Target-safe transforms and reproducible history enabled</p>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    st.markdown('<h3 class="studio-section-heading">Dataset Overview</h3>', unsafe_allow_html=True)
    st.markdown('<p class="studio-section-subtext">Inspect schema, profile missingness, and validate transformations before model training.</p>', unsafe_allow_html=True)
    studio_render_preview(preview)
    st.divider()
    studio_render_intelligence_panel()
    st.divider()
    studio_render_transform_panel(preview)
    st.divider()
    studio_render_export_panel()
    st.divider()
    studio_render_history_panel()


# ==================== MAIN APP ====================

def main():
    init_state()
    inject_styles()
    inject_screen_mode_override()
    render_sidebar()
    
    # Route to appropriate page
    page = st.session_state.current_page
    
    if page == "Data Studio":
        page_data_studio()
    elif page == "Data Sources":
        page_data_sources()
    elif page == "Workspace":
        page_workspace()
    elif page == "Public Datasets":
        page_public_datasets()
    elif page == "Reports":
        page_reports()


if __name__ == "__main__":
    main()
