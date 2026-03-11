"""
Utility functions for applydf backend.
Helpers for data processing, validation, and file handling.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import os
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


# ==================== DATA VALIDATION ====================

class DataValidator:
    """Validate and check data quality."""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate DataFrame structure.
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        if df is None or df.empty:
            return False, ["DataFrame is empty"]
        
        if df.shape[0] > 1000000:
            warnings.append(f"Large dataset ({df.shape[0]:,} rows) may be slow")
        
        if df.isnull().sum().sum() > len(df) * 0.5:
            warnings.append("More than 50% missing values")
        
        return True, warnings
    
    @staticmethod
    def check_numeric_columns(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Check if DataFrame has numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        return len(numeric_cols) > 0, numeric_cols
    
    @staticmethod
    def check_categorical_columns(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Check if DataFrame has categorical columns."""
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        return len(cat_cols) > 0, cat_cols
    
    @staticmethod
    def check_text_columns(df: pd.DataFrame, min_length: int = 10) -> Tuple[bool, List[str]]:
        """Check if DataFrame has text columns (strings with reasonable length)."""
        text_cols = []
        for col in df.select_dtypes(include=['object']).columns:
            avg_length = df[col].astype(str).str.len().mean()
            if avg_length >= min_length:
                text_cols.append(col)
        return len(text_cols) > 0, text_cols


# ==================== DATA TYPE CONVERSION ====================

