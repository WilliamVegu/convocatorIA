"""Alumni repository for TCS Peru ex-collaborator catalog in SQLAlchemy 2.0."""
from __future__ import annotations

from datetime import datetime, date, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.adapters.persistence.models import HistorialAlumniModel
from src.domain.exceptions import DuplicateEntityError, EntityNotFoundError


class AlumniRepository:
    """Repository handling persistence for HistorialAlumniModel."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, alumni_id: str) -> Optional[HistorialAlumniModel]:
        return self.session.execute(
            select(HistorialAlumniModel).where(HistorialAlumniModel.id == alumni_id)
        ).scalar_one_or_none()

    def get_by_dni(self, dni: str) -> Optional[HistorialAlumniModel]:
        return self.session.execute(
            select(HistorialAlumniModel).where(
                HistorialAlumniModel.numero_documento == dni.strip()
            )
        ).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[HistorialAlumniModel]:
        return self.session.execute(
            select(HistorialAlumniModel).where(
                HistorialAlumniModel.email_corporativo_historico == email.strip().lower()
            )
        ).scalar_one_or_none()

    def search_by_normalized_name(self, normalized_name: str) -> List[HistorialAlumniModel]:
        stmt = select(HistorialAlumniModel).where(
            HistorialAlumniModel.nombres_normalizado.like(f"%{normalized_name.strip()}%")
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self, limit: int = 100, offset: int = 0) -> List[HistorialAlumniModel]:
        stmt = select(HistorialAlumniModel).order_by(HistorialAlumniModel.fecha_cese.desc()).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def create(
        self,
        alumni_id: str,
        tipo_documento: str,
        numero_documento: str,
        nombres_completos: str,
        nombres_normalizado: str,
        fecha_cese: date,
        email_corporativo_historico: Optional[str] = None,
        fecha_ingreso: Optional[date] = None,
        ultima_cuenta_proyecto: Optional[str] = None,
        motivo_desvinculacion: Optional[str] = None,
        estatus_recontratacion: str = "Rehire_Eligible",
    ) -> HistorialAlumniModel:
        existing = self.get_by_dni(numero_documento)
        if existing:
            raise DuplicateEntityError(
                f"El registro Alumni con documento '{numero_documento}' ya existe."
            )

        alumni = HistorialAlumniModel(
            id=alumni_id,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento.strip(),
            nombres_completos=nombres_completos.strip(),
            nombres_normalizado=nombres_normalizado.strip(),
            fecha_cese=fecha_cese,
            email_corporativo_historico=email_corporativo_historico.strip().lower() if email_corporativo_historico else None,
            fecha_ingreso=fecha_ingreso,
            ultima_cuenta_proyecto=ultima_cuenta_proyecto,
            motivo_desvinculacion=motivo_desvinculacion,
            estatus_recontratacion=estatus_recontratacion,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(alumni)
        self.session.flush()
        return alumni
