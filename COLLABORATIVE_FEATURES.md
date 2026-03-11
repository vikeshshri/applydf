# applydf Collaborative Features Documentation

## Overview

applydf has been extended from a data transformation tool into a **collaborative data workspace platform** with the following new capabilities:

- 🔌 **Connect to External Data Sources** (databases, S3, Google Sheets, APIs)
- 💼 **User Workspace** (manage datasets, view shared resources)
- 🌐 **Public Dataset Playground** (share and discover datasets)
- 📄 **Shareable Reports** (generate comprehensive analysis reports)
- 🔗 **Sharing System** (share datasets, reports, and pipelines)
- 👥 **User Management** (authentication and permissions)

---

## Architecture

### Backend Modules

All new modules are located in `backend/`:

1. **data_source_connector.py** - Connect to external data sources
2. **database_models.py** - SQLAlchemy models for persistence
3. **report_generator.py** - Generate shareable reports with visualizations
4. **dataset_registry.py** - Manage dataset metadata and discovery
5. **sharing_manager.py** - Handle sharing and permissions
6. **user_manager.py** - User authentication and management

### Frontend

- **app.py** - Original Streamlit frontend (existing features)
- **app_collaborative.py** - NEW enhanced multi-page UI with all collaborative features

### Database

- **applydf.db** (SQLite) - Automatically created on first run
- Tables: `users`, `datasets`, `reports`, `pipelines`, `shares`, `activities`

---

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install sqlalchemy boto3 gspread google-auth pymysql psycopg2-binary
```

### 2. Initialize Database

The database is automatically initialized on first backend startup.

Alternatively, run manually:

```bash
cd backend
python database_models.py
```

### 3. Start Backend

```bash
cd backend
python app.py
```

Backend API: `http://localhost:8000`

### 4. Start Frontend

**Option A: Original Frontend**
```bash
cd frontend
streamlit run app.py
```

**Option B: Collaborative Frontend (NEW)**
```bash
cd frontend
streamlit run app_collaborative.py
```

Frontend UI: `http://localhost:8501`

---

## Features Guide

### 🔌 1. Data Source Connectivity

Connect to multiple data sources beyond file uploads.

#### Supported Sources

- **CSV URL**: Load CSV from any public URL
- **PostgreSQL**: Connect to PostgreSQL databases
- **MySQL**: Connect to MySQL databases
- **AWS S3**: Load files from S3 buckets
- **Google Sheets**: Import from Google Sheets
- **SQLite**: Connect to local SQLite databases
- **API (JSON)**: Fetch JSON data from REST APIs

#### API Endpoint

```http
POST /connect-source
Content-Type: application/json

{
  "source_type": "csv_url",
  "config": {
    "url": "https://example.com/data.csv"
  }
}
```

#### Example: PostgreSQL

```python
import requests

result = requests.post('http://localhost:8000/connect-source', json={
    "source_type": "postgres",
    "config": {
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "username": "user",
        "password": "password",
        "table_name": "customers"
    }
}).json()

print(f"Loaded {result['shape'][0]} rows")
```

#### Frontend Usage

1. Navigate to **🔌 Data Sources** page
2. Select source type
3. Enter connection details
4. Click **Connect**

---

### 💼 2. User Workspace

Manage your datasets and view shared resources.

#### Register a Dataset

After uploading or connecting to data, register it to your workspace:

```http
POST /datasets/register
{
  "dataset_name": "Customer Data 2026",
  "description": "Q1 customer analytics",
  "visibility": "private"  // or "public", "shared"
}
```

#### View Your Datasets

```http
GET /workspace/datasets
```

Returns list of all datasets owned by current user with metadata.

#### Frontend Usage

1. Upload/connect to data
2. Navigate to **💼 Workspace** > **Register Dataset** tab
3. Enter dataset name, description, visibility
4. Click **Register Dataset**

---

### 🌐 3. Public Dataset Playground

Discover and clone public datasets from other users.

#### List Public Datasets

```http
GET /datasets/public?limit=50&offset=0
```

#### Load Public Dataset

```http
GET /datasets/{dataset_id}/load
```

Loads the dataset as the current working dataframe.

#### Clone Pipeline

Clone the transformation pipeline from a public dataset:

```http
POST /datasets/{dataset_id}/clone-pipeline
```

Returns the pipeline configuration that can be applied to your own data.

#### Frontend Usage

1. Navigate to **🌐 Public Datasets**
2. Browse available datasets
3. Click **Load Dataset** to work with it
4. Click **Clone Pipeline** to copy transformations

