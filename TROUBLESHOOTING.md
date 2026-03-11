# TROUBLESHOOTING Guide for applydf

Comprehensive troubleshooting for common issues.

## Installation Issues

### Issue: "Module not found" on pip install

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement ...
```

**Solutions:**
1. Update pip first:
```bash
pip install --upgrade pip
```

2. Install packages one by one to identify the problematic one:
```bash
pip install fastapi
pip install uvicorn
# ... etc
```

3. For torch issues (common on Windows), try:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue: Virtual environment not activating

**Symptoms:**
```
Command not recognized or (venv) doesn't appear in terminal
```

**Solutions:**

**Windows PowerShell:**
```powershell
# If you get an execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate:
venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Issue: NLTK data download fails

**Symptoms:**
```
LookupError: Resource punkt not found
```

**Solutions:**
```python
# Method 1: Download via Python
python -c "import nltk; nltk.download('punkt'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"

# Method 2: Download via interactive shell
python
>>> import nltk
>>> nltk.download('punkt')
>>> exit()

# Method 3: Set NLTK data path
export NLTK_DATA=~/nltk_data  # macOS/Linux
set NLTK_DATA=%USERPROFILE%\nltk_data  # Windows
```

---

## Backend Issues

### Issue: "Address already in use" on port 8000

**Symptoms:**
```
OSError: [WinError 10048] Only one usage of each socket address (protocol/IP/port) is normally permitted
```

**Solutions:**

**Windows:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or use a different port
python -m uvicorn app:app --port 8001
```

**macOS/Linux:**
```bash
# Find process
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
python -m uvicorn app:app --port 8001
```

### Issue: Backend not responding / Connection refuses

**Symptoms:**
```
ConnectionRefusedError: [Errno 111] Connection refused
or
Could not connect to backend message in Streamlit
```

**Solutions:**
1. Check backend is running:
```bash
# Terminal should show:
# Uvicorn running on http://0.0.0.0:8000
```

2. Check URL is correct:
```python
# In frontend/app.py
API_BASE_URL = "http://localhost:8000"  # Should match backend port
```

3. Check firewall isn't blocking:
   - Windows Defender: Allow Python.exe through firewall
   - macOS: System Preferences → Security & Privacy → Firewall

4. Check backend logs for errors:
   - Look for error messages in terminal where backend is running
   - Common errors: Import errors, missing dependencies

### Issue: "ModuleNotFoundError" when running backend

**Symptoms:**
```
ModuleNotFoundError: No module named 'transformations'
```

**Solutions:**
1. Ensure you're in the correct directory:
```bash
cd backend
python -m uvicorn app:app --reload
```

2. Or run from project root with:
```bash
python -m uvicorn backend.app:app --reload
```

3. Check PYTHONPATH:
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/2026-applydf"  # macOS/Linux
set PYTHONPATH=%PYTHONPATH%;C:\path\to\2026-applydf  # Windows
```

### Issue: Transformer model download is slow or stuck

**Symptoms:**
- Freezes at "Applying Transformer Embeddings"
- Takes 10+ minutes on first run
- Network timeout errors

**Solutions:**
1. Models are cached after first download:
   - First run: 5-10 minutes (normal, downloading ~100MB models)
   - Subsequent runs: Instant

2. Check internet connection:
   - Ensure stable internet (models hosted on Hugging Face)
   - Try with smaller model:
     ```python
     # In frontend, select:
     'sentence-transformers/all-MiniLM-L6-v2'  # Smallest, ~27MB
     ```

3. Pre-download models:
   ```python
   from transformers import AutoTokenizer, AutoModel
   
   model_name = 'sentence-transformers/all-MiniLM-L6-v2'
   tokenizer = AutoTokenizer.from_pretrained(model_name)
   model = AutoModel.from_pretrained(model_name)
   ```

4. Increase timeout in frontend:
   ```python
   # In frontend/app.py
   with st.spinner("This may take a few minutes on first run..."):
       # Apply transformation
   ```

### Issue: Out of Memory (OOM) error

