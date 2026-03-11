"""
Example usage of applydf API.
Demonstrates programmatic interaction with the backend.
"""

import requests
import pandas as pd
import json
from typing import Dict, Any

# ==================== CONFIGURATION ====================

API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30


# ==================== HELPER FUNCTIONS ====================

def make_request(endpoint: str, method: str = "GET", data: Dict = None, 
                files: Dict = None) -> Dict[str, Any]:
    """
    Make HTTP request to API.
    
    Args:
        endpoint: API endpoint (e.g., '/transform')
        method: HTTP method ('GET', 'POST', 'DELETE')
        data: JSON data for POST requests
        files: Files for multipart requests
    
    Returns:
        Response JSON
    """
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=TIMEOUT)
            else:
                response = requests.post(url, json=data, timeout=TIMEOUT)
        elif method == "DELETE":
            response = requests.delete(url, timeout=TIMEOUT)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return None


# ==================== EXAMPLE 1: BASIC WORKFLOW ====================

def example_basic_workflow():
    """
    Example: Upload data, apply PCA, download results.
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Workflow")
    print("="*60)
    
    # 1. Create sample data
    print("\n1. Creating sample data...")
    sample_data = {
        'feature1': [1.5, 2.1, 1.9, 3.2, 2.5],
        'feature2': [2.3, 1.8, 2.2, 1.5, 2.0],
        'feature3': [3.1, 2.5, 3.0, 2.8, 3.2]
    }
    df = pd.DataFrame(sample_data)
    df.to_csv('example_data.csv', index=False)
    print("   ✓ Sample data created: example_data.csv")
    
    # 2. Upload data
    print("\n2. Uploading data...")
    with open('example_data.csv', 'rb') as f:
        files = {'file': f}
        response = make_request('/upload', method='POST', files=files)
    
    if response and response.get('success'):
        print(f"   ✓ Upload successful: {response['message']}")
        print(f"   Shape: {response['shape']}")
    else:
        print("   ✗ Upload failed")
        return
    
    # 3. Get preview
    print("\n3. Fetching data preview...")
    response = make_request('/preview')
    if response:
        print(f"   ✓ Preview retrieved")
        print(f"   Columns: {response['columns']}")
        print(f"   Data types: {response['data_types']}")
    
    # 4. Apply PCA
    print("\n4. Applying PCA transformation...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'PCA',
            'parameters': {'n_components': 2}
        }
    )
    
    if response and response.get('success'):
        print(f"   ✓ {response['message']}")
        print(f"   New shape: {response['shape']}")
        print(f"   Metadata: {response['metadata']}")
    else:
        print("   ✗ Transformation failed")
        return
    
    # 5. Download results
    print("\n5. Downloading results...")
    download_response = requests.get(f"{API_BASE_URL}/download/csv")
    if download_response.status_code == 200:
        with open('pca_results.csv', 'wb') as f:
            f.write(download_response.content)
        print("   ✓ Results downloaded: pca_results.csv")
    else:
        print("   ✗ Download failed")


# ==================== EXAMPLE 2: TEXT PROCESSING ====================

def example_text_processing():
    """
    Example: Process text data with TF-IDF and embeddings.
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Text Processing")
    print("="*60)
    
    # Create sample text data
    print("\n1. Creating sample text data...")
    text_data = {
        'document': [
            'machine learning is amazing',
            'deep learning with neural networks',
            'natural language processing',
            'computer vision techniques',
            'artificial intelligence applications'
        ],
        'category': ['ML', 'DL', 'NLP', 'CV', 'AI']
    }
    df = pd.DataFrame(text_data)
    df.to_csv('example_text.csv', index=False)
    print("   ✓ Text data created: example_text.csv")
    
    # Upload
    print("\n2. Uploading text data...")
    with open('example_text.csv', 'rb') as f:
        files = {'file': f}
        response = make_request('/upload', method='POST', files=files)
    if response and response.get('success'):
        print("   ✓ Upload successful")
    
    # Apply text normalization
    print("\n3. Applying text normalization...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'Text Normalization',
            'parameters': {
                'lowercase': True,
                'remove_special': True,
                'lemmatize': True
            },
            'text_column': 'document'
        }
    )
    if response and response.get('success'):
        print(f"   ✓ Text normalized")
    
    # Apply TF-IDF
    print("\n4. Applying TF-IDF...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'TF-IDF',
            'parameters': {'max_features': 10},
            'text_column': 'document'
        }
    )
    if response and response.get('success'):
        print(f"   ✓ TF-IDF applied: {response['metadata']}")


