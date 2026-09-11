"""Screening service for recording human 7-dimensional telephone calls (HITL)."""
from __future__ import annotations

import uuid
from typing import Optional, Dict, Any

from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.services.audit_service import AuditService
from src.services.commute_matrix import evaluate_commute
from src.adapters.persistence.models import ScreeningModel
from src.domain.exceptions import EntityNotFoundError, DuplicateEntityError


class ScreeningService:
    """Service governing qualitative human phone screening and commute alerts."""

    def __init__(
        self,
        postulacion_repository: PostulacionRepository,
        candidato_repository: CandidatoRepository,
        audit_service: AuditService,
    ):
        self.postulacion_repo = postulacion_repository
        self.candidato_repo = candidato_repository
        self.audit_service = audit_service

    def record_screening_call(
        self,
        evaluador_user_id: str,
        evaluador_email: str,
        evaluador_role: str,
        postulacion_id: str,
        dim1_disponibilidad: str,
        dim2_resumen_tecnico: str,
        dim3_expectativa_declarada: float,
        dim4_interes_vacante: str,
        dim5_modalidad_aceptada: str,
        dim7_impresion_general: str,
        dictamen_humano: str,
        dim6_override_viabilidad: Optional[str] = None,
        justificacion_descarte: Optional[str] = None,
    ) -> ScreeningModel:
        """Register the 7 dimensions of a telephone screening call with human sovereign decision."""
        post = self.postulacion_repo.get_by_id(postulacion_id)
        if not post:
            raise EntityNotFoundError(f"Postulación {postulacion_id} no encontrada.")

        cand = self.candidato_repo.get_by_id(post.candidato_id)
        if not cand:
            raise EntityNotFoundError(f"Candidato asociado a postulación {postulacion_id} no encontrado.")

        # Calculate automatic commute feasibility
        auto_viabilidad, alerta_nota = evaluate_commute(
            residence_district=cand.distrito_residencia,
            client_or_workplace=post.cliente_cuenta,
            modalidad=dim5_modalidad_aceptada,
        )

        dim6_viabilidad = dim6_override_viabilidad or auto_viabilidad

        screening_id = f"scr-{uuid.uuid4()}"
        screening = self.postulacion_repo.create_screening(
            screening_id=screening_id,
            postulacion_id=postulacion_id,
            evaluador_user_id=evaluador_user_id,
            dim1_disponibilidad=dim1_disponibilidad,
            dim2_resumen_tecnico=dim2_resumen_tecnico,
            dim3_expectativa_declarada=dim3_expectativa_declarada,
            dim4_interes_vacante=dim4_interes_vacante,
            dim5_modalidad_aceptada=dim5_modalidad_aceptada,
            dim6_viabilidad_traslado=dim6_viabilidad,
            dim6_alerta_distancia_nota=alerta_nota,
            dim7_impresion_general=dim7_impresion_general,
            dictamen_humano=dictamen_humano,
        )

        # Update application funnel state based on human decision
        if dictamen_humano == "Avanza_Entrevista_Tecnica":
            self.postulacion_repo.update_postulacion_status(
                postulacion_id=post.id,
                new_status="Pendiente_Entrevistas",
                expected_version=post.record_version,
                updated_by_user_id=evaluador_user_id,
                observaciones=f"Screening aprobado por reclutador {evaluador_email}. Expectativa: S/. {dim3_expectativa_declarada:,.2f}",
            )
        elif dictamen_humano == "No_Apto_Filtro_Inicial":
            self.postulacion_repo.update_postulacion_status(
                postulacion_id=post.id,
                new_status="Descartado_Tecnico",
                expected_version=post.record_version,
                updated_by_user_id=evaluador_user_id,
                motivo_cierre_tipo="Temporal_No_Excluyente",
                motivo_cierre_detalle=justificacion_descarte or "No superó el filtro técnico/modalidad del screening inicial.",
            )

        # Audit event
        self.audit_service.record_mutation(
            usuario_id=evaluador_user_id,
            usuario_email=evaluador_email,
            rol_en_momento=evaluador_role,
            tipo_accion="Creacion",
            entidad_objeto="Screening",
            registro_id=screening.id,
            valores_nuevos={
                "postulacion_id": postulacion_id,
                "dictamen": dictamen_humano,
                "viabilidad_traslado": dim6_viabilidad,
            },
            justificacion_operativa="Registro de llamada de screening humano (7 dimensiones)",
        )

        return screening
