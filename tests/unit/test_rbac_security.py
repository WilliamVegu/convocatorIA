"""Unit tests for RBAC, password security, and account lockout policies."""
import pytest
from datetime import datetime, timedelta, timezone
from src.adapters.security.password_hasher import (
    hash_password,
    verify_password,
    validate_password_complexity,
)
from src.domain.value_objects import EmailCorporativo


def test_password_complexity_valid():
    validate_password_complexity("StrongPass123!")


def test_password_complexity_missing_length():
    with pytest.raises(ValueError, match="al menos 8 caracteres"):
        validate_password_complexity("Pass1!")


def test_password_complexity_missing_uppercase():
    with pytest.raises(ValueError, match="letra mayúscula"):
        validate_password_complexity("password123!")


def test_password_complexity_missing_lowercase():
    with pytest.raises(ValueError, match="letra minúscula"):
        validate_password_complexity("PASSWORD123!")


def test_password_complexity_missing_number():
    with pytest.raises(ValueError, match="dígito numérico"):
        validate_password_complexity("PasswordSpecial!")


def test_password_complexity_missing_special_char():
    with pytest.raises(ValueError, match="carácter especial"):
        validate_password_complexity("Password123")


def test_password_hash_and_verify():
    raw = "TcsSecure#2026"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_email_corporativo_valid():
    email = EmailCorporativo("valeria.soto@tcs.com")
    assert str(email) == "valeria.soto@tcs.com"


def test_email_corporativo_rejects_external_domains():
    with pytest.raises(ValueError, match="Acceso restringido"):
        EmailCorporativo("valeria.soto@gmail.com")
    with pytest.raises(ValueError, match="Acceso restringido"):
        EmailCorporativo("valeria.soto@adecco.com")


def test_auth_service_registration_and_login_flow(db_session):
    from src.adapters.persistence.repositories.user_repository import UserRepository
    from src.adapters.persistence.repositories.audit_repository import AuditRepository
    from src.services.audit_service import AuditService
    from src.services.auth_service import AuthService
    from src.domain.exceptions import AuthenticationError, AccountLockedError, InsufficientPermissionsError

    user_repo = UserRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_svc = AuditService(audit_repo)
    auth_svc = AuthService(user_repo, audit_svc)

    # 1. Register new user
    res = auth_svc.register_user(
        nombres_completos="Lucia Mendez",
        email="lucia.mendez@tcs.com",
        password="Password123!",
    )
    assert res["email"] == "lucia.mendez@tcs.com"
    assert res["rol"] == "Compliance_Officer"

    # 2. Login successfully
    auth_res = auth_svc.authenticate("lucia.mendez@tcs.com", "Password123!")
    assert auth_res["email"] == "lucia.mendez@tcs.com"

    # 3. Failed password increments attempts
    with pytest.raises(AuthenticationError):
        auth_svc.authenticate("lucia.mendez@tcs.com", "WrongPassword1!")

    # 4. 5 failed attempts locks the account
    for _ in range(3):
        with pytest.raises(AuthenticationError):
            auth_svc.authenticate("lucia.mendez@tcs.com", "WrongPassword1!")

    # 5th attempt triggers lockout
    with pytest.raises(AccountLockedError):
        auth_svc.authenticate("lucia.mendez@tcs.com", "WrongPassword1!")

    # Subsequent login blocked
    with pytest.raises(AccountLockedError):
        auth_svc.authenticate("lucia.mendez@tcs.com", "Password123!")

    # 5. Admin can unlock and elevate role
    admin = user_repo.get_by_email("admin.ta@tcs.com")
    assert admin is not None
    auth_svc.unlock_user_account(admin.id, res["id"], "Desbloqueo solicitado por gerencia")

    elevated = auth_svc.change_user_role(
        admin_user_id=admin.id,
        target_user_id=res["id"],
        new_role="Senior_Technical_Recruiter",
        justification="Promocion autorizada para liderar cuenta BCP",
        expected_version=1,
    )
    assert elevated["rol"] == "Senior_Technical_Recruiter"

