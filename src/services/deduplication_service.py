"""Multi-criteria deduplication service with exact and phonetic/fuzzy algorithms."""
from __future__ import annotations

import re
from typing import Optional, Dict, Any, List
from rapidfuzz import fuzz

from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.models import CandidatoModel
from src.domain.value_objects import TelefonoE164
from src.services.candidate_service import normalize_full_name


class DeduplicationService:
    """Service detecting duplicates via exact identifiers and phonetic fuzzy matching."""

    def __init__(self, candidato_repository: CandidatoRepository):
        self.candidato_repo = candidato_repository

    def check_duplicate(
        self,
        dni: Optional[str] = None,
        telefono: Optional[str] = None,
        email: Optional[str] = None,
        nombre_completo: Optional[str] = None,
        threshold_ratio: float = 85.0,
    ) -> Dict[str, Any]:
        # 1. Exact DNI match
        if dni:
            clean_dni = dni.strip()
            cand = self.candidato_repo.get_by_dni(clean_dni)
            if cand:
                return {
                    "is_duplicate": True,
                    "matched_field": "DNI",
                    "existing_candidate_id": cand.id,
                    "similarity_score": 100.0,
                    "existing_candidate": cand,
                }

        # 2. Exact Phone match (E.164 normalized)
        if telefono:
            try:
                e164 = str(TelefonoE164(telefono))
                cand = self.candidato_repo.get_by_phone(e164)
                if cand:
                    return {
                        "is_duplicate": True,
                        "matched_field": "Telefono",
                        "existing_candidate_id": cand.id,
                        "similarity_score": 100.0,
                        "existing_candidate": cand,
                    }
            except Exception:
                pass

        # 3. Exact Email match (lowercase)
        if email:
            clean_email = email.strip().lower()
            cand = self.candidato_repo.get_by_email(clean_email)
            if cand:
                return {
                    "is_duplicate": True,
                    "matched_field": "Email",
                    "existing_candidate_id": cand.id,
                    "similarity_score": 100.0,
                    "existing_candidate": cand,
                }

        # 4. Fuzzy / Phonetic Name match
        if nombre_completo:
            target_norm = normalize_full_name(nombre_completo)
            all_candidates = self.candidato_repo.list_all(limit=1000)
            best_cand: Optional[CandidatoModel] = None
            best_score: float = 0.0

            for cand in all_candidates:
                score = fuzz.token_sort_ratio(target_norm, cand.nombres_completos_normalizado)
                if score > best_score:
                    best_score = score
                    best_cand = cand

            if best_score >= threshold_ratio and best_cand:
                return {
                    "is_duplicate": True,
                    "matched_field": "Nombre_Fonetico",
                    "existing_candidate_id": best_cand.id,
                    "similarity_score": round(best_score, 1),
                    "existing_candidate": best_cand,
                }

        return {
            "is_duplicate": False,
            "matched_field": None,
            "existing_candidate_id": None,
            "similarity_score": 0.0,
            "existing_candidate": None,
        }
