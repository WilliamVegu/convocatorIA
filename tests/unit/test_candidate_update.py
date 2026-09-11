"""Unit tests for candidate and job application dynamic editing and audit logging."""
import pytest
from datetime import date
from src.services.candidate_service import CandidateService
from src.services.audit_service import AuditService
from src.adapters.identity.apisperu_adapter import APIsPeruDNIAdapter
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.domain.exceptions import OptimisticLockError, DuplicateEntityError


def test_candidate_update_success_and_audit(db_session, recruiter_user):
    """Ensure candidate fields can be edited dynamically with automatic E.164 normalization and audit logging."""
    cand_repo = CandidatoRepository(db_session)
    post_repo = PostulacionRepository(db_session)
    audit_repo = AuditRepository(db_session)
    alumni_repo = AlumniRepository(db_session)

    audit_svc = AuditService(audit_repo)
    dni_adapter = APIsPeruDNIAdapter(cand_repo)
    cand_svc = CandidateService(cand_repo, dni_adapter, audit_svc, alumni_repo)

    # 1. Create candidate
    cand = cand_svc.create_candidate(
        actor_user_id=recruiter_user.id,
        actor_email=recruiter_user.email,
        actor_role=recruiter_user.rol,
        tipo_documento="DNI",
        numero_documento="48991122",
        nombres="CARLOS ALBERTO",
        apellido_paterno="MENDOZA",
        apellido_materno="RODRIGUEZ",
        telefono_raw="991234567",
        email="carlos.mendoza@gmail.com",
        fecha_nacimiento=date(1993, 5, 20),
        distrito_residencia="San Borja",
    )
    db_session.flush()

    assert cand.record_version == 1
    assert cand.telefono_e164 == "+51991234567"
    assert cand.nombres_completos_normalizado == "CARLOS ALBERTO MENDOZA RODRIGUEZ"

    # 2. Update candidate: new phone number with spaces/dashes, updated district and name
    updated_cand = cand_svc.update_candidate(
        candidato_id=cand.id,
        actor_user_id=recruiter_user.id,
        actor_email=recruiter_user.email,
        actor_role=recruiter_user.rol,
        expected_version=1,
        justification="Actualización de teléfono y distrito solicitada por candidato",
        nombres="CARLOS ANDRES",
        telefono_raw="988-765-432",
        distrito_residencia="Miraflores",
        email="carlos.andres.mendoza@gmail.com",
    )
    db_session.flush()

    assert updated_cand.record_version == 2
    assert updated_cand.nombres == "CARLOS ANDRES"
    assert updated_cand.telefono_e164 == "+51988765432"
    assert updated_cand.distrito_residencia == "Miraflores"
    assert updated_cand.email == "carlos.andres.mendoza@gmail.com"
    assert updated_cand.nombres_completos_normalizado == "CARLOS ANDRES MENDOZA RODRIGUEZ"

    # 3. Check audit trail
    events = audit_repo.list_by_entity("Candidato", cand.id)
    assert len(events) >= 2
    mod_event = next(e for e in events if e.tipo_accion == "Modificacion")
    assert mod_event.usuario_email == recruiter_user.email
    assert mod_event.version_registro == 2
    assert mod_event.justificacion_operativa == "Actualización de teléfono y distrito solicitada por candidato"


def test_candidate_update_optimistic_lock_conflict(db_session, recruiter_user):
    """Ensure update fails with OptimisticLockError if version has changed concurrently."""
    cand_repo = CandidatoRepository(db_session)
    audit_repo = AuditRepository(db_session)
    alumni_repo = AlumniRepository(db_session)

    audit_svc = AuditService(audit_repo)
    dni_adapter = APIsPeruDNIAdapter(cand_repo)
    cand_svc = CandidateService(cand_repo, dni_adapter, audit_svc, alumni_repo)

    cand = cand_svc.create_candidate(
        actor_user_id=recruiter_user.id,
        actor_email=recruiter_user.email,
        actor_role=recruiter_user.rol,
        tipo_documento="DNI",
        numero_documento="48991133",
        nombres="LUCIA",
        apellido_paterno="SANTOS",
        telefono_raw="977112233",
        email="lucia.santos@gmail.com",
    )
    db_session.flush()

    with pytest.raises(OptimisticLockError):
        cand_svc.update_candidate(
            candidato_id=cand.id,
            actor_user_id=recruiter_user.id,
            actor_email=recruiter_user.email,
            actor_role=recruiter_user.rol,
            expected_version=99,  # Wrong expected version
            justification="Concurrent edit test",
            distrito_residencia="Surco",
        )


