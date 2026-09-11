"""Repository for Postulaciones, Screening, CTC, and Compliance entities."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.adapters.persistence.models import (
    PostulacionModel,
    ScreeningModel,
    EvaluacionCTCModel,
    ComplianceModel,
)
from src.domain.exceptions import EntityNotFoundError, OptimisticLockError, DuplicateEntityError


class PostulacionRepository:
    """Repository handling persistence for job applications and related evaluations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, postulacion_id: str) -> Optional[PostulacionModel]:
        return self.session.execute(
            select(PostulacionModel).where(PostulacionModel.id == postulacion_id)
        ).scalar_one_or_none()

    def get_by_candidato(self, candidato_id: str) -> List[PostulacionModel]:
        stmt = (
            select(PostulacionModel)
            .where(PostulacionModel.candidato_id == candidato_id)
            .order_by(PostulacionModel.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self, limit: int = 100, offset: int = 0) -> List[PostulacionModel]:
        stmt = select(PostulacionModel).order_by(PostulacionModel.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def create_postulacion(
        self,
        postulacion_id: str,
        candidato_id: str,
        cliente_cuenta: str,
        rgs_vacante_id: str,
        perfil_tecnico: str,
        reclutador_asignado_id: str,
        fuente_origen: str,
        trimestre_fiscal: str,
        created_by_user_id: str,
        estado_embudo: str = "Nuevo",
        observaciones: Optional[str] = None,
    ) -> PostulacionModel:
        post = PostulacionModel(
            id=postulacion_id,
            candidato_id=candidato_id,
            cliente_cuenta=cliente_cuenta,
            rgs_vacante_id=rgs_vacante_id,
            perfil_tecnico=perfil_tecnico,
            reclutador_asignado_id=reclutador_asignado_id,
            fuente_origen=fuente_origen,
            trimestre_fiscal=trimestre_fiscal,
            estado_embudo=estado_embudo,
            observaciones=observaciones,
            record_version=1,
            created_by_user_id=created_by_user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(post)
        self.session.flush()
        return post

    def update_postulacion_status(
        self,
        postulacion_id: str,
        new_status: str,
        expected_version: int,
        updated_by_user_id: str,
        motivo_cierre_tipo: Optional[str] = None,
        motivo_cierre_detalle: Optional[str] = None,
        observaciones: Optional[str] = None,
    ) -> PostulacionModel:
        post = self.get_by_id(postulacion_id)
        if not post:
            raise EntityNotFoundError(f"Postulación {postulacion_id} no encontrada.")

        if post.record_version != expected_version:
            raise OptimisticLockError(
                f"Conflicto de concurrencia en postulación {postulacion_id}. Versión esperada: {expected_version}, actual: {post.record_version}"
            )

        post.estado_embudo = new_status
        if motivo_cierre_tipo:
            post.motivo_cierre_tipo = motivo_cierre_tipo
            post.motivo_cierre_detalle = motivo_cierre_detalle
            post.fecha_cierre_descarte = datetime.now(timezone.utc)
        if observaciones:
            post.observaciones = observaciones

        post.record_version += 1
        post.updated_by_user_id = updated_by_user_id
        post.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return post

    def update_postulacion(
        self,
        postulacion_id: str,
        updated_by_user_id: str,
        expected_version: Optional[int] = None,
        **updates: Any,
    ) -> PostulacionModel:
        """Update any postulación attributes with optimistic locking."""
        post = self.get_by_id(postulacion_id)
        if not post:
            raise EntityNotFoundError(f"Postulación {postulacion_id} no encontrada.")

        if expected_version is not None and post.record_version != expected_version:
            raise OptimisticLockError(
                f"Conflicto de concurrencia en postulación {postulacion_id}. Versión esperada: {expected_version}, actual: {post.record_version}"
            )

        for field_name, value in updates.items():
            if hasattr(post, field_name):
                setattr(post, field_name, value)

        post.record_version += 1
        post.updated_by_user_id = updated_by_user_id
        post.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return post

    # Screening
    def create_screening(
        self,
        screening_id: str,
        postulacion_id: str,
        evaluador_user_id: str,
        dim1_disponibilidad: str,
        dim2_resumen_tecnico: str,
        dim3_expectativa_declarada: float,
        dim4_interes_vacante: str,
        dim5_modalidad_aceptada: str,
        dim6_viabilidad_traslado: str,
        dim7_impresion_general: str,
        dictamen_humano: str,
        dim6_alerta_distancia_nota: Optional[str] = None,
    ) -> ScreeningModel:
        existing = self.get_screening_by_postulacion(postulacion_id)
        if existing:
            raise DuplicateEntityError(f"Ya existe un screening registrado para la postulación {postulacion_id}.")

        screening = ScreeningModel(
            id=screening_id,
            postulacion_id=postulacion_id,
            evaluador_user_id=evaluador_user_id,
            dim1_disponibilidad=dim1_disponibilidad,
            dim2_resumen_tecnico=dim2_resumen_tecnico,
            dim3_expectativa_declarada=dim3_expectativa_declarada,
            dim4_interes_vacante=dim4_interes_vacante,
            dim5_modalidad_aceptada=dim5_modalidad_aceptada,
            dim6_viabilidad_traslado=dim6_viabilidad_traslado,
            dim6_alerta_distancia_nota=dim6_alerta_distancia_nota,
            dim7_impresion_general=dim7_impresion_general,
            dictamen_humano=dictamen_humano,
            fecha_hora_llamada=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(screening)
        self.session.flush()
        return screening

    def get_screening_by_postulacion(self, postulacion_id: str) -> Optional[ScreeningModel]:
        return self.session.execute(
            select(ScreeningModel).where(ScreeningModel.postulacion_id == postulacion_id)
        ).scalar_one_or_none()

    # CTC
    def create_ctc_eval(
        self,
        ctc_id: str,
        postulacion_id: str,
        tipo_expectativa: str,
        monto_declarado: float,
        salario_bruto_mensual: float,
        factor_ctc: float,
        ctc_solicitado: float,
        evaluado_por_user_id: str,
        ctc_presupuestado: Optional[float] = None,
        variacion_porcentual: Optional[float] = None,
        semaforo_presupuestal: str = "Pendiente_Presupuesto",
        requiere_aprobacion: bool = False,
        aprobado_por_user_id: Optional[str] = None,
        justificacion_aprobacion: Optional[str] = None,
    ) -> EvaluacionCTCModel:
        existing = self.get_ctc_by_postulacion(postulacion_id)
        if existing:
            raise DuplicateEntityError(f"Ya existe una evaluación CTC para la postulación {postulacion_id}.")

        eval_ctc = EvaluacionCTCModel(
            id=ctc_id,
            postulacion_id=postulacion_id,
            tipo_expectativa=tipo_expectativa,
            monto_declarado=monto_declarado,
            salario_bruto_mensual=salario_bruto_mensual,
            factor_ctc=factor_ctc,
            ctc_solicitado=ctc_solicitado,
            ctc_presupuestado=ctc_presupuestado,
            variacion_porcentual=variacion_porcentual,
            semaforo_presupuestal=semaforo_presupuestal,
            requiere_aprobacion=requiere_aprobacion,
            aprobado_por_user_id=aprobado_por_user_id,
            justificacion_aprobacion=justificacion_aprobacion,
            evaluado_por_user_id=evaluado_por_user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(eval_ctc)
        self.session.flush()
        return eval_ctc

    def get_ctc_by_postulacion(self, postulacion_id: str) -> Optional[EvaluacionCTCModel]:
        return self.session.execute(
            select(EvaluacionCTCModel).where(EvaluacionCTCModel.postulacion_id == postulacion_id)
        ).scalar_one_or_none()

    def get_ctc_evals(self, postulacion_id: str) -> List[EvaluacionCTCModel]:
        """Return list of CTC evaluations for postulation."""
        item = self.get_ctc_by_postulacion(postulacion_id)
        return [item] if item else []

    # Compliance
    def create_compliance(
        self,
        compliance_id: str,
        postulacion_id: str,
        estado_bgc: str = "Pendiente",
        consulta_equifax_realizada: bool = False,
        tiene_deuda_castigada_banca: bool = False,
        es_elegible_compliance: bool = True,
        notas_compliance: Optional[str] = None,
        verificado_por_user_id: Optional[str] = None,
    ) -> ComplianceModel:
        existing = self.get_compliance_by_postulacion(postulacion_id)
        if existing:
            raise DuplicateEntityError(f"Ya existe un registro de compliance para {postulacion_id}.")

        comp = ComplianceModel(
            id=compliance_id,
            postulacion_id=postulacion_id,
            estado_bgc=estado_bgc,
            consulta_equifax_realizada=consulta_equifax_realizada,
            tiene_deuda_castigada_banca=tiene_deuda_castigada_banca,
            es_elegible_compliance=es_elegible_compliance,
            notas_compliance=notas_compliance,
            verificado_por_user_id=verificado_por_user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(comp)
        self.session.flush()
        return comp

    def get_compliance_by_postulacion(self, postulacion_id: str) -> Optional[ComplianceModel]:
        return self.session.execute(
            select(ComplianceModel).where(ComplianceModel.postulacion_id == postulacion_id)
        ).scalar_one_or_none()
