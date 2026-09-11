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
                "alumni_id": record.id,
                "documento": record.numero_documento,
                "nombres_completos": record.nombres_completos,
                "estatus_recontratacion": record.estatus_recontratacion,
                "ultima_cuenta_proyecto": record.ultima_cuenta_proyecto,
                "motivo_desvinculacion": record.motivo_desvinculacion,
                "fecha_cese": record.fecha_cese,
                "bloquear_comision_agencia": True,
                "badge_color": "purple",
                "badge_label": "Ex-Colaborador TCS (Boomerang)",
            }

        return {
            "is_alumni": False,
            "alumni_id": None,
            "documento": None,
            "nombres_completos": None,
            "estatus_recontratacion": None,
            "ultima_cuenta_proyecto": None,
            "motivo_desvinculacion": None,
            "fecha_cese": None,
            "bloquear_comision_agencia": False,
            "badge_color": None,
            "badge_label": None,
        }
