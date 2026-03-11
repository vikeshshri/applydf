"""
User Management Module
Handles user authentication and profile management.
"""

from typing import Optional, Dict, Any
import logging
import hashlib
import secrets
from datetime import datetime
from database_models import User, db

logger = logging.getLogger(__name__)


class UserManager:
    """Manages user accounts and authentication."""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash password with salt.
        
        Args:
            password: Plain text password
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        
        return hashed.hex(), salt
    
    
    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Optional[User]:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            email: User email
            password: Plain text password (will be hashed)
            full_name: Optional full name
            
        Returns:
            User model instance or None
        """
        try:
            session = db.get_session()
            
            # Check if username or email already exists
            existing = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing:
                logger.warning(f"Username or email already exists: {username}, {email}")
                session.close()
                return None
            
            # Hash password
            password_hash, salt = UserManager.hash_password(password)
            stored_hash = f"{salt}:{password_hash}"
            
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=stored_hash,
                full_name=full_name,
                is_active=True
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            logger.info(f"User created: {username} (ID: {user.id})")
            session.close()
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            session.rollback()
            session.close()
            return None
    
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User model instance if authenticated, None otherwise
        """
        try:
            session = db.get_session()
            
            # Find user by username or email
            user = session.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user or not user.is_active:
                session.close()
                return None
            
            # Verify password
            if ':' in user.password_hash:
                salt, stored_hash = user.password_hash.split(':', 1)
                computed_hash, _ = UserManager.hash_password(password, salt)
                
                if computed_hash == stored_hash:
                    # Update last login
                    user.last_login = datetime.utcnow()
                    session.commit()
                    session.refresh(user)
                    
                    logger.info(f"User authenticated: {username}")
                    session.close()
                    return user
            
            session.close()
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            session.close()
            return None
    
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User model instance or None
        """
        try:
            session = db.get_session()
            user = session.query(User).filter(User.id == user_id).first()
            session.close()
            return user
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User model instance or None
        """
        try:
            session = db.get_session()
            user = session.query(User).filter(User.username == username).first()
            session.close()
            return user
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    
    @staticmethod
    def update_user_profile(
        user_id: int,
        full_name: Optional[str] = None,
        email: Optional[str] = None
    ) -> bool:
        """
        Update user profile information.
        
        Args:
            user_id: User ID
            full_name: Optional new full name
            email: Optional new email
            
        Returns:
            True if successful
        """
        try:
            session = db.get_session()
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                session.close()
                return False
            
            if full_name:
                user.full_name = full_name
            
            if email:
                # Check if email is already taken
                existing = session.query(User).filter(
                    User.email == email,
                    User.id != user_id
                ).first()
                if existing:
                    logger.warning(f"Email already in use: {email}")
                    session.close()
                    return False
                user.email = email
            
            session.commit()
            logger.info(f"User profile updated: {user_id}")
            session.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            session.rollback()
            session.close()
            return False
    
    
    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            True if successful
        """
        try:
            session = db.get_session()
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                session.close()
                return False
            
            # Verify old password
            if ':' in user.password_hash:
                salt, stored_hash = user.password_hash.split(':', 1)
                computed_hash, _ = UserManager.hash_password(old_password, salt)
                
                if computed_hash != stored_hash:
                    logger.warning(f"Invalid old password for user {user_id}")
                    session.close()
                    return False
            
            # Hash new password
            new_hash, new_salt = UserManager.hash_password(new_password)
            user.password_hash = f"{new_salt}:{new_hash}"
            
            session.commit()
            logger.info(f"Password changed for user {user_id}")
            session.close()
            return True
            
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            session.rollback()
            session.close()
            return False
    
    
    @staticmethod
    def deactivate_user(user_id: int) -> bool:
        """
        Deactivate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            session = db.get_session()
            user = session.query(User).filter(User.id == user_id).first()
            
            if user:
                user.is_active = False
                session.commit()
                logger.info(f"User deactivated: {user_id}")
                session.close()
                return True
            
            session.close()
            return False
            
        except Exception as e:
            logger.error(f"Error deactivating user: {str(e)}")
            session.rollback()
            session.close()
            return False
    
    
    @staticmethod
    def get_demo_user() -> User:
        """
        Get or create demo user for testing.
        
        Returns:
            Demo user instance
        """
        try:
            session = db.get_session()
            demo_user = session.query(User).filter(User.username == 'demo').first()
            
            if not demo_user:
                # Create demo user
                password_hash, salt = UserManager.hash_password('demo123')
                demo_user = User(
                    username='demo',
                    email='demo@applydf.com',
                    password_hash=f"{salt}:{password_hash}",
                    full_name='Demo User',
                    is_active=True
                )
                session.add(demo_user)
                session.commit()
                session.refresh(demo_user)
                logger.info("Demo user created")
            
            session.close()
            return demo_user
            
        except Exception as e:
            logger.error(f"Error getting demo user: {str(e)}")
            return None


# Convenience functions

def create_user(username: str, email: str, password: str, **kwargs) -> Optional[User]:
    """Create a new user."""
    return UserManager.create_user(username, email, password, **kwargs)


def authenticate(username: str, password: str) -> Optional[User]:
    """Authenticate user."""
    return UserManager.authenticate(username, password)


def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID."""
    return UserManager.get_user_by_id(user_id)


def get_demo_user() -> User:
    """Get demo user."""
    return UserManager.get_demo_user()