# ==================== EXAMPLE 3: DATA CLEANING ====================

def example_data_cleaning():
    """
    Example: Clean data with imputation, outlier detection, deduplication.
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Data Cleaning")
    print("="*60)
    
    # Create data with issues
    print("\n1. Creating dirty data...")
    data = {
        'id': [1, 2, 3, 4, 5, 5, 6, 7],  # Duplicate
        'value1': [1.0, 2.0, None, 4.0, 5.0, 5.0, 100.0, 8.0],  # Missing & outlier
        'value2': [10, 20, 30, 40, 50, 50, 60, 70]
    }
    df = pd.DataFrame(data)
    df.to_csv('example_dirty.csv', index=False)
    print("   ✓ Dirty data created with:")
    print("     - Missing values (None)")
    print("     - Outliers (100.0)")
    print("     - Duplicates (id=5)")
    
    # Upload
    print("\n2. Uploading data...")
    with open('example_dirty.csv', 'rb') as f:
        files = {'file': f}
        make_request('/upload', method='POST', files=files)
    print("   ✓ Upload successful")
    
    # KNN Imputation
    print("\n3. Applying KNN imputation...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'KNN Imputation',
            'parameters': {'n_neighbors': 3}
        }
    )
    if response:
        print(f"   ✓ {response['message']}")
        print(f"   Missing values imputed: {response['metadata'].get('missing_values_imputed')}")
    
    # Deduplication
    print("\n4. Removing duplicates...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'Deduplication',
            'parameters': {'keep': 'first'}
        }
    )
    if response:
        print(f"   ✓ {response['message']}")
        print(f"   Duplicates removed: {response['metadata'].get('duplicates_removed')}")
    
    # Outlier detection
    print("\n5. Detecting and removing outliers...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'Isolation Forest Outlier Detection',
            'parameters': {
                'contamination': 0.1,
                'remove_outliers': True
            }
        }
    )
    if response:
        print(f"   ✓ {response['message']}")
        print(f"   Outliers detected: {response['metadata'].get('outliers_detected')}")


# ==================== EXAMPLE 4: FEATURE ENGINEERING ====================

def example_feature_engineering():
    """
    Example: Feature engineering with encoding, scaling, binning.
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Feature Engineering")
    print("="*60)
    
    # Create mixed data
    print("\n1. Creating mixed numeric/categorical data...")
    data = {
        'age': [25, 30, 45, 50, 28, 35],
        'income': [30000, 40000, 80000, 100000, 35000, 50000],
        'category': ['A', 'B', 'A', 'C', 'B', 'A']
    }
    df = pd.DataFrame(data)
    df.to_csv('example_features.csv', index=False)
    print("   ✓ Data created with mixed types")
    
    # Upload
    print("\n2. Uploading data...")
    with open('example_features.csv', 'rb') as f:
        files = {'file': f}
        make_request('/upload', method='POST', files=files)
    print("   ✓ Upload successful")
    
    # One-Hot Encoding
    print("\n3. Applying one-hot encoding...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'One-Hot Encoding',
            'parameters': {'columns': ['category']}
        }
    )
    if response:
        print(f"   ✓ {response['message']}")
        print(f"   New features: {response['metadata'].get('n_new_features')}")
    
    # Standardization
    print("\n4. Applying standardization...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'Standardization (Z-score)',
            'parameters': {}
        }
    )
    if response:
        print(f"   ✓ {response['message']}")
    
    # Binning
    print("\n5. Applying binning...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'Binning/Discretization',
            'parameters': {
                'n_bins': 3,
                'strategy': 'quantile'
            }
        }
    )
    if response:
        print(f"   ✓ {response['message']}")


# ==================== EXAMPLE 5: DIMENSIONALITY REDUCTION ====================

