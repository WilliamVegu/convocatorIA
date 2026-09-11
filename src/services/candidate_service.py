"""Candidate application service for central identity profiles and lifecycle management."""
from __future__ import annotations

import uuid
import re
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any, List

from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.ports.dni_port import DNIPort
from src.services.audit_service import AuditService
from src.domain.value_objects import TelefonoE164, DocumentoIdentidad
from src.domain.entities import Candidato
from src.adapters.persistence.models import CandidatoModel
from src.domain.exceptions import DuplicateEntityError, EntityNotFoundError, OptimisticLockError


def normalize_full_name(names: str) -> str:
    """Normalize full name to uppercase, removing accents and common particles."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", names.strip().upper())
    clean = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Remove excessive whitespace
    return re.sub(r"\s+", " ", clean)


class CandidateService:
    """Service orchestrating candidate profiles, identity validation, and deduplication."""

    def __init__(
        self,
        candidato_repository: CandidatoRepository,
        dni_port: DNIPort,
        audit_service: AuditService,
        alumni_repository: Optional[AlumniRepository] = None,
    ):
        self.candidato_repo = candidato_repository
        self.dni_port = dni_port
        self.audit_service = audit_service
        self.alumni_repo = alumni_repository

    def lookup_dni(self, dni: str) -> Dict[str, Any]:
        """Lookup citizen identity via DNI port (local cache or APIsPERU)."""
        return self.dni_port.resolve_dni(dni)

    def lookup_ruc(self, ruc: str) -> Dict[str, Any]:
        """Lookup corporate / taxpayer identity via APIsPERU SUNAT port."""
        return self.dni_port.resolve_ruc(ruc)

    def create_candidate(
        self,
        actor_user_id: str,
        actor_email: str,
        actor_role: str,
        tipo_documento: str,
        numero_documento: str,
        nombres: str,
        apellido_paterno: str,
        telefono_raw: str,
        email: str,
        apellido_materno: str = "",
        fecha_nacimiento: Optional[date] = None,
        ubigeo: Optional[str] = None,
        departamento: str = "Lima",
        provincia: str = "Lima",
        distrito_residencia: Optional[str] = None,
        direccion_residencia: Optional[str] = None,
        estado_identidad: str = "Validado_Oficialmente",
        regularizacion_pendiente: bool = False,
        cv_documento_url: Optional[str] = None,
        cv_hash_sha256: Optional[str] = None,
        cv_resumen_tecnico: Optional[str] = None,
        cv_anios_experiencia: Optional[float] = None,
        cv_idiomas_json: Optional[Any] = None,
    ) -> CandidatoModel:
        """Create and persist a new candidate profile with automatic Boomerang detection and E.164 normalization."""
        # 1. Canonical Value Object validations
        doc = DocumentoIdentidad(tipo=tipo_documento, numero=numero_documento)
        telefono_e164 = str(TelefonoE164(telefono_raw))
        email_clean = email.strip().lower()

        # 2. Duplicate checking
        if self.candidato_repo.get_by_dni(doc.numero):
            raise DuplicateEntityError(
                f"El candidato con {doc.tipo} '{doc.numero}' ya existe en la base de datos."
            )
        if self.candidato_repo.get_by_phone(telefono_e164):
            raise DuplicateEntityError(
                f"El teléfono '{telefono_e164}' ya está asignado a otro candidato registrado."
            )
        if self.candidato_repo.get_by_email(email_clean):
            raise DuplicateEntityError(
                f"El correo electrónico '{email_clean}' ya está asignado a otro candidato registrado."
            )

        # 3. Normalized full name for deduplication
        raw_full_name = f"{nombres} {apellido_paterno} {apellido_materno or ''}".strip()
        nombres_normalizados = normalize_full_name(raw_full_name)

        # 4. Automatic Alumni / Boomerang cross-check
        is_alumni = False
        alumni_id = None
        if self.alumni_repo:
            alm = self.alumni_repo.get_by_dni(doc.numero)
            if alm:
                is_alumni = True
                alumni_id = alm.id

        cand_id = f"cand-{uuid.uuid4()}"
        candidate = self.candidato_repo.create(
            candidato_id=cand_id,
            tipo_documento=doc.tipo,
            numero_documento=doc.numero,
            nombres=nombres.strip(),
            apellido_paterno=apellido_paterno.strip(),
            apellido_materno=apellido_materno.strip() if apellido_materno else "",
            nombres_completos_normalizado=nombres_normalizados,
            telefono_e164=telefono_e164,
            email=email_clean,
            fecha_nacimiento=fecha_nacimiento,
            ubigeo=ubigeo,
            departamento=departamento,
            provincia=provincia,
            distrito_residencia=distrito_residencia,
            direccion_residencia=direccion_residencia,
            is_tcs_alumni=is_alumni,
            alumni_id=alumni_id,
            estado_identidad=estado_identidad,
            regularizacion_pendiente=regularizacion_pendiente,
            cv_documento_url=cv_documento_url,
            cv_hash_sha256=cv_hash_sha256,
            cv_resumen_tecnico=cv_resumen_tecnico,
            cv_anios_experiencia=cv_anios_experiencia,
            cv_idiomas_json=cv_idiomas_json,
            created_by_user_id=actor_user_id,
        )

        # 5. Audit creation event
        self.audit_service.record_mutation(
            usuario_id=actor_user_id,
            usuario_email=actor_email,
            rol_en_momento=actor_role,
            tipo_accion="Creacion",
            entidad_objeto="Candidato",
            registro_id=candidate.id,
            version_registro=1,
            valores_nuevos={
                "dni": candidate.numero_documento,
                "nombres": candidate.nombres_completos_normalizado,
                "telefono": candidate.telefono_e164,
                "email": candidate.email,
                "is_tcs_alumni": is_alumni,
            },
            justificacion_operativa="Registro de Ficha Unica de Candidato",
        )

        return candidate

    def update_candidate(
        self,
        candidato_id: str,
        actor_user_id: str,
        actor_email: str,
        actor_role: str,
        expected_version: int,
        justification: str,
        **updates: Any,
    ) -> CandidatoModel:
        """Update candidate with optimistic locking and full audit trailing."""
        cand_before = self.candidato_repo.get_by_id(candidato_id)
        if not cand_before:
            raise EntityNotFoundError(f"Candidato {candidato_id} no encontrado.")

        prev_values = {
            "distrito_residencia": cand_before.distrito_residencia,
            "telefono_e164": cand_before.telefono_e164,
            "email": cand_before.email,
            "record_version": cand_before.record_version,
        }

        # Normalize phone if updated and check collision
        if "telefono_raw" in updates:
            new_tel = str(TelefonoE164(updates.pop("telefono_raw")))
            if new_tel != cand_before.telefono_e164:
                existing_p = self.candidato_repo.get_by_phone(new_tel)
                if existing_p and existing_p.id != candidato_id:
                    raise DuplicateEntityError(f"El teléfono '{new_tel}' ya está asignado a otro candidato registrado.")
            updates["telefono_e164"] = new_tel

        # Validate email if updated and check collision
        if "email" in updates:
            clean_email = updates["email"].strip().lower()
            if clean_email != cand_before.email:
                existing_e = self.candidato_repo.get_by_email(clean_email)
                if existing_e and existing_e.id != candidato_id:
                    raise DuplicateEntityError(f"El correo '{clean_email}' ya está asignado a otro candidato registrado.")
            updates["email"] = clean_email

        # Recalculate normalized full name if names change
        if any(k in updates for k in ("nombres", "apellido_paterno", "apellido_materno")):
            new_nom = updates.get("nombres", cand_before.nombres)
            new_pat = updates.get("apellido_paterno", cand_before.apellido_paterno)
            new_mat = updates.get("apellido_materno", cand_before.apellido_materno)
            raw_full = f"{new_nom} {new_pat} {new_mat or ''}".strip()
            updates["nombres_completos_normalizado"] = normalize_full_name(raw_full)

        updated = self.candidato_repo.update(
            candidato_id=candidato_id,
            expected_version=expected_version,
            updated_by_user_id=actor_user_id,
            **updates,
        )

        self.audit_service.record_mutation(
            usuario_id=actor_user_id,
            usuario_email=actor_email,
            rol_en_momento=actor_role,
            tipo_accion="Modificacion",
            entidad_objeto="Candidato",
            registro_id=candidato_id,
            version_registro=updated.record_version,
            valores_previos=prev_values,
            valores_nuevos={k: getattr(updated, k, None) for k in updates.keys()},
            justificacion_operativa=justification,
        )

        return updated

    def process_pending_regularizations(
        self,
        actor_user_id: str,
        actor_email: str,
        actor_role: str,
    ) -> int:
        """Process offline regularization queue against APIsPERU / RENIEC."""
        pending = self.candidato_repo.list_pending_regularizations()
        regularized_count = 0

        for cand in pending:
            res = self.dni_port.resolve_dni(cand.numero_documento)
            if res.get("success") and res.get("datos"):
                d = res["datos"]
                self.candidato_repo.update(
                    candidato_id=cand.id,
                    expected_version=cand.record_version,
                    updated_by_user_id=actor_user_id,
                    nombres=d.get("nombres") or cand.nombres,
                    apellido_paterno=d.get("apellido_paterno") or cand.apellido_paterno,
                    apellido_materno=d.get("apellido_materno") or cand.apellido_materno,
                    fecha_nacimiento=d.get("fecha_nacimiento") or cand.fecha_nacimiento,
                    ubigeo=d.get("ubigeo") or cand.ubigeo,
                    distrito_residencia=d.get("distrito") or cand.distrito_residencia,
                    estado_identidad="Validado_Oficialmente",
                    regularizacion_pendiente=False,
                )
                regularized_count += 1
                self.audit_service.record_mutation(
                    usuario_id=actor_user_id,
                    usuario_email=actor_email,
                    rol_en_momento=actor_role,
                    tipo_accion="Modificacion",
                    entidad_objeto="Candidato",
                    registro_id=cand.id,
                    version_registro=cand.record_version + 1,
                    justificacion_operativa="Regularizacion asincrona automatica de identidad DNI completada",
                )

        return regularized_count

    def get_candidate_by_id(self, candidato_id: str) -> Optional[CandidatoModel]:
        return self.candidato_repo.get_by_id(candidato_id)

    def get_candidate_by_dni(self, dni: str) -> Optional[CandidatoModel]:
        return self.candidato_repo.get_by_dni(dni)

    def list_candidates(self, limit: int = 100, offset: int = 0) -> List[CandidatoModel]:
        return self.candidato_repo.list_all(limit=limit, offset=offset)