---

### 📄 4. Shareable Reports

Generate comprehensive dataset analysis reports with visualizations.

#### Generate Report

```http
POST /reports/generate
{
  "report_name": "Q1 Sales Analysis",
  "description": "Comprehensive sales data analysis"
}
```

Returns report with:
- Dataset summary (rows, columns, types)
- Data quality score
- Missing value analysis
- Visualizations (distributions, correlations, etc.)
- Before/after comparison (if transformations applied)
- Download link for cleaned dataset

#### Report Structure

```json
{
  "report_id": "abc123def4",
  "report_name": "Q1 Sales Analysis",
  "dataset_summary": {
    "shape": {"rows": 10000, "columns": 25},
    "missing_values": {...},
    "duplicates": {...}
  },
  "visualizations": [
    {
      "type": "histogram",
      "title": "Revenue Distribution",
      "config": "{plotly_json}"
    }
  ],
  "data_quality_score": 87.5,
  "before_after_comparison": {...}
}
```

#### Frontend Usage

1. Load/transform dataset
2. Navigate to **📄 Reports** > **Generate Report**
3. Enter report name and description
4. Click **Generate Report**
5. View report in **View Last Report** tab

---

### 🔗 5. Sharing System

Share datasets, reports, and pipelines with others.

#### Create Share Link

```http
POST /share/create
{
  "resource_type": "dataset",  // or "report", "pipeline"
  "resource_id": 123,
  "access_level": "viewer",  // or "editor", "owner"
  "is_public_link": true,
  "expires_in_days": 30  // optional
}
```

Returns:
```json
{
  "success": true,
  "share_id": "xyz789abc",
  "share_url": "/share/xyz789abc"
}
```

#### Access Shared Resource

```http
GET /share/{share_id}?user_id=123
```

#### Permission Levels

- **viewer**: Read-only access
- **editor**: Can modify (for datasets/pipelines)
- **owner**: Full control

#### Sharing Options

1. **Public Link**: Anyone with link can access
2. **Private Share**: Share with specific user(s)
3. **Team Access**: Share with multiple team members (via user IDs)

---

### 👥 6. User Management

#### Register User

```http
POST /auth/register
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}
```

#### Login

```http
POST /auth/login
{
  "username": "john_doe",
  "password": "secure_password"
}
```

Returns user session token and profile.

#### Demo User

For testing, use the demo user:

```http
GET /auth/demo-login
```

Creates/returns demo user (username: `demo`, password: `demo123`)

---

## API Reference

### Complete Endpoint List

#### Core Data Operations
- `POST /upload` - Upload file
- `POST /connect-source` - Connect to external data source
- `GET /preview` - Preview current data
- `POST /transform` - Apply transformation
- `POST /auto-clean` - Auto-clean dataset
- `GET /download/{format}` - Download data

#### User Management
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/demo-login` - Demo user login
- `GET /auth/current-user` - Get current user

#### Dataset Management
- `POST /datasets/register` - Register dataset
- `GET /datasets/public` - List public datasets
- `GET /datasets/{id}` - Get dataset info
- `GET /datasets/{id}/load` - Load dataset
- `POST /datasets/{id}/clone-pipeline` - Clone pipeline
- `GET /datasets/search?q=query` - Search datasets
- `GET /workspace/datasets` - User's datasets

#### Reports
- `POST /reports/generate` - Generate report
- `GET /reports/{id}` - View report

#### Sharing
- `POST /share/create` - Create share link
- `GET /share/{id}` - Access shared resource
- `GET /workspace/shared` - Resources shared with user

---

## Database Schema

### Users Table
```sql
- id: INTEGER PRIMARY KEY
- username: VARCHAR(100) UNIQUE
- email: VARCHAR(255) UNIQUE
- password_hash: VARCHAR(255)
- full_name: VARCHAR(255)
- created_at: DATETIME
- is_active: BOOLEAN
```

### Datasets Table
```sql
- id: INTEGER PRIMARY KEY
- dataset_id: VARCHAR(50) UNIQUE
- dataset_name: VARCHAR(255)
- description: TEXT
- owner_id: INTEGER FOREIGN KEY
- source_type: VARCHAR(50)
- row_count: INTEGER
- column_count: INTEGER
- data_quality_score: FLOAT
- visibility: ENUM (private/public/shared)
- created_at: DATETIME
```

### Shares Table
```sql
- id: INTEGER PRIMARY KEY
- share_id: VARCHAR(50) UNIQUE
- resource_type: ENUM (dataset/report/pipeline)
- resource_id: INTEGER
- owner_id: INTEGER FOREIGN KEY
- shared_with_user_id: INTEGER FOREIGN KEY (NULL for public)
- access_level: ENUM (viewer/editor/owner)
- is_public_link: BOOLEAN
- access_count: INTEGER
- created_at: DATETIME
```

---

## Security Considerations

### Implemented
- ✅ Password hashing with PBKDF2-HMAC-SHA256
- ✅ Public/private visibility controls
- ✅ Share link access validation
- ✅ User authentication required for private resources

### Production Recommendations
- 🔐 Add JWT token-based authentication
- 🔐 Implement rate limiting
- 🔐 Add HTTPS/SSL
- 🔐 Sanitize database credentials in source configs
- 🔐 Add CSRF protection
- 🔐 Implement proper session management

---

## Performance Optimization

The system includes optional performance features:

### Large Dataset Handling

When datasets exceed 100k rows, the system automatically uses:
- **Polars** for faster DataFrame operations
- **DuckDB** for SQL-based analytics

Install for better performance:
```bash
pip install polars duckdb
```

### Caching

- Dataset files stored as Parquet (compressed, fast)
- Report visualizations cached in JSON
- Pipeline configurations stored for instant cloning

---

## Development Workflow

### 1. Local Development

```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: Frontend
cd frontend
streamlit run app_collaborative.py
```

### 2. Add New Data Source

Edit `backend/data_source_connector.py`:

```python
@staticmethod
def load_my_source(config: Dict[str, Any]) -> pd.DataFrame:
    """Load from my custom source."""
    # Your implementation
    return df
