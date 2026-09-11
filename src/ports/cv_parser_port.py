"""Abstract port for structured CV and CUL extraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, BinaryIO
from pathlib import Path


class CVParserPort(ABC):
    """Port interface for extracting structured competencies from CV documents."""

    @abstractmethod
    def extract_from_pdf(self, file_content_or_path: bytes | str | Path) -> Dict[str, Any]:
        """Extract structured technical skills, experience, and education, strictly omitting protected demographic attributes."""
        pass
