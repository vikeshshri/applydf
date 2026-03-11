# applydf - Interactive Data Transformation & Cleaning

A full-stack Python application for interactive data transformation, cleaning, and analysis with a modern, intuitive UI/UX. applydf supports both tabular and text data transformations with 20+ powerful algorithms.

## 🌟 Features

### Core Capabilities
- **Multi-format File Support**: CSV, Excel, JSON, Parquet
- **Real-time Data Preview**: View data shape, types, missing values, and statistics
- **20+ Transformation Algorithms**: Covering dimensionality reduction, feature engineering, text processing, and data cleaning
- **Interactive Parameter Tuning**: Adjust algorithm hyperparameters in real-time
- **Multiple Export Formats**: Download results as CSV, Excel, or Parquet
- **Pipeline Management**: Save and reuse transformation pipelines
- **Responsive Design**: Works seamlessly on desktop and tablet devices

### Transformation Categories

#### 1. Dimensionality Reduction & Structure (6 algorithms)
- **Covariance Matrix Calculation**: Analyze feature correlations
- **Eigenvalue/Eigenvector Extraction**: Decompose covariance matrices
- **Principal Component Analysis (PCA)**: Linear dimensionality reduction with configurable components
- **Singular Value Decomposition (SVD)**: Matrix factorization for compression
- **t-SNE**: Non-linear dimensionality reduction for visualization (2D/3D)
- **UMAP**: Scalable non-linear dimensionality reduction with adjustable parameters

#### 2. Feature Engineering & Scaling (6 algorithms)
- **Standardization (Z-score)**: Mean=0, Std=1 normalization
- **Min-Max Normalization**: Scale to [0, 1] range with custom bounds
- **Log/Power Transforms**: Apply log or exponential transformations
- **One-Hot Encoding**: Convert categorical to binary features
- **Ordinal Encoding**: Assign integer labels to categories
- **Binning/Discretization**: Convert continuous to categorical with multiple strategies

#### 3. Text-Specific Transformation (4 algorithms)
- **TF-IDF**: Term Frequency-Inverse Document Frequency vectorization
- **N-gram Analysis**: Extract n-grams with configurable ranges
- **Word2Vec**: Generate word embeddings with custom vector sizes
- **Transformer Embeddings**: Use pre-trained models (all-MiniLM, all-mpnet, etc.)

#### 4. Data Cleaning & Quality (4 algorithms)
- **KNN Imputation**: Handle missing values using k-nearest neighbors
- **Isolation Forest Outlier Detection**: Detect and remove anomalies
- **Deduplication**: Remove duplicate rows with flexible options
- **Text Normalization**: Lowercase, remove special chars, lemmatization

## 📋 Project Structure

```
2026-applydf/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── transformations.py     # Transformation pipeline classes
│   └── __pycache__/
├── frontend/
│   ├── app.py                 # Streamlit UI application
│   └── __pycache__/
├── requirements.txt           # Project dependencies
├── README.md                  # This file
└── .gitignore
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone/Navigate to the project**
```bash
cd 2026-applydf
```

2. **Create a virtual environment (recommended)**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download required NLTK data** (one-time setup)
```python
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')"
```

### Running the Application

**Terminal 1 - Start the FastAPI Backend:**
```bash
cd backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
Uvicorn running on http://0.0.0.0:8000
```

API documentation available at: http://localhost:8000/docs

**Terminal 2 - Start the Streamlit Frontend:**
```bash
cd frontend
streamlit run app.py
```

You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Open your browser to http://localhost:8501 and start using applydf!

## 📖 Usage Guide

### 1. Upload Data
- Click "Upload a file" in the left sidebar
- Select a CSV, Excel, JSON, or Parquet file
- Click "📤 Upload & Parse"

### 2. Preview Data
- View data shape, types, and statistics
- Check for missing values
- Review first 5 rows in multiple formats

### 3. Apply Transformations
- Select a category from the tabs (e.g., "Dimensionality Reduction")
- Choose a specific transformation
- Adjust parameters using interactive controls
- Click "▶️ Apply [Transformation]"

### 4. Export Results
- Choose export format (CSV, Excel, Parquet)
- Click the corresponding download button
- File will be downloaded automatically

### 5. Save Pipelines
- After applying transformations, enter a pipeline name
- Add an optional description
- Click "💾 Save Pipeline"
- Pipelines can be loaded and reused later

## 🔧 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| POST | `/upload` | Upload and parse file |
| GET | `/preview` | Get data preview |
| GET | `/categories` | List transformation categories |
| POST | `/transform` | Apply transformation |
| GET | `/history` | Get transformation history |
| POST | `/reset` | Clear current data |
| GET | `/download/{format}` | Download data (csv, excel, parquet) |

### Pipeline Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/save-pipeline` | Save transformation pipeline |
| GET | `/pipelines` | List saved pipelines |
| GET | `/load-pipeline/{name}` | Load specific pipeline |
| DELETE | `/pipeline/{name}` | Delete saved pipeline |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats` | Get detailed statistics |

### Example API Call

```bash
# Upload a file
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data.csv"

# Apply PCA transformation
curl -X POST "http://localhost:8000/transform" \
  -H "Content-Type: application/json" \
  -d '{
    "transformation_type": "PCA",
    "parameters": {"n_components": 3}
  }'

# Download result as CSV
curl -X GET "http://localhost:8000/download/csv" \
  -o transformed_data.csv
