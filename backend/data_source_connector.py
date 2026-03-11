"""
Data Source Connector Module
Connects to external data sources and returns pandas DataFrames.

Supported sources:
- CSV URL
- Google Sheets
- PostgreSQL
- MySQL
- AWS S3
- SQLite
- API Endpoints
"""

import pandas as pd
import io
import os
import importlib
import importlib.util
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Optional imports - handled gracefully if not installed
try:
    import sqlalchemy
    from sqlalchemy import create_engine
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    logger.warning("SQLAlchemy not available - database connections disabled")

HAS_BOTO3 = importlib.util.find_spec("boto3") is not None
if not HAS_BOTO3:
    logger.warning("boto3 not available - S3 connections disabled")

HAS_GSPREAD = (
    importlib.util.find_spec("gspread") is not None
    and importlib.util.find_spec("google.oauth2.service_account") is not None
)
if not HAS_GSPREAD:
    logger.warning("gspread/google-auth not available - Google Sheets connections disabled")


class DataSourceConnector:
    """Connects to various data sources and returns pandas DataFrames."""
    
    @staticmethod
    def load_csv_url(url: str, **kwargs) -> pd.DataFrame:
        """
        Load CSV from a public URL.
        
        Args:
            url: Public URL to CSV file
            **kwargs: Additional arguments passed to pd.read_csv
            
        Returns:
            pd.DataFrame
            
        Example:
            df = load_csv_url('https://example.com/data.csv')
        """
        try:
            logger.info(f"Loading CSV from URL: {url}")
            df = pd.read_csv(url, **kwargs)
            logger.info(f"Successfully loaded CSV: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV from URL: {str(e)}")
            raise ValueError(f"Failed to load CSV from URL: {str(e)}")
    
    
    @staticmethod
    def load_google_sheet(
        sheet_url: str, 
        credentials_json: Optional[str] = None,
        api_key: Optional[str] = None,
        sheet_name: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load data from Google Sheets.
        
        Args:
            sheet_url: Google Sheet URL or ID
            credentials_json: Path to service account JSON credentials
            sheet_name: Optional specific sheet name/index
            **kwargs: Additional arguments
            
        Returns:
            pd.DataFrame
            
        Example:
            df = load_google_sheet(
                'https://docs.google.com/spreadsheets/d/ABC123/edit',
                credentials_json='service_account.json'
            )
        """
        # API-key flow for public sheets
        if api_key:
            try:
                import requests

                # Extract sheet id from URL if provided as full link
                sheet_id = sheet_url
                if 'docs.google.com' in sheet_url:
                    marker = '/d/'
                    if marker in sheet_url:
                        tail = sheet_url.split(marker, 1)[1]
                        sheet_id = tail.split('/', 1)[0]

                value_range = sheet_name if sheet_name else 'Sheet1'
                endpoint = (
                    f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{value_range}"
                    f"?key={api_key}"
                )
                response = requests.get(endpoint, timeout=30)
                response.raise_for_status()
                payload = response.json()
                rows = payload.get('values', [])
                if not rows:
                    return pd.DataFrame()

                headers = rows[0]
                data_rows = rows[1:] if len(rows) > 1 else []
                return pd.DataFrame(data_rows, columns=headers)
            except Exception as e:
                logger.warning(f"Google Sheets API key flow failed, trying gspread fallback: {str(e)}")

        if not HAS_GSPREAD:
            raise ImportError(
                "gspread is required for Google Sheets. "
                "Install: pip install gspread google-auth"
            )
        
        try:
            logger.info(f"Connecting to Google Sheet: {sheet_url}")
            gspread = importlib.import_module("gspread")
            Credentials = importlib.import_module("google.oauth2.service_account").Credentials
            
            # Setup credentials
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            if credentials_json and os.path.exists(credentials_json):
                creds = Credentials.from_service_account_file(credentials_json, scopes=scopes)
            else:
                # Try default credentials
                creds = Credentials.from_service_account_file(
                    os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json'),
                    scopes=scopes
                )
            
            client = gspread.authorize(creds)
            
            # Open spreadsheet
            if 'docs.google.com' in sheet_url:
                sheet = client.open_by_url(sheet_url)
            else:
                sheet = client.open_by_key(sheet_url)
            
            # Get worksheet
            if sheet_name:
                worksheet = sheet.worksheet(sheet_name)
            else:
                worksheet = sheet.get_worksheet(0)  # First sheet
            
            # Convert to DataFrame
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            logger.info(f"Successfully loaded Google Sheet: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading Google Sheet: {str(e)}")
            raise ValueError(f"Failed to load Google Sheet: {str(e)}")
    
    
    @staticmethod
    def load_postgres_table(
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        table_name: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load data from PostgreSQL database.
        
        Args:
            host: Database host
            port: Database port (default: 5432)
            database: Database name
            username: Database username
            password: Database password
            table_name: Table name to load
            query: Custom SQL query (alternative to table_name)
            **kwargs: Additional arguments
            
        Returns:
            pd.DataFrame
            
        Example:
            df = load_postgres_table(
                host='localhost',
                port=5432,
                database='mydb',
                username='user',
                password='pass',
                table_name='customers'
            )
        """
        if not HAS_SQLALCHEMY:
            raise ImportError(
                "SQLAlchemy is required for database connections. "
                "Install: pip install sqlalchemy psycopg2-binary"
            )
        
        try:
            logger.info(f"Connecting to PostgreSQL: {host}:{port}/{database}")
            
            # Create connection string
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string)
            
            # Execute query or select table
            if query:
                df = pd.read_sql_query(query, engine)
            elif table_name:
                df = pd.read_sql_table(table_name, engine)
            else:
                raise ValueError("Either table_name or query must be provided")
            
            logger.info(f"Successfully loaded from PostgreSQL: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading from PostgreSQL: {str(e)}")
            raise ValueError(f"Failed to load from PostgreSQL: {str(e)}")
    
    
    @staticmethod
    def load_mysql_table(
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        table_name: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load data from MySQL database.
        
        Args:
            host: Database host
            port: Database port (default: 3306)
            database: Database name
            username: Database username
            password: Database password
            table_name: Table name to load
            query: Custom SQL query (alternative to table_name)
            **kwargs: Additional arguments
            
        Returns:
            pd.DataFrame
            
        Example:
            df = load_mysql_table(
                host='localhost',
                port=3306,
                database='mydb',
                username='user',
                password='pass',
                table_name='orders'
            )
        """
        if not HAS_SQLALCHEMY:
            raise ImportError(
                "SQLAlchemy is required for database connections. "
                "Install: pip install sqlalchemy pymysql"
            )
        
        try:
            logger.info(f"Connecting to MySQL: {host}:{port}/{database}")
            
            # Create connection string
            connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string)
            
            # Execute query or select table
            if query:
                df = pd.read_sql_query(query, engine)
            elif table_name:
                df = pd.read_sql_table(table_name, engine)
            else:
                raise ValueError("Either table_name or query must be provided")
            
            logger.info(f"Successfully loaded from MySQL: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading from MySQL: {str(e)}")
            raise ValueError(f"Failed to load from MySQL: {str(e)}")
    
    
    @staticmethod
    def load_s3_file(
        bucket_name: str,
        file_key: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = 'us-east-1',
        file_format: str = 'csv',
        **kwargs
    ) -> pd.DataFrame:
        """
        Load file from AWS S3.
        
        Args:
            bucket_name: S3 bucket name
            file_key: File key/path in bucket
            aws_access_key_id: AWS access key (or use env vars)
            aws_secret_access_key: AWS secret key (or use env vars)
            region_name: AWS region
            file_format: File format (csv, excel, parquet, json)
            **kwargs: Additional arguments for pandas reader
            
        Returns:
            pd.DataFrame
            
        Example:
            df = load_s3_file(
                bucket_name='my-bucket',
                file_key='data/customers.csv',
                aws_access_key_id='KEY',
                aws_secret_access_key='SECRET'
            )
        """
        if not HAS_BOTO3:
            raise ImportError(
                "boto3 is required for S3 connections. "
                "Install: pip install boto3"
            )
        
        try:
            logger.info(f"Connecting to S3: {bucket_name}/{file_key}")
            boto3 = importlib.import_module("boto3")
            
            # Create S3 client
            s3_kwargs = {'region_name': region_name}
            if aws_access_key_id and aws_secret_access_key:
                s3_kwargs['aws_access_key_id'] = aws_access_key_id
                s3_kwargs['aws_secret_access_key'] = aws_secret_access_key
            
            s3_client = boto3.client('s3', **s3_kwargs)
            
            # Download file
            response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            file_content = response['Body'].read()
            
            # Parse based on format
            if file_format == 'csv':
                df = pd.read_csv(io.BytesIO(file_content), **kwargs)
            elif file_format in ['xlsx', 'xls', 'excel']:
                df = pd.read_excel(io.BytesIO(file_content), **kwargs)
            elif file_format == 'parquet':
                df = pd.read_parquet(io.BytesIO(file_content), **kwargs)
            elif file_format == 'json':
                df = pd.read_json(io.BytesIO(file_content), **kwargs)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            logger.info(f"Successfully loaded from S3: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading from S3: {str(e)}")
            raise ValueError(f"Failed to load from S3: {str(e)}")
    
    
    @staticmethod
    def load_sqlite_table(
        database_path: str,
        table_name: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load data from SQLite database.
        
        Args:
            database_path: Path to SQLite database file
            table_name: Table name to load
            query: Custom SQL query (alternative to table_name)
            **kwargs: Additional arguments
            
        Returns:
            pd.DataFrame
            
        Example:
            df = load_sqlite_table(
                database_path='data.db',
                table_name='users'
            )
        """
        if not HAS_SQLALCHEMY:
            raise ImportError(
                "SQLAlchemy is required for database connections. "
                "Install: pip install sqlalchemy"
            )
        
        try:
            logger.info(f"Connecting to SQLite: {database_path}")
            
            # Create connection string
            connection_string = f"sqlite:///{database_path}"
            engine = create_engine(connection_string)
            
            # Execute query or select table
            if query:
                df = pd.read_sql_query(query, engine)
            elif table_name:
                df = pd.read_sql_table(table_name, engine)
            else:
                raise ValueError("Either table_name or query must be provided")
            
            logger.info(f"Successfully loaded from SQLite: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading from SQLite: {str(e)}")
            raise ValueError(f"Failed to load from SQLite: {str(e)}")
    
    
    @staticmethod
    def load_api_json(
        url: str,
        method: str = 'GET',
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_path: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load JSON data from API endpoint.
        
        Args:
            url: API endpoint URL
            method: HTTP method (GET/POST)
            headers: HTTP headers (for authentication)
            params: Query parameters
            json_path: JSON path to data (e.g., 'data.items')
            **kwargs: Additional arguments
            
        Returns:
            pd.DataFrame
            
        Example:
            df = load_api_json(
                url='https://api.example.com/data',
                headers={'Authorization': 'Bearer TOKEN'}
            )
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required. Install: pip install requests")
        
        try:
            logger.info(f"Requesting API: {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, **kwargs)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=params, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            data = response.json()
            
            # Navigate to nested data if json_path provided
            if json_path:
                for key in json_path.split('.'):
                    data = data[key]
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                raise ValueError("API response is not convertible to DataFrame")
            
            logger.info(f"Successfully loaded from API: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading from API: {str(e)}")
            raise ValueError(f"Failed to load from API: {str(e)}")


# Convenience functions
def load_csv_url(url: str, **kwargs) -> pd.DataFrame:
    """Load CSV from URL."""
    return DataSourceConnector.load_csv_url(url, **kwargs)


def load_google_sheet(sheet_url: str, credentials_json: Optional[str] = None, **kwargs) -> pd.DataFrame:
    """Load Google Sheet."""
    return DataSourceConnector.load_google_sheet(sheet_url, credentials_json, **kwargs)


def load_postgres_table(host: str, port: int, database: str, username: str, password: str, 
                       table_name: Optional[str] = None, query: Optional[str] = None, **kwargs) -> pd.DataFrame:
    """Load PostgreSQL table."""
    return DataSourceConnector.load_postgres_table(host, port, database, username, password, 
                                                   table_name, query, **kwargs)


def load_mysql_table(host: str, port: int, database: str, username: str, password: str,
                    table_name: Optional[str] = None, query: Optional[str] = None, **kwargs) -> pd.DataFrame:
    """Load MySQL table."""
    return DataSourceConnector.load_mysql_table(host, port, database, username, password,
                                              table_name, query, **kwargs)


def load_s3_file(bucket_name: str, file_key: str, aws_access_key_id: Optional[str] = None,
                aws_secret_access_key: Optional[str] = None, region_name: str = 'us-east-1',
                file_format: str = 'csv', **kwargs) -> pd.DataFrame:
    """Load file from S3."""
    return DataSourceConnector.load_s3_file(bucket_name, file_key, aws_access_key_id,
                                           aws_secret_access_key, region_name, file_format, **kwargs)


def load_sqlite_table(database_path: str, table_name: Optional[str] = None, 
                     query: Optional[str] = None, **kwargs) -> pd.DataFrame:
    """Load SQLite table."""
    return DataSourceConnector.load_sqlite_table(database_path, table_name, query, **kwargs)


def load_api_json(url: str, method: str = 'GET', headers: Optional[Dict[str, str]] = None,
                 params: Optional[Dict[str, Any]] = None, json_path: Optional[str] = None, 
                 **kwargs) -> pd.DataFrame:
    """Load JSON from API."""
    return DataSourceConnector.load_api_json(url, method, headers, params, json_path, **kwargs)
