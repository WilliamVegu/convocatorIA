"""Integration tests verifying physical immutability and append-only semantics of bitacora_auditoria."""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.persistence.models import BitacoraAuditoriaModel


def test_audit_log_append_and_filter(db_session: Session, admin_user):
    repo = AuditRepository(db_session)
    log = repo.append_log(
        log_id="test-log-001",
        usuario_id=admin_user.id,
        usuario_email=admin_user.email,
        rol_en_momento=admin_user.rol,
        tipo_accion="Creacion",
        entidad_objeto="Candidato",
        registro_id="cand-001",
        valores_nuevos={"nombres": "Pedro", "apellido": "Perez"},
        justificacion_operativa="Registro de prueba para auditoria",
    )
    db_session.commit()

    assert log.id == "test-log-001"
    fetched = repo.get_by_id("test-log-001")
    assert fetched is not None
    assert fetched.usuario_email == admin_user.email
    assert "Pedro" in fetched.valores_nuevos_json

    filtered = repo.filter_logs(usuario_email=admin_user.email, entidad_objeto="Candidato")
    assert len(filtered) >= 1
    assert any(entry.id == "test-log-001" for entry in filtered)


def test_audit_log_physical_update_blocked_by_trigger(db_session: Session, admin_user):
    repo = AuditRepository(db_session)
    repo.append_log(
        log_id="test-log-tamper-update",
        usuario_id=admin_user.id,
        usuario_email=admin_user.email,
        rol_en_momento=admin_user.rol,
        tipo_accion="Creacion",
        entidad_objeto="Candidato",
        registro_id="cand-tamper-1",
    )
    db_session.commit()

    # Attempt physical SQL UPDATE
    with pytest.raises(Exception, match="Violacion de Integridad.*inmutable"):
        db_session.execute(
            text("UPDATE bitacora_auditoria SET usuario_email = 'hacked@tcs.com' WHERE id = 'test-log-tamper-update'")
        )
        db_session.commit()
    db_session.rollback()


def test_audit_log_physical_delete_blocked_by_trigger(db_session: Session, admin_user):
    repo = AuditRepository(db_session)
    repo.append_log(
        log_id="test-log-tamper-delete",
        usuario_id=admin_user.id,
        usuario_email=admin_user.email,
        rol_en_momento=admin_user.rol,
        tipo_accion="Creacion",
        entidad_objeto="Candidato",
        registro_id="cand-tamper-2",
    )
    db_session.commit()

    # Attempt physical SQL DELETE
    with pytest.raises(Exception, match="Violacion de Integridad.*eliminacion"):
        db_session.execute(
            text("DELETE FROM bitacora_auditoria WHERE id = 'test-log-tamper-delete'")
        )
        db_session.commit()
    db_session.rollback()
