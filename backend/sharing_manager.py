"""
Sharing Manager Module
Manages sharing of datasets, reports, and pipelines.
"""

from typing import Dict, List, Any, Optional
import logging
import uuid
from datetime import datetime, timedelta
from database_models import Share, ResourceType, AccessLevel, db

logger = logging.getLogger(__name__)


class SharingManager:
    """Manages resource sharing and permissions."""
    
    @staticmethod
    def generate_share_id() -> str:
        """Generate unique share ID."""
        return uuid.uuid4().hex[:10]
    
    
    @staticmethod
    def create_share(
        resource_type: ResourceType,
        resource_id: int,
        owner_id: int,
        access_level: AccessLevel = AccessLevel.VIEWER,
        shared_with_user_id: Optional[int] = None,
        is_public_link: bool = False,
        expires_in_days: Optional[int] = None
    ) -> Optional[Share]:
        """
        Create a new share.
        
        Args:
            resource_type: Type of resource (dataset/report/pipeline)
            resource_id: ID of the resource
            owner_id: Owner user ID
            access_level: Access level (viewer/editor/owner)
            shared_with_user_id: Target user ID (None for public links)
            is_public_link: Whether this is a public link
            expires_in_days: Optional expiration in days
            
        Returns:
            Share model instance or None
        """
        try:
            session = db.get_session()
            
            share_id = SharingManager.generate_share_id()
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            share = Share(
                share_id=share_id,
                resource_type=resource_type,
                resource_id=resource_id,
                owner_id=owner_id,
                shared_with_user_id=shared_with_user_id,
                access_level=access_level,
                is_public_link=is_public_link,
                link_expires_at=expires_at
            )
            
            session.add(share)
            session.commit()
            session.refresh(share)
            
            logger.info(f"Share created: {share_id} for {resource_type.value}")
            session.close()
            return share
            
        except Exception as e:
            logger.error(f"Error creating share: {str(e)}")
            session.rollback()
            session.close()
            return None
    
    
    @staticmethod
    def get_share(share_id: str) -> Optional[Share]:
        """
        Get share by ID.
        
        Args:
            share_id: Share ID
            
        Returns:
            Share model instance or None
        """
        try:
            session = db.get_session()
            share = session.query(Share).filter(Share.share_id == share_id).first()
            
            # Check expiration
            if share and share.link_expires_at:
                if datetime.utcnow() > share.link_expires_at:
                    logger.warning(f"Share link expired: {share_id}")
                    session.close()
                    return None
            
            session.close()
            return share
            
        except Exception as e:
            logger.error(f"Error getting share: {str(e)}")
            return None
    
    
    @staticmethod
    def check_access(
        share_id: str,
        user_id: Optional[int] = None,
        required_level: AccessLevel = AccessLevel.VIEWER
    ) -> bool:
        """
        Check if user has access to shared resource.
        
        Args:
            share_id: Share ID
            user_id: User ID (None for anonymous)
            required_level: Minimum required access level
            
        Returns:
            True if access is granted
        """
        try:
            share = SharingManager.get_share(share_id)
            
            if not share:
                return False
            
            # Public links allow anyone
            if share.is_public_link:
                # Update access count
                SharingManager.record_access(share_id)
                return True
            
            # Check user-specific sharing
            if user_id:
                if share.shared_with_user_id == user_id or share.owner_id == user_id:
                    # Check access level
                    access_levels = {
                        AccessLevel.VIEWER: 1,
                        AccessLevel.EDITOR: 2,
                        AccessLevel.OWNER: 3
                    }
                    
                    if access_levels.get(share.access_level, 0) >= access_levels.get(required_level, 0):
                        SharingManager.record_access(share_id)
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking access: {str(e)}")
            return False
    
    
    @staticmethod
    def record_access(share_id: str):
        """
        Record access to shared resource.
        
        Args:
            share_id: Share ID
        """
        try:
            session = db.get_session()
            share = session.query(Share).filter(Share.share_id == share_id).first()
            
            if share:
                share.access_count += 1
                share.last_accessed = datetime.utcnow()
                session.commit()
            
            session.close()
            
        except Exception as e:
            logger.error(f"Error recording access: {str(e)}")
            session.rollback()
            session.close()
    
    
    @staticmethod
    def list_shares_by_resource(
        resource_type: ResourceType,
        resource_id: int
    ) -> List[Dict[str, Any]]:
        """
        List all shares for a specific resource.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            
        Returns:
            List of share dictionaries
        """
        try:
            session = db.get_session()
            shares = session.query(Share)\
                .filter(
                    Share.resource_type == resource_type,
                    Share.resource_id == resource_id
                )\
                .all()
            
            result = [
                {
                    'share_id': s.share_id,
                    'resource_type': s.resource_type.value,
                    'owner_id': s.owner_id,
                    'shared_with_user_id': s.shared_with_user_id,
                    'access_level': s.access_level.value,
                    'is_public_link': s.is_public_link,
                    'link_expires_at': s.link_expires_at.isoformat() if s.link_expires_at else None,
                    'access_count': s.access_count,
                    'created_at': s.created_at.isoformat() if s.created_at else None
                }
                for s in shares
            ]
            
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error listing shares: {str(e)}")
            return []
    
    
    @staticmethod
    def list_shares_for_user(user_id: int) -> List[Dict[str, Any]]:
        """
        List all resources shared with a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of shared resource dictionaries
        """
        try:
            session = db.get_session()
            shares = session.query(Share)\
                .filter(Share.shared_with_user_id == user_id)\
                .order_by(Share.created_at.desc())\
                .all()
            
            result = [
                {
                    'share_id': s.share_id,
                    'resource_type': s.resource_type.value,
                    'resource_id': s.resource_id,
                    'owner_id': s.owner_id,
                    'access_level': s.access_level.value,
                    'created_at': s.created_at.isoformat() if s.created_at else None
                }
                for s in shares
            ]
            
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error listing user shares: {str(e)}")
            return []
    
    
    @staticmethod
    def create_public_link(
        resource_type: ResourceType,
        resource_id: int,
        owner_id: int,
        access_level: AccessLevel = AccessLevel.VIEWER,
        expires_in_days: Optional[int] = None
    ) -> Optional[str]:
        """
        Create a public sharing link.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            owner_id: Owner ID
            access_level: Access level
            expires_in_days: Optional expiration
            
        Returns:
            Share ID (public link) or None
        """
        share = SharingManager.create_share(
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=owner_id,
            access_level=access_level,
            is_public_link=True,
            expires_in_days=expires_in_days
        )
        
        return share.share_id if share else None
    
    
    @staticmethod
    def share_with_user(
        resource_type: ResourceType,
        resource_id: int,
        owner_id: int,
        target_user_id: int,
        access_level: AccessLevel = AccessLevel.VIEWER
    ) -> Optional[str]:
        """
        Share resource with specific user.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            owner_id: Owner ID
            target_user_id: User to share with
            access_level: Access level
            
        Returns:
            Share ID or None
        """
        share = SharingManager.create_share(
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=owner_id,
            shared_with_user_id=target_user_id,
            access_level=access_level,
            is_public_link=False
        )
        
        return share.share_id if share else None
    
    
    @staticmethod
    def revoke_share(share_id: str, owner_id: int) -> bool:
        """
        Revoke a share (only by owner).
        
        Args:
            share_id: Share ID
            owner_id: Owner ID (must match)
            
        Returns:
            True if successful
        """
        try:
            session = db.get_session()
            share = session.query(Share)\
                .filter(Share.share_id == share_id, Share.owner_id == owner_id)\
                .first()
            
            if share:
                session.delete(share)
                session.commit()
                logger.info(f"Share revoked: {share_id}")
                session.close()
                return True
            else:
                session.close()
                return False
                
        except Exception as e:
            logger.error(f"Error revoking share: {str(e)}")
            session.rollback()
            session.close()
            return False
    
    
    @staticmethod
    def update_access_level(
        share_id: str,
        owner_id: int,
        new_access_level: AccessLevel
    ) -> bool:
        """
        Update share access level.
        
        Args:
            share_id: Share ID
            owner_id: Owner ID
            new_access_level: New access level
            
        Returns:
            True if successful
        """
        try:
            session = db.get_session()
            share = session.query(Share)\
                .filter(Share.share_id == share_id, Share.owner_id == owner_id)\
                .first()
            
            if share:
                share.access_level = new_access_level
                session.commit()
                logger.info(f"Share {share_id} access level updated to {new_access_level}")
                session.close()
                return True
            else:
                session.close()
                return False
                
        except Exception as e:
            logger.error(f"Error updating access level: {str(e)}")
            session.rollback()
            session.close()
            return False


# Convenience functions

def create_public_link(
    resource_type: ResourceType,
    resource_id: int,
    owner_id: int,
    **kwargs
) -> Optional[str]:
    """Create public sharing link."""
    return SharingManager.create_public_link(resource_type, resource_id, owner_id, **kwargs)


def share_with_user(
    resource_type: ResourceType,
    resource_id: int,
    owner_id: int,
    target_user_id: int,
    access_level: AccessLevel = AccessLevel.VIEWER
) -> Optional[str]:
    """Share with specific user."""
    return SharingManager.share_with_user(
        resource_type, resource_id, owner_id, target_user_id, access_level
    )


def check_access(share_id: str, user_id: Optional[int] = None, **kwargs) -> bool:
    """Check user access to shared resource."""
    return SharingManager.check_access(share_id, user_id, **kwargs)


def revoke_share(share_id: str, owner_id: int) -> bool:
    """Revoke a share."""
    return SharingManager.revoke_share(share_id, owner_id)
