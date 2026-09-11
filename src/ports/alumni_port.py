"""Abstract port for Alumni TCS (Boomerang) detection."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AlumniPort(ABC):
    """Port interface for detecting and querying former TCS collaborators."""

    @abstractmethod
    def detect_alumni(
        self,
        dni: Optional[str] = None,
        email: Optional[str] = None,
        nombre_completo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check if an applicant is a former employee.
        Returns dict with is_alumni (bool), estatus_recontratacion, and alert metadata.
        """
        pass
