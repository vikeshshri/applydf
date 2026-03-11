# applydf - Architecture & Design Guide

Comprehensive technical documentation of the applydf application architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Streamlit Frontend (UI)                    │
│  - File Upload                                              │
│  - Data Preview                                             │
│  - Transformation Selection & Parameter Input               │
│  - Results Visualization                                    │
│  - Pipeline Management                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                    HTTP/REST API
                         │
┌────────────────────────┴────────────────────────────────────┐
│               FastAPI Backend Server                        │
│  - Request Validation                                       │
│  - Data Processing Engine                                   │
│  - Transformation Orchestration                             │
│  - File Management                                          │
└┬───────────────────────────────────────────────────────────┴┘
 │
 └─────────────────┬──────────────────┬──────────────────┐
                   │                  │                  │
        ┌──────────▼──────┐  ┌───────▼────────┐  ┌────┴─────────┐
        │ Pandas/NumPy    │  │ scikit-learn   │  │ Transformers │
        │ Data Tables     │  │ ML Algorithms  │  │ NLTK/Gensim  │
        │ File I/O        │  │ Preprocessing  │  │ Deep Learning│
        └─────────────────┘  └────────────────┘  └──────────────┘
```

## Project Directory Structure

```
2026-applydf/
├── backend/
│   ├── app.py                 # FastAPI application (main server)
│   ├── transformations.py     # Transformation pipeline classes
│   ├── config.py              # Configuration settings
│   ├── utils.py               # Utility functions
│   ├── requirements.txt       # Backend dependencies
│   └── __pycache__/           # Python cache
│
├── frontend/
│   ├── app.py                 # Streamlit UI application
│   ├── requirements.txt       # Frontend dependencies
│   └── __pycache__/           # Python cache
│
├── requirements.txt           # All project dependencies
├── examples.py                # API usage examples
├── config.py                  # Global configuration (if using)
│
├── README.md                  # Full documentation
├── QUICKSTART.md              # Quick setup guide
├── TROUBLESHOOTING.md         # Troubleshooting guide
├── ARCHITECTURE.md            # This file
│
└── .gitignore                 # Git ignore patterns
```

## Component Details

### 1. Frontend (Streamlit)

**File**: `frontend/app.py`

**Responsibilities**:
- User interface and interactions
- File upload handling
- Data preview display
- Parameter input controls
- Results visualization
- Download management

**Key Components**:
```
- Page Config: Title, layout, styling
- Sidebar: Navigation, file upload, pipeline management
- Main Content: Data preview, transformation tabs, export options
- Session State: Maintain user data across reruns
```

**Libraries Used**:
- `streamlit`: UI framework
- `plotly`: Interactive visualizations
- `requests`: API communication
- `pandas`: Data display

### 2. Backend (FastAPI)

**File**: `backend/app.py`

**Responsibilities**:
- REST API endpoints
- Request routing and validation
- Data processing orchestration
- File management
- Error handling

**Key Endpoints**:
```
GET  /                    # API info
POST /upload              # Upload & parse file
GET  /preview             # Get data preview
GET  /categories          # List transformations
POST /transform           # Apply transformation
GET  /history             # Get history
GET  /download/{format}   # Download data
```

**Core Features**:
- CORS middleware for cross-origin requests
- Global error handling
- Session-based data management
- File format support (CSV, Excel, JSON, Parquet)

### 3. Transformation Pipeline

**File**: `backend/transformations.py`

**Architecture**: 
- Base class: `TransformationPipeline`
- Specialized classes for each algorithm
- Modular design for easy extension

**Transformation Classes**:

```python
TransformationPipeline (Base)
├── Dimensionality Reduction
│   ├── CovarianceMatrixTransform
│   ├── EigenvalueEigenvectorTransform
│   ├── PCATransform
│   ├── SVDTransform
│   ├── TSNETransform
│   └── UMAPTransform
│
├── Feature Engineering
│   ├── StandardizationTransform
│   ├── MinMaxNormalizationTransform
│   ├── LogPowerTransform
│   ├── OneHotEncodingTransform
│   ├── OrdinalEncodingTransform
│   └── BinningTransform
│
├── Text Processing
│   ├── TFIDFTransform
│   ├── NGramTransform
│   ├── Word2VecTransform
│   └── TransformerEmbeddingTransform
│
└── Data Cleaning
    ├── KNNImputationTransform
    ├── IsolationForestOutlierTransform
    ├── DeduplicationTransform
    └── TextNormalizationTransform
```

**Transformation Flow**:
```
Input Data (DataFrame)
    ↓
Validation (check columns, types)
    ↓
Preprocessing (handle missing values)
    ↓
Algorithm Application (transform data)
    ↓
Metadata Generation (stats, diagnostics)
    ↓
