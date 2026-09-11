"""Candidate repository for centralized identity profiles in SQLAlchemy 2.0."""
from __future__ import annotations

import json
from datetime import datetime, date, timezone
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from src.adapters.persistence.models import CandidatoModel, CacheDNIReniecModel
from src.domain.exceptions import EntityNotFoundError, DuplicateEntityError, OptimisticLockError


class CandidatoRepository:
    """Repository handling persistence for CandidatoModel and RENIEC offline cache."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, candidato_id: str) -> Optional[CandidatoModel]:
        return self.session.execute(
            select(CandidatoModel).where(CandidatoModel.id == candidato_id)
        ).scalar_one_or_none()

    def get_by_dni(self, dni: str) -> Optional[CandidatoModel]:
        return self.session.execute(
            select(CandidatoModel).where(CandidatoModel.numero_documento == dni.strip())
        ).scalar_one_or_none()

    def get_by_phone(self, phone: str) -> Optional[CandidatoModel]:
        return self.session.execute(
            select(CandidatoModel).where(CandidatoModel.telefono_e164 == phone.strip())
        ).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[CandidatoModel]:
        return self.session.execute(
            select(CandidatoModel).where(CandidatoModel.email == email.strip().lower())
        ).scalar_one_or_none()

    def list_all(self, limit: int = 100, offset: int = 0) -> List[CandidatoModel]:
        stmt = select(CandidatoModel).order_by(CandidatoModel.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def list_pending_regularizations(self) -> List[CandidatoModel]:
        stmt = select(CandidatoModel).where(CandidatoModel.regularizacion_pendiente == True)
        return list(self.session.execute(stmt).scalars().all())

    def search_by_normalized_name(self, normalized_name: str) -> List[CandidatoModel]:
        stmt = select(CandidatoModel).where(
            CandidatoModel.nombres_completos_normalizado.like(f"%{normalized_name.strip()}%")
        )
        return list(self.session.execute(stmt).scalars().all())

    def create(
        self,
        candidato_id: str,
        tipo_documento: str,
        numero_documento: str,
        nombres: str,
        apellido_paterno: str,
        nombres_completos_normalizado: str,
        telefono_e164: str,
        email: str,
        created_by_user_id: str,
        apellido_materno: str = "",
        fecha_nacimiento: Optional[date] = None,
        ubigeo: Optional[str] = None,
        departamento: str = "Lima",
        provincia: str = "Lima",
        distrito_residencia: Optional[str] = None,
        direccion_residencia: Optional[str] = None,
        is_tcs_alumni: bool = False,
        alumni_id: Optional[str] = None,
        estado_identidad: str = "Validado_Oficialmente",
        regularizacion_pendiente: bool = False,
        cv_documento_url: Optional[str] = None,
        cv_hash_sha256: Optional[str] = None,
        cv_resumen_tecnico: Optional[str] = None,
        cv_anios_experiencia: Optional[float] = None,
        cv_idiomas_json: Optional[Any] = None,
    ) -> CandidatoModel:
        # Check duplicates
        if self.get_by_dni(numero_documento):
            raise DuplicateEntityError(
                f"Ya existe un candidato registrado con el documento '{numero_documento}'."
            )
        if self.get_by_phone(telefono_e164):
            raise DuplicateEntityError(
                f"Ya existe un candidato registrado con el teléfono '{telefono_e164}'."
            )
        if self.get_by_email(email):
            raise DuplicateEntityError(
                f"Ya existe un candidato registrado con el correo '{email}'."
            )

        idiomas_str = (
            json.dumps(cv_idiomas_json)
            if isinstance(cv_idiomas_json, (list, dict))
            else cv_idiomas_json
        )

        candidato = CandidatoModel(
            id=candidato_id,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento.strip(),
            nombres=nombres.strip(),
            apellido_paterno=apellido_paterno.strip(),
            apellido_materno=apellido_materno.strip() if apellido_materno else "",
            nombres_completos_normalizado=nombres_completos_normalizado.strip(),
            telefono_e164=telefono_e164.strip(),
            email=email.strip().lower(),
            fecha_nacimiento=fecha_nacimiento,
            ubigeo=ubigeo,
            departamento=departamento,
            provincia=provincia,
            distrito_residencia=distrito_residencia,
            direccion_residencia=direccion_residencia,
            is_tcs_alumni=is_tcs_alumni,
            alumni_id=alumni_id,
            estado_identidad=estado_identidad,
            regularizacion_pendiente=regularizacion_pendiente,
            cv_documento_url=cv_documento_url,
            cv_hash_sha256=cv_hash_sha256,
            cv_resumen_tecnico=cv_resumen_tecnico,
            cv_anios_experiencia=cv_anios_experiencia,
            cv_idiomas_json=idiomas_str,
            record_version=1,
            created_by_user_id=created_by_user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(candidato)
        self.session.flush()
        return candidato

    def update(
        self,
        candidato_id: str,
        expected_version: int,
        updated_by_user_id: str,
        **updates: Any,
    ) -> CandidatoModel:
        cand = self.get_by_id(candidato_id)
        if not cand:
            raise EntityNotFoundError(f"Candidato {candidato_id} no encontrado.")

        if cand.record_version != expected_version:
            raise OptimisticLockError(
                f"Conflicto de concurrencia al actualizar candidato {candidato_id}. Versión esperada: {expected_version}, actual: {cand.record_version}"
            )

        for field_name, value in updates.items():
            if hasattr(cand, field_name):
                if field_name == "cv_idiomas_json" and isinstance(value, (list, dict)):
                    value = json.dumps(value)
                setattr(cand, field_name, value)

        cand.record_version += 1
        cand.updated_by_user_id = updated_by_user_id
        cand.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return cand

    # Offline RENIEC cache helpers
    def get_cached_dni(self, dni: str) -> Optional[CacheDNIReniecModel]:
        return self.session.execute(
            select(CacheDNIReniecModel).where(CacheDNIReniecModel.dni == dni.strip())
        ).scalar_one_or_none()

    def set_cached_dni(
        self,
        dni: str,
        nombres: str,
        apellido_paterno: str,
        apellido_materno: str = "",
        fecha_nacimiento: Optional[date] = None,
        ubigeo: Optional[str] = None,
        distrito: Optional[str] = None,
        direccion: Optional[str] = None,
    ) -> CacheDNIReniecModel:
        existing = self.get_cached_dni(dni)
        if existing:
            existing.nombres = nombres
            existing.apellido_paterno = apellido_paterno
            existing.apellido_materno = apellido_materno
            existing.fecha_nacimiento = fecha_nacimiento
            existing.ubigeo = ubigeo
            existing.distrito = distrito
            existing.direccion = direccion
            existing.cached_at = datetime.now(timezone.utc)
            self.session.flush()
            return existing

        entry = CacheDNIReniecModel(
            dni=dni.strip(),
            nombres=nombres.strip(),
            apellido_paterno=apellido_paterno.strip(),
            apellido_materno=apellido_materno.strip() if apellido_materno else "",
            fecha_nacimiento=fecha_nacimiento,
            ubigeo=ubigeo,
            distrito=distrito,
            direccion=direccion,
            cached_at=datetime.now(timezone.utc),
        )
        self.session.add(entry)
        self.session.flush()
        return entry
