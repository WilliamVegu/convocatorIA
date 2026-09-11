"""Abstract port for Peruvian national identity resolution (DNI/RENIEC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class DNIPort(ABC):
    """Port interface for resolving Peruvian identity documents."""

    @abstractmethod
    def resolve_dni(self, dni: str) -> Dict[str, Any]:
        """
        Resolve citizen identity by DNI:
        1. Check local cache (cache_dni_reniec).
        2. If missed, query APIsPERU endpoint.
        3. If offline/error, return fallback structure with regularizacion_pendiente=True.
        """
        pass

    def resolve_ruc(self, ruc: str) -> Dict[str, Any]:
        """
        Resolve company / taxpayer identity by RUC via SUNAT endpoint.
        """
        return {"success": False, "mensaje": "No implementado", "datos": {}}