class DataTypeConverter:
    """Convert between data types safely."""
    
    @staticmethod
    def infer_optimal_types(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert columns to optimal data types.
        Reduces memory usage significantly.
        """
        df = df.copy()
        
        # Numeric optimization
        for col in df.select_dtypes(include=['int64']).columns:
            if df[col].max() < 2147483647:  # int32 limit
                df[col] = df[col].astype('int32')
        
        for col in df.select_dtypes(include=['float64']).columns:
            if df[col].max() < 3.4e38:  # float32 limit
                df[col] = df[col].astype('float32')
        
        # Category optimization for object columns
        for col in df.select_dtypes(include=['object']).columns:
            num_unique = df[col].nunique()
            num_total = len(df)
            if num_unique / num_total < 0.05:  # Less than 5% unique values
                df[col] = df[col].astype('category')
        
        return df
    
    @staticmethod
    def get_memory_usage(df: pd.DataFrame) -> Dict[str, float]:
        """Get memory usage in MB by column type."""
        memory = df.memory_usage(deep=True)
        return {
            'total_mb': float(memory.sum() / 1024**2),
            'by_column': {col: float(mem / 1024**2) for col, mem in memory.items()}
        }


# ==================== STATISTICAL HELPERS ====================

class StatisticalHelpers:
    """Statistical analysis helpers."""
    
    @staticmethod
    def get_percentiles(series: pd.Series, percentiles: List[float] = None) -> Dict:
        """Calculate percentiles for a series."""
        if percentiles is None:
            percentiles = [0, 25, 50, 75, 100]
        
        return {
            f'p{int(p)}': float(series.quantile(p / 100))
            for p in percentiles
        }
    
    @staticmethod
    def detect_outliers_iqr(df: pd.DataFrame, multiplier: float = 1.5) -> Dict[str, int]:
        """Detect outliers using IQR method."""
        outlier_counts = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - multiplier * IQR
            upper = Q3 + multiplier * IQR
            outliers = ((df[col] < lower) | (df[col] > upper)).sum()
            outlier_counts[col] = int(outliers)
        
        return outlier_counts
    
    @staticmethod
    def calculate_correlation(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix."""
        numeric_df = df.select_dtypes(include=[np.number])
        return numeric_df.corr()


# ==================== FILE HANDLING ====================

class FileHandler:
    """Handle file operations safely."""
    
    @staticmethod
    def create_temp_directory(base_path: str = "temp_files") -> str:
        """Create temporary directory if it doesn't exist."""
        os.makedirs(base_path, exist_ok=True)
        return base_path
    
    @staticmethod
    def get_temp_filepath(filename: str, base_path: str = "temp_files", 
                         add_timestamp: bool = True) -> str:
        """Generate safe temporary filepath."""
        FileHandler.create_temp_directory(base_path)
        
        if add_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
        
        return os.path.join(base_path, filename)
    
    @staticmethod
    def cleanup_temp_files(base_path: str = "temp_files", 
                          max_age_hours: int = 24) -> int:
        """Delete old temporary files."""
        if not os.path.exists(base_path):
            return 0
        
        deleted_count = 0
        current_time = datetime.now()
        
        for filename in os.listdir(base_path):
            filepath = os.path.join(base_path, filename)
            if os.path.isfile(filepath):
                file_age = datetime.fromtimestamp(os.path.getmtime(filepath))
                age_hours = (current_time - file_age).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {filepath}: {str(e)}")
        
        return deleted_count
    
    @staticmethod
    def get_file_size_mb(filepath: str) -> float:
        """Get file size in MB."""
        if os.path.exists(filepath):
            return os.path.getsize(filepath) / (1024 * 1024)
        return 0.0


# ==================== TEXT PROCESSING ====================

class TextProcessor:
    """Text processing utilities."""
    
    @staticmethod
    def get_text_stats(text: str) -> Dict[str, Any]:
        """Get statistics about text."""
        words = text.split()
        
        return {
            'length': len(text),
            'word_count': len(words),
            'avg_word_length': len(text) / len(words) if words else 0,
            'unique_words': len(set(w.lower() for w in words)),
            'has_numbers': any(c.isdigit() for c in text),
            'has_special': any(not c.isalnum() and not c.isspace() for c in text)
        }
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Truncate text to max length."""
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text
    
    @staticmethod
    def clean_text(text: str, lowercase: bool = True, 
                  remove_whitespace: bool = True) -> str:
        """Basic text cleaning."""
        if not isinstance(text, str):
            return ""
        
        if lowercase:
            text = text.lower()
        
        if remove_whitespace:
            text = ' '.join(text.split())
        
        return text


# ==================== BATCH PROCESSING ====================

class BatchProcessor:
    """Process data in batches."""
    
    @staticmethod
    def split_dataframe(df: pd.DataFrame, batch_size: int = 1000) -> List[pd.DataFrame]:
        """Split DataFrame into batches."""
        batches = []
        for i in range(0, len(df), batch_size):
            batches.append(df.iloc[i:i+batch_size])
        return batches
    
    @staticmethod
    def process_in_batches(func, df: pd.DataFrame, batch_size: int = 1000, *args, **kwargs):
        """Apply function to all batches and concatenate results."""
        batches = BatchProcessor.split_dataframe(df, batch_size)
        results = []
        
        for batch in batches:
            result = func(batch, *args, **kwargs)
            results.append(result)
        
        return pd.concat(results, ignore_index=True)


# ==================== LOGGING & DEBUGGING ====================

class DebugHelper:
    """Debugging utilities."""
    
    @staticmethod
    def log_dataframe_info(df: pd.DataFrame, name: str = "DataFrame") -> None:
        """Log DataFrame information."""
        logger.info(f"\n{'='*50}")
        logger.info(f"DataFrame: {name}")
        logger.info(f"Shape: {df.shape}")
        logger.info(f"Columns: {df.columns.tolist()}")
        logger.info(f"Data types:\n{df.dtypes}")
        logger.info(f"Missing values:\n{df.isnull().sum()}")
        logger.info(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        logger.info(f"{'='*50}\n")
    
    @staticmethod
    def get_transformation_report(before_df: pd.DataFrame, 
                                 after_df: pd.DataFrame,
                                 transformation_name: str) -> Dict:
        """Generate transformation report."""
        return {
            'transformation': transformation_name,
            'timestamp': datetime.now().isoformat(),
            'input': {
                'shape': before_df.shape,
                'memory_mb': float(before_df.memory_usage(deep=True).sum() / 1024**2),
                'columns': before_df.columns.tolist()
            },
            'output': {
                'shape': after_df.shape,
                'memory_mb': float(after_df.memory_usage(deep=True).sum() / 1024**2),
                'columns': after_df.columns.tolist()
            },
            'changes': {
                'rows_change': after_df.shape[0] - before_df.shape[0],
                'cols_change': after_df.shape[1] - before_df.shape[1],
                'memory_change_mb': float(
                    (after_df.memory_usage(deep=True).sum() - 
                     before_df.memory_usage(deep=True).sum()) / 1024**2
                )
            }
        }


# ==================== CACHING ====================

class CacheManager:
    """Simple caching mechanism."""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_key(self, *args) -> str:
        """Generate cache key from arguments."""
        import hashlib
        key_string = '|'.join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Any:
        """Get cached value."""
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
        return None
    
    def set(self, key: str, value: Any, ttl_hours: int = 24) -> bool:
        """Cache a value."""
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            with open(cache_file, 'w') as f:
                json.dump({
                    'value': value,
                    'timestamp': datetime.now().isoformat(),
                    'ttl_hours': ttl_hours
                }, f)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
        return False
    
    def clear(self) -> int:
        """Clear all cache files."""
        count = 0
        for filename in os.listdir(self.cache_dir):
            try:
                os.remove(os.path.join(self.cache_dir, filename))
                count += 1
            except Exception as e:
                logger.error(f"Clear cache error: {str(e)}")
        return count


if __name__ == "__main__":
    # Test utilities
    print("Utilities loaded successfully")
    print(f"DataValidator: {DataValidator}")
    print(f"FileHandler: {FileHandler}")
    print(f"StatisticalHelpers: {StatisticalHelpers}")
    print(f"TextProcessor: {TextProcessor}")