Output (transformed DataFrame + metadata)
```

### 4. Utilities (Helpers)

**File**: `backend/utils.py`

**Modules**:
- **DataValidator**: Input validation and quality checks
- **DataTypeConverter**: Automatic type optimization
- **StatisticalHelpers**: Statistical analysis functions
- **FileHandler**: Safe file operations
- **TextProcessor**: Text cleaning and analysis
- **BatchProcessor**: Process data in chunks
- **DebugHelper**: Logging and debugging utilities
- **CacheManager**: Simple caching mechanism

## Data Flow

### Upload Flow
```
User selects file
    ↓
Streamlit sends multipart request
    ↓
FastAPI receives file
    ↓
Parse file based on extension
    ↓
Store in global variable (current_dataframe)
    ↓
Generate metadata
    ↓
Return success response
    ↓
Frontend displays preview
```

### Transformation Flow
```
User selects algorithm & parameters
    ↓
Frontend sends POST /transform
    ↓
Backend validates request
    ↓
Get transformation class
    ↓
Validate input data
    ↓
Handle missing values (if needed)
    ↓
Apply algorithm with parameters
    ↓
Generate metadata & statistics
    ↓
Update global DataFrame
    ↓
Record in history
    ↓
Return transformed data preview
    ↓
Frontend displays preview & metadata
```

### Download Flow
```
User clicks download button
    ↓
Frontend sends GET /download/{format}
    ↓
Backend gets current DataFrame
    ↓
Convert to requested format (CSV/Excel/Parquet)
    ↓
Save to temporary file
    ↓
Return file as response
    ↓
Browser downloads file
    ↓
Optional: Cleanup old temp files
```

## Design Patterns

### 1. Pipeline Pattern
Each transformation is a self-contained pipeline:
```python
class TransformationPipeline:
    def transform(self, data: DataFrame, **params) -> (DataFrame, Dict):
        # Validation
        # Processing
        # Return transformed data + metadata
```

### 2. Strategy Pattern
Different algorithms can be swapped:
```python
if transformation_type == 'PCA':
    transformer = PCATransform()
elif transformation_type == 'UMAP':
    transformer = UMAPTransform()
# Use transformer.transform(data, **params)
```

### 3. Session Pattern
Streamlit uses session state for data persistence across reruns:
```python
st.session_state.current_data = None
st.session_state.preview_data = None
st.session_state.transformation_history = []
```

### 4. Global State Pattern
FastAPI backend uses module-level variables:
```python
current_dataframe = None
transformation_history = []
saved_pipelines = {}
```

## Extension Guide

### Adding a New Transformation

1. **Create class in `transformations.py`**:
```python
class MyNewTransform(TransformationPipeline):
    def transform(self, data: pd.DataFrame, param1: int, param2: str) -> Tuple[pd.DataFrame, Dict]:
        # Validate data
        self.validate_data(data)
        
        # Process
        result = # ... your algorithm
        metadata = {'param1': param1, 'param2': param2}
        
        # Return
        return result, metadata
```

2. **Add endpoint in `app.py`**:
```python
elif transformation_type == 'My New Transform':
    transformer = MyNewTransform()
    param1 = params.get('param1', default_value)
    param2 = params.get('param2', default_value)
    transformed_df, metadata = transformer.transform(current_dataframe, param1, param2)
    current_dataframe = transformed_df
    result = dataframe_to_json(transformed_df, limit=5)
```

3. **Add UI in `frontend/app.py`**:
```python
elif selected_method == 'My New Transform':
    param1 = st.slider("Parameter 1", min_val, max_val, default)
    param2 = st.selectbox("Parameter 2", ['option1', 'option2'])
    params['param1'] = param1
    params['param2'] = param2
```

4. **Update categories in `transformations.py`**:
```python
'Category Name': [
    '...',
    'My New Transform',
    '...'
]
```

## Configuration Management

### Backend Config (`config.py`)
- API settings (host, port, CORS)
- File upload limits
- Model caching options
- Transformation defaults
- Performance parameters

### Environment Variables
```bash
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
API_BASE_URL=http://localhost:8000
MAX_FILE_SIZE_MB=100
```

## Error Handling

### Front-to-Back Error Flow
```
Frontend Validation
    ↓
Backend Validation
    ↓
Transformation Validation
    ↓
Algorithm Execution
    ↓
Error occurs
    ↓
Try/Except catches error
    ↓
Log error with traceback
    ↓
Return 400/500 response
    ↓
Frontend receives error
    ↓
