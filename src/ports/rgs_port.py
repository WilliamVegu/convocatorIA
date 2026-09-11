"""Port interface for normalizing unstructured client requests (RGS to JD)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from src.domain.entities import RGSNormalizado


class RGSPort(ABC):
    """Abstract port for transforming messy text into structured JD and boolean search strings."""

    @abstractmethod
    def normalize_raw_text(self, raw_text: str, cliente_sugerido: str = "BCP") -> RGSNormalizado:
        """Parse raw email or message into structured RGS."""
        pass
