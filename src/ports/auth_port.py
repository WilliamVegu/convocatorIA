"""Abstract port for authentication and RBAC operations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime


class AuthPort(ABC):
    """Port interface for user authentication and authorization."""

    @abstractmethod
    def register_user(
        self,
        nombres_completos: str,
        email: str,
        password: str,
        actor_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a new user, defaulting to Compliance_Officer role."""
        pass

    @abstractmethod
    def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Authenticate user credentials and enforce lockout policy."""
        pass

    @abstractmethod
    def change_user_role(
        self,
        admin_user_id: str,
        target_user_id: str,
        new_role: str,
        justification: str,
        expected_version: int,
    ) -> Dict[str, Any]:
        """Elevate or change a user's RBAC role (restricted to Head of TA)."""
        pass

    @abstractmethod
    def unlock_user_account(
        self,
        admin_user_id: str,
        target_user_id: str,
        justification: str,
    ) -> Dict[str, Any]:
        """Manually unlock an account (restricted to Head of TA)."""
        pass
