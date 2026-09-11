import importlib
import pytest

contracts = importlib.import_module("specs.001-ats-core-mvp.contracts")


def test_user_registration_valid_tcs_email_and_password():
    req = contracts.UserRegistrationRequest(
        nombres_completos="Carla Soto Mendoza",
        email="carla.soto@tcs.com",
        password="Password123!",
    )
    assert req.email == "carla.soto@tcs.com"


def test_user_registration_rejects_non_tcs_email():
    with pytest.raises(ValueError, match="dominio institucional '@tcs.com'"):
        contracts.UserRegistrationRequest(
            nombres_completos="Carla Soto",
            email="carla.soto@gmail.com",
            password="Password123!",
        )


def test_user_registration_rejects_weak_password_missing_special_char():
    with pytest.raises(ValueError, match="al menos un carácter especial"):
        contracts.UserRegistrationRequest(
            nombres_completos="Carla Soto",
            email="carla.soto@tcs.com",
            password="Password123",  # No special char
        )


def test_session_payload_permissions():
    # Compliance Officer: cannot mutate
    session_compliance = contracts.SessionPayload(
        user_id="u-01",
        nombres_completos="Auditor Test",
        email="auditor@tcs.com",
        rol=contracts.RolUsuarioEnum.COMPLIANCE_OFFICER,
        session_token="tok-123",
    )
    assert session_compliance.can_mutate() is False
    assert session_compliance.is_admin() is False

    # Senior Recruiter: can mutate, not admin
    session_recruiter = contracts.SessionPayload(
        user_id="u-02",
        nombres_completos="Recruiter Test",
        email="recruiter@tcs.com",
        rol=contracts.RolUsuarioEnum.SENIOR_TECHNICAL_RECRUITER,
        session_token="tok-456",
    )
    assert session_recruiter.can_mutate() is True
    assert session_recruiter.is_admin() is False

    # Head of TA: can mutate, is admin
    session_admin = contracts.SessionPayload(
        user_id="u-03",
        nombres_completos="Admin TA",
        email="admin.ta@tcs.com",
        rol=contracts.RolUsuarioEnum.HEAD_OF_TALENT_ACQUISITION,
        session_token="tok-789",
    )
    assert session_admin.can_mutate() is True
    assert session_admin.is_admin() is True


def test_audit_search_filter_with_email():
    f = contracts.AuditSearchFilter(
        usuario_email="carla.soto@tcs.com",
        entidad_objeto=contracts.EntidadAuditoriaEnum.CANDIDATO,
        tipo_accion=contracts.TipoAccionAuditoriaEnum.CREACION,
    )
    assert f.usuario_email == "carla.soto@tcs.com"
    assert f.limit == 100
