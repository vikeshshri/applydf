"""
Database Models for applydf
Handles persistent storage for users, datasets, reports, pipelines, and sharing.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

Base = declarative_base()


class VisibilityType(enum.Enum):
    """Dataset/Report visibility options."""
    PRIVATE = "private"
    PUBLIC = "public"
    SHARED = "shared"


class AccessLevel(enum.Enum):
    """Sharing access levels."""
    VIEWER = "viewer"
    EDITOR = "editor"
    OWNER = "owner"


class ResourceType(enum.Enum):
    """Types of shareable resources."""
    DATASET = "dataset"
    REPORT = "report"
    PIPELINE = "pipeline"


class User(Base):
    """User model."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))  # Store hashed passwords only
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    datasets = relationship("Dataset", back_populates="owner", foreign_keys="Dataset.owner_id")
    reports = relationship("Report", back_populates="owner")
    pipelines = relationship("Pipeline", back_populates="owner")
    owned_shares = relationship("Share", back_populates="owner", foreign_keys="Share.owner_id")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Dataset(Base):
    """Dataset model - stores metadata about uploaded/connected datasets."""
    __tablename__ = 'datasets'
    
    id = Column(Integer, primary_key=True)
    dataset_id = Column(String(50), unique=True, nullable=False, index=True)  # Public ID (e.g., 'abc123')
    dataset_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Data source information
    source_type = Column(String(50))  # 'upload', 'csv_url', 'postgres', 'mysql', 's3', 'google_sheets', etc.
    source_config = Column(JSON)  # Store connection details (sanitized)
    file_path = Column(String(500))  # Local storage path
    
    # Dataset metadata
    row_count = Column(Integer)
    column_count = Column(Integer)
    columns_info = Column(JSON)  # Column names and types
    data_quality_score = Column(Float)
    
    # Pipeline information
    pipeline_applied = Column(Boolean, default=False)
    pipeline_config = Column(JSON)  # Transformation steps applied
    
    # Visibility and sharing
    visibility = Column(Enum(VisibilityType), default=VisibilityType.PRIVATE)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="datasets", foreign_keys=[owner_id])
    reports = relationship("Report", back_populates="dataset")
    
    def __repr__(self):
        return f"<Dataset(id={self.dataset_id}, name='{self.dataset_name}')>"


class Report(Base):
    """Report model - stores shareable dataset analysis reports."""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(String(50), unique=True, nullable=False, index=True)  # Public ID
    dataset_id = Column(Integer, ForeignKey('datasets.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Report content
    report_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Dataset summary
    dataset_summary = Column(JSON)  # Shape, columns, types, missing values, etc.
    data_quality_score = Column(Float)
    
    # Pipeline information
    pipeline_steps = Column(JSON)  # List of transformations applied
    
    # Visualizations
    visualizations = Column(JSON)  # Chart configurations and data
    
    # Before/after comparison
    before_stats = Column(JSON)
    after_stats = Column(JSON)
    
    # File attachments
    cleaned_dataset_path = Column(String(500))  # Path to cleaned dataset file
    
    # Visibility
    visibility = Column(Enum(VisibilityType), default=VisibilityType.PRIVATE)
    view_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="reports")
    dataset = relationship("Dataset", back_populates="reports")
    
    def __repr__(self):
        return f"<Report(id={self.report_id}, name='{self.report_name}')>"


class Pipeline(Base):
    """Pipeline model - stores reusable transformation pipelines."""
    __tablename__ = 'pipelines'
    
    id = Column(Integer, primary_key=True)
    pipeline_id = Column(String(50), unique=True, nullable=False, index=True)  # Public ID
    pipeline_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Pipeline configuration
    pipeline_steps = Column(JSON, nullable=False)  # List of transformation steps
    pipeline_code = Column(Text)  # Generated code (Python/sklearn/PySpark)
    
    # Metadata
    category = Column(String(100))  # e.g., 'cleaning', 'feature_engineering', 'ml_preprocessing'
    tags = Column(JSON)  # List of tags
    
    # Usage statistics
    clone_count = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    
    # Visibility
    visibility = Column(Enum(VisibilityType), default=VisibilityType.PRIVATE)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="pipelines")
    
    def __repr__(self):
        return f"<Pipeline(id={self.pipeline_id}, name='{self.pipeline_name}')>"


class Share(Base):
    """Share model - manages sharing permissions for datasets, reports, and pipelines."""
    __tablename__ = 'shares'
    
    id = Column(Integer, primary_key=True)
    share_id = Column(String(50), unique=True, nullable=False, index=True)  # Public share ID
    
    # Resource information
    resource_type = Column(Enum(ResourceType), nullable=False)
    resource_id = Column(Integer, nullable=False)  # ID of dataset/report/pipeline
    
    # Owner and permissions
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # NULL for public links
    access_level = Column(Enum(AccessLevel), default=AccessLevel.VIEWER)
    
    # Link settings
    is_public_link = Column(Boolean, default=False)
    link_expires_at = Column(DateTime, nullable=True)
    
    # Usage tracking
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    owner = relationship("User", back_populates="owned_shares", foreign_keys=[owner_id])
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id])
    
    # Resource joins are handled in sharing_manager using resource_type/resource_id.
    # Keeping this model simple avoids invalid mapper joins for polymorphic resources.
    
    def __repr__(self):
        return f"<Share(id={self.share_id}, type={self.resource_type}, access={self.access_level})>"


class Activity(Base):
    """Activity model - tracks user actions for audit log."""
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action_type = Column(String(100), nullable=False)  # 'upload', 'transform', 'share', 'download', etc.
    resource_type = Column(Enum(ResourceType), nullable=True)
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON)  # Additional context
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<Activity(user_id={self.user_id}, action='{self.action_type}')>"


# Database setup and utilities

class Database:
    """Database manager class."""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database connection.
        
        Args:
            database_url: SQLAlchemy database URL 
                         (default: sqlite:///applydf.db in current directory)
        """
        if database_url is None:
            # Default to SQLite in backend directory
            db_path = os.path.join(os.path.dirname(__file__), 'applydf.db')
            database_url = f'sqlite:///{db_path}'
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
    
    def drop_all_tables(self):
        """Drop all tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)


# Global database instance
db = Database()


def init_database():
    """Initialize database tables."""
    db.create_tables()
    print("Database tables created successfully")


def get_db_session():
    """Get database session (for dependency injection)."""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
