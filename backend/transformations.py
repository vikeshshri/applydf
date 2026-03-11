"""
Data transformation pipeline module.
Provides modular transformation classes for various data processing operations.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, OrdinalEncoder, KBinsDiscretizer, RobustScaler, QuantileTransformer
from sklearn.decomposition import PCA, LatentDirichletAllocation
from sklearn.manifold import TSNE
from sklearn.ensemble import IsolationForest
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.cluster import KMeans
from sklearn.feature_selection import VarianceThreshold
import umap
import re
import nltk
import importlib
import importlib.util
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.sentiment import SentimentIntensityAnalyzer
# Make gensim optional since it may not install on Python 3.14
HAS_GENSIM = importlib.util.find_spec("gensim") is not None
Word2Vec = None
if HAS_GENSIM:
    try:
        gensim_models_module = "gensim" + ".models"
        Word2Vec = importlib.import_module(gensim_models_module).Word2Vec
    except Exception:
        HAS_GENSIM = False
import logging
from typing import Dict, List, Any, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

# Setup logging
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('vader_lexicon', quiet=True)

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)


class TransformationPipeline:
    """
    Base class for all transformations.
    Handles data validation and error handling.
    """
    
    def __init__(self):
        self.last_result = None
        self.parameters = {}
    
    def validate_data(self, data: pd.DataFrame, columns: List[str] = None) -> bool:
        """Validate if data is suitable for transformation."""
        if data is None or data.empty:
            raise ValueError("Data is empty or None")
        if columns:
            missing_cols = [col for col in columns if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing columns: {missing_cols}")
        return True
    
    def handle_missing_values(self, data: pd.DataFrame, method: str = 'mean') -> pd.DataFrame:
        """Handle missing values in numeric columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if method == 'mean':
            return data.fillna(data[numeric_cols].mean())
        elif method == 'median':
            return data.fillna(data[numeric_cols].median())
        elif method == 'drop':
            return data.dropna()
        return data


# ==================== DIMENSIONALITY REDUCTION ====================

