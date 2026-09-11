"""Port interface for semantic Fit & Gap comparison between CV and vacancy requirements."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.domain.entities import FitGapResult


class FitGapPort(ABC):
    """Abstract port for evaluating technical match score (0-100%), strengths and gaps."""

    @abstractmethod
    def compare_cv_vs_rgs(
        self,
        cv_text: str,
        cv_skills: List[Dict[str, Any]],
        perfil_puesto: str,
        must_have: List[str],
        nice_to_have: List[str],
    ) -> FitGapResult:
        """Compare candidate CV against RGS requirements."""
        pass