```

## ⚙️ Configuration

### Backend Configuration

Edit `backend/app.py` to customize:
- **API Port**: Change `port=8000` in the main runner
- **CORS Settings**: Modify the CORS middleware for different origins
- **Logging Level**: Adjust `logging.basicConfig(level=logging.INFO)`

### Frontend Configuration

Edit `frontend/app.py` to customize:
- **API Base URL**: Change `API_BASE_URL = "http://localhost:8000"`
- **Page Title & Icon**: Modify `st.set_page_config()`
- **Custom Styling**: Edit CSS in the markdown section

## 📦 Dependencies

### Core Libraries
- **FastAPI**: Modern web framework for building APIs
- **Streamlit**: Rapid UI prototyping framework
- **pandas/numpy**: Data manipulation and numerical computing
- **scikit-learn**: Machine learning algorithms
- **plotly**: Interactive visualizations

### Specialized
- **umap-learn**: UMAP dimensionality reduction
- **gensim**: Word2Vec embeddings
- **transformers**: Pre-trained transformer models
- **nltk**: Natural language processing

See `requirements.txt` for complete list with versions.

## 🎓 Transformation Details

### PCA Example
```
Input: 100 rows × 20 features
Parameters: n_components=2
Output: 100 rows × 2 principal components
Use Case: Visualization, feature reduction, noise removal
```

### Text Normalization Example
```
Input: "Hello, World!!! 123"
Parameters: lowercase=True, remove_special=True, lemmatize=True
Output: "hello world"
Use Case: Text preprocessing, NLP preparation
```

### t-SNE Example
```
Input: 1000 rows × 50 features
Parameters: n_components=2, perplexity=30
Output: 1000 rows × 2 t-SNE coordinates
Use Case: Cluster visualization, pattern discovery
```

## 🐛 Troubleshooting

### "Could not connect to backend"
- Ensure FastAPI is running: `python -m uvicorn app:app --reload`
- Check port 8000 is available: `netstat -ano | findstr :8000` (Windows)
- Verify API URL in frontend: `API_BASE_URL = "http://localhost:8000"`

### "No numeric columns found"
- Some transformations require numeric data
- Check your data types in the "Data Types" tab
- Convert categorical columns to numeric first using encoding

### "Memory Error" with large datasets
- Try dimensionality reduction first (PCA, SVD)
- Use sampling: `df.sample(n=10000)` before uploading
- Export and process in chunks

### Missing NLTK data
```python
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')"
```

### Transformer model download takes long
- First download is slow (model caching)
- Subsequent runs will be instant
- Models stored in `.cache/huggingface/`

## 📊 Example Workflows

### Workflow 1: Dimensionality Reduction Visualization
1. Upload 50+ dimensional dataset (e.g., images, sensor data)
2. Apply PCA with 2 components
3. Export as CSV
4. Visualize in external tool

### Workflow 2: Text Analysis Pipeline
1. Upload CSV with text column
2. Apply Text Normalization
3. Apply TF-IDF or Word2Vec
4. Export embeddings
5. Use for clustering/classification

### Workflow 3: Data Cleaning
1. Upload data with missing values
2. Apply KNN Imputation
3. Apply Deduplication
4. Apply Isolation Forest for outlier removal
5. Export clean dataset

### Workflow 4: Feature Engineering
1. Upload mixed numeric/categorical data
2. Apply One-Hot Encoding for categories
3. Apply Standardization for scaling
4. Apply Binning for feature creation
5. Save pipeline for reuse

## 🔒 Security Notes

- **File Uploads**: Validate file types and sizes in production
- **API Access**: Implement authentication for production use
- **Data Privacy**: Ensure compliance with data protection regulations
- **Secret Management**: Use environment variables for sensitive config

## 📈 Performance Tips

1. **For Large Datasets**:
   - Use dimensionality reduction first
   - Apply transformations in sequence (pipeline)
   - Consider batch processing

2. **For Slow Transformations**:
   - t-SNE and UMAP are slower on large datasets
   - Reduce n_iter for t-SNE if needed
   - Use UMAP for better scalability

3. **Memory Optimization**:
   - Work with numeric data types (int32 vs int64)
   - Delete intermediate DataFrames
   - Use sparse formats for text

## 🤝 Contributing

To add new transformations:

1. **Create a new class** in `backend/transformations.py`:
```python
class MyTransform(TransformationPipeline):
    def transform(self, data: pd.DataFrame, param: int) -> Tuple[pd.DataFrame, Dict]:
        # Implementation
        return result_df, metadata
```

2. **Add API endpoint** in `backend/app.py`:
```python
elif transformation_type == 'My Transform':
    transformer = MyTransform()
    transformed_df, metadata = transformer.transform(current_dataframe, param=params['param'])
```

3. **Add UI controls** in `frontend/app.py`:
```python
elif selected_method == 'My Transform':
    param = st.slider("Parameter", 1, 100, 50)
    params['param'] = param
```

4. **Update categories** in `transformations.py`:
```python
'Category Name': ['My Transform', ...]
```

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [scikit-learn Guide](https://scikit-learn.org/)
- [pandas Documentation](https://pandas.pydata.org/)
- [Plotly Reference](https://plotly.com/python/)

## 📄 License

This project is provided as-is for educational and commercial use.

## 🎯 Roadmap

**Future Enhancements**:
- [ ] Advanced visualizations (heatmaps, correlation matrices)
- [ ] Real-time data streaming support
- [ ] GPU acceleration for deep learning models
- [ ] Advanced outlier visualization
- [ ] A/B testing for transformations
- [ ] Data quality report generation
- [ ] Integration with popular databases
- [ ] Cloud deployment support (AWS, GCP, Azure)

## 📞 Support

For issues, questions, or feature requests:
1. Check the Troubleshooting section
2. Review API documentation at http://localhost:8000/docs
3. Check transformation parameters and data compatibility

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Created with**: Python, FastAPI, Streamlit