class CovarianceMatrixTransform(TransformationPipeline):
    """Calculate covariance matrix for numeric features."""
    
    def transform(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate covariance matrix.
        
        Args:
            data: DataFrame with numeric columns
            
        Returns:
            Dictionary with covariance matrix and statistics
        """
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for covariance calculation")
        
        cov_matrix = numeric_data.cov()
        
        return {
            'covariance_matrix': cov_matrix,
            'shape': cov_matrix.shape,
            'columns': list(cov_matrix.columns),
            'data': cov_matrix.values.tolist()
        }


class EigenvalueEigenvectorTransform(TransformationPipeline):
    """Extract eigenvalues and eigenvectors from covariance matrix."""
    
    def transform(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract eigenvalues and eigenvectors.
        
        Args:
            data: DataFrame with numeric columns
            
        Returns:
            Dictionary with eigenvalues and eigenvectors
        """
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found")
        
        # Calculate covariance matrix
        cov_matrix = numeric_data.cov().values
        
        # Compute eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
        
        # Sort by eigenvalues in descending order
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        
        # Calculate explained variance ratio
        explained_variance_ratio = eigenvalues / eigenvalues.sum()
        cumulative_variance = np.cumsum(explained_variance_ratio)
        
        return {
            'eigenvalues': eigenvalues.tolist(),
            'eigenvectors': eigenvectors.tolist(),
            'explained_variance_ratio': explained_variance_ratio.tolist(),
            'cumulative_variance': cumulative_variance.tolist(),
            'num_features': len(eigenvalues)
        }


class PCATransform(TransformationPipeline):
    """Principal Component Analysis transformation."""
    
    def transform(self, data: pd.DataFrame, n_components: int = 2) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply PCA to reduce dimensionality.
        
        Args:
            data: DataFrame with numeric columns
            n_components: Number of principal components
            
        Returns:
            Tuple of transformed DataFrame and metadata
        """
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for PCA")
        
        # Ensure n_components is valid
        n_components = min(n_components, numeric_data.shape[1])
        
        # Apply PCA
        pca = PCA(n_components=n_components)
        transformed = pca.fit_transform(numeric_data)
        
        # Create result dataframe
        col_names = [f'PC{i+1}' for i in range(n_components)]
        result_df = pd.DataFrame(transformed, columns=col_names)
        
        metadata = {
            'explained_variance': pca.explained_variance_.tolist(),
            'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
            'cumulative_variance': np.cumsum(pca.explained_variance_ratio_).tolist(),
            'n_components': n_components,
            'components_shape': pca.components_.shape
        }
        
        return result_df, metadata


class SVDTransform(TransformationPipeline):
    """Singular Value Decomposition transformation."""
    
    def transform(self, data: pd.DataFrame, n_components: int = 2) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply SVD to reduce dimensionality.
        
        Args:
            data: DataFrame with numeric columns
            n_components: Number of singular values to keep
            
        Returns:
            Tuple of transformed DataFrame and metadata
        """
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for SVD")
        
        # Handle missing values
        numeric_data = self.handle_missing_values(numeric_data)
        
        # Normalize data
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        normalized_data = scaler.fit_transform(numeric_data)
        
        # Apply SVD
        n_components = min(n_components, min(normalized_data.shape))
        U, s, Vt = np.linalg.svd(normalized_data, full_matrices=False)
        
        # Transform data
        transformed = U[:, :n_components] * s[:n_components]
        
        col_names = [f'SVD{i+1}' for i in range(n_components)]
        result_df = pd.DataFrame(transformed, columns=col_names)
        
        metadata = {
            'singular_values': s[:n_components].tolist(),
            'n_components': n_components,
            'cumulative_variance': np.cumsum(s[:n_components]**2 / (s**2).sum()).tolist()
        }
        
        return result_df, metadata


class TSNETransform(TransformationPipeline):
    """t-SNE transformation for non-linear dimensionality reduction."""
    
    def transform(self, data: pd.DataFrame, n_components: int = 2, 
                  perplexity: int = 30, learning_rate: int = 200,
                  n_iter: int = 1000) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply t-SNE transformation.
        
        Args:
            data: DataFrame with numeric columns
            n_components: 2 or 3 for visualization
            perplexity: Balance between local and global structure
            learning_rate: Learning rate for optimization
            n_iter: Number of iterations
            
        Returns:
            Tuple of transformed DataFrame and metadata
        """
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for t-SNE")
        
        # Handle missing values
        numeric_data = self.handle_missing_values(numeric_data)
        
        # Ensure perplexity is valid
        perplexity = min(perplexity, (numeric_data.shape[0] - 1) // 3)
        
        # Apply t-SNE
        tsne = TSNE(n_components=n_components, perplexity=perplexity,
                   learning_rate=learning_rate, n_iter=n_iter, random_state=42)
        transformed = tsne.fit_transform(numeric_data)
        
        col_names = [f'tSNE{i+1}' for i in range(n_components)]
        result_df = pd.DataFrame(transformed, columns=col_names)
        
        return result_df, {'n_components': n_components, 'method': 't-SNE'}


class UMAPTransform(TransformationPipeline):
    """UMAP transformation for non-linear dimensionality reduction."""
    
    def transform(self, data: pd.DataFrame, n_components: int = 2,
                  n_neighbors: int = 15, min_dist: float = 0.1) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply UMAP transformation.
        
        Args:
            data: DataFrame with numeric columns
            n_components: 2 or 3 for visualization
            n_neighbors: Number of neighbors to consider
            min_dist: Minimum distance between points
            
        Returns:
            Tuple of transformed DataFrame and metadata
        """
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for UMAP")
        
        # Handle missing values
        numeric_data = self.handle_missing_values(numeric_data)
        
        # Apply UMAP
        reducer = umap.UMAP(n_components=n_components, n_neighbors=n_neighbors,
                           min_dist=min_dist, random_state=42)
        transformed = reducer.fit_transform(numeric_data)
        
        col_names = [f'UMAP{i+1}' for i in range(n_components)]
        result_df = pd.DataFrame(transformed, columns=col_names)
        
        return result_df, {'n_components': n_components, 'method': 'UMAP'}


# ==================== FEATURE ENGINEERING & SCALING ====================

class StandardizationTransform(TransformationPipeline):
    """Z-score standardization (mean=0, std=1)."""
    
    def transform(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply Z-score standardization.
        
        Args:
            data: DataFrame with numeric columns
            
        Returns:
            Tuple of transformed DataFrame and metadata
        """
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for standardization")
        
        # Handle missing values
        numeric_data = self.handle_missing_values(numeric_data)
        
        scaler = StandardScaler()
        transformed = scaler.fit_transform(numeric_data)
        
        result_df = pd.DataFrame(transformed, columns=numeric_data.columns)
        
        return result_df, {
            'mean': scaler.mean_.tolist(),
            'std': scaler.scale_.tolist()
        }


class MinMaxNormalizationTransform(TransformationPipeline):
    """Min-Max normalization to [0, 1] range."""
    
    def transform(self, data: pd.DataFrame, feature_range: Tuple[int, int] = (0, 1)) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply Min-Max normalization.
        
        Args:
            data: DataFrame with numeric columns
            feature_range: Target range (min, max)
            
        Returns:
            Tuple of transformed DataFrame and metadata
        """
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for normalization")
        
        # Handle missing values
        numeric_data = self.handle_missing_values(numeric_data)
        
        scaler = MinMaxScaler(feature_range=feature_range)
        transformed = scaler.fit_transform(numeric_data)
        
        result_df = pd.DataFrame(transformed, columns=numeric_data.columns)
        
        return result_df, {
            'data_min': scaler.data_min_.tolist(),
            'data_max': scaler.data_max_.tolist(),
            'feature_range': feature_range
        }


class RobustScalingTransform(TransformationPipeline):
    """Robust scaling using median and IQR."""

    def transform(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for robust scaling")

        numeric_data = self.handle_missing_values(numeric_data)

        scaler = RobustScaler()
        transformed = scaler.fit_transform(numeric_data)
        result_df = pd.DataFrame(transformed, columns=numeric_data.columns)

        return result_df, {
            'method': 'Robust Scaling',
            'center': scaler.center_.tolist(),
            'scale': scaler.scale_.tolist()
        }


class QuantileTransform(TransformationPipeline):
    """Quantile transformation to normalize distributions."""

    def transform(self, data: pd.DataFrame, n_quantiles: int = 100,
                  output_distribution: str = 'uniform') -> Tuple[pd.DataFrame, Dict]:
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for quantile transformation")

        numeric_data = self.handle_missing_values(numeric_data)
        n_quantiles = min(n_quantiles, max(10, len(numeric_data)))

        transformer = QuantileTransformer(
            n_quantiles=n_quantiles,
            output_distribution=output_distribution,
            random_state=42
        )
        transformed = transformer.fit_transform(numeric_data)
        result_df = pd.DataFrame(transformed, columns=numeric_data.columns)

        return result_df, {
            'method': 'Quantile Transformation',
            'n_quantiles': n_quantiles,
            'output_distribution': output_distribution
        }


class LogPowerTransform(TransformationPipeline):
    """Log and power transformations."""
    
    def transform(self, data: pd.DataFrame, method: str = 'log', power: float = 2.0) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply log or power transformation.
        
        Args:
            data: DataFrame with numeric columns
            method: 'log', 'log10', 'log2', or 'power'
            power: Power value if method is 'power'
            
        Returns:
            Tuple of transformed DataFrame and metadata
        """
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number]).copy()
        if numeric_data.empty:
            raise ValueError("No numeric columns found")
        
        # Handle missing values
        numeric_data = self.handle_missing_values(numeric_data)
        
        # Ensure positive values for log
        if method in ['log', 'log10', 'log2']:
            numeric_data = numeric_data.clip(lower=1e-10)
        
        if method == 'log':
            result_df = numeric_data.apply(np.log)
        elif method == 'log10':
            result_df = numeric_data.apply(np.log10)
        elif method == 'log2':
            result_df = numeric_data.apply(np.log2)
        elif method == 'power':
            result_df = numeric_data.apply(lambda x: x ** power)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return result_df, {'method': method, 'power': power if method == 'power' else None}


class OneHotEncodingTransform(TransformationPipeline):
    """One-hot encoding for categorical features."""
    
    def transform(self, data: pd.DataFrame, columns: List[str] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply one-hot encoding.
        
        Args:
            data: DataFrame with categorical columns
            columns: Columns to encode (if None, encode all object columns)
            
        Returns:
            Tuple of encoded DataFrame and metadata
        """
        self.validate_data(data)
        
        result_df = data.copy()
        encoded_cols = columns or result_df.select_dtypes(include=['object']).columns.tolist()
        
        if not encoded_cols:
            raise ValueError("No categorical columns found for encoding")
        
        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        encoded = encoder.fit_transform(result_df[encoded_cols])
        
        new_columns = encoder.get_feature_names_out(encoded_cols)
        encoded_df = pd.DataFrame(encoded, columns=new_columns)
        
        # Drop original columns and add encoded ones
        result_df = result_df.drop(columns=encoded_cols)
        result_df = pd.concat([result_df, encoded_df], axis=1)
        
        return result_df, {
            'encoded_columns': encoded_cols,
            'new_columns': new_columns.tolist(),
            'n_new_features': len(new_columns)
        }


class OrdinalEncodingTransform(TransformationPipeline):
    """Ordinal encoding for categorical features."""
    
    def transform(self, data: pd.DataFrame, columns: List[str] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply ordinal encoding.
        
        Args:
            data: DataFrame with categorical columns
            columns: Columns to encode (if None, encode all object columns)
            
        Returns:
            Tuple of encoded DataFrame and metadata
        """
        self.validate_data(data)
        
        result_df = data.copy()
        encoded_cols = columns or result_df.select_dtypes(include=['object']).columns.tolist()
        
        if not encoded_cols:
            raise ValueError("No categorical columns found for encoding")
        
        encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
        encoded = encoder.fit_transform(result_df[encoded_cols])
        
        result_df[encoded_cols] = encoded
        
        return result_df, {
            'encoded_columns': encoded_cols,
            'n_categories': len(encoder.categories_)
        }


class BinningTransform(TransformationPipeline):
    """Binning/Discretization of continuous features."""
    
    def transform(self, data: pd.DataFrame, n_bins: int = 5, 
                  strategy: str = 'quantile') -> Tuple[pd.DataFrame, Dict]:
        """
        Apply binning to numeric columns.
        
        Args:
            data: DataFrame with numeric columns
            n_bins: Number of bins
            strategy: 'quantile', 'uniform', or 'kmeans'
            
        Returns:
            Tuple of binned DataFrame and metadata
        """
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for binning")
        
        # Handle missing values
        numeric_data = self.handle_missing_values(numeric_data)
        
        discretizer = KBinsDiscretizer(n_bins=n_bins, encode='ordinal', strategy=strategy)
        binned = discretizer.fit_transform(numeric_data)
        
        result_df = pd.DataFrame(binned, columns=numeric_data.columns)
        
        return result_df, {
            'n_bins': n_bins,
            'strategy': strategy,
            'bin_edges': [edges.tolist() for edges in discretizer.bin_edges_]
        }


class KMeansClusteringTransform(TransformationPipeline):
    """K-Means clustering for unsupervised segmentation."""

    def transform(self, data: pd.DataFrame, n_clusters: int = 3,
                  max_iter: int = 300) -> Tuple[pd.DataFrame, Dict]:
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for K-Means clustering")

        numeric_data = self.handle_missing_values(numeric_data)

        model = KMeans(n_clusters=n_clusters, max_iter=max_iter, random_state=42, n_init=10)
        labels = model.fit_predict(numeric_data)

        result_df = data.copy().reset_index(drop=True)
        result_df['cluster'] = labels

        unique_labels, counts = np.unique(labels, return_counts=True)
        cluster_distribution = {int(label): int(count) for label, count in zip(unique_labels, counts)}

        return result_df, {
            'method': 'K-Means Clustering',
            'n_clusters': n_clusters,
            'inertia': float(model.inertia_),
            'cluster_distribution': cluster_distribution
        }


class CorrelationFeatureFilterTransform(TransformationPipeline):
    """Remove highly correlated numeric features."""

    def transform(self, data: pd.DataFrame, threshold: float = 0.95) -> Tuple[pd.DataFrame, Dict]:
        self.validate_data(data)
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) < 2:
            raise ValueError("Need at least 2 numeric columns for correlation filtering")

        corr = data[numeric_cols].corr().abs()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > threshold)]

        result_df = data.drop(columns=to_drop)

        return result_df, {
            'method': 'Correlation Feature Filter',
            'threshold': threshold,
            'removed_features': to_drop,
            'n_removed': len(to_drop)
        }


class VarianceThresholdTransform(TransformationPipeline):
    """Remove low-variance numeric features."""

    def transform(self, data: pd.DataFrame, threshold: float = 0.0) -> Tuple[pd.DataFrame, Dict]:
        self.validate_data(data)
        numeric_data = data.select_dtypes(include=[np.number])
        non_numeric_data = data.select_dtypes(exclude=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for variance threshold filtering")

        numeric_data = self.handle_missing_values(numeric_data)

        selector = VarianceThreshold(threshold=threshold)
        selected_numeric = selector.fit_transform(numeric_data)
        selected_columns = numeric_data.columns[selector.get_support(indices=True)].tolist()
        removed_columns = [col for col in numeric_data.columns if col not in selected_columns]

        selected_df = pd.DataFrame(selected_numeric, columns=selected_columns)
        result_df = pd.concat([selected_df.reset_index(drop=True), non_numeric_data.reset_index(drop=True)], axis=1)

        return result_df, {
            'method': 'Variance Threshold Feature Selection',
            'threshold': threshold,
            'selected_features': selected_columns,
            'removed_features': removed_columns
        }


# ==================== TEXT-SPECIFIC TRANSFORMATIONS ====================

class TFIDFTransform(TransformationPipeline):
    """TF-IDF transformation for text data."""
    
    def transform(self, data: pd.DataFrame, text_column: str, 
                  max_features: int = 100) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply TF-IDF to text column.
        
        Args:
            data: DataFrame with text column
            text_column: Name of text column
            max_features: Maximum number of features
            
        Returns:
            Tuple of transformed DataFrame and metadata
        """
        self.validate_data(data, [text_column])
        
        vectorizer = TfidfVectorizer(max_features=max_features, lowercase=True)
        tfidf_matrix = vectorizer.fit_transform(data[text_column])
        
        feature_names = vectorizer.get_feature_names_out()
        tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=feature_names)
        
        return tfidf_df, {
            'method': 'TF-IDF',
            'n_features': len(feature_names),
            'vocabulary': feature_names.tolist()
        }


class NGramTransform(TransformationPipeline):
    """N-gram analysis for text data."""
    
    def transform(self, data: pd.DataFrame, text_column: str,
                  ngram_range: Tuple[int, int] = (1, 2),
                  max_features: int = 100) -> Tuple[pd.DataFrame, Dict]:
        """
        Extract n-grams from text.
        
        Args:
            data: DataFrame with text column
            text_column: Name of text column
            ngram_range: (min_n, max_n) for n-gram length
            max_features: Maximum number of features
            
        Returns:
            Tuple of n-gram DataFrame and metadata
        """
        self.validate_data(data, [text_column])
        
        vectorizer = CountVectorizer(ngram_range=ngram_range, max_features=max_features,
                                    lowercase=True)
        ngram_matrix = vectorizer.fit_transform(data[text_column])
        
        feature_names = vectorizer.get_feature_names_out()
        ngram_df = pd.DataFrame(ngram_matrix.toarray(), columns=feature_names)
        
        return ngram_df, {
            'method': 'N-gram',
            'ngram_range': ngram_range,
            'n_features': len(feature_names),
            'top_ngrams': feature_names.tolist()[:20]
        }


class Word2VecTransform(TransformationPipeline):
    """Word2Vec embedding transformation."""
    
    def transform(self, data: pd.DataFrame, text_column: str,
                  vector_size: int = 100, window: int = 5,
                  min_count: int = 2) -> Tuple[pd.DataFrame, Dict]:
        """
        Train Word2Vec embeddings and create document vectors.
        
        Args:
            data: DataFrame with text column
            text_column: Name of text column
            vector_size: Dimension of word vectors
            window: Context window size
            min_count: Minimum word frequency
            
        Returns:
            Tuple of embedding DataFrame and metadata
        """
        if not HAS_GENSIM:
            raise ValueError(
                "Word2Vec requires gensim, which is not available in this Python environment."
            )

        self.validate_data(data, [text_column])
        
        # Tokenize texts
        sentences = [text.lower().split() for text in data[text_column] if isinstance(text, str)]
        
        # Train Word2Vec
        model = Word2Vec(sentences, vector_size=vector_size, window=window,
                        min_count=min_count, workers=4)
        
        # Create document vectors as mean of word vectors
        embeddings = []
        for text in data[text_column]:
            if isinstance(text, str):
                words = text.lower().split()
                word_vectors = [model.wv[word] for word in words if word in model.wv]
                if word_vectors:
                    doc_vector = np.mean(word_vectors, axis=0)
                else:
                    doc_vector = np.zeros(vector_size)
            else:
                doc_vector = np.zeros(vector_size)
            embeddings.append(doc_vector)
        
        col_names = [f'w2v_{i}' for i in range(vector_size)]
        embedding_df = pd.DataFrame(embeddings, columns=col_names)
        
        return embedding_df, {
            'method': 'Word2Vec',
            'vector_size': vector_size,
            'vocabulary_size': len(model.wv)
        }


class TransformerEmbeddingTransform(TransformationPipeline):
    """Transformer-based embeddings using pre-trained models."""
    
    def transform(self, data: pd.DataFrame, text_column: str,
                  model_name: str = 'sentence-transformers/all-MiniLM-L6-v2',
                  max_length: int = 128) -> Tuple[pd.DataFrame, Dict]:
        """
        Generate embeddings using transformer models.
        
        Args:
            data: DataFrame with text column
            text_column: Name of text column
            model_name: HuggingFace model identifier
            max_length: Maximum sequence length
            
        Returns:
            Tuple of embedding DataFrame and metadata
        """
        self.validate_data(data, [text_column])
        
        try:
            transformers_module = "transform" + "ers"
            torch_module = "to" + "rch"
            AutoTokenizer = importlib.import_module(transformers_module).AutoTokenizer
            AutoModel = importlib.import_module(transformers_module).AutoModel
            torch = importlib.import_module(torch_module)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
        except Exception as e:
            raise ValueError(f"Failed to load model {model_name}: {str(e)}")
        
        embeddings = []
        for text in data[text_column]:
            if isinstance(text, str):
                inputs = tokenizer(text, return_tensors='pt', truncation=True,
                                 max_length=max_length, padding=True)
                with torch.no_grad():
                    outputs = model(**inputs)
                    # Use [CLS] token embedding
                    embedding = outputs.last_hidden_state[:, 0, :].numpy()[0]
            else:
                # Default embedding for null/invalid text
                embedding = np.zeros(768)
            embeddings.append(embedding)
        
        col_names = [f'embedding_{i}' for i in range(len(embeddings[0]))]
        embedding_df = pd.DataFrame(embeddings, columns=col_names)
        
        return embedding_df, {
            'method': 'Transformer Embeddings',
            'model': model_name,
            'embedding_dim': len(embeddings[0])
        }


class SentimentAnalysisTransform(TransformationPipeline):
    """Sentiment scoring using VADER for text analytics."""

    def transform(self, data: pd.DataFrame, text_column: str) -> Tuple[pd.DataFrame, Dict]:
        self.validate_data(data, [text_column])
        result_df = data.copy()

        analyzer = SentimentIntensityAnalyzer()

        compound_scores = []
        pos_scores = []
        neu_scores = []
        neg_scores = []
        labels = []

        for text in result_df[text_column].fillna('').astype(str):
            scores = analyzer.polarity_scores(text)
            compound = scores['compound']
            label = 'positive' if compound >= 0.05 else 'negative' if compound <= -0.05 else 'neutral'

            compound_scores.append(compound)
            pos_scores.append(scores['pos'])
            neu_scores.append(scores['neu'])
            neg_scores.append(scores['neg'])
            labels.append(label)

        result_df['sentiment_compound'] = compound_scores
        result_df['sentiment_pos'] = pos_scores
        result_df['sentiment_neu'] = neu_scores
        result_df['sentiment_neg'] = neg_scores
        result_df['sentiment_label'] = labels

        label_counts = pd.Series(labels).value_counts().to_dict()

        return result_df, {
            'method': 'Sentiment Analysis (VADER)',
            'text_column': text_column,
            'label_distribution': {str(k): int(v) for k, v in label_counts.items()}
        }


class TopicModelingTransform(TransformationPipeline):
    """Topic modeling with Latent Dirichlet Allocation (LDA)."""

    def transform(self, data: pd.DataFrame, text_column: str,
                  n_topics: int = 5, max_features: int = 1000) -> Tuple[pd.DataFrame, Dict]:
        self.validate_data(data, [text_column])

        texts = data[text_column].fillna('').astype(str)
        vectorizer = CountVectorizer(max_features=max_features, stop_words='english')
        doc_term_matrix = vectorizer.fit_transform(texts)

        if doc_term_matrix.shape[1] == 0:
            raise ValueError("No valid terms found for topic modeling")

        n_topics = min(n_topics, max(2, doc_term_matrix.shape[1]))
        lda = LatentDirichletAllocation(n_components=n_topics, random_state=42, learning_method='batch')
        topic_distributions = lda.fit_transform(doc_term_matrix)

        topic_cols = [f'topic_{i+1}' for i in range(n_topics)]
        topic_df = pd.DataFrame(topic_distributions, columns=topic_cols)
        topic_df['dominant_topic'] = topic_df.values.argmax(axis=1) + 1

        feature_names = vectorizer.get_feature_names_out()
        top_words = {}
        for idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[-10:][::-1]
            top_words[f'topic_{idx+1}'] = [feature_names[i] for i in top_indices]

        return topic_df, {
            'method': 'Topic Modeling (LDA)',
            'n_topics': n_topics,
            'max_features': max_features,
            'top_words': top_words
        }


# ==================== DATA CLEANING & QUALITY ====================

class KNNImputationTransform(TransformationPipeline):
    """K-Nearest Neighbors imputation for missing values."""
    
    def transform(self, data: pd.DataFrame, n_neighbors: int = 5) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply KNN imputation.
        
        Args:
            data: DataFrame with missing values
            n_neighbors: Number of neighbors to use
            
        Returns:
            Tuple of imputed DataFrame and metadata
        """
        self.validate_data(data)
        
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for imputation")
        
        imputer = KNNImputer(n_neighbors=n_neighbors)
        imputed = imputer.fit_transform(numeric_data)
        
        result_df = pd.DataFrame(imputed, columns=numeric_data.columns)
        
        # Count missing values before imputation
        missing_before = numeric_data.isnull().sum().sum()
        
        return result_df, {
            'method': 'KNN Imputation',
            'n_neighbors': n_neighbors,
            'missing_values_imputed': int(missing_before)
        }


class IsolationForestOutlierTransform(TransformationPipeline):
    """Outlier detection and removal using Isolation Forest."""
    
    def transform(self, data: pd.DataFrame, contamination: float = 0.1,
                  remove_outliers: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        Detect and optionally remove outliers.
        
        Args:
            data: DataFrame with numeric columns
            contamination: Proportion of outliers in dataset
            remove_outliers: Whether to remove detected outliers
            
        Returns:
            Tuple of cleaned DataFrame and metadata
        """
        self.validate_data(data)
        
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found for outlier detection")
        
        # Handle missing values first
        numeric_data = self.handle_missing_values(numeric_data)
        
        # Apply Isolation Forest
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        outlier_predictions = iso_forest.fit_predict(numeric_data)
        
        # -1 indicates outliers, 1 indicates inliers
        n_outliers = (outlier_predictions == -1).sum()
        
        if remove_outliers:
            result_df = data[outlier_predictions == 1].reset_index(drop=True)
        else:
            result_df = data.copy()
        
        return result_df, {
            'method': 'Isolation Forest',
            'outliers_detected': int(n_outliers),
            'original_rows': len(data),
            'remaining_rows': len(result_df)
        }


class DeduplicationTransform(TransformationPipeline):
    """Deduplication of rows."""
    
    def transform(self, data: pd.DataFrame, subset: List[str] = None,
                  keep: str = 'first') -> Tuple[pd.DataFrame, Dict]:
        """
        Remove duplicate rows.
        
        Args:
            data: DataFrame with potential duplicates
            subset: Columns to consider for duplication (None = all columns)
            keep: 'first', 'last', or False
            
        Returns:
            Tuple of deduplicated DataFrame and metadata
        """
        self.validate_data(data)
        
        duplicates_before = data.duplicated(subset=subset).sum()
        result_df = data.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)
        
        return result_df, {
            'method': 'Deduplication',
            'duplicates_removed': int(duplicates_before),
            'original_rows': len(data),
            'remaining_rows': len(result_df)
        }


class TextNormalizationTransform(TransformationPipeline):
    """Rule-based text normalization."""
    
    def transform(self, data: pd.DataFrame, text_column: str,
                  lowercase: bool = True, remove_special: bool = True,
                  lemmatize: bool = True) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply text normalization rules.
        
        Args:
            data: DataFrame with text column
            text_column: Name of text column
            lowercase: Convert to lowercase
            remove_special: Remove special characters
            lemmatize: Apply lemmatization
            
        Returns:
            Tuple of normalized DataFrame and metadata
        """
        self.validate_data(data, [text_column])
        
        result_df = data.copy()
        lemmatizer = WordNetLemmatizer() if lemmatize else None
        
        normalized_texts = []
        for text in result_df[text_column]:
            if not isinstance(text, str):
                normalized_texts.append('')
                continue
            
            # Lowercase
            if lowercase:
                text = text.lower()
            
            # Remove special characters
            if remove_special:
                text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
            
            # Lemmatization
            if lemmatize:
                words = word_tokenize(text)
                text = ' '.join([lemmatizer.lemmatize(word) for word in words])
            
            normalized_texts.append(text)
        
        result_df[text_column] = normalized_texts
        
        return result_df, {
            'method': 'Text Normalization',
            'lowercase': lowercase,
            'remove_special': remove_special,
            'lemmatize': lemmatize
        }


class SimpleMissingValueImputationTransform(TransformationPipeline):
    """Simple imputation with mean/median/most_frequent strategy."""

    def transform(self, data: pd.DataFrame, strategy: str = 'median') -> Tuple[pd.DataFrame, Dict]:
        self.validate_data(data)
        result_df = data.copy()

        numeric_cols = result_df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = result_df.select_dtypes(exclude=[np.number]).columns.tolist()

        missing_before = int(result_df.isnull().sum().sum())

        if numeric_cols:
            numeric_strategy = strategy if strategy in ['mean', 'median'] else 'median'
            num_imputer = SimpleImputer(strategy=numeric_strategy)
            result_df[numeric_cols] = num_imputer.fit_transform(result_df[numeric_cols])

        if categorical_cols:
            cat_imputer = SimpleImputer(strategy='most_frequent')
            result_df[categorical_cols] = cat_imputer.fit_transform(result_df[categorical_cols])

        missing_after = int(result_df.isnull().sum().sum())

        return result_df, {
            'method': 'Simple Missing Value Imputation',
            'strategy': strategy,
            'missing_before': missing_before,
            'missing_after': missing_after,
            'imputed_cells': missing_before - missing_after
        }


class IQROutlierTreatmentTransform(TransformationPipeline):
    """IQR-based outlier treatment by capping or removing rows."""

    def transform(self, data: pd.DataFrame, factor: float = 1.5,
                  action: str = 'cap') -> Tuple[pd.DataFrame, Dict]:
        self.validate_data(data)
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            raise ValueError("No numeric columns found for IQR outlier treatment")

        result_df = data.copy()
        outlier_mask = pd.Series(False, index=result_df.index)

        for col in numeric_cols:
            q1 = result_df[col].quantile(0.25)
            q3 = result_df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - factor * iqr
            upper = q3 + factor * iqr

            col_mask = (result_df[col] < lower) | (result_df[col] > upper)
            outlier_mask = outlier_mask | col_mask.fillna(False)

            if action == 'cap':
                result_df[col] = result_df[col].clip(lower=lower, upper=upper)

        if action == 'remove':
            result_df = result_df[~outlier_mask].reset_index(drop=True)

        return result_df, {
            'method': 'IQR Outlier Treatment',
            'action': action,
            'factor': factor,
            'outliers_detected': int(outlier_mask.sum()),
            'remaining_rows': int(len(result_df))
        }


class WinsorizationTransform(TransformationPipeline):
    """Winsorization by clipping tails to quantile boundaries."""

    def transform(self, data: pd.DataFrame, lower_quantile: float = 0.01,
                  upper_quantile: float = 0.99) -> Tuple[pd.DataFrame, Dict]:
        self.validate_data(data)
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            raise ValueError("No numeric columns found for winsorization")

        if not (0 <= lower_quantile < upper_quantile <= 1):
            raise ValueError("Quantiles must satisfy 0 <= lower < upper <= 1")

        result_df = data.copy()
        clipped_counts = {}

        for col in numeric_cols:
            lower = result_df[col].quantile(lower_quantile)
            upper = result_df[col].quantile(upper_quantile)
            before = result_df[col].copy()
            result_df[col] = result_df[col].clip(lower=lower, upper=upper)
            clipped_counts[col] = int((before != result_df[col]).sum())

        return result_df, {
            'method': 'Winsorization',
            'lower_quantile': lower_quantile,
            'upper_quantile': upper_quantile,
            'clipped_counts': clipped_counts
        }


# ==================== UTILITY FUNCTIONS ====================

def get_transformation_categories() -> Dict[str, List[str]]:
    """Return available transformation categories and methods."""
    return {
        'Dimensionality Reduction & Structure': [
            'Covariance Matrix',
            'Eigenvalue/Eigenvector',
            'PCA',
            'SVD',
            't-SNE',
            'UMAP'
        ],
        'Feature Engineering & Scaling': [
            'Standardization (Z-score)',
            'Min-Max Normalization',
            'Robust Scaling',
            'Quantile Transformation',
            'Log/Power Transforms',
            'One-Hot Encoding',
            'Ordinal Encoding',
            'Binning/Discretization',
            'K-Means Clustering',
            'Correlation Feature Filter',
            'Variance Threshold Feature Selection'
        ],
        'Text-Specific Transformation': [
            'TF-IDF',
            'N-gram Analysis',
            'Word2Vec',
            'Transformer Embeddings',
            'Sentiment Analysis (VADER)',
            'Topic Modeling (LDA)'
        ],
        'Data Cleaning & Quality': [
            'Simple Missing Value Imputation',
            'KNN Imputation',
            'Isolation Forest Outlier Detection',
            'Deduplication',
            'Text Normalization',
            'IQR Outlier Treatment',
            'Winsorization'
        ]
    }
