"""Abstract port for audit logging and non-repudiation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime


class AuditPort(ABC):
    """Port interface for append-only audit trail logging."""

    @abstractmethod
    def record_mutation(
        self,
        usuario_id: str,
        usuario_email: str,
        rol_en_momento: str,
        tipo_accion: str,
        entidad_objeto: str,
        registro_id: str,
        version_registro: Optional[int] = None,
        valores_previos: Optional[Dict[str, Any]] = None,
        valores_nuevos: Optional[Dict[str, Any]] = None,
        justificacion_operativa: Optional[str] = None,
        ip_address: str = "127.0.0.1",
        session_id: Optional[str] = None,
    ) -> str:
        """Record an entity creation or update event."""
        pass

    @abstractmethod
    def record_file_upload(
        self,
        usuario_id: str,
        usuario_email: str,
        rol_en_momento: str,
        entidad_objeto: str,
        registro_id: str,
        nombre_archivo: str,
        hash_sha256: str,
        ip_address: str = "127.0.0.1",
    ) -> str:
        """Record an uploaded file event (CV or Adecco batch)."""
        pass

    @abstractmethod
    def record_export(
        self,
        usuario_id: str,
        usuario_email: str,
        rol_en_momento: str,
        entidad_objeto: str,
        registro_id: str,
        hash_sha256: str,
        ip_address: str = "127.0.0.1",
    ) -> str:
        """Record an official report download or export under Ley 29733."""
        pass

    @abstractmethod
    def record_security_event(
        self,
        usuario_id: str,
        usuario_email: str,
        rol_en_momento: str,
        tipo_accion: str,
        justificacion: str,
        ip_address: str = "127.0.0.1",
    ) -> str:
        """Record authentication or access-denied security events."""
        pass
