"""
Setup script for applydf collaborative features.
Initializes database and creates demo data.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from database_models import init_database, db
from user_manager import UserManager
from dataset_registry import DatasetRegistry
import pandas as pd
import numpy as np


def create_demo_data():
    """Create demo datasets for testing."""
    print("\n📊 Creating demo datasets...")
    
    # Get demo user
    demo_user = UserManager.get_demo_user()
    print(f"✅ Demo user: {demo_user.username} (ID: {demo_user.id})")
    
    # Create sample dataset 1: Sales Data
    print("\n📁 Creating sample sales dataset...")
    sales_df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=100),
        'product': np.random.choice(['Product A', 'Product B', 'Product C'], 100),
        'revenue': np.random.randint(100, 1000, 100),
        'units_sold': np.random.randint(1, 50, 100),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 100)
    })
    
    from database_models import VisibilityType
    
    try:
        dataset1 = DatasetRegistry.register_dataset(
            df=sales_df,
            dataset_name="Sample Sales Data",
            owner_id=demo_user.id,
            description="Demo sales data for testing",
            source_type='demo',
            visibility=VisibilityType.PUBLIC,
            data_quality_score=92.5,
            save_file=True
        )
        print(f"✅ Dataset registered: {dataset1.dataset_id} - {dataset1.dataset_name}")
    except Exception as e:
        print(f"⚠️  Could not create demo dataset: {str(e)}")
    
    # Create sample dataset 2: Customer Data
    print("\n📁 Creating sample customer dataset...")
    customer_df = pd.DataFrame({
        'customer_id': range(1, 51),
        'age': np.random.randint(18, 70, 50),
        'income': np.random.randint(30000, 150000, 50),
        'spending_score': np.random.randint(1, 100, 50),
        'loyalty_years': np.random.randint(0, 10, 50)
    })
    
    try:
        dataset2 = DatasetRegistry.register_dataset(
            df=customer_df,
            dataset_name="Customer Profile Data",
            owner_id=demo_user.id,
            description="Customer demographics and behavior",
            source_type='demo',
            visibility=VisibilityType.PUBLIC,
            data_quality_score=88.0,
            save_file=True
        )
        print(f"✅ Dataset registered: {dataset2.dataset_id} - {dataset2.dataset_name}")
    except Exception as e:
        print(f"⚠️  Could not create demo dataset: {str(e)}")


def main():
    """Run setup."""
    print("=" * 60)
    print("🚀 applydf Collaborative Features Setup")
    print("=" * 60)
    
    # Initialize database
    print("\n🗄️  Initializing database...")
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database warning: {str(e)}")
    
    # Create demo user and data
    try:
        create_demo_data()
    except Exception as e:
        print(f"⚠️  Demo data creation failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\n📝 Next steps:")
    print("1. Start backend:  cd backend && python app.py")
    print("2. Start frontend: cd frontend && streamlit run app_collaborative.py")
    print("3. Open browser:   http://localhost:8501")
    print("\n👤 Demo login credentials:")
    print("   Username: demo")
    print("   Password: demo123")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