**Symptoms:**
```
MemoryError or
CUDA out of memory (if using GPU)
```

**Solutions:**
1. Reduce dataset size:
   ```python
   # Sample dataset before uploading
   df = pd.read_csv('large_file.csv')
   df.sample(n=10000).to_csv('sample.csv', index=False)
   ```

2. Apply dimensionality reduction first:
   - Upload data
   - Apply PCA to reduce features
   - Then apply other transformations

3. Use lighter algorithms:
   - Replace Transformer Embeddings with TF-IDF
   - Use SVD instead of t-SNE (O(n²) memory)
   - Skip UMAP for very large datasets

4. Increase available memory:
   - Close other applications
   - Restart system
   - Use batch processing

---

## Frontend Issues

### Issue: Streamlit won't start

**Symptoms:**
```
ModuleNotFoundError: No module named 'streamlit'
or
Address already in use (port 8501)
```

**Solutions:**
1. Install Streamlit:
```bash
pip install streamlit
```

2. Check you're using the same virtual environment:
```bash
# Ensure venv is activated
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

streamlit run app.py
```

3. Use different port:
```bash
streamlit run app.py --server.port 8502
```

### Issue: "No data uploaded" message

**Symptoms:**
- File upload button appears but nothing happens
- Can't see data preview

**Solutions:**
1. Ensure backend is running (see Backend Issues)

2. Check file is correct format:
   - Supported: CSV, Excel (.xlsx, .xls), JSON, Parquet
   - Not supported: .txt, .xml, .sql, etc.

3. Check file size:
   - Max 100MB by default (increase in config.py)
   - Large files may timeout

4. Check file content:
   - File should have data rows
   - Headers should be in first row
   - Avoid special characters in column names

### Issue: Transformation dropdown/buttons not appearing

**Symptoms:**
- Can't see transformation category tabs
- Buttons appear but don't work

**Solutions:**
1. Refresh page:
   - Press Ctrl+R or Cmd+R
   - Or use Streamlit "Rerun" button

2. Check browser compatibility:
   - Recommended: Chrome, Firefox, Safari
   - Not supported: Internet Explorer

3. Clear browser cache:
   - Chrome: Ctrl+Shift+Delete
   - Firefox: Ctrl+Shift+Delete
   - Safari: Develop → Empty Web Caches

4. Check console for JavaScript errors:
   - Press F12 to open Developer Tools
   - Check Console tab for errors
   - Report error with full message

### Issue: Download button doesn't work

**Symptoms:**
- Click download but nothing happens
- No file appears in downloads folder

**Solutions:**
1. Check browser settings:
   - Allow downloads from localhost
   - Check pop-up blocker (may have blocked download)

2. Check backend can export:
   - Verify transformation was successful
   - Check "📊 Data Preview" shows data

3. Increase timeout:
   - Large files may time out
   - Use CSV for faster download (less overhead than Parquet)

4. Try different download format:
   - If CSV fails, try Excel
   - If Excel fails, try Parquet
   - If all fail, problem is in backend

---

## Data Issues

### Issue: "No numeric columns found"

**Symptoms:**
- Error when applying PCA, Standardization, etc.
- Message: "No numeric columns found"

**Solutions:**
1. Check data types in "Data Types" tab
   - Object columns are treated as text
   - Need at least one numeric column

2. Convert categorical to numeric:
   - Use One-Hot Encoding for categories
   - Then apply numeric transforms

3. Ensure CSV headers are correct:
   - First row should be column names
   - Not data values

### Issue: "No text columns found"

**Symptoms:**
- Error when applying TF-IDF, Word2Vec, etc.
- Need to select text column but none available

**Solutions:**
1. Check column types:
   - Text columns should be "object" type
   - Numeric data can't be used for text transforms

2. If data looks like text:
   - It may be stored as numbers
   - Try converting: `df['col'] = df['col'].astype(str)`

3. Ensure no empty columns:
   - Text transforms need non-empty text values
   - Use text normalization to clean first

### Issue: Missing values cause transformation to fail

