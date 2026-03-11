# 🚀 applydf v2.0 - Collaborative Data Platform

**Transform applydf into a shareable data workspace with collaboration features!**

## What's New in v2.0

### 🔌 Connect to External Data Sources
- CSV URLs
- PostgreSQL & MySQL databases
- AWS S3
- Google Sheets
- SQLite
- REST APIs (JSON)

### 💼 User Workspace
- Manage personal datasets
- View shared resources
- Track data quality scores
- Download and clone pipelines

### 🌐 Public Dataset Playground
- Browse community datasets
- Clone transformation pipelines
- Share your work publicly
- Collaborate with others

### 📄 Shareable Reports
- Auto-generate comprehensive analysis
- Beautiful visualizations
- Before/after comparisons
- Exportable insights

### 🔗 Sharing System
- Public links
- Private sharing
- Team access control
- Permission levels (viewer/editor/owner)

---

## Quick Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements-collaborative.txt
```

### 2. Initialize System

```bash
cd backend
python setup_collaborative.py
```

This creates:
- Database tables (applydf.db)
- Demo user account
- Sample public datasets

### 3. Start Servers

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app_collaborative.py
```

### 4. Access Application

Open browser: **http://localhost:8501**

Demo credentials:
- Username: `demo`
- Password: `demo123`

---

## Architecture

```
applydf/
├── backend/
│   ├── app.py                     # Main API (enhanced)
│   ├── data_source_connector.py   # NEW: External sources
│   ├── database_models.py         # NEW: SQLAlchemy models
│   ├── report_generator.py        # NEW: Report generation
│   ├── dataset_registry.py        # NEW: Dataset management
│   ├── sharing_manager.py         # NEW: Sharing system
│   ├── user_manager.py            # NEW: Authentication
│   ├── setup_collaborative.py     # NEW: Setup script
│   └── applydf.db                 # SQLite database (auto-created)
│
├── frontend/
│   ├── app.py                     # Original UI
│   └── app_collaborative.py       # NEW: Multi-page UI
│
└── COLLABORATIVE_FEATURES.md      # Full documentation

```

---

## Usage Examples

### Connect to PostgreSQL

```python
import requests

response = requests.post('http://localhost:8000/connect-source', json={
    "source_type": "postgres",
    "config": {
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "username": "user",
        "password": "pass",
        "table_name": "customers"
    }
})

data = response.json()
print(f"Loaded {data['shape'][0]} rows")
```

### Register Dataset

```python
response = requests.post('http://localhost:8000/datasets/register', json={
    "dataset_name": "Sales Q1 2026",
    "description": "Quarterly sales analysis",
    "visibility": "public"
})

dataset = response.json()
print(f"Dataset ID: {dataset['dataset_id']}")
```

### Generate Report

```python
response = requests.post('http://localhost:8000/reports/generate', json={
    "report_name": "Monthly Analytics",
    "description": "Complete dataset analysis"
})

report = response.json()
print(f"Report URL: /reports/{report['report_id']}")
```

### Create Share Link

```python
response = requests.post('http://localhost:8000/share/create', json={
    "resource_type": "dataset",
    "resource_id": 1,
    "is_public_link": True
})

share = response.json()
print(f"Share link: {share['share_url']}")
```

---

## API Endpoints

### Data Sources
- `POST /connect-source` - Connect to external source

### Authentication
- `POST /auth/register` - Register user
- `POST /auth/login` - Login
- `GET /auth/demo-login` - Demo user
- `GET /auth/current-user` - Current session

### Datasets
- `POST /datasets/register` - Register dataset
- `GET /datasets/public` - Browse public datasets
- `GET /datasets/{id}` - Get dataset info
- `GET /datasets/{id}/load` - Load dataset
- `POST /datasets/{id}/clone-pipeline` - Clone pipeline
- `GET /datasets/search` - Search datasets
- `GET /workspace/datasets` - User's datasets

### Reports
- `POST /reports/generate` - Generate report
- `GET /reports/{id}` - View report

### Sharing
- `POST /share/create` - Create share link
- `GET /share/{id}` - Access shared resource
- `GET /workspace/shared` - Shared with me

