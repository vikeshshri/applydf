"""
Report Generator Module
Generates shareable dataset analysis reports with visualizations.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
import json
import logging
import math
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive dataset analysis reports."""

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Convert numeric values to finite float for JSON serialization."""
        try:
            numeric = float(value)
            return numeric if math.isfinite(numeric) else None
        except Exception:
            return None
    
    @staticmethod
    def generate_report_id() -> str:
        """Generate unique report ID."""
        return uuid.uuid4().hex[:10]
    
    
    @staticmethod
    def create_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Create comprehensive dataset summary.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with dataset summary
        """
        try:
            # Basic info
            summary = {
                'shape': {
                    'rows': int(df.shape[0]),
                    'columns': int(df.shape[1])
                },
                'columns': list(df.columns),
                'data_types': df.dtypes.astype(str).to_dict(),
                'memory_usage': {
                    'total_mb': float(df.memory_usage(deep=True).sum() / 1024 / 1024),
                    'per_column': df.memory_usage(deep=True).to_dict()
                }
            }
            
            # Missing values
            missing = df.isnull().sum()
            summary['missing_values'] = {
                'count': missing.to_dict(),
                'percentage': (missing / len(df) * 100).to_dict(),
                'total_missing': int(missing.sum())
            }
            
            # Duplicate rows
            summary['duplicates'] = {
                'count': int(df.duplicated().sum()),
                'percentage': float(df.duplicated().sum() / len(df) * 100)
            }
            
            # Numeric columns statistics
            numeric_df = df.select_dtypes(include=['number'])
            if not numeric_df.empty:
                summary['numeric_statistics'] = {
                    col: {
                        'mean': ReportGenerator._safe_float(numeric_df[col].mean()),
                        'median': ReportGenerator._safe_float(numeric_df[col].median()),
                        'std': ReportGenerator._safe_float(numeric_df[col].std()),
                        'min': ReportGenerator._safe_float(numeric_df[col].min()),
                        'max': ReportGenerator._safe_float(numeric_df[col].max()),
                        'q25': ReportGenerator._safe_float(numeric_df[col].quantile(0.25)),
                        'q75': ReportGenerator._safe_float(numeric_df[col].quantile(0.75))
                    }
                    for col in numeric_df.columns
                }
            
            # Categorical columns
            categorical_df = df.select_dtypes(include=['object', 'category'])
            if not categorical_df.empty:
                summary['categorical_statistics'] = {
                    col: {
                        'unique_count': int(categorical_df[col].nunique()),
                        'top_values': categorical_df[col].value_counts().head(10).to_dict(),
                        'most_common': str(categorical_df[col].mode()[0]) if len(categorical_df[col].mode()) > 0 else None
                    }
                    for col in categorical_df.columns
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating dataset summary: {str(e)}")
            return {'error': str(e)}
    
    
    @staticmethod
    def create_visualizations(df: pd.DataFrame, max_plots: int = 10) -> List[Dict[str, Any]]:
        """
        Create visualizations for the report.
        
        Args:
            df: Input DataFrame
            max_plots: Maximum number of plots to generate
            
        Returns:
            List of visualization configurations
        """
        visualizations = []
        
        try:
            # 1. Missing values heatmap
            missing = df.isnull().sum()
            if missing.sum() > 0:
                fig = go.Figure(data=[go.Bar(
                    x=missing.index.tolist(),
                    y=missing.values.tolist(),
                    marker_color='indianred'
                )])
                fig.update_layout(
                    title='Missing Values by Column',
                    xaxis_title='Column',
                    yaxis_title='Missing Count',
                    height=400
                )
                visualizations.append({
                    'type': 'missing_values',
                    'title': 'Missing Values Analysis',
                    'config': fig.to_json()
                })
            
            # 2. Data types distribution
            dtype_counts = df.dtypes.astype(str).value_counts()
            fig = go.Figure(data=[go.Pie(
                labels=dtype_counts.index.tolist(),
                values=dtype_counts.values.tolist(),
                hole=0.3
            )])
            fig.update_layout(title='Data Types Distribution', height=400)
            visualizations.append({
                'type': 'data_types',
                'title': 'Data Types Distribution',
                'config': fig.to_json()
            })
            
            # 3. Numeric distributions (first 5 numeric columns)
            numeric_cols = df.select_dtypes(include=['number']).columns[:5]
            for col in numeric_cols:
                if len(visualizations) >= max_plots:
                    break
                    
                fig = go.Figure(data=[go.Histogram(
                    x=df[col].dropna(),
                    nbinsx=30,
                    marker_color='steelblue'
                )])
                fig.update_layout(
                    title=f'Distribution of {col}',
                    xaxis_title=col,
                    yaxis_title='Frequency',
                    height=400
                )
                visualizations.append({
                    'type': 'histogram',
                    'column': col,
                    'title': f'Distribution of {col}',
                    'config': fig.to_json()
                })
            
            # 4. Correlation heatmap (if multiple numeric columns)
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr()
                fig = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns.tolist(),
                    y=corr_matrix.columns.tolist(),
                    colorscale='RdBu',
                    zmid=0
                ))
                fig.update_layout(
                    title='Correlation Matrix',
                    height=500
                )
                visualizations.append({
                    'type': 'correlation',
                    'title': 'Feature Correlations',
                    'config': fig.to_json()
                })
            
            # 5. Top categorical values (first 3 categorical columns)
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns[:3]
            for col in categorical_cols:
                if len(visualizations) >= max_plots:
                    break
                
                value_counts = df[col].value_counts().head(10)
                fig = go.Figure(data=[go.Bar(
                    x=value_counts.index.tolist(),
                    y=value_counts.values.tolist(),
                    marker_color='lightseagreen'
                )])
                fig.update_layout(
                    title=f'Top Values in {col}',
                    xaxis_title=col,
                    yaxis_title='Count',
                    height=400
                )
                visualizations.append({
                    'type': 'categorical',
                    'column': col,
                    'title': f'Top Values in {col}',
                    'config': fig.to_json()
                })
            
            logger.info(f"Generated {len(visualizations)} visualizations")
            return visualizations
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            return []
    
    
    @staticmethod
    def create_quality_score_visualization(score: float, breakdown: Dict[str, float]) -> Dict[str, Any]:
        """
        Create data quality score visualization.
        
        Args:
            score: Overall quality score (0-100)
            breakdown: Score breakdown by category
            
        Returns:
            Visualization configuration
        """
        try:
            # Gauge chart for overall score
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Data Quality Score"},
                delta={'reference': 80},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 75], 'color': "gray"},
                        {'range': [75, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=300)
            
            return {
                'type': 'quality_score',
                'title': 'Data Quality Score',
                'config': fig.to_json(),
                'score': score,
                'breakdown': breakdown
            }
            
        except Exception as e:
            logger.error(f"Error creating quality score visualization: {str(e)}")
            return {'error': str(e)}
    
    
    @staticmethod
    def create_before_after_comparison(
        before_df: pd.DataFrame,
        after_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Create before/after comparison for cleaned dataset.
        
        Args:
            before_df: Original DataFrame
            after_df: Cleaned DataFrame
            
        Returns:
            Comparison statistics
        """
        try:
            comparison = {
                'shape': {
                    'before': {'rows': int(before_df.shape[0]), 'columns': int(before_df.shape[1])},
                    'after': {'rows': int(after_df.shape[0]), 'columns': int(after_df.shape[1])}
                },
                'missing_values': {
                    'before': int(before_df.isnull().sum().sum()),
                    'after': int(after_df.isnull().sum().sum()),
                    'reduction': int(before_df.isnull().sum().sum() - after_df.isnull().sum().sum())
                },
                'duplicates': {
                    'before': int(before_df.duplicated().sum()),
                    'after': int(after_df.duplicated().sum()),
                    'reduction': int(before_df.duplicated().sum() - after_df.duplicated().sum())
                }
            }
            
            # Create comparison visualization
            metrics = ['Missing Values', 'Duplicates', 'Rows']
            before_vals = [
                comparison['missing_values']['before'],
                comparison['duplicates']['before'],
                comparison['shape']['before']['rows']
            ]
            after_vals = [
                comparison['missing_values']['after'],
                comparison['duplicates']['after'],
                comparison['shape']['after']['rows']
            ]
            
            fig = go.Figure(data=[
                go.Bar(name='Before', x=metrics, y=before_vals, marker_color='indianred'),
                go.Bar(name='After', x=metrics, y=after_vals, marker_color='lightseagreen')
            ])
            fig.update_layout(
                title='Before vs After Comparison',
                barmode='group',
                height=400
            )
            
            comparison['visualization'] = fig.to_json()
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error creating before/after comparison: {str(e)}")
            return {'error': str(e)}
    
    
    @staticmethod
    def generate_full_report(
        df: pd.DataFrame,
        report_name: str,
        description: Optional[str] = None,
        data_quality_score: Optional[float] = None,
        pipeline_steps: Optional[List[Dict[str, Any]]] = None,
        before_df: Optional[pd.DataFrame] = None,
        cleaned_dataset_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete report with all components.
        
        Args:
            df: Current DataFrame
            report_name: Name of the report
            description: Optional report description
            data_quality_score: Data quality score
            pipeline_steps: List of transformation steps applied
            before_df: Original DataFrame for before/after comparison
            cleaned_dataset_path: Path to saved cleaned dataset
            
        Returns:
            Complete report dictionary
        """
        try:
            logger.info(f"Generating full report: {report_name}")
            
            report = {
                'report_id': ReportGenerator.generate_report_id(),
                'report_name': report_name,
                'description': description or f"Analysis report for {report_name}",
                'created_at': datetime.utcnow().isoformat(),
                'dataset_summary': ReportGenerator.create_dataset_summary(df),
                'visualizations': ReportGenerator.create_visualizations(df),
                'pipeline_steps': pipeline_steps or [],
                'cleaned_dataset_path': cleaned_dataset_path
            }
            
            # Add quality score visualization
            if data_quality_score is not None:
                report['data_quality_score'] = data_quality_score
                # Note: breakdown would come from calculate_data_quality_score function
                report['quality_visualization'] = ReportGenerator.create_quality_score_visualization(
                    data_quality_score, 
                    {}  # Breakdown not available in this context
                )
            
            # Add before/after comparison
            if before_df is not None:
                report['before_after_comparison'] = ReportGenerator.create_before_after_comparison(
                    before_df, df
                )
            
            logger.info(f"Report generated successfully: {report['report_id']}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating full report: {str(e)}")
            raise ValueError(f"Failed to generate report: {str(e)}")


def generate_report(
    df: pd.DataFrame,
    report_name: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to generate a report.
    
    Args:
        df: DataFrame to analyze
        report_name: Name of the report
        **kwargs: Additional arguments passed to generate_full_report
        
    Returns:
        Complete report dictionary
    """
    return ReportGenerator.generate_full_report(df, report_name, **kwargs)


def create_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Create dataset summary."""
    return ReportGenerator.create_dataset_summary(df)


def create_visualizations(df: pd.DataFrame, max_plots: int = 10) -> List[Dict[str, Any]]:
    """Create visualizations."""
    return ReportGenerator.create_visualizations(df, max_plots)


def create_before_after_comparison(before_df: pd.DataFrame, after_df: pd.DataFrame) -> Dict[str, Any]:
    """Create before/after comparison."""
    return ReportGenerator.create_before_after_comparison(before_df, after_df)
