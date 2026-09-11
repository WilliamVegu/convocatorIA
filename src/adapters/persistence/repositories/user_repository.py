"""User repository for RBAC management in SQLAlchemy 2.0."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.adapters.persistence.models import UsuarioModel
from src.domain.exceptions import EntityNotFoundError, DuplicateEntityError, OptimisticLockError


class UserRepository:
    """Repository handling persistence for UsuarioModel."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: str) -> Optional[UsuarioModel]:
        return self.session.execute(
            select(UsuarioModel).where(UsuarioModel.id == user_id)
        ).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[UsuarioModel]:
        return self.session.execute(
            select(UsuarioModel).where(UsuarioModel.email == email.strip().lower())
        ).scalar_one_or_none()

    def list_all(self) -> List[UsuarioModel]:
        return list(self.session.execute(select(UsuarioModel)).scalars().all())

    def create_user(
        self,
        user_id: str,
        nombres_completos: str,
        email: str,
        hashed_password: str,
        rol: str = "Compliance_Officer",
        autorizado_por_id: Optional[str] = None,
    ) -> UsuarioModel:
        existing = self.get_by_email(email)
        if existing:
            raise DuplicateEntityError(f"El correo electrónico '{email}' ya se encuentra registrado.")

        user = UsuarioModel(
            id=user_id,
            nombres_completos=nombres_completos,
            email=email.strip().lower(),
            hashed_password=hashed_password,
            rol=rol,
            estado_cuenta="Activa",
            intentos_fallidos=0,
            autorizado_por_id=autorizado_por_id,
            record_version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.session.add(user)
        self.session.flush()
        return user

    def update_user_role(
        self,
        user_id: str,
        new_role: str,
        authorized_by_id: str,
        expected_version: int,
    ) -> UsuarioModel:
        user = self.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(f"Usuario con id '{user_id}' no encontrado.")

        if user.record_version != expected_version:
            raise OptimisticLockError(
                f"Conflicto de concurrencia al actualizar usuario {user_id}. Versión esperada: {expected_version}, actual: {user.record_version}"
            )

        user.rol = new_role
        user.autorizado_por_id = authorized_by_id
        user.record_version += 1
        user.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return user

    def increment_failed_attempts(self, user_id: str) -> int:
        user = self.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(f"Usuario {user_id} no encontrado.")

        user.intentos_fallidos += 1
        user.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return user.intentos_fallidos

    def reset_failed_attempts(self, user_id: str) -> None:
        user = self.get_by_id(user_id)
        if user:
            user.intentos_fallidos = 0
            user.bloqueado_hasta = None
            if user.estado_cuenta == "Bloqueada_Por_Intentos":
                user.estado_cuenta = "Activa"
            user.ultimo_login = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            self.session.flush()

    def lock_account_until(self, user_id: str, until: datetime) -> UsuarioModel:
        user = self.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(f"Usuario {user_id} no encontrado.")

        user.estado_cuenta = "Bloqueada_Por_Intentos"
        user.bloqueado_hasta = until
        user.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return user

    def unlock_account(self, user_id: str) -> UsuarioModel:
        user = self.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(f"Usuario {user_id} no encontrado.")

        user.estado_cuenta = "Activa"
        user.intentos_fallidos = 0
        user.bloqueado_hasta = None
        user.updated_at = datetime.now(timezone.utc)
        self.session.flush()
        return user
