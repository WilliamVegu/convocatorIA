"""Port interface for public GitHub repository and profile auditing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any
from src.domain.entities import GitHubAudit


class GitHubPort(ABC):
    """Abstract port for querying and auditing candidate's public technical activity."""

    @abstractmethod
    def audit_user(self, username_or_url: str) -> GitHubAudit:
        """Audit candidate's public GitHub activity, languages and contributions."""
        pass
