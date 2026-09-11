"""Audit repository for append-only log persistence in SQLAlchemy 2.0."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from src.adapters.persistence.models import BitacoraAuditoriaModel
from src.domain.exceptions import AuditIntegrityError


class AuditRepository:
    """Repository strictly enforcing append-only semantics for audit logs."""

    def __init__(self, session: Session):
        self.session = session

    def append_log(
        self,
        log_id: str,
        usuario_id: str,
        usuario_email: str,
        rol_en_momento: str,
        tipo_accion: str,
        entidad_objeto: str,
        registro_id: str,
        version_registro: Optional[int] = None,
        valores_previos: Optional[Dict[str, Any] | str] = None,
        valores_nuevos: Optional[Dict[str, Any] | str] = None,
        justificacion_operativa: Optional[str] = None,
        ip_address: str = "127.0.0.1",
        session_id: Optional[str] = None,
        nombre_archivo_adjunto: Optional[str] = None,
        hash_integridad_sha256: Optional[str] = None,
    ) -> BitacoraAuditoriaModel:
        """Append a new non-repudiable audit entry."""
        prev_json = (
            json.dumps(valores_previos, default=str)
            if isinstance(valores_previos, dict)
            else valores_previos
        )
        new_json = (
            json.dumps(valores_nuevos, default=str)
            if isinstance(valores_nuevos, dict)
            else valores_nuevos
        )

        entry = BitacoraAuditoriaModel(
            id=log_id,
            timestamp=datetime.now(timezone.utc),
            usuario_id=usuario_id,
            usuario_email=usuario_email,
            rol_en_momento=rol_en_momento,
            tipo_accion=tipo_accion,
            entidad_objeto=entidad_objeto,
            registro_id=registro_id,
            version_registro=version_registro,
            valores_previos_json=prev_json,
            valores_nuevos_json=new_json,
            justificacion_operativa=justificacion_operativa,
            ip_address=ip_address,
            session_id=session_id,
            nombre_archivo_adjunto=nombre_archivo_adjunto,
            hash_integridad_sha256=hash_integridad_sha256,
        )
        self.session.add(entry)
        self.session.flush()
        return entry

    def list_logs(self, limit: int = 100, offset: int = 0) -> List[BitacoraAuditoriaModel]:
        stmt = (
            select(BitacoraAuditoriaModel)
            .order_by(desc(BitacoraAuditoriaModel.timestamp))
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().all())

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
        stmt = select(BitacoraAuditoriaModel)

        if usuario_email:
            stmt = stmt.where(BitacoraAuditoriaModel.usuario_email == usuario_email.strip().lower())
        if entidad_objeto:
            stmt = stmt.where(BitacoraAuditoriaModel.entidad_objeto == entidad_objeto)
        if tipo_accion:
            stmt = stmt.where(BitacoraAuditoriaModel.tipo_accion == tipo_accion)
        if fecha_desde:
            stmt = stmt.where(BitacoraAuditoriaModel.timestamp >= fecha_desde)
        if fecha_hasta:
            stmt = stmt.where(BitacoraAuditoriaModel.timestamp <= fecha_hasta)

        stmt = stmt.order_by(desc(BitacoraAuditoriaModel.timestamp)).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_id(self, log_id: str) -> Optional[BitacoraAuditoriaModel]:
        return self.session.execute(
            select(BitacoraAuditoriaModel).where(BitacoraAuditoriaModel.id == log_id)
        ).scalar_one_or_none()

    def list_by_entity(self, entidad_objeto: str, registro_id: str) -> List[BitacoraAuditoriaModel]:
        """List audit events for a specific entity and record ID."""
        stmt = (
            select(BitacoraAuditoriaModel)
            .where(
                BitacoraAuditoriaModel.entidad_objeto == entidad_objeto,
                BitacoraAuditoriaModel.registro_id == registro_id,
            )
            .order_by(desc(BitacoraAuditoriaModel.timestamp))
        )
        return list(self.session.execute(stmt).scalars().all())
