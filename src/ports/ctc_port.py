"""Abstract port for Peruvian labor cost (CTC) simulation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class CTCPort(ABC):
    """Port interface for CTC financial calculation with Factor 1.56."""

    @abstractmethod
    def calculate(
        self,
        tipo_expectativa: str,
        monto_declarado: float,
        ctc_presupuestado: Optional[float] = None,
        factor_ctc: float = 1.56,
    ) -> Dict[str, Any]:
        """Perform CTC calculation with mathematical zero-division guards."""
        pass