**Symptoms:**
- Transformation works on preview but fails on full data
- Error mentions NaN or missing values

**Solutions:**
1. Apply KNN Imputation first:
   - Handles missing values automatically
   - Doesn't remove data rows

2. Drop missing values:
   - Use Deduplication (has missing value handling)
   - Manually remove in CSV before upload

3. Fill with default:
   ```python
   df.fillna(method='ffill')  # Forward fill
   df.fillna(0)  # Fill with 0
   df.fillna(df.mean())  # Fill with mean
   ```

### Issue: Outliers affect transformation results

**Symptoms:**
- Some data points very different from others
- Visualization shows extreme points
- Scaling doesn't work well

**Solutions:**
1. Apply Outlier Detection:
   - Use "Isolation Forest Outlier Detection"
   - Set contamination to expected outlier %

2. Apply before scaling:
   ```
   Upload → Outlier Detection → Standardization → Other transforms
   ```

3. Manual outlier removal:
   - Use IQR method
   - Remove points beyond Q1 - 1.5*IQR to Q3 + 1.5*IQR

---

## Performance Issues

### Issue: Transformation very slow (5+ minutes)

**Symptoms:**
- Spinner appears for long time
- Backend seems to hang
- Browser shows "Loading"

**Solutions:**
1. Check system resources:
   - Open Task Manager / Activity Monitor
   - Check CPU and Memory usage
   - Close other heavy applications

2. Reduce dataset:
   - Use smaller sample first (test with 1000 rows)
   - Confirm transformation works
   - Then apply to full dataset

3. Use faster algorithms:
   ```
   t-SNE (slow) → Use UMAP instead
   Transformer Embeddings (slow) → Use Word2Vec or TF-IDF
   ```

4. Increase backend timeout:
   ```python
   # In frontend/app.py
   TIMEOUT = 600  # 10 minutes instead of default
   ```

5. Check backend logs:
   - Look in terminal where backend runs
   - May show what's taking time
   - Consider GPU acceleration (if available)

### Issue: Visualization doesn't render / shows blank

**Symptoms:**
- Interactive plot area appears empty
- No charts showing after transformation

**Solutions:**
1. Check data was transformed:
   - Look at "Data Preview" tab
   - Should show transformed columns

2. Clear Streamlit cache:
   - Sidebar: "Always rerun" option
   - Or restart: `streamlit run app.py`

3. Check browser console:
   - F12 → Console tab
   - Look for JavaScript errors from Plotly

4. Try simpler visualization:
   - Basic bar chart instead of complex plot
   - Download data and plot externally

---

## API / Integration Issues

### Issue: API returns 400 or 422 error

**Symptoms:**
```
Bad Request or Unprocessable Entity
```

**Solutions:**
1. Check request format:
   - Ensure JSON is valid: `python -m json.tool file.json`
   - All required parameters included
   - Correct parameter types (int, str, list, etc.)

2. Check data format:
   - CSV should be RFC 4180 compliant
   - Excel should be .xlsx or .xls
   - JSON should be array of objects

3. See error message:
   - API returns detailed error
   - Check "detail" field for specifics

### Issue: API times out (500 error)

**Symptoms:**
```
500 Internal Server Error or Timeout
```

**Solutions:**
1. Check backend logs:
   - Terminal where backend is running
   - Should show error traceback
   - Common: Out of memory, model download

2. Restart backend:
   ```bash
   # Kill and restart
   Ctrl+C in backend terminal
   python -m uvicorn app:app --reload
   ```

3. Check resource usage:
   - Memory: Close other applications
   - Disk: Ensure disk not full
   - Network: Check internet connection

### Issue: File upload fails

**Symptoms:**
```
Error uploading file or
File upload appears in logs but doesn't appear in app
```

**Solutions:**
1. Check file validity:
   ```bash
   python -m pandas.io.common file.csv  # Test CSV
   ```

2. Check file size:
   - Default max: 100MB (in config.py)
   - Increase if needed: `MAX_FILE_SIZE_MB = 500`

3. Check permissions:
   - File should be readable by Python process
   - Try saving to different location