```

Register in `backend/app.py`:

```python
elif source_type == 'my_source':
    df = DataSourceConnector.load_my_source(config)
```

### 3. Database Migrations

Currently using SQLAlchemy auto-create. For production:

1. Use Alembic for migrations
2. Add migration scripts
3. Version control schema changes

---

## Troubleshooting

### Database Issues

**Problem**: Database not initialized
```
Solution: python backend/database_models.py
```

**Problem**: Table schema outdated
```
Solution: Delete applydf.db and restart backend
```

### Connection Issues

**Problem**: Cannot connect to PostgreSQL
```
Check: Firewall, credentials, pg_hba.conf settings
Install: pip install psycopg2-binary
```

**Problem**: Google Sheets authentication failed
```
Solution: Create service account, download JSON, set GOOGLE_APPLICATION_CREDENTIALS
```

### Frontend Issues

**Problem**: Page not updating after data operation
```
Solution: Click st.rerun() or refresh browser
```

---

## Examples

### Complete Workflow Example

```python
import requests

API = "http://localhost:8000"

# 1. Login as demo user
login = requests.get(f"{API}/auth/demo-login").json()
print(f"Logged in as: {login['username']}")

# 2. Connect to CSV URL
data = requests.post(f"{API}/connect-source", json={
    "source_type": "csv_url",
    "config": {"url": "https://example.com/sales.csv"}
}).json()
print(f"Loaded {data['shape'][0]} rows")

# 3. Auto-clean dataset
clean = requests.post(f"{API}/auto-clean").json()
print(f"Quality improved: {clean['before_score']} → {clean['after_score']}")

# 4. Register dataset
register = requests.post(f"{API}/datasets/register", json={
    "dataset_name": "Sales Data Q1",
    "description": "Cleaned sales data",
    "visibility": "public"
}).json()
dataset_id = register['dataset_id']
print(f"Dataset registered: {dataset_id}")

# 5. Generate report
report = requests.post(f"{API}/reports/generate", json={
    "report_name": "Q1 Sales Report",
    "description": "Comprehensive analysis"
}).json()
print(f"Report generated: {report['report_id']}")

# 6. Create public share link
share = requests.post(f"{API}/share/create", json={
    "resource_type": "dataset",
    "resource_id": 1,
    "is_public_link": True
}).json()
print(f"Share link: {share['share_url']}")
```

---

## Roadmap

### Planned Features
- [ ] Real-time collaboration (WebSocket)
- [ ] Advanced analytics dashboard
- [ ] ML model training and deployment
- [ ] Dataset versioning
- [ ] Scheduled data refreshes
- [ ] Email notifications
- [ ] API webhooks
- [ ] Data lineage tracking
- [ ] Advanced visualization builder

---

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review API docs: `http://localhost:8000/docs` (FastAPI auto-docs)
- Examine logs in terminal output

---

## License

MIT License - Feel free to extend and customize!
