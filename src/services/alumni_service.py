"""Alumni service for Boomerang detection and agency fee prevention."""
from __future__ import annotations

from typing import Optional, Dict, Any, List
from rapidfuzz import fuzz

from src.ports.alumni_port import AlumniPort
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.adapters.persistence.models import HistorialAlumniModel
from src.services.candidate_service import normalize_full_name


class AlumniService(AlumniPort):
    """Application service detecting ex-TCS collaborators and protecting against improper fees."""

    def __init__(self, alumni_repository: AlumniRepository):
        self.repo = alumni_repository

    def detect_alumni(
        self,
        dni: Optional[str] = None,
        email: Optional[str] = None,
        nombre_completo: Optional[str] = None,
    ) -> Dict[str, Any]:
        record: Optional[HistorialAlumniModel] = None

        # 1. Exact match by DNI
        if dni:
            clean_dni = dni.strip()
            record = self.repo.get_by_dni(clean_dni)

        # 2. Match by historical corporate email
        if not record and email:
            clean_email = email.strip().lower()
            record = self.repo.get_by_email(clean_email)

        # 3. Phonetic and fuzzy match by full name (Token Sort Ratio >= 85%)
        if not record and nombre_completo:
            target_norm = normalize_full_name(nombre_completo)
            all_alumni = self.repo.list_all(limit=500)
            best_match = None
            best_score = 0.0

            for alm in all_alumni:
                score = fuzz.token_sort_ratio(target_norm, alm.nombres_normalizado)
                if score > best_score:
                    best_score = score
                    best_match = alm

            if best_score >= 85.0:
                record = best_match

        if record:
            return {
                "is_alumni": True,
                "es_boomerang": True,
                "alumni_id": record.id,
                "documento": record.numero_documento,
                "nombres_completos": record.nombres_completos,
                "estatus_recontratacion": record.estatus_recontratacion,
                "elegible_recontratacion": record.estatus_recontratacion == "Rehire_Eligible",
                "ultima_cuenta_proyecto": record.ultima_cuenta_proyecto,
                "motivo_desvinculacion": record.motivo_desvinculacion,
                "fecha_ingreso": str(record.fecha_ingreso) if record.fecha_ingreso else "",
                "fecha_cese": str(record.fecha_cese),
                "bloquear_comision_agencia": True,
                "badge_color": "purple",
                "badge_label": "Ex-Colaborador TCS (Boomerang)",
            }

        return {
            "is_alumni": False,
            "es_boomerang": False,
            "alumni_id": None,
            "documento": None,
            "nombres_completos": None,
            "estatus_recontratacion": None,
            "elegible_recontratacion": False,
            "ultima_cuenta_proyecto": None,
            "motivo_desvinculacion": None,
            "fecha_ingreso": "",
            "fecha_cese": None,
            "bloquear_comision_agencia": False,
            "badge_color": None,
            "badge_label": None,
        }

    def detect_boomerang(
        self,
        dni: Optional[str] = None,
        email: Optional[str] = None,
        nombre_completo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Alias for detect_alumni ensuring compatibility with both terminologies."""
        return self.detect_alumni(dni=dni, email=email, nombre_completo=nombre_completo)
