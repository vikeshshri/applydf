"""
Configuration file for applydf application.
Centralized settings for backend and frontend.
"""

import os
from typing import Dict, List

# ==================== APPLICATION CONFIG ====================

APP_NAME = "applydf"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Interactive Data Transformation & Cleaning"

# ==================== BACKEND CONFIG ====================

# FastAPI Settings
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
BACKEND_RELOAD = os.getenv("BACKEND_RELOAD", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API Settings
API_TITLE = "applydf API"
API_DESCRIPTION = "Interactive Data Transformation and Cleaning API"
CORS_ORIGINS = [
    "http://localhost:8501",  # Streamlit default
    "http://localhost:3000",  # React default
    "http://127.0.0.1:8501",
    "http://127.0.0.1:3000",
    "*"  # Allow all in development
]

# ==================== FRONTEND CONFIG ====================

# Streamlit Settings
STREAMLIT_PORT = 8501
STREAMLIT_LOGGER_LEVEL = "info"
STREAMLIT_CLIENT_SHOW_ERROR_DETAILS = True

# API Endpoint
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# ==================== FILE UPLOAD CONFIG ====================

UPLOAD_FOLDER = "temp_files"
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json', '.parquet'}
MAX_FILE_SIZE_MB = 100  # Maximum file size in MB

# ==================== DATA CONFIG ====================

# DataFrame Preview
PREVIEW_ROWS = 5
DATAFRAME_DISPLAY_MAX_ROWS = 100
DATAFRAME_DISPLAY_MAX_COLUMNS = 50

# ==================== MODEL CONFIG ====================

# Transformer Models
TRANSFORMER_MODELS = [
    'sentence-transformers/all-MiniLM-L6-v2',      # Lightweight, balanced
    'sentence-transformers/all-mpnet-base-v2',     # Higher quality
    'sentence-transformers/paraphrase-MiniLM-L6-v2'  # Paraphrase task
]
DEFAULT_TRANSFORMER_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'

# ==================== TRANSFORMATION DEFAULTS ====================

TRANSFORMATION_DEFAULTS = {
    'PCA': {'n_components': 2},
    'SVD': {'n_components': 2},
    't-SNE': {
        'n_components': 2,
        'perplexity': 30,
        'learning_rate': 200,
        'n_iter': 1000
    },
    'UMAP': {
        'n_components': 2,
        'n_neighbors': 15,
        'min_dist': 0.1
    },
    'Min-Max Normalization': {'feature_range': (0, 1)},
    'TF-IDF': {'max_features': 100},
    'N-gram Analysis': {'ngram_range': (1, 2), 'max_features': 100},
    'Word2Vec': {'vector_size': 100, 'window': 5, 'min_count': 2},
    'Binning': {'n_bins': 5, 'strategy': 'quantile'},
    'KNN Imputation': {'n_neighbors': 5},
    'Isolation Forest': {'contamination': 0.1, 'remove_outliers': True}
}

# ==================== VISUALIZATION CONFIG ====================

# Plotly Theme
PLOTLY_TEMPLATE = "plotly_white"

# Color Schemes
COLOR_PALETTE = [
    '#1f77b4',  # Blue
    '#ff7f0e',  # Orange
    '#2ca02c',  # Green
    '#d62728',  # Red
    '#9467bd',  # Purple
    '#8c564b',  # Brown
    '#e377c2',  # Pink
    '#7f7f7f',  # Gray
    '#bcbd22',  # Yellow-green
    '#17becf'   # Cyan
]

# ==================== CACHE CONFIG ====================

# Model Caching
CACHE_MODELS = True
CACHE_DIR = os.path.expanduser("~/.cache/applydf")

# ==================== ERROR HANDLING ====================

# Error Messages
ERROR_MESSAGES = {
    'empty_data': "Data is empty or None",
    'missing_columns': "Missing required columns",
    'no_numeric_cols': "No numeric columns found",
    'no_categorical_cols': "No categorical columns found",
    'no_text_cols': "No text columns found",
    'invalid_format': "Unsupported file format",
    'connection_error': "Could not connect to backend"
}

# ==================== LOGGING CONFIG ====================

LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGING_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ==================== FEATURE FLAGS ====================

FEATURES = {
    'enable_advanced_stats': True,
    'enable_pipeline_save': True,
    'enable_batch_processing': False,
    'enable_gpu_acceleration': False,
    'enable_real_time_preview': True,
}

# ==================== PERFORMANCE CONFIG ====================

# Processing
MAX_SAMPLES_FOR_TSNE = 5000  # Limit for t-SNE due to O(n²) complexity
MAX_VOCAB_SIZE_FOR_TEXT = 10000
BATCH_SIZE = 32

# Timeout (seconds)
API_TIMEOUT = 300
TRANSFORMATION_TIMEOUT = 600

# ==================== UTILITY FUNCTIONS ====================

def get_config() -> Dict:
    """Get all configuration as dictionary."""
    return {
        'app': {
            'name': APP_NAME,
            'version': APP_VERSION,
            'description': APP_DESCRIPTION
        },
        'backend': {
            'host': BACKEND_HOST,
            'port': BACKEND_PORT,
            'reload': BACKEND_RELOAD
        },
        'frontend': {
            'api_url': API_BASE_URL
        },
        'upload': {
            'max_size_mb': MAX_FILE_SIZE_MB,
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        },
        'features': FEATURES,
        'models': {
            'transformers': TRANSFORMER_MODELS,
            'default': DEFAULT_TRANSFORMER_MODEL
        }
    }


def get_transformation_categories() -> Dict[str, List[str]]:
    """Get transformation categories and methods."""
    return {
        'Dimensionality Reduction & Structure': [
            'Covariance Matrix',
            'Eigenvalue/Eigenvector',
            'PCA',
            'SVD',
            't-SNE',
            'UMAP'
        ],
        'Feature Engineering & Scaling': [
            'Standardization (Z-score)',
            'Min-Max Normalization',
            'Log/Power Transforms',
            'One-Hot Encoding',
            'Ordinal Encoding',
            'Binning/Discretization'
        ],
        'Text-Specific Transformation': [
            'TF-IDF',
            'N-gram Analysis',
            'Word2Vec',
            'Transformer Embeddings'
        ],
        'Data Cleaning & Quality': [
            'KNN Imputation',
            'Isolation Forest Outlier Detection',
            'Deduplication',
            'Text Normalization'
        ]
    }


if __name__ == "__main__":
    # Display configuration
    import json
    config = get_config()
    print(json.dumps(config, indent=2))
