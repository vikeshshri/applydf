"""
FastAPI backend for applydf application.
Handles data transformations and API endpoints.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import io
import logging
import json
import os
from datetime import datetime
import traceback

# Import transformation classes
from transformations import (
    CovarianceMatrixTransform,
    EigenvalueEigenvectorTransform,
    PCATransform,
    SVDTransform,
    TSNETransform,
    UMAPTransform,
    StandardizationTransform,
    MinMaxNormalizationTransform,
    RobustScalingTransform,
    QuantileTransform,
    LogPowerTransform,
    OneHotEncodingTransform,
    OrdinalEncodingTransform,
    BinningTransform,
    KMeansClusteringTransform,
    CorrelationFeatureFilterTransform,
    VarianceThresholdTransform,
    TFIDFTransform,
    NGramTransform,
    Word2VecTransform,
    TransformerEmbeddingTransform,
    SentimentAnalysisTransform,
    TopicModelingTransform,
    SimpleMissingValueImputationTransform,
    KNNImputationTransform,
    IsolationForestOutlierTransform,
    DeduplicationTransform,
    TextNormalizationTransform,
    IQROutlierTreatmentTransform,
    WinsorizationTransform,
    get_transformation_categories
)
from auto_cleaner import auto_clean_dataset
from data_quality_score import calculate_data_quality_score
from dataset_analyzer import analyze_dataset
from pipeline_generator import export_pipeline_as_code, generate_auto_pipeline
from pipeline_history import PipelineHistoryManager
from visualization_engine import build_pipeline_visualization, build_quality_snapshot

# Import new collaborative features
from data_source_connector import DataSourceConnector
from report_generator import ReportGenerator
from dataset_registry import DatasetRegistry
from sharing_manager import SharingManager
from user_manager import UserManager
from database_models import (
    db,
    init_database,
    ResourceType,
    AccessLevel,
    VisibilityType,
    Dataset,
    Report,
    Pipeline,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="applydf API",
    description="Interactive Data Transformation and Cleaning API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
try:
    init_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.warning(f"Database initialization warning: {str(e)}")

# ==================== DATA MODELS ====================

class TransformationRequest(BaseModel):
    """Request model for transformation operations."""
    transformation_type: str
    parameters: Dict[str, Any] = {}
    text_column: Optional[str] = None


class DataPreview(BaseModel):
    """Response model for data preview."""
    shape: tuple
    columns: List[str]
    data_types: Dict[str, str]
    missing_values: Dict[str, int]
    statistics: Dict[str, Dict[str, float]]
    preview_data: List[Dict[str, Any]]


class TransformationResponse(BaseModel):
    """Response model for transformation results."""
    success: bool
    message: str
    data: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    shape: Optional[tuple] = None


# ==================== NEW COLLABORATIVE MODELS ====================

class DataSourceRequest(BaseModel):
    """Request model for connecting to data sources."""
    source_type: str  # 'csv_url', 'postgres', 'mysql', 's3', 'google_sheets'
    config: Dict[str, Any]  # Connection configuration


class UserLoginRequest(BaseModel):
    """Request model for user login."""
    username: str
    password: str


class UserRegisterRequest(BaseModel):
    """Request model for user registration."""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class ShareRequest(BaseModel):
    """Request model for sharing resources."""
    resource_type: str  # 'dataset', 'report', 'pipeline'
    resource_id: int | str
    access_level: str = 'viewer'  # 'viewer', 'editor', 'owner'
    shared_with_user_id: Optional[int] = None
    is_public_link: bool = False
    expires_in_days: Optional[int] = None


class DatasetRegisterRequest(BaseModel):
    """Request model for registering datasets."""
    dataset_name: str
    description: Optional[str] = None
    visibility: str = 'private'  # 'private', 'public', 'shared'


class ReportGenerateRequest(BaseModel):
    """Request model for report generation."""
    report_name: str
    description: Optional[str] = None


# ==================== GLOBAL VARIABLES ====================

current_dataframe = None
original_dataframe = None
transformation_history = []
saved_pipelines = {}
pipeline_history_manager = PipelineHistoryManager()

# New collaborative features globals
current_user = None  # Demo user for prototyping (auth not fully implemented)
last_registered_dataset_id = None
last_report_id = None
current_source_type = "upload"
current_source_config = {}


# ==================== HELPER FUNCTIONS ====================

def parse_uploaded_file(file: UploadFile) -> pd.DataFrame:
    """
    Parse uploaded file and return DataFrame.
    Supports CSV, Excel, JSON, and Parquet formats.
    """
    file_extension = file.filename.split('.')[-1].lower()
    
    try:
        # Read file content into memory first
        content = file.file.read()
        
        if file_extension == 'csv':
            df = pd.read_csv(io.BytesIO(content))
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(io.BytesIO(content))
        elif file_extension == 'json':
            df = pd.read_json(io.BytesIO(content))
        elif file_extension == 'parquet':
            df = pd.read_parquet(io.BytesIO(content))
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        if df.empty:
            raise ValueError("Uploaded file is empty")
        
        return df
    
    except Exception as e:
        raise ValueError(f"Error parsing file: {str(e)}")


def get_data_statistics(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Generate statistics for numeric columns."""
    numeric_df = df.select_dtypes(include=[np.number])
    stats = {}
    
    for col in numeric_df.columns:
        stats[col] = {
            'mean': float(numeric_df[col].mean()),
            'median': float(numeric_df[col].median()),
            'std': float(numeric_df[col].std()),
            'min': float(numeric_df[col].min()),
            'max': float(numeric_df[col].max()),
            'q25': float(numeric_df[col].quantile(0.25)),
            'q75': float(numeric_df[col].quantile(0.75))
        }
    
    return stats