def example_dimensionality_reduction():
    """
    Example: Reduce dimensionality with PCA, t-SNE, UMAP.
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Dimensionality Reduction")
    print("="*60)
    
    # Create high-dimensional data
    print("\n1. Creating high-dimensional data...")
    import numpy as np
    np.random.seed(42)
    data = np.random.randn(100, 20)
    df = pd.DataFrame(data, columns=[f'feature_{i}' for i in range(20)])
    df.to_csv('example_high_dim.csv', index=False)
    print("   ✓ Data created: 100 samples × 20 features")
    
    # Upload
    print("\n2. Uploading data...")
    with open('example_high_dim.csv', 'rb') as f:
        files = {'file': f}
        make_request('/upload', method='POST', files=files)
    print("   ✓ Upload successful")
    
    # PCA
    print("\n3. Applying PCA...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'PCA',
            'parameters': {'n_components': 2}
        }
    )
    if response:
        print(f"   ✓ Reduced to 2 components")
        print(f"   Explained variance: {response['metadata']['explained_variance_ratio']}")
    
    # UMAP
    print("\n4. Applying UMAP...")
    response = make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'UMAP',
            'parameters': {
                'n_components': 2,
                'n_neighbors': 15,
                'min_dist': 0.1
            }
        }
    )
    if response:
        print(f"   ✓ UMAP applied: {response['message']}")


# ==================== EXAMPLE 6: PIPELINE MANAGEMENT ====================

def example_pipeline_management():
    """
    Example: Save and manage transformation pipelines.
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Pipeline Management")
    print("="*60)
    
    # Create and upload sample data
    print("\n1. Creating sample data...")
    data = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10]
    })
    data.to_csv('example_pipeline.csv', index=False)
    
    print("\n2. Uploading data...")
    with open('example_pipeline.csv', 'rb') as f:
        files = {'file': f}
        make_request('/upload', method='POST', files=files)
    
    # Apply transformations
    print("\n3. Applying transformations...")
    # Standardization
    make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'Standardization (Z-score)',
            'parameters': {}
        }
    )
    print("   ✓ Standardization applied")
    
    # PCA
    make_request(
        '/transform',
        method='POST',
        data={
            'transformation_type': 'PCA',
            'parameters': {'n_components': 1}
        }
    )
    print("   ✓ PCA applied")
    
    # Save pipeline
    print("\n4. Saving pipeline...")
    response = make_request(
        '/save-pipeline',
        method='POST',
        data={
            'pipeline_name': 'standardize_and_reduce',
            'description': 'Standardize features and apply PCA'
        }
    )
    if response and response.get('success'):
        print(f"   ✓ Pipeline saved: {response['message']}")
    
    # List pipelines
    print("\n5. Listing pipelines...")
    response = make_request('/pipelines')
    if response and response.get('success'):
        for pipeline in response.get('pipelines', []):
            print(f"   - {pipeline['name']}: {len(pipeline.get('num_transformations', 0))} transformations")


# ==================== EXAMPLE 7: API INFO ====================

def example_api_info():
    """
    Example: Get API information and capabilities.
    """
    print("\n" + "="*60)
    print("EXAMPLE 7: API Information")
    print("="*60)
    
    # Get root info
    print("\n1. API Information:")
    response = make_request('/')
    if response:
        print(f"   Name: {response.get('name')}")
        print(f"   Version: {response.get('version')}")
        print(f"   Description: {response.get('description')}")
    
    # Get categories
    print("\n2. Transformation Categories:")
    response = make_request('/categories')
    if response and response.get('success'):
        for category, methods in response.get('categories', {}).items():
            print(f"\n   {category}:")
            for method in methods:
                print(f"     - {method}")


# ==================== MAIN ====================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("applydf API Examples")
    print("="*60)
    print("\nMake sure the FastAPI backend is running:")
    print("  python -m uvicorn backend.app:app --reload")
    print("\nThen run this script to see API examples.")
    
    # Uncomment examples to run:
    example_api_info()
    # example_basic_workflow()
    # example_text_processing()
    # example_data_cleaning()
    # example_feature_engineering()
    # example_dimensionality_reduction()
    # example_pipeline_management()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60 + "\n")