---

## Browser / Client Issues

### Issue: Streamlit page doesn't load / shows blank

**Symptoms:**
- Navigate to localhost:8501 but see nothing
- Or "Connecting..." spinner never completes

**Solutions:**
1. Check Streamlit is running:
   - Terminal showing "Streamlit running on..."
   - Look for error messages

2. Clear browser cache:
   - Ctrl+Shift+Delete (Windows/Linux)
   - Cmd+Shift+Delete (macOS)
   - Try incognito/private mode

3. Check localhost resolution:
   - Can you ping localhost?
   - Try `http://127.0.0.1:8501`
   - Instead of `http://localhost:8501`

4. Restart Streamlit:
   ```bash
   Ctrl+C in frontend terminal
   streamlit run app.py
   ```

### Issue: "Forbidden" or "Not allowed" message

**Symptoms:**
- CORS error in browser console
- "Access-Control-Allow-Origin" error

**Solutions:**
1. CORS is already configured:
   - Should allow `http://localhost:*`
   - If running on different machine, update:
   ```python
   # In backend/app.py
   CORS_ORIGINS = ["http://your-ip:8501"]
   ```

2. Check if backend is different machine:
   - Update frontend API URL:
   ```python
   API_BASE_URL = "http://your-backend-ip:8000"
   ```

---

## Data Quality Issues

### Issue: "All values are NaN" or similar error

**Symptoms:**
- Transformation fails silently
- Result has only null/empty values

**Solutions:**
1. Check input data:
   - Use "Data Preview" → "Data Preview" tab
   - Look for appropriate data types
   - Visualize with preview

2. Ensure correct column selection:
   - Text transforms need text columns
   - Numeric transforms need numeric columns
   - Can't mix types for same transformation

3. Check data encoding:
   - CSV should be UTF-8
   - Excel should be .xlsx (not .xls if very old)
   - JSON should be valid UTF-8

---

## Memory / Storage Issues

### Issue: Large temporary files accumulating

**Symptoms:**
- Disk usage growing
- `temp_files/` folder getting huge
- "Disk full" errors

**Solutions:**
1. Clean up temp files manually:
```bash
rm -rf temp_files/*  # macOS/Linux
rmdir /s temp_files  # Windows
```

2. Set automatic cleanup:
```python
# In backend/app.py startup
from utils import FileHandler
cleanup_count = FileHandler.cleanup_temp_files(max_age_hours=24)
```

3. Monitor disk space:
```bash
# macOS/Linux
du -sh temp_files/

# Windows
dir temp_files
```

---

## Still Having Issues?

### Debugging Steps

1. **Check logs carefully**:
   - Backend terminal for errors
   - Browser console (F12) for client errors
   - Screenshot error message

2. **Test components individually**:
   - Can you connect to API? Visit http://localhost:8000/docs
   - Can you see API categories? Visit http://localhost:8000/categories
   - Can you render Streamlit? Visit http://localhost:8501

3. **Try simple test cases**:
   - Start with small CSV file
   - Apply simple transformation (PCA)
   - Download result

4. **Check versions**:
   ```bash
   python --version  # Should be 3.8+
   pip list | grep -E "fastapi|streamlit|pandas"  # Check installed versions
   ```

5. **Create minimal reproducer**:
   - Small CSV file
   - Single transformation
   - Note exact error message
   - Try to replicate issue

### Getting Help

1. **Check README.md** for comprehensive documentation
2. **Check QUICKSTART.md** for basic setup
3. **Check API docs** at http://localhost:8000/docs
4. **Review transformation parameters** in code comments
5. **Check examples.py** for usage patterns

### Common Commands

```bash
# Check Python version
python --version

# List installed packages
pip list

# Check if port is in use
# Windows
netstat -ano | findstr :8000
# macOS/Linux
lsof -i :8000

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -name "*.pyc" -delete

# Check API health
curl http://localhost:8000/

# Test file upload
curl -X POST http://localhost:8000/upload -F "file=@data.csv"
```

---

**Last Updated**: 2024
**Version**: 1.0.0
