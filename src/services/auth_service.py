"""Authentication and RBAC application service for ATS Core MVP."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from src.ports.auth_port import AuthPort
from src.adapters.persistence.repositories.user_repository import UserRepository
from src.services.audit_service import AuditService
from src.adapters.security.password_hasher import hash_password, verify_password, validate_password_complexity
from src.domain.value_objects import EmailCorporativo
from src.domain.exceptions import (
    AuthenticationError,
    AccountLockedError,
    InsufficientPermissionsError,
    EntityNotFoundError,
    DuplicateEntityError,
)
from src.config import config


class AuthService(AuthPort):
    """Application service managing authentication, lockout policy, and RBAC."""

    def __init__(self, user_repository: UserRepository, audit_service: AuditService):
        self.user_repo = user_repository
        self.audit_service = audit_service

    def register_user(
        self,
        nombres_completos: str,
        email: str,
        password: str,
        actor_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a new institutional user with default minimum privilege (Compliance_Officer)."""
        # Validate domain @tcs.com
        corp_email = EmailCorporativo(email)
        # Validate password complexity
        validate_password_complexity(password)
        hashed = hash_password(password)

        new_user_id = f"usr-{uuid.uuid4()}"
        user = self.user_repo.create_user(
            user_id=new_user_id,
            nombres_completos=nombres_completos.strip(),
            email=str(corp_email),
            hashed_password=hashed,
            rol="Compliance_Officer",
            autorizado_por_id=actor_user_id,
        )

        # Audit event
        self.audit_service.record_mutation(
            usuario_id=user.id,
            usuario_email=user.email,
            rol_en_momento=user.rol,
            tipo_accion="Creacion",
            entidad_objeto="Usuario",
            registro_id=user.id,
            version_registro=user.record_version,
            valores_nuevos={"nombres": user.nombres_completos, "email": user.email, "rol": user.rol},
            justificacion_operativa="Auto-registro institucional con rol por defecto Compliance_Officer",
        )

        return {
            "id": user.id,
            "nombres_completos": user.nombres_completos,
            "email": user.email,
            "rol": user.rol,
            "estado_cuenta": user.estado_cuenta,
        }

    def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """Authenticate credentials, incrementing failed attempts or locking account if necessary."""
        clean_email = email.strip().lower()
        user = self.user_repo.get_by_email(clean_email)

        if not user:
            # Prevent timing enumeration by still performing fake verify
            verify_password("DummyPassword123!", "$2b$10$tWCu/Q2bgbrav6OqZKxHEOcsOR269cc0Qh2axuaUlEp45DB7rq20y")
            raise AuthenticationError("Credenciales institucionales incorrectas.")

        # Check lockout
        if user.estado_cuenta == "Bloqueada_Por_Intentos":
            now_utc = datetime.now(timezone.utc)
            # Normalize user.bloqueado_hasta
            locked_until = user.bloqueado_hasta
            if locked_until and locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)

            if locked_until and locked_until > now_utc:
                remaining_minutes = int((locked_until - now_utc).total_seconds() // 60) + 1
                raise AccountLockedError(
                    f"Cuenta bloqueada por seguridad tras 5 intentos fallidos. Intente nuevamente en {remaining_minutes} minutos o contacte al Head of Talent Acquisition."
                )
            else:
                # Lockout period has elapsed, unlock automatically
                self.user_repo.unlock_account(user.id)

        # Verify password
        if not verify_password(password, user.hashed_password):
            attempts = self.user_repo.increment_failed_attempts(user.id)
            if attempts >= config.MAX_LOGIN_ATTEMPTS:
                lock_until = datetime.now(timezone.utc) + timedelta(minutes=config.LOCKOUT_DURATION_MINUTES)
                self.user_repo.lock_account_until(user.id, lock_until)

                self.audit_service.record_security_event(
                    usuario_id=user.id,
                    usuario_email=user.email,
                    rol_en_momento=user.rol,
                    tipo_accion="Acceso_Denegado",
                    justificacion=f"Bloqueo preventivo de cuenta activado tras {attempts} intentos fallidos consecutivos",
                    ip_address=ip_address,
                )
                raise AccountLockedError(
                    f"Cuenta bloqueada preventivamente tras {attempts} intentos fallidos. Intente nuevamente en 15 minutos."
                )

            self.audit_service.record_security_event(
                usuario_id=user.id,
                usuario_email=user.email,
                rol_en_momento=user.rol,
                tipo_accion="Acceso_Denegado",
                justificacion=f"Intento fallido de autenticacion ({attempts}/{config.MAX_LOGIN_ATTEMPTS})",
                ip_address=ip_address,
            )
            raise AuthenticationError("Credenciales institucionales incorrectas.")

        # Successful login
        self.user_repo.reset_failed_attempts(user.id)
        self.audit_service.record_security_event(
            usuario_id=user.id,
            usuario_email=user.email,
            rol_en_momento=user.rol,
            tipo_accion="Autenticacion",
            justificacion="Inicio de sesion corporativo exitoso",
            ip_address=ip_address,
        )

        return {
            "id": user.id,
            "nombres_completos": user.nombres_completos,
            "email": user.email,
            "rol": user.rol,
            "estado_cuenta": user.estado_cuenta,
            "record_version": user.record_version,
        }

    def change_user_role(
        self,
        admin_user_id: str,
        target_user_id: str,
        new_role: str,
        justification: str,
        expected_version: int,
    ) -> Dict[str, Any]:
        """Elevate or modify an operator's role (exclusive privilege of Head_of_Talent_Acquisition)."""
        admin = self.user_repo.get_by_id(admin_user_id)
        if not admin or admin.rol != "Head_of_Talent_Acquisition":
            raise InsufficientPermissionsError(
                "Operación denegada: Solo el Head of Talent Acquisition puede autorizar la modificación de roles."
            )

        if not justification or len(justification.strip()) < 5:
            raise ValueError("Se requiere una justificación operativa formal para el cambio de rol.")

        valid_roles = {
            "Head_of_Talent_Acquisition",
            "Senior_Technical_Recruiter",
            "Account_Recruitment_Coordinator",
            "Compliance_Officer",
        }
        if new_role not in valid_roles:
            raise ValueError(f"Rol '{new_role}' no es válido.")

        target = self.user_repo.get_by_id(target_user_id)
        if not target:
            raise EntityNotFoundError(f"Usuario {target_user_id} no encontrado.")

        old_role = target.rol
        updated = self.user_repo.update_user_role(
            user_id=target_user_id,
            new_role=new_role,
            authorized_by_id=admin_user_id,
            expected_version=expected_version,
        )

        self.audit_service.record_mutation(
            usuario_id=admin.id,
            usuario_email=admin.email,
            rol_en_momento=admin.rol,
            tipo_accion="Modificacion_Rol",
            entidad_objeto="Usuario",
            registro_id=target_user_id,
            version_registro=updated.record_version,
            valores_previos={"rol": old_role},
            valores_nuevos={"rol": new_role},
            justificacion_operativa=justification,
        )

        return {
            "id": updated.id,
            "email": updated.email,
            "rol": updated.rol,
            "record_version": updated.record_version,
        }

    def unlock_user_account(
        self,
        admin_user_id: str,
        target_user_id: str,
        justification: str,
    ) -> Dict[str, Any]:
        """Manually unlock an account before lockout timeout."""
        admin = self.user_repo.get_by_id(admin_user_id)
        if not admin or admin.rol != "Head_of_Talent_Acquisition":
            raise InsufficientPermissionsError(
                "Operación denegada: Solo el Head of Talent Acquisition puede desbloquear cuentas."
            )

        updated = self.user_repo.unlock_account(target_user_id)
        self.audit_service.record_security_event(
            usuario_id=admin.id,
            usuario_email=admin.email,
            rol_en_momento=admin.rol,
            tipo_accion="Desbloqueo_Manual",
            justificacion=justification,
        )
        return {
            "id": updated.id,
            "email": updated.email,
            "estado_cuenta": updated.estado_cuenta,
        }
