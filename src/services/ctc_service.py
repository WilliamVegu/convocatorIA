"""Application service for CTC evaluation persistence, workflow, and approval tracking."""
from __future__ import annotations

import uuid
from typing import Optional, Dict, Any

from src.services.ctc_calculator_service import CTCCalculatorService
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.services.audit_service import AuditService
from src.adapters.persistence.models import EvaluacionCTCModel
from src.domain.exceptions import EntityNotFoundError, InsufficientPermissionsError


class CTCService:
    """Service orchestrating financial simulation, exception approval, and persistence."""

    def __init__(
        self,
        postulacion_repository: PostulacionRepository,
        audit_service: AuditService,
        calculator: Optional[CTCCalculatorService] = None,
    ):
        self.postulacion_repo = postulacion_repository
        self.audit_service = audit_service
        self.calculator = calculator or CTCCalculatorService()

    def evaluate_and_persist_ctc(
        self,
        actor_user_id: str,
        actor_email: str,
        actor_role: str,
        postulacion_id: str,
        tipo_expectativa: str,
        monto_declarado: float,
        ctc_presupuestado: Optional[float] = None,
        factor_ctc: float = 1.56,
    ) -> EvaluacionCTCModel:
        """Run CTC calculation and persist evaluation under the application process."""
        post = self.postulacion_repo.get_by_id(postulacion_id)
        if not post:
            raise EntityNotFoundError(f"Postulación {postulacion_id} no encontrada.")

        calc = self.calculator.calculate(
            tipo_expectativa=tipo_expectativa,
            monto_declarado=monto_declarado,
            ctc_presupuestado=ctc_presupuestado,
            factor_ctc=factor_ctc,
        )

        ctc_id = f"ctc-{uuid.uuid4()}"
        eval_ctc = self.postulacion_repo.create_ctc_eval(
            ctc_id=ctc_id,
            postulacion_id=postulacion_id,
            tipo_expectativa=calc["tipo_expectativa"],
            monto_declarado=calc["monto_declarado"],
            salario_bruto_mensual=calc["salario_bruto_mensual"],
            factor_ctc=calc["factor_ctc"],
            ctc_solicitado=calc["ctc_solicitado"],
            ctc_presupuestado=calc["ctc_presupuestado"],
            variacion_porcentual=calc["variacion_porcentual"],
            semaforo_presupuestal=calc["semaforo_presupuestal"],
            requiere_aprobacion=calc["requiere_aprobacion"],
            evaluado_por_user_id=actor_user_id,
        )

        # Audit financial simulation
        self.audit_service.record_mutation(
            usuario_id=actor_user_id,
            usuario_email=actor_email,
            rol_en_momento=actor_role,
            tipo_accion="Creacion",
            entidad_objeto="Evaluacion_CTC",
            registro_id=eval_ctc.id,
            valores_nuevos={
                "postulacion_id": postulacion_id,
                "salario_bruto": calc["salario_bruto_mensual"],
                "ctc_solicitado": calc["ctc_solicitado"],
                "semaforo": calc["semaforo_presupuestal"],
            },
            justificacion_operativa="Simulacion financiera CTC Factor 1.56",
        )

        return eval_ctc

    def approve_ctc_exception(
        self,
        approver_user_id: str,
        approver_email: str,
        approver_role: str,
        postulacion_id: str,
        justification: str,
    ) -> EvaluacionCTCModel:
        """Approve salary variance exceeding budget (Head of TA exclusive)."""
        if approver_role != "Head_of_Talent_Acquisition":
            raise InsufficientPermissionsError(
                "Solo el Head of Talent Acquisition puede autorizar excepciones salariales fuera de banda."
            )

        eval_ctc = self.postulacion_repo.get_ctc_by_postulacion(postulacion_id)
        if not eval_ctc:
            raise EntityNotFoundError(f"Evaluación CTC para postulación {postulacion_id} no encontrada.")

        eval_ctc.aprobado_por_user_id = approver_user_id
        eval_ctc.justificacion_aprobacion = justification
        eval_ctc.requiere_aprobacion = False
        self.postulacion_repo.session.flush()

        self.audit_service.record_mutation(
            usuario_id=approver_user_id,
            usuario_email=approver_email,
            rol_en_momento=approver_role,
            tipo_accion="Modificacion",
            entidad_objeto="Evaluacion_CTC",
            registro_id=eval_ctc.id,
            valores_previos={"requiere_aprobacion": True},
            valores_nuevos={"requiere_aprobacion": False, "aprobado_por": approver_email},
            justificacion_operativa=justification,
        )

        return eval_ctc