def test_candidate_update_phone_collision_prevention(db_session, recruiter_user):
    """Ensure update prevents changing a phone to one already registered by another candidate."""
    cand_repo = CandidatoRepository(db_session)
    audit_repo = AuditRepository(db_session)
    alumni_repo = AlumniRepository(db_session)

    audit_svc = AuditService(audit_repo)
    dni_adapter = APIsPeruDNIAdapter(cand_repo)
    cand_svc = CandidateService(cand_repo, dni_adapter, audit_svc, alumni_repo)

    # Cand A
    cand_a = cand_svc.create_candidate(
        actor_user_id=recruiter_user.id,
        actor_email=recruiter_user.email,
        actor_role=recruiter_user.rol,
        tipo_documento="DNI",
        numero_documento="48991144",
        nombres="PEDRO",
        apellido_paterno="ROJAS",
        telefono_raw="966111222",
        email="pedro.rojas@gmail.com",
    )
    # Cand B
    cand_b = cand_svc.create_candidate(
        actor_user_id=recruiter_user.id,
        actor_email=recruiter_user.email,
        actor_role=recruiter_user.rol,
        tipo_documento="DNI",
        numero_documento="48991155",
        nombres="MARIA",
        apellido_paterno="FLORES",
        telefono_raw="966333444",
        email="maria.flores@gmail.com",
    )
    db_session.flush()

    # Attempt to update Cand B's phone to Cand A's phone
    with pytest.raises(DuplicateEntityError) as exc:
        cand_svc.update_candidate(
            candidato_id=cand_b.id,
            actor_user_id=recruiter_user.id,
            actor_email=recruiter_user.email,
            actor_role=recruiter_user.rol,
            expected_version=cand_b.record_version,
            justification="Changing phone collision",
            telefono_raw="966111222",  # Collision!
        )
    assert "ya está asignado a otro candidato" in str(exc.value)


def test_postulacion_update_success(db_session, recruiter_user):
    """Ensure job application fields (status, client, observations, availability) can be updated with versioning."""
    cand_repo = CandidatoRepository(db_session)
    post_repo = PostulacionRepository(db_session)
    audit_repo = AuditRepository(db_session)
    alumni_repo = AlumniRepository(db_session)

    audit_svc = AuditService(audit_repo)
    dni_adapter = APIsPeruDNIAdapter(cand_repo)
    cand_svc = CandidateService(cand_repo, dni_adapter, audit_svc, alumni_repo)

    cand = cand_svc.create_candidate(
        actor_user_id=recruiter_user.id,
        actor_email=recruiter_user.email,
        actor_role=recruiter_user.rol,
        tipo_documento="DNI",
        numero_documento="48991166",
        nombres="ESTEBAN",
        apellido_paterno="GOMEZ",
        telefono_raw="955112233",
        email="esteban.gomez@gmail.com",
    )
    post = post_repo.create_postulacion(
        postulacion_id="post-test-edit-001",
        candidato_id=cand.id,
        cliente_cuenta="Interbank",
        rgs_vacante_id="RGS-TEST-01",
        perfil_tecnico="Full Stack Developer",
        reclutador_asignado_id=recruiter_user.id,
        fuente_origen="LinkedIn_Oficial",
        trimestre_fiscal="FY27-Q1",
        created_by_user_id=recruiter_user.id,
        estado_embudo="Nuevo",
        observaciones="Inicial",
    )
    db_session.flush()

    assert post.record_version == 1
    assert post.cliente_cuenta == "Interbank"
    assert post.estado_embudo == "Nuevo"

    # Update postulacion
    updated_p = post_repo.update_postulacion(
        postulacion_id=post.id,
        updated_by_user_id=recruiter_user.id,
        expected_version=1,
        cliente_cuenta="BBVA",
        perfil_tecnico="Lead Architect",
        estado_embudo="Screening_Telefonico",
        disponibilidad_incorporacion="15 días",
        observaciones="Candidato evaluado y en espera de entrevista técnica",
    )
    db_session.flush()

    assert updated_p.record_version == 2
    assert updated_p.cliente_cuenta == "BBVA"
    assert updated_p.perfil_tecnico == "Lead Architect"
    assert updated_p.estado_embudo == "Screening_Telefonico"
    assert updated_p.disponibilidad_incorporacion == "15 días"
    assert updated_p.observaciones == "Candidato evaluado y en espera de entrevista técnica"
