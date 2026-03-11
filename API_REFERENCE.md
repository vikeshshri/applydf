# API Reference Guide for applydf

Complete documentation of all API endpoints and their usage.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required (development mode). For production, implement JWT tokens or API keys.

---

## Core Endpoints

### 1. GET `/`

**Description**: Get API information and available endpoints.

**Response**:
```json
{
  "name": "applydf API",
  "version": "1.0.0",
  "description": "Interactive Data Transformation and Cleaning API",
  "endpoints": {
    "upload": "POST /upload - Upload and parse data file",
    "preview": "GET /preview - Get data preview",
    ...
  }
}
```

**cURL Example**:
```bash
curl http://localhost:8000/
```

---

### 2. POST `/upload`

**Description**: Upload and parse a data file.

**Supported Formats**: CSV, Excel (.xlsx, .xls), JSON, Parquet

**Request**:
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `file` (required): The file to upload

**Response**:
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "filename": "data.csv",
  "shape": [100, 5]
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data.csv"
```

**Python Example**:
```python
import requests

with open('data.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/upload', files=files)
    print(response.json())
```

**Error Responses**:
- **400 Bad Request**: Invalid file format
- **413 Payload Too Large**: File exceeds size limit

---

### 3. GET `/preview`

**Description**: Get preview of currently uploaded data.

**Response**:
```json
{
  "shape": [100, 5],
  "columns": ["feature1", "feature2", "feature3", "label", "id"],
  "data_types": {
    "feature1": "float64",
    "feature2": "int64",
    "feature3": "object",
    "label": "object",
    "id": "int64"
  },
  "missing_values": {
    "feature1": 2,
    "feature2": 0,
    "feature3": 5,
    "label": 0,
    "id": 0
  },
  "statistics": {
    "feature1": {
      "mean": 0.5,
      "median": 0.4,
      "std": 0.15,
      "min": 0.1,
      "max": 0.9,
      "q25": 0.3,
      "q75": 0.7
    },
    "feature2": { ... }
  },
  "preview_data": [
    {"feature1": 0.5, "feature2": 1, ...},
    ...
  ]
}
```

**cURL Example**:
```bash
curl http://localhost:8000/preview
```

**Error Responses**:
- **400 Bad Request**: No data uploaded yet

---

### 4. GET `/categories`

**Description**: Get available transformation categories and methods.

**Response**:
```json
{
  "success": true,
  "categories": {
    "Dimensionality Reduction & Structure": [
      "Covariance Matrix",
      "Eigenvalue/Eigenvector",
      "PCA",
      "SVD",
      "t-SNE",
      "UMAP"
    ],
    "Feature Engineering & Scaling": [
      "Standardization (Z-score)",
      "Min-Max Normalization",
      ...
    ],
    "Text-Specific Transformation": [...],
    "Data Cleaning & Quality": [...]
  }
}
```

**cURL Example**:
```bash
curl http://localhost:8000/categories
```

---

## Transformation Endpoints

### 5. POST `/transform`

**Description**: Apply a transformation to the current dataset.

**Request**:
- **Method**: POST
- **Content-Type**: application/json
- **Body**: TransformationRequest

**Request Schema**:
```json
{
  "transformation_type": "string (required)",
  "parameters": {
    "key1": "value1",
    "key2": "value2"
  },
  "text_column": "string (optional)"
}
```

**Response**:
```json
{
  "success": true,
  "message": "PCA applied successfully",
  "data": [
    {"PC1": 0.5, "PC2": -0.3},
    {"PC1": 0.2, "PC2": 0.8},
    ...
  ],
  "metadata": {
    "explained_variance": [0.5, 0.3],
    "explained_variance_ratio": [0.625, 0.375],
    "n_components": 2
  },
  "shape": [100, 2]
}
```

---

### Transformation-Specific Parameters

#### PCA
```json
{
  "transformation_type": "PCA",
  "parameters": {
    "n_components": 2
  }
}
```
- `n_components` (int): Number of principal components (2-10)

#### SVD
```json
{
  "transformation_type": "SVD",
  "parameters": {
    "n_components": 2
  }
}
```
- `n_components` (int): Number of singular values

#### t-SNE
```json
{
  "transformation_type": "t-SNE",
  "parameters": {
    "n_components": 2,
    "perplexity": 30,
    "learning_rate": 200,
    "n_iter": 1000
  }
}
```
- `n_components` (int): 2 or 3
- `perplexity` (int): 5-50, balance between local and global
- `learning_rate` (int): 10-1000
- `n_iter` (int): 250-2000

#### UMAP
```json
{
  "transformation_type": "UMAP",
  "parameters": {
    "n_components": 2,
    "n_neighbors": 15,
    "min_dist": 0.1
  }
}
```
- `n_components` (int): 2 or 3
- `n_neighbors` (int): 5-50
- `min_dist` (float): 0.0-1.0

#### Standardization (Z-score)
```json
{
  "transformation_type": "Standardization (Z-score)",
  "parameters": {}
}
```
No parameters needed - standardizes all numeric columns.

#### Min-Max Normalization
```json
{
  "transformation_type": "Min-Max Normalization",
  "parameters": {
    "feature_range": [0, 1]
  }
}
```
- `feature_range` (list): [min, max] for scaling

#### Log/Power Transforms
```json
{
  "transformation_type": "Log/Power Transforms",
  "parameters": {
    "method": "log",
    "power": 2.0
  }
}
```
- `method` (str): "log", "log10", "log2", or "power"
- `power` (float): Exponent if method="power"

#### One-Hot Encoding
```json
{
  "transformation_type": "One-Hot Encoding",
  "parameters": {
    "columns": ["category1", "category2"]
  }
}
```
- `columns` (list, optional): Columns to encode. If null, encodes all object columns

#### Ordinal Encoding
```json
{
  "transformation_type": "Ordinal Encoding",
  "parameters": {
    "columns": ["status", "priority"]
  }
}
```
- `columns` (list, optional): Columns to encode

#### Binning/Discretization
```json
{
  "transformation_type": "Binning/Discretization",
  "parameters": {
    "n_bins": 5,
    "strategy": "quantile"
  }
}
```
- `n_bins` (int): 2-20
- `strategy` (str): "quantile", "uniform", or "kmeans"

#### TF-IDF
```json
{
  "transformation_type": "TF-IDF",
  "parameters": {
    "max_features": 100
  },
  "text_column": "document"
}
```
- `max_features` (int): Maximum n features
- `text_column` (str, required): Column with text

#### N-gram Analysis
```json
{
  "transformation_type": "N-gram Analysis",
  "parameters": {
    "ngram_range": [1, 2],
    "max_features": 100
  },
  "text_column": "document"
}
```
- `ngram_range` (list): [min_n, max_n]
- `max_features` (int): Maximum n features
- `text_column` (str, required): Column with text

#### Word2Vec
```json
{
  "transformation_type": "Word2Vec",
  "parameters": {
    "vector_size": 100,
    "window": 5,
    "min_count": 2
  },
  "text_column": "document"
}
```
- `vector_size` (int): Embedding dimension
- `window` (int): Context window size
- `min_count` (int): Minimum word frequency
- `text_column` (str, required): Column with text

#### Transformer Embeddings
```json
{
  "transformation_type": "Transformer Embeddings",
  "parameters": {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "max_length": 128
  },
  "text_column": "document"
}
```
- `model_name` (str): HuggingFace model ID
- `max_length` (int): Maximum sequence length
- `text_column` (str, required): Column with text

Available models:
- `sentence-transformers/all-MiniLM-L6-v2` (Recommended - fast)
- `sentence-transformers/all-mpnet-base-v2` (Higher quality)
- `sentence-transformers/paraphrase-MiniLM-L6-v2` (Paraphrase task)

#### KNN Imputation
```json
{
  "transformation_type": "KNN Imputation",
  "parameters": {
    "n_neighbors": 5
  }
}
```
- `n_neighbors` (int): Number of neighbors

#### Isolation Forest Outlier Detection
```json
{
  "transformation_type": "Isolation Forest Outlier Detection",
  "parameters": {
    "contamination": 0.1,
    "remove_outliers": true
  }
}
```
- `contamination` (float): 0.01-0.5, expected outlier proportion
- `remove_outliers` (bool): Remove detected outliers or keep

#### Deduplication
```json
{
  "transformation_type": "Deduplication",
  "parameters": {
    "subset": ["column1", "column2"],
    "keep": "first"
  }
}
```
- `subset` (list, optional): Columns to consider. If null, use all
- `keep` (str): "first" or "last"

#### Text Normalization
```json
{
  "transformation_type": "Text Normalization",
  "parameters": {
    "lowercase": true,
    "remove_special": true,
    "lemmatize": true
  },
  "text_column": "document"
}
```
- `lowercase` (bool): Convert to lowercase
- `remove_special` (bool): Remove special characters
- `lemmatize` (bool): Apply lemmatization
- `text_column` (str, required): Column with text

---

### 6. GET `/history`

**Description**: Get history of applied transformations.

**Response**:
```json
{
  "success": true,
  "history": [
    {
      "timestamp": "2024-01-15T10:30:45.123456",
      "type": "PCA",
      "parameters": {"n_components": 2},
      "result_shape": [100, 2]
    },
    {
      "timestamp": "2024-01-15T10:31:12.654321",
      "type": "Standardization (Z-score)",
      "parameters": {},
      "result_shape": [100, 2]
    }
  ]
}
```

**cURL Example**:
```bash
curl http://localhost:8000/history
```

---

### 7. POST `/reset`

**Description**: Clear current data and reset session.

**Response**:
```json
{
  "success": true,
  "message": "Data reset successfully"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/reset
```

---

## Data Export Endpoints

### 8. GET `/download/{format}`

**Description**: Download transformed data in specified format.

**Parameters**:
- `format` (str): "csv", "excel", or "parquet"

**Response**: File binary stream

**cURL Example**:
```bash
# Download as CSV
curl http://localhost:8000/download/csv -o output.csv

# Download as Excel
curl http://localhost:8000/download/excel -o output.xlsx

# Download as Parquet
curl http://localhost:8000/download/parquet -o output.parquet
```

**Python Example**:
```python
import requests

response = requests.get('http://localhost:8000/download/csv')
with open('output.csv', 'wb') as f:
    f.write(response.content)
```

**Error Responses**:
- **400 Bad Request**: No data to download or invalid format
- **500 Internal Server Error**: Download generation failed

---

## Pipeline Management Endpoints

### 9. POST `/save-pipeline`

**Description**: Save current transformation pipeline.

**Request Parameters** (query string):
- `pipeline_name` (str): Name for the pipeline
- `description` (str, optional): Short description

**Response**:
```json
{
  "success": true,
  "message": "Pipeline 'my_pipeline' saved successfully",
  "pipeline": {
    "name": "my_pipeline",
    "description": "PCA + standardization",
    "created_at": "2024-01-15T10:35:00.000000",
    "transformations": [
      {"type": "Standardization (Z-score)", "parameters": {}},
      {"type": "PCA", "parameters": {"n_components": 2}}
    ]
  }
}
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/save-pipeline?pipeline_name=my_pipeline&description=Quick%20reduction"
```

**Error Responses**:
- **400 Bad Request**: No transformations to save

---

### 10. GET `/pipelines`

**Description**: List all saved pipelines.

**Response**:
```json
{
  "success": true,
  "pipelines": [
    {
      "name": "pipeline1",
      "description": "Initial processing",
      "created_at": "2024-01-15T10:35:00.000000",
      "num_transformations": 3
    },
    {
      "name": "pipeline2",
      "description": "Advanced analysis",
      "created_at": "2024-01-15T10:40:00.000000",
      "num_transformations": 5
    }
  ]
}
```

**cURL Example**:
```bash
curl http://localhost:8000/pipelines
```

---

### 11. GET `/load-pipeline/{pipeline_name}`

**Description**: Load a specific saved pipeline.

**Parameters**:
- `pipeline_name` (str): Name of pipeline to load

**Response**:
```json
{
  "success": true,
  "pipeline": {
    "name": "pipeline1",
    "description": "Initial processing",
    "created_at": "2024-01-15T10:35:00.000000",
    "transformations": [
      {"type": "Standardization (Z-score)", "parameters": {}, "timestamp": "..."},
      {"type": "PCA", "parameters": {"n_components": 2}, "timestamp": "..."}
    ]
  }
}
```

**cURL Example**:
```bash
curl http://localhost:8000/load-pipeline/pipeline1
```

**Error Responses**:
- **404 Not Found**: Pipeline doesn't exist

---

### 12. DELETE `/pipeline/{pipeline_name}`

**Description**: Delete a saved pipeline.

**Parameters**:
- `pipeline_name` (str): Name of pipeline to delete

**Response**:
```json
{
  "success": true,
  "message": "Pipeline 'pipeline1' deleted successfully"
}
```

**cURL Example**:
```bash
curl -X DELETE http://localhost:8000/pipeline/pipeline1
```

**Error Responses**:
- **404 Not Found**: Pipeline doesn't exist

---

## Statistics Endpoints

### 13. GET `/stats`

**Description**: Get detailed statistics about current data.

**Response**:
```json
{
  "success": true,
  "statistics": {
    "shape": [100, 5],
    "columns": ["feature1", "feature2", "feature3", "label", "id"],
    "numeric_columns": ["feature1", "feature2", "id"],
    "categorical_columns": ["label"],
    "missing_values": {"feature1": 2, "feature2": 0, ...},
    "unique_values": {"feature1": 98, "feature2": 50, ...},
    "memory_usage": 0.005
  }
}
```

**cURL Example**:
```bash
curl http://localhost:8000/stats
```

---

## Error Handling

### Standard Error Response

All errors follow this format:
```json
{
  "success": false,
  "message": "Error occurred",
  "detail": "Detailed error message"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Transformation applied successfully |
| 400 | Bad Request | Invalid file format, missing columns |
| 404 | Not Found | Pipeline doesn't exist |
| 422 | Unprocessable Entity | Invalid parameters |
| 500 | Internal Error | Algorithm failure, OOM |

---

## Rate Limiting

Currently enabled: None (development mode)

For production, implement rate limiting:
```
- 100 requests/minute per IP
- 10 uploads/hour per IP
- 5 long-running transformations/hour per IP
```

---

## Expected Limitations

### Dataset Size
- **Recommended**: < 100,000 rows
- **Maximum**: Depends on available RAM
- **Problematic**: > 1,000,000 rows without sampling

### Transformation Size
- **PCA**: Moderate (O(n × d))
- **t-SNE**: High (O(n²)) - limit to 10,000 rows
- **UMAP**: Better scalability than t-SNE
- **Transformers**: GPU-accelerated for large text

### Time Limits
- Most transformations: < 30 seconds
- t-SNE: 1-5 minutes for 10,000 rows
- Transformer embeddings: 5-30 minutes first run (model download)

---

## Interactive API Documentation

Visit http://localhost:8000/docs for:
- Swagger UI with interactive testing
- Automatic documentation from code
- Request/response schemas
- Try-it-out functionality

---

## Batch API

For processing multiple transformations:

```bash
# Example: Sequential transformations
curl -X POST http://localhost:8000/transform \
  -H "Content-Type: application/json" \
  -d '{"transformation_type": "PCA", "parameters": {"n_components": 2}}'

curl -X POST http://localhost:8000/transform \
  -H "Content-Type: application/json" \
  -d '{"transformation_type": "Standardization (Z-score)", "parameters": {}}'

curl http://localhost:8000/download/csv -o result.csv
```

---

## Webhook Support

Not currently implemented. For production:
```json
{
  "webhook_url": "https://your-server.com/webhook",
  "events": ["transformation_complete", "upload_complete"]
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024 | Initial release |

---

**Last Updated**: 2024
**API Version**: 1.0.0
