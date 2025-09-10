from dataclasses import dataclass
from typing import Optional
from utils.database import User
import hashlib


@dataclass
class UserInfo:
    """Data class to represent user information without exposing ORM details"""
    id: int
    name: str
    email: str
    preferred_class: Optional[str] = None

    @classmethod
    def from_orm(cls, user: User) -> 'UserInfo':
        """Convert ORM User object to UserInfo"""
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            preferred_class=user.preferred_class
        )


class Auth:
    def __init__(self):
        self._current_user: Optional[User] = None

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, name: str, email: str, password: str) -> tuple[bool, str]:
        """Register a new user with preferred_class as None initially"""
        try:
            # Check if email already exists
            if User.select().where(User.email == email).exists():
                return False, "Email already registered"

            # Create new user with hashed password and None preferred_class
            user = User.create(
                name=name,
                email=email,
                password=self._hash_password(password),
                preferred_class=None
            )
            self._current_user = user
            return True, "Registration successful"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    def login(self, email: str, password: str) -> tuple[bool, str]:
        """Login user with email and password"""
        try:
            user = User.get(User.email == email)
            if user and user.password == self._hash_password(password):
                self._current_user = user
                return True, "Login successful"
            return False, "Invalid email or password"
        except User.DoesNotExist:
            return False, "Invalid email or password"

    def update_name(self, new_name: str) -> tuple[bool, str]:
        """Update user's name"""
        if not self.is_authenticated():
            return False, "User not authenticated"

        try:
            query = User.update(name=new_name).where(
                User.id == self._current_user.id)
            query.execute()
            self._current_user.name = new_name
            return True, "Name updated successfully"
        except Exception as e:
            return False, f"Failed to update name: {str(e)}"

    def update_preferred_class(self, new_class: Optional[str]) -> tuple[bool, str]:
        """Update user's preferred class"""
        if not self.is_authenticated():
            return False, "User not authenticated"

        valid_classes = {'ECONOMY', 'BUSINESS', 'FIRST', None}
        if new_class not in valid_classes:
            return False, "Invalid class. Must be one of: ECONOMY, BUSINESS, FIRST"

        try:
            query = User.update(preferred_class=new_class).where(
                User.id == self._current_user.id)
            query.execute()
            self._current_user.preferred_class = new_class
            return True, "Preferred class updated successfully"
        except Exception as e:
            return False, f"Failed to update preferred class: {str(e)}"

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self._current_user is not None

    @property
    def current_user(self) -> Optional[UserInfo]:
        """Get current user information"""
        if self._current_user is None:
            return None
        return UserInfo.from_orm(self._current_user)

    def logout(self) -> tuple[bool, str]:
        """Logout current user"""
        self._current_user = None
        return True, "Logged out successfully"
