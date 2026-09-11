"""Integration test covering the end-to-end candidate lifecycle."""
import pytest
from datetime import date
from src.services.candidate_service import CandidateService
from src.services.screening_service import ScreeningService
from src.services.ctc_service import CTCService
from src.services.audit_service import AuditService
from src.adapters.identity.apisperu_adapter import APIsPeruDNIAdapter
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.domain.exceptions import OptimisticLockError, DuplicateEntityError


def test_complete_candidate_lifecycle_flow(db_session, recruiter_user, admin_user):
    cand_repo = CandidatoRepository(db_session)
    post_repo = PostulacionRepository(db_session)
    audit_repo = AuditRepository(db_session)
    alumni_repo = AlumniRepository(db_session)

    audit_svc = AuditService(audit_repo)
    dni_adapter = APIsPeruDNIAdapter(cand_repo)
    cand_svc = CandidateService(cand_repo, dni_adapter, audit_svc, alumni_repo)
    scr_svc = ScreeningService(post_repo, cand_repo, audit_svc)
    ctc_svc = CTCService(post_repo, audit_svc)

    # 1. Identity lookup and Candidate Registration (DNI from seeded cache: 72345678 Ana Lucia Quispe)
    dni_info = cand_svc.lookup_dni("72345678")
    assert dni_info["success"] is True
    assert dni_info["datos"]["nombres"] == "ANA LUCIA"

    cand = cand_svc.create_candidate(
        actor_user_id=recruiter_user.id,
        actor_email=recruiter_user.email,
        actor_role=recruiter_user.rol,
        tipo_documento="DNI",
        numero_documento="72345678",
        nombres=dni_info["datos"]["nombres"],
        apellido_paterno=dni_info["datos"]["apellido_paterno"],
        apellido_materno=dni_info["datos"]["apellido_materno"],
        telefono_raw="987654321",
        email="ana.quispe@gmail.com",
        fecha_nacimiento=dni_info["datos"]["fecha_nacimiento"],
        distrito_residencia="Los Olivos",
    )
    assert cand.id is not None
    assert cand.telefono_e164 == "+51987654321"

    # 2. Candidate dynamic age
    age = cand.calcular_edad(referencia=date(2026, 12, 1))
    assert age == 28

    # 3. Create Job Application for client BCP
    post = post_repo.create_postulacion(
        postulacion_id="post-lifecycle-001",
        candidato_id=cand.id,
        cliente_cuenta="BCP",
        rgs_vacante_id="RGS-LIFECYCLE-01",
        perfil_tecnico="Data Engineer",
        reclutador_asignado_id=recruiter_user.id,
        fuente_origen="LinkedIn_Oficial",
        trimestre_fiscal="FY27-Q1",
        created_by_user_id=recruiter_user.id,
    )
    assert post.estado_embudo == "Nuevo"

    # 4. Human Screening (7 dimensions)
    # Los Olivos to BCP La Molina triggers commute alert
    screening = scr_svc.record_screening_call(
        evaluador_user_id=recruiter_user.id,
        evaluador_email=recruiter_user.email,
        evaluador_role=recruiter_user.rol,
        postulacion_id=post.id,
        dim1_disponibilidad="2_semanas",
        dim2_resumen_tecnico="Validada experiencia en PySpark, AWS Glue y SQL.",
        dim3_expectativa_declarada=7500.0,
        dim4_interes_vacante="Alto",
        dim5_modalidad_aceptada="Híbrido",
        dim7_impresion_general="Excelente comunicación y fit técnico.",
        dictamen_humano="Avanza_Entrevista_Tecnica",
    )
    assert screening.dim6_viabilidad_traslado == "Alerta_Distancia_Critica"
    assert screening.dim6_alerta_distancia_nota is not None
    # Funnel status updated to Pendiente_Entrevistas
    post_updated = post_repo.get_by_id(post.id)
    assert post_updated.estado_embudo == "Pendiente_Entrevistas"

    # 5. Financial CTC Evaluation (Factor 1.56)
    # Expectation S/. 7,500 with budget S/. 11,000 -> CTC = 7,500 * 1.56 = 11,700 (+6.36% -> Requiere_Aprobacion)
    eval_ctc = ctc_svc.evaluate_and_persist_ctc(
        actor_user_id=recruiter_user.id,
        actor_email=recruiter_user.email,
        actor_role=recruiter_user.rol,
        postulacion_id=post.id,
        tipo_expectativa="Bruto",
        monto_declarado=7500.0,
        ctc_presupuestado=11000.0,
    )
    assert eval_ctc.ctc_solicitado == 11700.0
    assert eval_ctc.semaforo_presupuestal == "Requiere_Aprobacion"
    assert eval_ctc.requiere_aprobacion is True

    # 6. Admin Approval of CTC Exception
    approved_ctc = ctc_svc.approve_ctc_exception(
        approver_user_id=admin_user.id,
        approver_email=admin_user.email,
        approver_role=admin_user.rol,
        postulacion_id=post.id,
        justification="Aprobado por perfil escaso con alta demanda en BCP",
    )
    assert approved_ctc.requiere_aprobacion is False
    assert approved_ctc.aprobado_por_user_id == admin_user.id

    # 7. Optimistic Locking Test
    # Updating candidate with stale version must raise OptimisticLockError
    with pytest.raises(OptimisticLockError):
        cand_svc.update_candidate(
            candidato_id=cand.id,
            actor_user_id=recruiter_user.id,
            actor_email=recruiter_user.email,
            actor_role=recruiter_user.rol,
            expected_version=99,  # Stale version
            justification="Intento concurrente fallido",
            distrito_residencia="Miraflores",
        )

    # 8. Audit Trail Verification
    logs = audit_svc.filter_logs(entidad_objeto="Candidato")
    assert len(logs) >= 1
    mutation_actions = [l.tipo_accion for l in logs]
    assert "Creacion" in mutation_actions
