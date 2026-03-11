"""
Dataset Registry Module
Manages public and private datasets with cloning capabilities.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
import logging
import uuid
from datetime import datetime
from database_models import Dataset, db, VisibilityType
import os
import json

logger = logging.getLogger(__name__)


class DatasetRegistry:
    """Manages dataset registration, visibility, and cloning."""
    
    @staticmethod
    def generate_dataset_id() -> str:
        """Generate unique dataset ID."""
        return uuid.uuid4().hex[:12]
    
    
    @staticmethod
    def register_dataset(
        df: pd.DataFrame,
        dataset_name: str,
        owner_id: int,
        description: Optional[str] = None,
        source_type: str = 'upload',
        source_config: Optional[Dict[str, Any]] = None,
        visibility: VisibilityType = VisibilityType.PRIVATE,
        pipeline_config: Optional[Dict[str, Any]] = None,
        data_quality_score: Optional[float] = None,
        save_file: bool = True
    ) -> Dataset:
        """
        Register a new dataset in the registry.
        
        Args:
            df: DataFrame to register
            dataset_name: Name of the dataset
            owner_id: User ID of the owner
            description: Optional description
            source_type: Type of data source
            source_config: Source configuration (sanitized)
            visibility: Dataset visibility
            pipeline_config: Applied transformation pipeline
            data_quality_score: Data quality score
            save_file: Whether to save the DataFrame to disk
            
        Returns:
            Dataset model instance
        """
        try:
            session = db.get_session()
            
            # Generate unique ID
            dataset_id = DatasetRegistry.generate_dataset_id()
            
            # Save DataFrame to file if requested
            file_path = None
            if save_file:
                datasets_dir = os.path.join(os.path.dirname(__file__), 'datasets')
                os.makedirs(datasets_dir, exist_ok=True)
                file_path = os.path.join(datasets_dir, f"{dataset_id}.parquet")
                df.to_parquet(file_path, index=False)
            
            # Create columns info
            columns_info = {
                'names': list(df.columns),
                'types': df.dtypes.astype(str).to_dict(),
                'sample_values': df.head(3).astype(str).to_dict('records')
            }
            
            # Create dataset record
            dataset = Dataset(
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                description=description,
                owner_id=owner_id,
                source_type=source_type,
                source_config=source_config,
                file_path=file_path,
                row_count=int(df.shape[0]),
                column_count=int(df.shape[1]),
                columns_info=columns_info,
                data_quality_score=data_quality_score,
                pipeline_applied=pipeline_config is not None,
                pipeline_config=pipeline_config,
                visibility=visibility
            )
            
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            
            logger.info(f"Dataset registered: {dataset_id} - {dataset_name}")
            session.close()
            return dataset
            
        except Exception as e:
            logger.error(f"Error registering dataset: {str(e)}")
            session.rollback()
            session.close()
            raise ValueError(f"Failed to register dataset: {str(e)}")
    
    
    @staticmethod
    def get_dataset(dataset_id: str) -> Optional[Dataset]:
        """
        Get dataset by ID.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Dataset model instance or None
        """
        try:
            session = db.get_session()
            dataset = session.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
            session.close()
            return dataset
        except Exception as e:
            logger.error(f"Error getting dataset: {str(e)}")
            return None
    
    
    @staticmethod
    def load_dataset_dataframe(dataset_id: str) -> Optional[pd.DataFrame]:
        """
        Load DataFrame from registered dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            DataFrame or None
        """
        try:
            dataset = DatasetRegistry.get_dataset(dataset_id)
            if dataset and dataset.file_path and os.path.exists(dataset.file_path):
                df = pd.read_parquet(dataset.file_path)
                logger.info(f"Loaded dataset {dataset_id}: {df.shape}")
                return df
            else:
                logger.warning(f"Dataset file not found: {dataset_id}")
                return None
        except Exception as e:
            logger.error(f"Error loading dataset DataFrame: {str(e)}")
            return None
    
    
    @staticmethod
    def list_public_datasets(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all public datasets.
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of dataset dictionaries
        """
        try:
            session = db.get_session()
            datasets = session.query(Dataset)\
                .filter(Dataset.visibility == VisibilityType.PUBLIC)\
                .order_by(Dataset.created_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            result = [
                {
                    'dataset_id': d.dataset_id,
                    'dataset_name': d.dataset_name,
                    'description': d.description,
                    'owner_id': d.owner_id,
                    'row_count': d.row_count,
                    'column_count': d.column_count,
                    'columns_info': d.columns_info,
                    'data_quality_score': d.data_quality_score,
                    'pipeline_applied': d.pipeline_applied,
                    'created_at': d.created_at.isoformat() if d.created_at else None
                }
                for d in datasets
            ]
            
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error listing public datasets: {str(e)}")
            return []
    
    
    @staticmethod
    def list_user_datasets(owner_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all datasets for a specific user.
        
        Args:
            owner_id: User ID
            limit: Maximum number of results
            
        Returns:
            List of dataset dictionaries
        """
        try:
            session = db.get_session()
            datasets = session.query(Dataset)\
                .filter(Dataset.owner_id == owner_id)\
                .order_by(Dataset.created_at.desc())\
                .limit(limit)\
                .all()
            
            result = [
                {
                    'dataset_id': d.dataset_id,
                    'dataset_name': d.dataset_name,
                    'description': d.description,
                    'row_count': d.row_count,
                    'column_count': d.column_count,
                    'data_quality_score': d.data_quality_score,
                    'visibility': d.visibility.value,
                    'pipeline_applied': d.pipeline_applied,
                    'created_at': d.created_at.isoformat() if d.created_at else None
                }
                for d in datasets
            ]
            
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error listing user datasets: {str(e)}")
            return []
    
    
    @staticmethod
    def update_dataset_visibility(dataset_id: str, visibility: VisibilityType) -> bool:
        """
        Update dataset visibility.
        
        Args:
            dataset_id: Dataset ID
            visibility: New visibility setting
            
        Returns:
            True if successful
        """
        try:
            session = db.get_session()
            dataset = session.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
            
            if dataset:
                dataset.visibility = visibility
                dataset.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"Updated dataset {dataset_id} visibility to {visibility}")
                session.close()
                return True
            else:
                session.close()
                return False
                
        except Exception as e:
            logger.error(f"Error updating dataset visibility: {str(e)}")
            session.rollback()
            session.close()
            return False
    
    
    @staticmethod
    def clone_pipeline(dataset_id: str, target_user_id: int) -> Optional[Dict[str, Any]]:
        """
        Clone a dataset's transformation pipeline to another user's workspace.
        
        Args:
            dataset_id: Source dataset ID
            target_user_id: Target user ID
            
        Returns:
            Cloned pipeline configuration or None
        """
        try:
            dataset = DatasetRegistry.get_dataset(dataset_id)
            
            if not dataset:
                logger.warning(f"Dataset not found: {dataset_id}")
                return None
            
            if dataset.visibility == VisibilityType.PRIVATE and dataset.owner_id != target_user_id:
                logger.warning(f"Access denied to private dataset: {dataset_id}")
                return None
            
            if not dataset.pipeline_config:
                logger.warning(f"No pipeline configured for dataset: {dataset_id}")
                return None
            
            # Return pipeline configuration for cloning
            cloned_pipeline = {
                'source_dataset_id': dataset_id,
                'source_dataset_name': dataset.dataset_name,
                'pipeline_steps': dataset.pipeline_config,
                'cloned_at': datetime.utcnow().isoformat(),
                'cloned_by_user_id': target_user_id
            }
            
            logger.info(f"Pipeline cloned from {dataset_id} to user {target_user_id}")
            return cloned_pipeline
            
        except Exception as e:
            logger.error(f"Error cloning pipeline: {str(e)}")
            return None
    
    
    @staticmethod
    def search_datasets(
        query: str,
        visibility: Optional[VisibilityType] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search datasets by name or description.
        
        Args:
            query: Search query
            visibility: Optional visibility filter
            limit: Maximum number of results
            
        Returns:
            List of matching datasets
        """
        try:
            session = db.get_session()
            
            filters = [
                Dataset.dataset_name.ilike(f'%{query}%') | 
                Dataset.description.ilike(f'%{query}%')
            ]
            
            if visibility:
                filters.append(Dataset.visibility == visibility)
            
            datasets = session.query(Dataset)\
                .filter(*filters)\
                .order_by(Dataset.created_at.desc())\
                .limit(limit)\
                .all()
            
            result = [
                {
                    'dataset_id': d.dataset_id,
                    'dataset_name': d.dataset_name,
                    'description': d.description,
                    'owner_id': d.owner_id,
                    'row_count': d.row_count,
                    'column_count': d.column_count,
                    'data_quality_score': d.data_quality_score,
                    'visibility': d.visibility.value,
                    'created_at': d.created_at.isoformat() if d.created_at else None
                }
                for d in datasets
            ]
            
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error searching datasets: {str(e)}")
            return []
    
    
    @staticmethod
    def delete_dataset(dataset_id: str, owner_id: int) -> bool:
        """
        Delete a dataset (only by owner).
        
        Args:
            dataset_id: Dataset ID
            owner_id: User ID (must match owner)
            
        Returns:
            True if successful
        """
        try:
            session = db.get_session()
            dataset = session.query(Dataset)\
                .filter(Dataset.dataset_id == dataset_id, Dataset.owner_id == owner_id)\
                .first()
            
            if dataset:
                # Delete file if exists
                if dataset.file_path and os.path.exists(dataset.file_path):
                    os.remove(dataset.file_path)
                
                session.delete(dataset)
                session.commit()
                logger.info(f"Dataset deleted: {dataset_id}")
                session.close()
                return True
            else:
                session.close()
                return False
                
        except Exception as e:
            logger.error(f"Error deleting dataset: {str(e)}")
            session.rollback()
            session.close()
            return False


# Convenience functions

def register_dataset(df: pd.DataFrame, dataset_name: str, owner_id: int, **kwargs) -> Dataset:
    """Register a dataset."""
    return DatasetRegistry.register_dataset(df, dataset_name, owner_id, **kwargs)


def get_dataset(dataset_id: str) -> Optional[Dataset]:
    """Get dataset by ID."""
    return DatasetRegistry.get_dataset(dataset_id)


def load_dataset_dataframe(dataset_id: str) -> Optional[pd.DataFrame]:
    """Load dataset DataFrame."""
    return DatasetRegistry.load_dataset_dataframe(dataset_id)


def list_public_datasets(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """List public datasets."""
    return DatasetRegistry.list_public_datasets(limit, offset)


def clone_pipeline(dataset_id: str, target_user_id: int) -> Optional[Dict[str, Any]]:
    """Clone pipeline from dataset."""
    return DatasetRegistry.clone_pipeline(dataset_id, target_user_id)