---

## Frontend Pages

### 📊 Data Studio
Upload files and apply transformations (original features)

### 🔌 Data Sources
- Select source type (CSV URL, Database, S3, etc.)
- Enter connection details
- Load data directly

### 💼 Workspace
- **My Datasets**: View and manage your datasets
- **Shared With Me**: Access shared resources
- **Register Dataset**: Save current data to workspace

### 🌐 Public Datasets
- Browse community datasets
- Load any dataset
- Clone transformation pipelines
- See quality scores and metadata

### 📄 Reports
- **Generate Report**: Create comprehensive analysis
- **View Last Report**: See visualizations and insights

---

## Database Schema

### Tables Created

- **users** - User accounts and authentication
- **datasets** - Dataset metadata and files
- **reports** - Generated analysis reports
- **pipelines** - Reusable transformation pipelines
- **shares** - Sharing permissions and links
- **activities** - Audit log

See `COLLABORATIVE_FEATURES.md` for complete schema.

---

## Configuration

### Optional Dependencies

For better performance with large datasets:

```bash
pip install polars duckdb
```

For cloud/external sources:

```bash
pip install boto3              # AWS S3
pip install gspread google-auth # Google Sheets
pip install pymysql            # MySQL
pip install psycopg2-binary    # PostgreSQL
```

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///applydf.db

# AWS (for S3)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Google Sheets
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

---

## Features Comparison

| Feature | v1.0 (Original) | v2.0 (Collaborative) |
|---------|----------------|---------------------|
| File Upload | ✅ | ✅ |
| Transformations | ✅ | ✅ |
| Auto-Clean | ✅ | ✅ |
| Data Sources | ❌ | ✅ (7 types) |
| User Accounts | ❌ | ✅ |
| Dataset Registry | ❌ | ✅ |
| Public Sharing | ❌ | ✅ |
| Reports | ❌ | ✅ |
| Workspace | ❌ | ✅ |
| Collaboration | ❌ | ✅ |

---

## Security Notes

### Development Mode (Current)
- Demo user auto-login
- SQLite database
- No HTTPS
- Simple password hashing

### Production Recommendations
- Implement JWT tokens
- Use PostgreSQL/MySQL
- Add HTTPS/SSL
- Add rate limiting
- Implement CSRF protection
- Use environment variables for secrets
- Add input validation

---

## Troubleshooting

### Database not found
```bash
cd backend
python setup_collaborative.py
```

### Cannot connect to data source
- Check firewall settings
- Verify credentials
- Install required connector: `pip install psycopg2-binary` (example)

### Frontend not loading changes
- Hard refresh browser (Ctrl+F5)
- Clear st.cache
- Restart Streamlit

---

## Development

### Add New Data Source

1. Edit `backend/data_source_connector.py`
2. Add new `load_xxx()` method
3. Register in `backend/app.py` endpoint
4. Add UI in `frontend/app_collaborative.py`

### Extend Database Schema

1. Update `backend/database_models.py`
2. Delete `applydf.db`
3. Run `python setup_collaborative.py`

---

## Documentation

- **COLLABORATIVE_FEATURES.md** - Complete feature documentation
- **API Reference** - http://localhost:8000/docs (FastAPI auto-docs)
- **Architecture** - See this README

---

## Roadmap

**Phase 1 (Completed)** ✅
- External data sources
- User management
- Dataset registry
- Sharing system
- Reports

**Phase 2 (Planned)**
- Real-time collaboration
- Advanced analytics dashboard
- ML model deployment
- Data versioning
- Scheduled refreshes
- Email notifications
- Webhooks

---

## Support

For questions or issues:
1. Check `COLLABORATIVE_FEATURES.md`
2. Review API docs at `/docs`
3. Check terminal logs
4. Verify dependencies installed

---

## License

MIT License - Extend and customize freely!

---

## Credits

Built with:
- **FastAPI** - Backend API
- **Streamlit** - Frontend UI
- **SQLAlchemy** - Database ORM
- **Plotly** - Visualizations
- **pandas** - Data processing

---

**Enjoy your collaborative data workspace! 🚀**