Display error message to user
```

### Error Types
- **400 Bad Request**: Invalid input (bad file, missing columns, wrong types)
- **404 Not Found**: Resource doesn't exist (pipeline not saved)
- **422 Unprocessable Entity**: Invalid transformation parameters
- **500 Internal Server Error**: Algorithm failure, Out of Memory, etc.

## Performance Considerations

### Algorithm Complexity
```
O(n log n): KNN Imputation, Binning
O(n²): t-SNE, Isolation Forest, Correlation
O(n³): Some linear algebra operations
```

### Memory Usage
```
PCA: O(n × d) - Usually OK
t-SNE: O(n²) - Problematic for n > 10000
UMAP: O(n log n) - Better than t-SNE
Transformer Embeddings: O(n) - OK but slow first run
```

### Optimization Strategies
1. **Dimensionality Reduction First**: Reduce features before other transforms
2. **Batch Processing**: Process large files in chunks
3. **Caching**: Cache expensive operations (model downloads)
4. **Sampling**: Use smaller samples for testing
5. **Lazy Loading**: Load data on demand

## Security Considerations

### Data Handling
- Files stored in temporary directory
- Automatic cleanup of old files
- No persistence across sessions (unless saved)

### API Security
- CORS headers properly configured
- Input validation on all endpoints
- File type validation for uploads
- No authentication (development only)

### Production Deployment
For production, add:
- Authentication (API keys, JWT tokens)
- Rate limiting
- Request size limits
- HTTPS/TLS encryption
- Database for persistence
- Audit logging

## Testing Strategy

### Unit Tests
```python
def test_pca_transform():
    # Create test data
    # Apply PCA
    # Validate output shape, metadata
```

### Integration Tests
```python
def test_full_workflow():
    # Upload file
    # Apply transformation
    # Download result
    # Validate file format
```

### Performance Tests
```python
def test_large_dataset():
    # Load 1M row dataset
    # Apply transformation
    # Measure time and memory
```

## Maintenance & Monitoring

### Logging
- Backend logs all requests in uvicorn output
- Transformation errors logged with tracebacks
- File operations logged for debugging

### Health Checks
```bash
# Check API is running
curl http://localhost:8000/

# Check categories are loaded
curl http://localhost:8000/categories

# Check current data
curl http://localhost:8000/stats
```

### Performance Monitoring
- Monitor temp file directory size
- Track transformation execution time
- Monitor memory usage
- Check API response times

## Scaling Strategies

### Horizontal Scaling
- Run multiple backend instances behind load balancer
- Share session state via Redis/database
- Use message queue (Celery) for long-running tasks

### Vertical Scaling
- Increase machine resources (RAM, CPU)
- Enable GPU acceleration (CUDA)
- Use batch processing for large datasets

### Database Persistence
```
Add SQLAlchemy models:
- DatasetModel: Store uploaded datasets
- TransformationModel: Store transformation history
- PipelineModel: Store saved pipelines
```

## Future Enhancements

### Phase 1
- [ ] Advanced visualizations (heatmaps, dendrograms)
- [ ] A/B testing framework
- [ ] Data quality reports

### Phase 2
- [ ] Real-time data streaming
- [ ] GPU acceleration
- [ ] Advanced outlier visualization
- [ ] Database persistence

### Phase 3
- [ ] Distributed processing (Spark)
- [ ] Cloud deployment (AWS/GCP/Azure)
- [ ] Advanced monitoring and alerting
- [ ] Web-scale architecture

## Architecture Diagrams

### Request-Response Cycle
```
┌─────────────────┐
│  User Browser   │
└────────┬────────┘
         │ HTTP
         ▼
┌──────────────────────────┐
│   Streamlit Frontend     │
│ (renders HTML/CSS/JS)    │
└────────┬─────────────────┘
         │ REST API (JSON)
         ▼
┌──────────────────────────┐
│   FastAPI Backend        │
│ (processes requests)     │
└────────┬─────────────────┘
         │ Python libraries
         ▼
┌──────────────────────────┐
│   Transformation Engine  │
│ (algorithms, data ops)   │
└──────────────────────────┘
```

### State Management
```
┌──────────────────────────────┐
│   Streamlit Session State    │
│ (frontend-specific state)    │
└──────────────────────────────┘

┌──────────────────────────────┐
│   FastAPI Module Variables   │
│ (server-side state)          │
│ - current_dataframe          │
│ - transformation_history     │
│ - saved_pipelines            │
└──────────────────────────────┘

┌──────────────────────────────┐
│   Temporary File System      │
│ (downloaded files)           │
└──────────────────────────────┘
```

---

## Quick Reference

### Key Classes
- `FastAPI`: Web framework (backend)
- `Streamlit`: UI framework (frontend)
- `TransformationPipeline`: Base class for algorithms
- `pandas.DataFrame`: Core data structure

### Key Libraries
- `scikit-learn`: ML algorithms
- `umap`, `gensim`: Dimensionality reduction & embeddings
- `transformers`: Transformer models
- `plotly`: Visualizations

### Key Concepts
- REST API: Communication between frontend and backend
- Pipeline: Sequential transformation steps
- Metadata: Information about transformed data
- Session State: Data persistence in Streamlit

---

**Created**: 2024
**Version**: 1.0.0
**Maintainer**: Data Science Team
