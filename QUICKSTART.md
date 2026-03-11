# QUICKSTART Guide for applydf

Get started with applydf in 5 minutes!

## Prerequisites

- Python 3.8 or higher installed
- pip package manager
- Terminal/Command Prompt

## Step 1: Setup (2 minutes)

### Windows PowerShell
```powershell
# Navigate to project
cd "C:\Users\DELL\Documents\PYTHON 2025\2026-applydf"

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data (one-time)
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')"
```

### macOS/Linux
```bash
cd 2026-applydf
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet')"
```

## Step 2: Start Backend (1 minute)

**Open Terminal 1:**
```bash
cd backend
python -m uvicorn app:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://0.0.0.0:8000
Press CTRL+C to quit
```

✅ Backend is ready! Visit http://localhost:8000/docs to explore API.

## Step 3: Start Frontend (1 minute)

**Open Terminal 2 (in project root):**
```bash
cd frontend
streamlit run app.py
```

You should see:
```
  Local URL: http://localhost:8501
  Network URL: http://XXX.XXX.X.XXX:8501
```

✅ Frontend is ready! Browser will open automatically.

## Step 4: Use the App (1 minute)

1. **Upload Sample Data**
   - Click "Upload a file" in sidebar
   - Choose a CSV or Excel file
   - Click "📤 Upload & Parse"

2. **Apply a Transformation**
   - Select "Dimensionality Reduction & Structure" tab
   - Choose "PCA"
   - Set components to 2
   - Click "▶️ Apply PCA"

3. **Download Results**
   - Click "📥 Download as CSV"
   - File downloads automatically

4. **Save Pipeline**
   - Enter pipeline name
   - Click "💾 Save Pipeline"
   - Reuse anytime!

## Common Commands

### Stop Backend
```
Press Ctrl+C in Terminal 1
```

### Stop Frontend
```
Press Ctrl+C in Terminal 2
```

### Reset Virtual Environment
```bash
# Deactivate
deactivate

# Remove venv
rm -r venv  # macOS/Linux
rmdir /s venv  # Windows

# Recreate and reinstall
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### View API Documentation
Open http://localhost:8000/docs in browser

### View Available Transformations
```bash
curl http://localhost:8000/categories
```

## Sample Data Files

### CSV Example
```csv
feature1,feature2,feature3,category
1.5,2.3,3.1,A
2.1,1.8,2.5,B
1.9,2.2,3.0,A
3.2,1.5,2.8,C
```

### JSON Example
```json
[
  {"text": "Hello world", "sentiment": "positive"},
  {"text": "This is bad", "sentiment": "negative"}
]
```

## Troubleshooting Quick Fixes

### Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # macOS/Linux

# Kill process (Windows)
taskkill /PID <PID> /F
```

### Module Not Found Error
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Connection Refused
- Check backend is running on port 8000
- Check frontend API URL: `API_BASE_URL = "http://localhost:8000"`
- Ensure no firewall blocks connection

### Slow First Run
- First-time transformer model download is normal (~100MB)
- Subsequent runs will be instant
- Models cached in `.cache/huggingface/`

## Next Steps

1. **Explore Transformations**: Try different algorithms
2. **Read README.md**: Full documentation
3. **Check API Docs**: http://localhost:8000/docs
4. **Create Pipelines**: Save and reuse transformation sequences

## Key Features Checklist

- [ ] Upload data file
- [ ] View data preview
- [ ] Apply PCA transformation
- [ ] Download results
- [ ] Save transformation pipeline
- [ ] Apply text normalization
- [ ] Try dimensionality reduction
- [ ] Export as multiple formats

## Performance Tips

- **Large Files**: Apply dimensionality reduction first
- **Text Data**: Use TF-IDF instead of Transformer embeddings for speed
- **Memory Issues**: Process in smaller batches
- **Slow Visualization**: Reduce dataset size before t-SNE

## Video Walkthrough (If Available)

1. Project intro and setup
2. Uploading data
3. Applying transformations
4. Downloading results
5. Using pipelines

## Support Resources

| Need | Resource |
|------|----------|
| API Help | http://localhost:8000/docs |
| Full Docs | README.md |
| Code Questions | Check transformations.py comments |
| Issues | Review Troubleshooting in README |

## Common Workflows

### Workflow 1: Quick Visualization (3 min)
```
Upload CSV → Select PCA → Set components=2 → Download CSV
```

### Workflow 2: Text Analysis (5 min)
```
Upload CSV with text → Apply Text Normalization → Apply TF-IDF → Download
```

### Workflow 3: Data Cleaning (5 min)
```
Upload data → KNN Imputation → Deduplication → Outlier Detection → Download
```

### Workflow 4: Feature Engineering (8 min)
```
Upload mixed data → One-Hot Encoding → Standardization → Binning → Download
```

---

**Ready to transform data?** Open http://localhost:8501 and start!

For detailed documentation, see [README.md](README.md)