def dataframe_to_json(df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
    """Convert DataFrame to JSON-serializable format."""
    return df.head(limit).astype(str).to_dict('records')


def save_dataframe_to_temp(df: pd.DataFrame, format: str = 'csv') -> str:
    """Save DataFrame to temporary file and return path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = os.path.join(os.getcwd(), 'temp_files')
    os.makedirs(temp_dir, exist_ok=True)
    
    if format == 'csv':
        filepath = os.path.join(temp_dir, f"transformed_{timestamp}.csv")
        df.to_csv(filepath, index=False)
    elif format == 'excel':
        filepath = os.path.join(temp_dir, f"transformed_{timestamp}.xlsx")
        df.to_excel(filepath, index=False)
    elif format == 'parquet':
        filepath = os.path.join(temp_dir, f"transformed_{timestamp}.parquet")
        df.to_parquet(filepath, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return filepath


def sanitize_source_config(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Remove secrets from source config before storing metadata."""
    if not config:
        return {}

    blocked = {
        "password",
        "aws_secret_access_key",
        "aws_access_key_id",
        "credentials_json",
        "api_key",
        "token",
        "secret",
    }
    sanitized: Dict[str, Any] = {}
    for key, value in config.items():
        key_lower = str(key).lower()
        if any(blocked_key in key_lower for blocked_key in blocked):
            continue
        sanitized[key] = value
    return sanitized


def _resolve_internal_resource_id(resource_type: ResourceType, resource_id: int | str) -> int:
    """Resolve public resource IDs (dataset_id/report_id/pipeline_id) to internal numeric IDs."""
    session = db.get_session()
    try:
        if resource_type == ResourceType.DATASET:
            if isinstance(resource_id, int) or str(resource_id).isdigit():
                dataset = session.query(Dataset).filter(Dataset.id == int(resource_id)).first()
                if dataset:
                    return int(dataset.id)
            dataset = session.query(Dataset).filter(Dataset.dataset_id == str(resource_id)).first()
            if dataset:
                return int(dataset.id)

        elif resource_type == ResourceType.REPORT:
            if isinstance(resource_id, int) or str(resource_id).isdigit():
                report = session.query(Report).filter(Report.id == int(resource_id)).first()
                if report:
                    return int(report.id)
            report = session.query(Report).filter(Report.report_id == str(resource_id)).first()
            if report:
                return int(report.id)

        elif resource_type == ResourceType.PIPELINE:
            if isinstance(resource_id, int) or str(resource_id).isdigit():
                pipeline = session.query(Pipeline).filter(Pipeline.id == int(resource_id)).first()
                if pipeline:
                    return int(pipeline.id)
            pipeline = session.query(Pipeline).filter(Pipeline.pipeline_id == str(resource_id)).first()
            if pipeline:
                return int(pipeline.id)

        raise HTTPException(status_code=404, detail="Resource not found")
    finally:
        session.close()


def _serialize_report(report: Report) -> Dict[str, Any]:
    before = report.before_stats or {}
    after = report.after_stats or {}

    before_after = None
    if before or after:
        before_after = {
            "shape": {
                "before": before.get("shape", {}),
                "after": after.get("shape", {}),
            },
            "missing_values": {
                "before": before.get("missing_values", 0),
                "after": after.get("missing_values", 0),
            },
            "duplicates": {
                "before": before.get("duplicates", 0),
                "after": after.get("duplicates", 0),
            },
        }

    return {
        "report_id": report.report_id,
        "report_name": report.report_name,
        "description": report.description,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "dataset_summary": report.dataset_summary or {},
        "data_quality_score": report.data_quality_score,
        "pipeline_steps": report.pipeline_steps or [],
        "visualizations": report.visualizations or [],
        "before_after_comparison": before_after,
        "cleaned_dataset_path": report.cleaned_dataset_path,
        "visibility": report.visibility.value if report.visibility else VisibilityType.PRIVATE.value,
    }


# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "applydf API",
        "version": "2.0.0",
        "description": "Collaborative Data Transformation & Analysis Platform",
        "endpoints": {
            "core": {
                "upload": "POST /upload - Upload and parse data file",
                "preview": "GET /preview - Get data preview",
                "dataset_health": "GET /dataset-health - Dataset diagnosis and quality score",
                "auto_pipeline": "POST /auto-pipeline - Generate automatic preprocessing pipeline",
                "auto_clean": "POST /auto-clean - Automatically clean current dataset",
                "export_pipeline_code": "GET /pipeline/export-code?format=python - Export pipeline code",
                "pipeline_history": "GET /pipeline-history - Auto pipeline generation/export history",
                "pipeline_visualization": "GET /pipeline-visualization - Graph payload for pipeline display",
                "categories": "GET /categories - Get transformation categories",
                "transform": "POST /transform - Apply transformation",
                "history": "GET /history - Get transformation history",
                "download": "GET /download/{format} - Download transformed data",
                "save_pipeline": "POST /save-pipeline - Save transformation pipeline",
                "load_pipeline": "GET /load-pipeline/{name} - Load saved pipeline"
            },
            "data_sources": {
                "connect_source": "POST /connect-source - Connect to external data sources (CSV URL, DB, S3, Sheets)"
            },
            "auth": {
                "register": "POST /auth/register - Register new user",
                "login": "POST /auth/login - User login",
                "demo_login": "GET /auth/demo-login - Login as demo user",
                "current_user": "GET /auth/current-user - Get current user info"
            },
            "datasets": {
                "register": "POST /datasets/register - Register current dataset",
                "public": "GET /datasets/public - List public datasets",
                "get": "GET /datasets/{id} - Get dataset info",
                "load": "GET /datasets/{id}/load - Load dataset",
                "clone_pipeline": "POST /datasets/{id}/clone-pipeline - Clone transformation pipeline",
                "search": "GET /datasets/search?q=query - Search datasets",
                "user_datasets": "GET /workspace/datasets - Get user's datasets"
            },
            "reports": {
                "generate": "POST /reports/generate - Generate shareable report",
                "get": "GET /reports/{id} - Get report by ID"
            },
            "sharing": {
                "create": "POST /share/create - Create share link",
                "access": "GET /share/{id} - Access shared resource",
                "shared_with_me": "GET /workspace/shared - Resources shared with user"
            }
        }
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and parse a data file.
    
    Supported formats: CSV, Excel, JSON, Parquet
    """
    global current_dataframe, original_dataframe, transformation_history
    
    try:
        current_dataframe = parse_uploaded_file(file)
        original_dataframe = current_dataframe.copy(deep=True)
        transformation_history = []

        health_report = analyze_dataset(current_dataframe)
        quality_score = calculate_data_quality_score(current_dataframe.shape, health_report)
        auto_pipeline = generate_auto_pipeline(health_report, current_dataframe.shape)
        pipeline_history_manager.add_generated(auto_pipeline, source="upload")
        
        logger.info(f"File uploaded: {file.filename}, shape: {current_dataframe.shape}")
        
        return {
            "success": True,
            "message": f"File uploaded successfully",
            "filename": file.filename,
            "shape": current_dataframe.shape,
            "dataset_report": health_report,
            "dataset_health_report": health_report,
            "data_quality_score": quality_score,
            "auto_pipeline": auto_pipeline,
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/preview")
async def get_preview() -> DataPreview:
    """
    Get preview of current DataFrame.
    Returns: shape, columns, data types, missing values, statistics, and first 5 rows.
    """
    global current_dataframe
    
    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No data uploaded. Please upload a file first.")
    
    try:
        preview_data = {
            "shape": current_dataframe.shape,
            "columns": current_dataframe.columns.tolist(),
            "data_types": current_dataframe.dtypes.astype(str).to_dict(),
            "missing_values": current_dataframe.isnull().sum().to_dict(),
            "statistics": get_data_statistics(current_dataframe),
            "preview_data": dataframe_to_json(current_dataframe, limit=5)
        }
        
        return preview_data
    
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dataset-health")
async def get_dataset_health():
    """Return dataset diagnosis report and quality score for current dataframe."""
    global current_dataframe

    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No data uploaded. Please upload a file first.")

    try:
        health_report = analyze_dataset(current_dataframe)
        quality_score = calculate_data_quality_score(current_dataframe.shape, health_report)
        auto_pipeline = generate_auto_pipeline(health_report, current_dataframe.shape)
        snapshot = build_quality_snapshot(health_report, quality_score)

        return {
            "success": True,
            "dataset_report": health_report,
            "dataset_health_report": health_report,
            "data_quality_score": quality_score,
            "auto_pipeline": auto_pipeline,
            "quality_snapshot": snapshot,
        }
    except Exception as e:
        logger.error(f"Error generating dataset health report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auto-pipeline")
async def generate_automatic_pipeline():
    """Generate an automatic preprocessing pipeline with reasons and confidence."""
    global current_dataframe

    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No data uploaded. Please upload a file first.")

    try:
        health_report = analyze_dataset(current_dataframe)
        auto_pipeline = generate_auto_pipeline(health_report, current_dataframe.shape)
        pipeline_history_manager.add_generated(auto_pipeline, source="manual")
        return {
            "success": True,
            "pipeline": auto_pipeline,
        }
    except Exception as e:
        logger.error(f"Error generating automatic pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auto-clean")
async def auto_clean_current_dataset():
    """Automatically clean the current dataset and return quality improvement."""
    global current_dataframe, transformation_history

    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No data uploaded. Please upload a file first.")

    try:
        cleaned_result = auto_clean_dataset(current_dataframe)
        current_dataframe = cleaned_result["cleaned_df"]

        transformation_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "Auto Clean Dataset",
            "parameters": {
                "steps_applied": cleaned_result["steps_applied"],
                "pipeline_confidence": cleaned_result["pipeline"].get("confidence", 0.0),
            },
            "result_shape": current_dataframe.shape,
        })

        return {
            "success": True,
            "message": "Auto Clean Dataset completed",
            "shape": current_dataframe.shape,
            "preview_data": dataframe_to_json(current_dataframe, limit=5),
            "steps_applied": cleaned_result["steps_applied"],
            "before_score": cleaned_result["before_score"],
            "after_score": cleaned_result["after_score"],
            "quality_improvement": round(
                float(cleaned_result["after_score"].get("score", 0.0))
                - float(cleaned_result["before_score"].get("score", 0.0)),
                2,
            ),
            "before_report": cleaned_result["before_report"],
            "after_report": cleaned_result["after_report"],
            "dataset_health_report": cleaned_result["after_report"],
            "data_quality_score": cleaned_result["after_score"],
            "pipeline": cleaned_result["pipeline"],
            "processing_engine": cleaned_result.get("processing_engine", "pandas"),
        }
    except Exception as e:
        logger.error(f"Error during auto clean: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/export-code")
async def export_pipeline_code(format: str = Query(default="python")):
    """Export auto-generated pipeline as Python, sklearn, or PySpark code."""
    global current_dataframe

    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No data uploaded. Please upload a file first.")

    try:
        report = analyze_dataset(current_dataframe)
        pipeline = generate_auto_pipeline(report, current_dataframe.shape)
        exported = export_pipeline_as_code(pipeline, export_format=format)
        pipeline_history_manager.add_export(format, pipeline)
        return {
            "success": True,
            "export": exported,
        }
    except Exception as e:
        logger.error(f"Error exporting pipeline code: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/pipeline-history")
async def get_pipeline_history(limit: int = Query(default=50, ge=1, le=500)):
    """Return recent generated/exported pipeline events."""
    return {
        "success": True,
        "history": pipeline_history_manager.list_history(limit=limit),
    }


@app.get("/pipeline-visualization")
async def get_pipeline_visualization():
    """Return nodes/edges payload for automatic pipeline visualization."""
    global current_dataframe

    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No data uploaded. Please upload a file first.")

    report = analyze_dataset(current_dataframe)
    pipeline = generate_auto_pipeline(report, current_dataframe.shape)
    return {
        "success": True,
        "visualization": build_pipeline_visualization(pipeline),
    }


@app.get("/preview/original")
async def get_original_preview() -> DataPreview:
    """Get preview of original uploaded DataFrame (before transformations)."""
    global original_dataframe

    if original_dataframe is None:
        raise HTTPException(status_code=400, detail="No original data available. Please upload a file first.")

    try:
        preview_data = {
            "shape": original_dataframe.shape,
            "columns": original_dataframe.columns.tolist(),
            "data_types": original_dataframe.dtypes.astype(str).to_dict(),
            "missing_values": original_dataframe.isnull().sum().to_dict(),
            "statistics": get_data_statistics(original_dataframe),
            "preview_data": dataframe_to_json(original_dataframe, limit=5)
        }

        return preview_data

    except Exception as e:
        logger.error(f"Error generating original preview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visual-compare")
async def get_visual_compare_data(limit: int = Query(default=1000, ge=50, le=5000)):
    """Return before/after records for side-by-side visualization."""
    global current_dataframe, original_dataframe

    if current_dataframe is None or original_dataframe is None:
        raise HTTPException(status_code=400, detail="No data uploaded. Please upload a file first.")

    try:
        before_df = original_dataframe.head(limit).replace([np.inf, -np.inf], np.nan)
        after_df = current_dataframe.head(limit).replace([np.inf, -np.inf], np.nan)

        before_numeric_cols = before_df.select_dtypes(include=[np.number]).columns.tolist()
        after_numeric_cols = after_df.select_dtypes(include=[np.number]).columns.tolist()
        common_numeric_cols = [col for col in before_numeric_cols if col in after_numeric_cols]

        before_records = json.loads(before_df.to_json(orient="records", date_format="iso"))
        after_records = json.loads(after_df.to_json(orient="records", date_format="iso"))

        return {
            "success": True,
            "limit": limit,
            "before_shape": before_df.shape,
            "after_shape": after_df.shape,
            "before_numeric_columns": before_numeric_cols,
            "after_numeric_columns": after_numeric_cols,
            "common_numeric_columns": common_numeric_cols,
            "before_data": before_records,
            "after_data": after_records,
        }

    except Exception as e:
        logger.error(f"Error generating visual compare data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories")
async def get_categories():
    """Get available transformation categories and methods."""
    try:
        categories = get_transformation_categories()
        return {
            "success": True,
            "categories": categories
        }
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transform")
async def apply_transformation(request: TransformationRequest):
    """
    Apply a transformation to the current DataFrame.
    
    Transformation types:
    - Covariance Matrix
    - Eigenvalue/Eigenvector
    - PCA
    - SVD
    - t-SNE
    - UMAP
    - Standardization (Z-score)
    - Min-Max Normalization
    - Log/Power Transforms
    - One-Hot Encoding
    - Ordinal Encoding
    - Binning/Discretization
    - TF-IDF
    - N-gram Analysis
    - Word2Vec
    - Transformer Embeddings
    - KNN Imputation
    - Isolation Forest Outlier Detection
    - Deduplication
    - Text Normalization
    """
    global current_dataframe, transformation_history
    
    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No data uploaded. Please upload a file first.")
    
    try:
        result = None
        metadata = {}
        
        transformation_type = request.transformation_type
        params = request.parameters
        
        # Dimensionality Reduction
        if transformation_type == 'Covariance Matrix':
            transformer = CovarianceMatrixTransform()
            result = transformer.transform(current_dataframe)
            return {
                "success": True,
                "message": "Covariance matrix calculated successfully",
                "data": result,
                "metadata": result,
                "shape": None
            }
        
        elif transformation_type == 'Eigenvalue/Eigenvector':
            transformer = EigenvalueEigenvectorTransform()
            result = transformer.transform(current_dataframe)
            return {
                "success": True,
                "message": "Eigenvalues and eigenvectors extracted successfully",
                "data": result,
                "metadata": result,
                "shape": None
            }
        
        elif transformation_type == 'PCA':
            n_components = params.get('n_components', 2)
            transformer = PCATransform()
            transformed_df, metadata = transformer.transform(current_dataframe, n_components=n_components)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'SVD':
            n_components = params.get('n_components', 2)
            transformer = SVDTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, n_components=n_components)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 't-SNE':
            n_components = params.get('n_components', 2)
            perplexity = params.get('perplexity', 30)
            learning_rate = params.get('learning_rate', 200)
            n_iter = params.get('n_iter', 1000)
            transformer = TSNETransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                n_components=n_components,
                perplexity=perplexity,
                learning_rate=learning_rate,
                n_iter=n_iter
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'UMAP':
            n_components = params.get('n_components', 2)
            n_neighbors = params.get('n_neighbors', 15)
            min_dist = params.get('min_dist', 0.1)
            transformer = UMAPTransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                n_components=n_components,
                n_neighbors=n_neighbors,
                min_dist=min_dist
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        # Feature Engineering & Scaling
        elif transformation_type == 'Standardization (Z-score)':
            transformer = StandardizationTransform()
            transformed_df, metadata = transformer.transform(current_dataframe)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'Min-Max Normalization':
            feature_range = params.get('feature_range', (0, 1))
            transformer = MinMaxNormalizationTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, feature_range=tuple(feature_range))
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)

        elif transformation_type == 'Robust Scaling':
            transformer = RobustScalingTransform()
            transformed_df, metadata = transformer.transform(current_dataframe)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)

        elif transformation_type == 'Quantile Transformation':
            n_quantiles = params.get('n_quantiles', 100)
            output_distribution = params.get('output_distribution', 'uniform')
            transformer = QuantileTransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                n_quantiles=n_quantiles,
                output_distribution=output_distribution,
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'Log/Power Transforms':
            method = params.get('method', 'log')
            power = params.get('power', 2.0)
            transformer = LogPowerTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, method=method, power=power)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'One-Hot Encoding':
            columns = params.get('columns', None)
            transformer = OneHotEncodingTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, columns=columns)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'Ordinal Encoding':
            columns = params.get('columns', None)
            transformer = OrdinalEncodingTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, columns=columns)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'Binning/Discretization':
            n_bins = params.get('n_bins', 5)
            strategy = params.get('strategy', 'quantile')
            transformer = BinningTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, n_bins=n_bins, strategy=strategy)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)

        elif transformation_type == 'K-Means Clustering':
            n_clusters = params.get('n_clusters', 3)
            max_iter = params.get('max_iter', 300)
            transformer = KMeansClusteringTransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                n_clusters=n_clusters,
                max_iter=max_iter,
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)

        elif transformation_type == 'Correlation Feature Filter':
            threshold = params.get('threshold', 0.95)
            transformer = CorrelationFeatureFilterTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, threshold=threshold)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)

        elif transformation_type == 'Variance Threshold Feature Selection':
            threshold = params.get('threshold', 0.0)
            transformer = VarianceThresholdTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, threshold=threshold)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        # Text-Specific Transformations
        elif transformation_type == 'TF-IDF':
            text_column = request.text_column or params.get('text_column')
            max_features = params.get('max_features', 100)
            transformer = TFIDFTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, text_column=text_column, max_features=max_features)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'N-gram Analysis':
            text_column = request.text_column or params.get('text_column')
            ngram_range = params.get('ngram_range', (1, 2))
            max_features = params.get('max_features', 100)
            transformer = NGramTransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                text_column=text_column,
                ngram_range=tuple(ngram_range),
                max_features=max_features
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'Word2Vec':
            text_column = request.text_column or params.get('text_column')
            vector_size = params.get('vector_size', 100)
            window = params.get('window', 5)
            min_count = params.get('min_count', 2)
            transformer = Word2VecTransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                text_column=text_column,
                vector_size=vector_size,
                window=window,
                min_count=min_count
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'Transformer Embeddings':
            text_column = request.text_column or params.get('text_column')
            model_name = params.get('model_name', 'sentence-transformers/all-MiniLM-L6-v2')
            max_length = params.get('max_length', 128)
            transformer = TransformerEmbeddingTransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                text_column=text_column,
                model_name=model_name,
                max_length=max_length
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)

        elif transformation_type == 'Sentiment Analysis (VADER)':
            text_column = request.text_column or params.get('text_column')
            transformer = SentimentAnalysisTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, text_column=text_column)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)

        elif transformation_type == 'Topic Modeling (LDA)':
            text_column = request.text_column or params.get('text_column')
            n_topics = params.get('n_topics', 5)
            max_features = params.get('max_features', 1000)
            transformer = TopicModelingTransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                text_column=text_column,
                n_topics=n_topics,
                max_features=max_features,
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        # Data Cleaning & Quality
        elif transformation_type == 'Simple Missing Value Imputation':
            strategy = params.get('strategy', 'median')
            transformer = SimpleMissingValueImputationTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, strategy=strategy)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)

        elif transformation_type == 'KNN Imputation':
            n_neighbors = params.get('n_neighbors', 5)
            transformer = KNNImputationTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, n_neighbors=n_neighbors)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'Isolation Forest Outlier Detection':
            contamination = params.get('contamination', 0.1)
            remove_outliers = params.get('remove_outliers', True)
            transformer = IsolationForestOutlierTransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                contamination=contamination,
                remove_outliers=remove_outliers
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'Deduplication':
            subset = params.get('subset', None)
            keep = params.get('keep', 'first')
            transformer = DeduplicationTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, subset=subset, keep=keep)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        elif transformation_type == 'Text Normalization':
            text_column = request.text_column or params.get('text_column')
            lowercase = params.get('lowercase', True)
            remove_special = params.get('remove_special', True)
            lemmatize = params.get('lemmatize', True)
            transformer = TextNormalizationTransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                text_column=text_column,
                lowercase=lowercase,
                remove_special=remove_special,
                lemmatize=lemmatize
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)

        elif transformation_type == 'IQR Outlier Treatment':
            factor = params.get('factor', 1.5)
            action = params.get('action', 'cap')
            transformer = IQROutlierTreatmentTransform()
            transformed_df, metadata = transformer.transform(current_dataframe, factor=factor, action=action)
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)

        elif transformation_type == 'Winsorization':
            lower_quantile = params.get('lower_quantile', 0.01)
            upper_quantile = params.get('upper_quantile', 0.99)
            transformer = WinsorizationTransform()
            transformed_df, metadata = transformer.transform(
                current_dataframe,
                lower_quantile=lower_quantile,
                upper_quantile=upper_quantile,
            )
            current_dataframe = transformed_df
            result = dataframe_to_json(transformed_df, limit=5)
        
        else:
            raise ValueError(f"Unknown transformation type: {transformation_type}")
        
        # Record transformation in history
        transformation_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': transformation_type,
            'parameters': params,
            'result_shape': current_dataframe.shape
        })
        
        return {
            "success": True,
            "message": f"{transformation_type} applied successfully",
            "data": result,
            "metadata": metadata,
            "shape": current_dataframe.shape
        }
    
    except Exception as e:
        logger.error(f"Error applying transformation: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_transformation_history():
    """Get history of applied transformations."""
    return {
        "success": True,
        "history": transformation_history
    }


@app.post("/reset")
async def reset_data():
    """Reset/Clear current DataFrame."""
    global current_dataframe, original_dataframe, transformation_history
    
    current_dataframe = None
    original_dataframe = None
    transformation_history = []
    
    return {
        "success": True,
        "message": "Data reset successfully"
    }


@app.get("/download/{format}")
async def download_data(format: str):
    """
    Download transformed data in specified format.
    
    Formats: csv, excel, parquet
    """
    global current_dataframe
    
    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No data to download")
    
    if format not in ['csv', 'excel', 'parquet']:
        raise HTTPException(status_code=400, detail="Invalid format. Use: csv, excel, or parquet")
    
    try:
        filepath = save_dataframe_to_temp(current_dataframe, format=format)
        return FileResponse(filepath, media_type='application/octet-stream')
    
    except Exception as e:
        logger.error(f"Error downloading data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save-pipeline")
async def save_pipeline(pipeline_name: str, description: str = ""):
    """Save current transformation pipeline for reuse."""
    global saved_pipelines, transformation_history
    
    if not transformation_history:
        raise HTTPException(status_code=400, detail="No transformations to save")
    
    saved_pipelines[pipeline_name] = {
        'name': pipeline_name,
        'description': description,
        'transformations': transformation_history,
        'created_at': datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "message": f"Pipeline '{pipeline_name}' saved successfully",
        "pipeline": saved_pipelines[pipeline_name]
    }


@app.get("/pipelines")
async def list_pipelines():
    """List all saved pipelines."""
    pipelines = [
        {
            'name': name,
            'description': data.get('description', ''),
            'created_at': data.get('created_at', ''),
            'num_transformations': len(data.get('transformations', []))
        }
        for name, data in saved_pipelines.items()
    ]
    
    return {
        "success": True,
        "pipelines": pipelines
    }


@app.get("/load-pipeline/{pipeline_name}")
async def load_pipeline(pipeline_name: str):
    """Load a saved pipeline."""
    if pipeline_name not in saved_pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")
    
    return {
        "success": True,
        "pipeline": saved_pipelines[pipeline_name]
    }


@app.delete("/pipeline/{pipeline_name}")
async def delete_pipeline(pipeline_name: str):
    """Delete a saved pipeline."""
    if pipeline_name not in saved_pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")
    
    del saved_pipelines[pipeline_name]
    
    return {
        "success": True,
        "message": f"Pipeline '{pipeline_name}' deleted successfully"
    }


@app.get("/stats")
async def get_detailed_statistics():
    """Get detailed statistics about current data."""
    global current_dataframe
    
    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No data uploaded")
    
    try:
        stats = {
            'shape': current_dataframe.shape,
            'columns': current_dataframe.columns.tolist(),
            'numeric_columns': current_dataframe.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': current_dataframe.select_dtypes(include=['object']).columns.tolist(),
            'missing_values': current_dataframe.isnull().sum().to_dict(),
            'unique_values': {col: current_dataframe[col].nunique() for col in current_dataframe.columns},
            'memory_usage': float(current_dataframe.memory_usage(deep=True).sum() / 1024**2),  # MB
        }
        
        return {
            "success": True,
            "statistics": stats
        }
    
    except Exception as e:
        logger.error(f"Error calculating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DATA SOURCE CONNECTOR ENDPOINTS ====================

@app.post("/connect-source")
async def connect_data_source(request: DataSourceRequest):
    """
    Connect to external data source and load data.
    
    Supported sources: csv_url, postgres, mysql, s3, google_sheets, sqlite, api
    """
    global current_dataframe, original_dataframe, transformation_history, current_user
    global current_source_type, current_source_config
    
    try:
        source_type = request.source_type.lower()
        config = request.config
        
        # Load data based on source type
        if source_type == 'csv_url':
            df = DataSourceConnector.load_csv_url(config.get('url'))
        
        elif source_type == 'postgres':
            df = DataSourceConnector.load_postgres_table(
                host=config.get('host'),
                port=config.get('port', 5432),
                database=config.get('database'),
                username=config.get('username'),
                password=config.get('password'),
                table_name=config.get('table_name'),
                query=config.get('query')
            )
        
        elif source_type == 'mysql':
            df = DataSourceConnector.load_mysql_table(
                host=config.get('host'),
                port=config.get('port', 3306),
                database=config.get('database'),
                username=config.get('username'),
                password=config.get('password'),
                table_name=config.get('table_name'),
                query=config.get('query')
            )
        
        elif source_type == 's3':
            df = DataSourceConnector.load_s3_file(
                bucket_name=config.get('bucket_name'),
                file_key=config.get('file_key'),
                aws_access_key_id=config.get('aws_access_key_id'),
                aws_secret_access_key=config.get('aws_secret_access_key'),
                region_name=config.get('region_name', 'us-east-1'),
                file_format=config.get('file_format', 'csv')
            )
        
        elif source_type == 'google_sheets':
            df = DataSourceConnector.load_google_sheet(
                sheet_url=config.get('sheet_url'),
                credentials_json=config.get('credentials_json'),
                sheet_name=config.get('sheet_name')
            )
        
        elif source_type == 'sqlite':
            df = DataSourceConnector.load_sqlite_table(
                database_path=config.get('database_path'),
                table_name=config.get('table_name'),
                query=config.get('query')
            )
        
        elif source_type == 'api':
            df = DataSourceConnector.load_api_json(
                url=config.get('url'),
                method=config.get('method', 'GET'),
                headers=config.get('headers'),
                params=config.get('params'),
                json_path=config.get('json_path')
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source type: {source_type}")
        
        # Set as current dataframe
        current_dataframe = df
        original_dataframe = df.copy(deep=True)
        transformation_history = []
        current_source_type = source_type
        current_source_config = sanitize_source_config(config)
        
        # Analyze dataset
        health_report = analyze_dataset(df)
        quality_score = calculate_data_quality_score(df.shape, health_report)
        
        logger.info(f"Connected to {source_type}: {df.shape}")
        
        return {
            "success": True,
            "message": f"Successfully connected to {source_type}",
            "source_type": source_type,
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dataset_health_report": health_report,
            "data_quality_score": quality_score,
            "preview": dataframe_to_json(df, limit=5)
        }
    
    except Exception as e:
        logger.error(f"Error connecting to data source: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== USER MANAGEMENT ENDPOINTS ====================

@app.post("/auth/register")
async def register_user(request: UserRegisterRequest):
    """Register a new user account."""
    try:
        user = UserManager.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        if not user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user.id,
            "username": user.username
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login")
async def login_user(request: UserLoginRequest):
    """Authenticate user and create session."""
    global current_user
    
    try:
        user = UserManager.authenticate(request.username, request.password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        current_user = user
        
        return {
            "success": True,
            "message": "Login successful",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/demo-login")
async def demo_login():
    """Login as demo user for testing."""
    global current_user
    
    try:
        user = UserManager.get_demo_user()
        current_user = user
        
        return {
            "success": True,
            "message": "Logged in as demo user",
            "user_id": user.id,
            "username": user.username
        }
    
    except Exception as e:
        logger.error(f"Error with demo login: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/current-user")
async def get_current_user():
    """Get current logged-in user."""
    global current_user
    
    if not current_user:
        # Auto-login as demo user
        current_user = UserManager.get_demo_user()
    if not current_user:
        raise HTTPException(status_code=500, detail="Unable to initialize demo user")
    
    return {
        "success": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name
    }


# ==================== DATASET REGISTRY ENDPOINTS ====================

@app.post("/datasets/register")
async def register_current_dataset(request: DatasetRegisterRequest):
    """Register current dataset to user's workspace."""
    global current_dataframe, current_user, last_registered_dataset_id
    
    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")
    
    if not current_user:
        current_user = UserManager.get_demo_user()
    
    try:
        # Get dataset health and quality
        health_report = analyze_dataset(current_dataframe)
        quality_score = calculate_data_quality_score(current_dataframe.shape, health_report)
        quality_score_value = float(quality_score.get("score", 0.0)) if isinstance(quality_score, dict) else float(quality_score)
        
        # Map visibility string to enum
        visibility_map = {
            'private': VisibilityType.PRIVATE,
            'public': VisibilityType.PUBLIC,
            'shared': VisibilityType.SHARED
        }
        visibility = visibility_map.get(request.visibility.lower(), VisibilityType.PRIVATE)
        
        # Register dataset
        dataset = DatasetRegistry.register_dataset(
            df=current_dataframe,
            dataset_name=request.dataset_name,
            owner_id=current_user.id,
            description=request.description,
            source_type=current_source_type,
            source_config=current_source_config,
            visibility=visibility,
            data_quality_score=quality_score_value,
            pipeline_config={'steps': transformation_history} if transformation_history else None,
            save_file=True
        )
        
        last_registered_dataset_id = dataset.dataset_id
        
        return {
            "success": True,
            "message": "Dataset registered successfully",
            "dataset_id": dataset.dataset_id,
            "dataset_name": dataset.dataset_name,
            "visibility": visibility.value,
            "data_quality_score": quality_score_value,
            "data_quality_breakdown": quality_score if isinstance(quality_score, dict) else None,
        }
    
    except Exception as e:
        logger.error(f"Error registering dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/datasets/public")
async def list_public_datasets(limit: int = 50, offset: int = 0):
    """List all public datasets."""
    try:
        datasets = DatasetRegistry.list_public_datasets(limit=limit, offset=offset)
        
        return {
            "success": True,
            "count": len(datasets),
            "datasets": datasets
        }
    
    except Exception as e:
        logger.error(f"Error listing public datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/datasets/{dataset_id}")
async def get_dataset_info(dataset_id: str):
    """Get dataset information."""
    try:
        dataset = DatasetRegistry.get_dataset(dataset_id)
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        return {
            "success": True,
            "dataset": {
                "dataset_id": dataset.dataset_id,
                "dataset_name": dataset.dataset_name,
                "description": dataset.description,
                "owner_id": dataset.owner_id,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count,
                "columns_info": dataset.columns_info,
                "data_quality_score": dataset.data_quality_score,
                "pipeline_applied": dataset.pipeline_applied,
                "visibility": dataset.visibility.value,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/datasets/{dataset_id}/load")
async def load_registered_dataset(dataset_id: str):
    """Load a registered dataset as current dataframe."""
    global current_dataframe, original_dataframe, transformation_history, current_source_type, current_source_config
    global current_user
    
    try:
        dataset = DatasetRegistry.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        if dataset.visibility == VisibilityType.PRIVATE:
            if not current_user:
                current_user = UserManager.get_demo_user()
            if not current_user or dataset.owner_id != current_user.id:
                raise HTTPException(status_code=403, detail="Authentication required for private dataset")

        df = DatasetRegistry.load_dataset_dataframe(dataset_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="Dataset not found or file missing")
        
        current_dataframe = df
        original_dataframe = df.copy(deep=True)
        transformation_history = []
        current_source_type = dataset.source_type or "registered_dataset"
        current_source_config = sanitize_source_config(dataset.source_config or {})
        
        return {
            "success": True,
            "message": f"Dataset {dataset_id} loaded successfully",
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "preview": dataframe_to_json(df, limit=5)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/datasets/{dataset_id}/clone-pipeline")
async def clone_dataset_pipeline(dataset_id: str):
    """Clone transformation pipeline from a dataset."""
    global current_user
    
    if not current_user:
        current_user = UserManager.get_demo_user()
    
    try:
        cloned = DatasetRegistry.clone_pipeline(dataset_id, current_user.id)
        
        if not cloned:
            raise HTTPException(status_code=404, detail="Dataset not found or no pipeline available")
        
        return {
            "success": True,
            "message": "Pipeline cloned successfully",
            "pipeline": cloned
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workspace/datasets")
async def get_user_datasets():
    """Get all datasets for current user."""
    global current_user
    
    if not current_user:
        current_user = UserManager.get_demo_user()
    
    try:
        datasets = DatasetRegistry.list_user_datasets(current_user.id)
        
        return {
            "success": True,
            "count": len(datasets),
            "datasets": datasets
        }
    
    except Exception as e:
        logger.error(f"Error getting user datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/datasets/search")
async def search_datasets(q: str, limit: int = 20):
    """Search datasets by name or description."""
    try:
        datasets = DatasetRegistry.search_datasets(query=q, limit=limit)
        
        return {
            "success": True,
            "count": len(datasets),
            "query": q,
            "datasets": datasets
        }
    
    except Exception as e:
        logger.error(f"Error searching datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== REPORT GENERATION ENDPOINTS ====================

@app.post("/reports/generate")
async def generate_dataset_report(request: ReportGenerateRequest):
    """Generate comprehensive dataset report."""
    global current_dataframe, original_dataframe, current_user, last_report_id, last_registered_dataset_id
    
    if current_dataframe is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")
    
    if not current_user:
        current_user = UserManager.get_demo_user()
    
    try:
        session = db.get_session()

        dataset_record = None
        if last_registered_dataset_id:
            dataset_record = session.query(Dataset).filter(Dataset.dataset_id == last_registered_dataset_id).first()

        if dataset_record is None:
            health_for_registration = analyze_dataset(current_dataframe)
            quality_for_registration = calculate_data_quality_score(current_dataframe.shape, health_for_registration)
            quality_for_registration_value = float(quality_for_registration.get("score", 0.0)) if isinstance(quality_for_registration, dict) else float(quality_for_registration)
            registered = DatasetRegistry.register_dataset(
                df=current_dataframe,
                dataset_name=f"Report Source {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                owner_id=current_user.id,
                description="Auto-registered for report generation",
                source_type=current_source_type,
                source_config=current_source_config,
                visibility=VisibilityType.PRIVATE,
                data_quality_score=quality_for_registration_value,
                pipeline_config={"steps": transformation_history} if transformation_history else None,
                save_file=True,
            )
            dataset_record = session.query(Dataset).filter(Dataset.dataset_id == registered.dataset_id).first()
            last_registered_dataset_id = registered.dataset_id

        # Get quality score
        health_report = analyze_dataset(current_dataframe)
        quality_score = calculate_data_quality_score(current_dataframe.shape, health_report)
        quality_score_value = float(quality_score.get("score", 0.0)) if isinstance(quality_score, dict) else float(quality_score)
        
        # Generate report
        report_data = ReportGenerator.generate_full_report(
            df=current_dataframe,
            report_name=request.report_name,
            description=request.description,
            data_quality_score=quality_score_value,
            pipeline_steps=transformation_history,
            before_df=original_dataframe if original_dataframe is not None else None,
            cleaned_dataset_path=save_dataframe_to_temp(current_dataframe, format="csv"),
        )

        report_record = Report(
            report_id=report_data["report_id"],
            dataset_id=dataset_record.id,
            owner_id=current_user.id,
            report_name=report_data.get("report_name", request.report_name),
            description=report_data.get("description"),
            dataset_summary=report_data.get("dataset_summary"),
            data_quality_score=quality_score_value,
            pipeline_steps=report_data.get("pipeline_steps", []),
            visualizations=report_data.get("visualizations", []),
            before_stats={
                "shape": (report_data.get("before_after_comparison") or {}).get("shape", {}).get("before"),
                "missing_values": (report_data.get("before_after_comparison") or {}).get("missing_values", {}).get("before"),
                "duplicates": (report_data.get("before_after_comparison") or {}).get("duplicates", {}).get("before"),
            }
            if report_data.get("before_after_comparison")
            else None,
            after_stats={
                "shape": (report_data.get("before_after_comparison") or {}).get("shape", {}).get("after"),
                "missing_values": (report_data.get("before_after_comparison") or {}).get("missing_values", {}).get("after"),
                "duplicates": (report_data.get("before_after_comparison") or {}).get("duplicates", {}).get("after"),
            }
            if report_data.get("before_after_comparison")
            else None,
            cleaned_dataset_path=report_data.get("cleaned_dataset_path"),
            visibility=VisibilityType.PUBLIC,
        )
        session.add(report_record)
        session.commit()
        
        last_report_id = report_data['report_id']
        
        return {
            "success": True,
            "message": "Report generated successfully",
            "report_id": report_data['report_id'],
            "public_url": f"/report/{report_data['report_id']}",
            "report": report_data
        }
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'session' in locals():
            session.close()


@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get persisted report by public report_id."""
    session = db.get_session()
    try:
        report = session.query(Report).filter(Report.report_id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report.visibility == VisibilityType.PRIVATE:
            global current_user
            if not current_user:
                current_user = UserManager.get_demo_user()
            if not current_user or report.owner_id != current_user.id:
                raise HTTPException(status_code=403, detail="Authentication required for private report")

        report.view_count = int(report.view_count or 0) + 1
        session.commit()

        return {
            "success": True,
            "report": _serialize_report(report)
        }
    finally:
        session.close()


@app.get("/report/{report_id}")
async def get_report_public_page(report_id: str):
    """Public-style alias route for shareable reports."""
    return await get_report(report_id)


@app.get("/reports/{report_id}/download")
async def download_report_dataset(report_id: str):
    """Download cleaned dataset artifact associated with a report."""
    session = db.get_session()
    try:
        report = session.query(Report).filter(Report.report_id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        if not report.cleaned_dataset_path or not os.path.exists(report.cleaned_dataset_path):
            raise HTTPException(status_code=404, detail="Cleaned dataset file not found for this report")

        return FileResponse(
            path=report.cleaned_dataset_path,
            filename=f"report_{report_id}_cleaned.csv",
            media_type="text/csv",
        )
    finally:
        session.close()


@app.get("/workspace/reports")
async def get_user_reports(limit: int = 50):
    """List reports for current user workspace."""
    global current_user
    if not current_user:
        current_user = UserManager.get_demo_user()

    session = db.get_session()
    try:
        reports = (
            session.query(Report)
            .filter(Report.owner_id == current_user.id)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .all()
        )
        return {
            "success": True,
            "count": len(reports),
            "reports": [_serialize_report(r) for r in reports],
        }
    finally:
        session.close()


@app.get("/workspace/pipelines")
async def get_user_pipelines(limit: int = 50):
    """List pipelines for current user workspace."""
    global current_user
    if not current_user:
        current_user = UserManager.get_demo_user()

    session = db.get_session()
    try:
        pipelines = (
            session.query(Pipeline)
            .filter(Pipeline.owner_id == current_user.id)
            .order_by(Pipeline.created_at.desc())
            .limit(limit)
            .all()
        )
        return {
            "success": True,
            "count": len(pipelines),
            "pipelines": [
                {
                    "pipeline_id": p.pipeline_id,
                    "pipeline_name": p.pipeline_name,
                    "description": p.description,
                    "pipeline_steps": p.pipeline_steps,
                    "visibility": p.visibility.value if p.visibility else VisibilityType.PRIVATE.value,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in pipelines
            ],
        }
    finally:
        session.close()


# ==================== SHARING ENDPOINTS ====================

@app.post("/share/create")
async def create_share_link(request: ShareRequest):
    """Create a share link for dataset/report/pipeline."""
    global current_user
    
    if not current_user:
        current_user = UserManager.get_demo_user()
    
    try:
        # Map strings to enums
        resource_type_map = {
            'dataset': ResourceType.DATASET,
            'report': ResourceType.REPORT,
            'pipeline': ResourceType.PIPELINE
        }
        access_level_map = {
            'viewer': AccessLevel.VIEWER,
            'editor': AccessLevel.EDITOR,
            'owner': AccessLevel.OWNER
        }
        
        resource_type = resource_type_map.get(request.resource_type.lower())
        access_level = access_level_map.get(request.access_level.lower(), AccessLevel.VIEWER)
        
        if not resource_type:
            raise HTTPException(status_code=400, detail="Invalid resource type")
        
        # Resolve to internal numeric resource id (accept public id strings too)
        internal_resource_id = _resolve_internal_resource_id(resource_type, request.resource_id)

        # Create share
        share = SharingManager.create_share(
            resource_type=resource_type,
            resource_id=internal_resource_id,
            owner_id=current_user.id,
            access_level=access_level,
            shared_with_user_id=request.shared_with_user_id,
            is_public_link=request.is_public_link,
            expires_in_days=request.expires_in_days
        )
        
        if not share:
            raise HTTPException(status_code=500, detail="Failed to create share")
        
        return {
            "success": True,
            "message": "Share created successfully",
            "share_id": share.share_id,
            "share_url": f"/share/{share.share_id}",
            "resource_share_url": f"/share/{resource_type.value}/{request.resource_id}?share_id={share.share_id}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating share: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/share/{share_id}")
async def access_shared_resource(share_id: str, user_id: Optional[int] = None):
    """Access a shared resource via share link."""
    try:
        # Check access
        has_access = SharingManager.check_access(share_id, user_id)
        
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied or link expired")
        
        # Get share details
        share = SharingManager.get_share(share_id)
        
        if not share:
            raise HTTPException(status_code=404, detail="Share not found")
        
        return {
            "success": True,
            "share": {
                "share_id": share.share_id,
                "resource_type": share.resource_type.value,
                "resource_id": share.resource_id,
                "access_level": share.access_level.value,
                "access_count": share.access_count
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing share: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/share/{resource_type}/{resource_id}")
async def access_resource_share_url(resource_type: str, resource_id: str, share_id: Optional[str] = None):
    """Resource-based share URL endpoint, e.g. /share/dataset/{id}."""
    type_map = {
        "dataset": ResourceType.DATASET,
        "report": ResourceType.REPORT,
        "pipeline": ResourceType.PIPELINE,
    }
    normalized = type_map.get(resource_type.lower())
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid resource type")

    # If share link is provided, validate it through sharing manager.
    if share_id:
        return await access_shared_resource(share_id)

    # Public resource fallback (without share_id)
    session = db.get_session()
    try:
        if normalized == ResourceType.DATASET:
            dataset = session.query(Dataset).filter(Dataset.dataset_id == resource_id).first()
            if not dataset:
                raise HTTPException(status_code=404, detail="Dataset not found")
            if dataset.visibility != VisibilityType.PUBLIC:
                raise HTTPException(status_code=403, detail="Resource is not public")
            return {
                "success": True,
                "resource_type": "dataset",
                "resource": {
                    "dataset_id": dataset.dataset_id,
                    "dataset_name": dataset.dataset_name,
                    "description": dataset.description,
                    "row_count": dataset.row_count,
                    "column_count": dataset.column_count,
                    "data_quality_score": dataset.data_quality_score,
                },
            }

        if normalized == ResourceType.REPORT:
            report = session.query(Report).filter(Report.report_id == resource_id).first()
            if not report:
                raise HTTPException(status_code=404, detail="Report not found")
            if report.visibility != VisibilityType.PUBLIC:
                raise HTTPException(status_code=403, detail="Resource is not public")
            return {
                "success": True,
                "resource_type": "report",
                "resource": _serialize_report(report),
            }

        pipeline = session.query(Pipeline).filter(Pipeline.pipeline_id == resource_id).first()
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        if pipeline.visibility != VisibilityType.PUBLIC:
            raise HTTPException(status_code=403, detail="Resource is not public")
        return {
            "success": True,
            "resource_type": "pipeline",
            "resource": {
                "pipeline_id": pipeline.pipeline_id,
                "pipeline_name": pipeline.pipeline_name,
                "description": pipeline.description,
                "pipeline_steps": pipeline.pipeline_steps,
            },
        }
    finally:
        session.close()


@app.get("/workspace/shared")
async def get_shared_with_me():
    """Get all resources shared with current user."""
    global current_user
    
    if not current_user:
        current_user = UserManager.get_demo_user()
    
    try:
        shares = SharingManager.list_shares_for_user(current_user.id)
        
        return {
            "success": True,
            "count": len(shares),
            "shares": shares
        }
    
    except Exception as e:
        logger.error(f"Error getting shared resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ERROR HANDLING ====================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
