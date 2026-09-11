"""Audit application service for ATS Core MVP."""
from __future__ import annotations

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.ports.audit_port import AuditPort
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.persistence.models import BitacoraAuditoriaModel


class AuditService(AuditPort):
    """Application service for structured non-repudiable audit recording."""

    def __init__(self, audit_repository: AuditRepository):
        self.repository = audit_repository

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
        log_id = f"aud-{uuid.uuid4()}"
        self.repository.append_log(
            log_id=log_id,
            usuario_id=usuario_id,
            usuario_email=usuario_email,
            rol_en_momento=rol_en_momento,
            tipo_accion=tipo_accion,
            entidad_objeto=entidad_objeto,
            registro_id=registro_id,
            version_registro=version_registro,
            valores_previos=valores_previos,
            valores_nuevos=valores_nuevos,
            justificacion_operativa=justificacion_operativa,
            ip_address=ip_address,
            session_id=session_id,
        )
        return log_id

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
        log_id = f"aud-upload-{uuid.uuid4()}"
        self.repository.append_log(
            log_id=log_id,
            usuario_id=usuario_id,
            usuario_email=usuario_email,
            rol_en_momento=rol_en_momento,
            tipo_accion="Carga_Archivo",
            entidad_objeto=entidad_objeto,
            registro_id=registro_id,
            nombre_archivo_adjunto=nombre_archivo,
            hash_integridad_sha256=hash_sha256,
            ip_address=ip_address,
        )
        return log_id

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
        log_id = f"aud-exp-{uuid.uuid4()}"
        self.repository.append_log(
            log_id=log_id,
            usuario_id=usuario_id,
            usuario_email=usuario_email,
            rol_en_momento=rol_en_momento,
            tipo_accion="Exportacion",
            entidad_objeto=entidad_objeto,
            registro_id=registro_id,
            hash_integridad_sha256=hash_sha256,
            ip_address=ip_address,
        )
        return log_id

    def record_security_event(
        self,
        usuario_id: str,
        usuario_email: str,
        rol_en_momento: str,
        tipo_accion: str,
        justificacion: str,
        ip_address: str = "127.0.0.1",
    ) -> str:
        log_id = f"aud-sec-{uuid.uuid4()}"
        self.repository.append_log(
            log_id=log_id,
            usuario_id=usuario_id,
            usuario_email=usuario_email,
            rol_en_momento=rol_en_momento,
            tipo_accion=tipo_accion,
            entidad_objeto="Usuario",
            registro_id=usuario_id,
            justificacion_operativa=justificacion,
            ip_address=ip_address,
        )
        return log_id

    def list_logs(self, limit: int = 100, offset: int = 0) -> List[BitacoraAuditoriaModel]:
        return self.repository.list_logs(limit=limit, offset=offset)

    def filter_logs(
        self,
        usuario_email: Optional[str] = None,
        entidad_objeto: Optional[str] = None,
        tipo_accion: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BitacoraAuditoriaModel]:
        return self.repository.filter_logs(
            usuario_email=usuario_email,
            entidad_objeto=entidad_objeto,
            tipo_accion=tipo_accion,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limit=limit,
            offset=offset,
        )
