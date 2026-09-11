"""Integration tests for RBAC access control policies and permission enforcement."""
import pytest
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.adapters.persistence.repositories.user_repository import UserRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.domain.exceptions import InsufficientPermissionsError
from src.domain.entities import Usuario


def test_compliance_officer_read_only_restriction(db_session, compliance_user):
    user_repo = UserRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_svc = AuditService(audit_repo)
    auth_svc = AuthService(user_repo, audit_svc)

    u = Usuario(
        id=compliance_user.id,
        nombres_completos=compliance_user.nombres_completos,
        email=compliance_user.email,
        hashed_password=compliance_user.hashed_password,
        rol=compliance_user.rol,
    )
    # Compliance Officer has can_mutate() == False
    assert u.can_mutate() is False
    assert u.is_admin() is False

    # Attempting to elevate role using non-admin account must fail
    with pytest.raises(InsufficientPermissionsError, match="Solo el Head of Talent Acquisition"):
        auth_svc.change_user_role(
            admin_user_id=compliance_user.id,
            target_user_id=compliance_user.id,
            new_role="Senior_Technical_Recruiter",
            justification="Auto-elevación no autorizada",
            expected_version=1,
        )


def test_head_of_ta_elevates_role_with_audit_trail(db_session, admin_user, compliance_user):
    user_repo = UserRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_svc = AuditService(audit_repo)
    auth_svc = AuthService(user_repo, audit_svc)

    res = auth_svc.change_user_role(
        admin_user_id=admin_user.id,
        target_user_id=compliance_user.id,
        new_role="Senior_Technical_Recruiter",
        justification="Promoción a reclutador senior para proyecto banca",
        expected_version=compliance_user.record_version,
    )
    assert res["rol"] == "Senior_Technical_Recruiter"

    # Verify audit trail
    logs = audit_svc.filter_logs(tipo_accion="Modificacion_Rol")
    assert len(logs) >= 1
    recent_log = logs[0]
    assert recent_log.usuario_id == admin_user.id
    assert recent_log.registro_id == compliance_user.id
