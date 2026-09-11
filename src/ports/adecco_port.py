"""Abstract port for Adecco spreadsheet ingestion and processing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, BinaryIO
from pathlib import Path


class AdeccoPort(ABC):
    """Port interface for supplier payroll parsing and validation."""

    @abstractmethod
    def parse_spreadsheet(
        self,
        file_content_or_path: bytes | str | Path,
        filename: str = "planilla_adecco.xlsx",
    ) -> Dict[str, Any]:
        """Parse raw Excel/CSV with header alias tolerance and return normalized rows."""
        pass
