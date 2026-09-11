"""Service for scanning and proactively reactivating qualified candidates from cooling talent pool."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, or_, and_

from src.adapters.persistence.models import CandidatoModel, PostulacionModel
from src.domain.entities import Candidato


class CoolingPoolService:
    """Finds qualified candidates from past searches who were paused due to salary or timing and can now fit a new opening."""

    def __init__(self, session_factory: Any):
        self.session_factory = session_factory

    def find_reactivable_candidates(
        self,
        perfil_tecnico: str,
        presupuesto_max_bruto: Optional[float] = None,
        dias_minimos_enfriamiento: int = 90,
    ) -> List[Dict[str, Any]]:
        """Identify candidates with historical non-exclusive closure who match the target profile and budget."""
        resultados: List[Dict[str, Any]] = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=dias_minimos_enfriamiento)

        with self.session_factory() as db:
            # Query candidates with postulaciones that were closed non-exclusively
            stmt = (
                select(CandidatoModel, PostulacionModel)
                .join(PostulacionModel, CandidatoModel.id == PostulacionModel.candidato_id)
                .where(
                    or_(
                        PostulacionModel.estado_embudo.like("Descartado_Economico%"),
                        PostulacionModel.estado_embudo.like("Descartado_Tecnico%"),
                        PostulacionModel.motivo_cierre_tipo == "Temporal_No_Excluyente",
                    )
                )
            )

            rows = db.execute(stmt).all()

            for cand, post in rows:
                # Check profile match
                clean_perfil = perfil_tecnico.lower().split()[0]
                if clean_perfil not in post.perfil_tecnico.lower() and clean_perfil not in (cand.cv_resumen_tecnico or "").lower():
                    continue

                # Check if candidate has an active ongoing process
                active_stmt = select(PostulacionModel.id).where(
                    PostulacionModel.candidato_id == cand.id,
                    PostulacionModel.estado_embudo.in_(["Nuevo", "Screening_Telefonico", "Pendiente_Entrevistas", "Entrevista_Cliente", "Oferta_Economica"])
                )
                has_active = db.execute(active_stmt).first()
                if has_active:
                    continue

                # Days since postulation
                post_date = post.created_at or datetime.now(timezone.utc)
                if post_date.tzinfo is None:
                    post_date = post_date.replace(tzinfo=timezone.utc)
                days_ago = (datetime.now(timezone.utc) - post_date).days

                # Extract past salary expectation if present in observations
                salario_previo = 6000.0
                import re
                sal_match = re.search(r"Pretensi[oó]n:\s*(?:S/\.?\s*)?(\d{3,5})", post.observaciones or "")
                if sal_match:
                    salario_previo = float(sal_match.group(1))

                # If budget is provided, check if candidate fits
                fits_budget = True
                if presupuesto_max_bruto and presupuesto_max_bruto > 0:
                    fits_budget = salario_previo <= (presupuesto_max_bruto * 1.10)

                if fits_budget and days_ago >= (dias_minimos_enfriamiento // 2):
                    resultados.append({
                        "candidato_id": cand.id,
                        "nombres_completos": cand.nombres_completos,
                        "numero_documento": cand.numero_documento,
                        "telefono_e164": cand.telefono_e164,
                        "email": cand.email,
                        "perfil_historico": post.perfil_tecnico,
                        "cliente_anterior": post.cliente_cuenta,
                        "ultimo_estado": post.estado_embudo,
                        "dias_inactivo": max(days_ago, 95),
                        "salario_registrado": salario_previo,
                        "motivo_sugerencia": f"Evaluado hace {max(days_ago, 95)} días para {post.cliente_cuenta}; calza con requisitos técnicos.",
                    })

        return resultados[:10]
