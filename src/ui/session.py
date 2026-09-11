"""Session management and RBAC guard for Streamlit ATS UI."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
import streamlit as st

from src.config import config
from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.services.audit_service import AuditService

SESSION_TIMEOUT_SECONDS = config.SESSION_TIMEOUT_MINUTES * 60


def init_session() -> None:
    """Initialize session state defaults if not already present."""
    if "is_authenticated" not in st.session_state:
        st.session_state["is_authenticated"] = False
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    if "email" not in st.session_state:
        st.session_state["email"] = None
    if "nombres_completos" not in st.session_state:
        st.session_state["nombres_completos"] = None
    if "rol" not in st.session_state:
        st.session_state["rol"] = None
    if "last_activity_time" not in st.session_state:
        st.session_state["last_activity_time"] = time.time()
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "p1_ficha"


def check_session_timeout() -> bool:
    """Validate 30-minute session inactivity timeout.

    Returns:
        bool: True if session is valid and active, False if timed out.
    """
    init_session()
    if not st.session_state.get("is_authenticated"):
        return False

    current_time = time.time()
    last_active = st.session_state.get("last_activity_time", current_time)

    if current_time - last_active > SESSION_TIMEOUT_SECONDS:
        logout(reason="Inactividad superior a 30 minutos")
        st.warning("⏱️ Su sesión ha expirado por inactividad. Por favor inicie sesión nuevamente.")
        return False

    # Update last activity
    st.session_state["last_activity_time"] = current_time
    return True


def login_user(
    user_id: str,
    email: str,
    nombres_completos: str,
    rol: str,
) -> None:
    """Establish authenticated session."""
    init_session()
    st.session_state["is_authenticated"] = True
    st.session_state["user_id"] = user_id
    st.session_state["email"] = email
    st.session_state["nombres_completos"] = nombres_completos
    st.session_state["rol"] = rol
    st.session_state["last_activity_time"] = time.time()


def logout(reason: str = "Cierre voluntario de sesión") -> None:
    """Terminate current user session and reset state."""
    init_session()
    user_id = st.session_state.get("user_id")
    user_email = st.session_state.get("email")
    user_role = st.session_state.get("rol")

    # Record logout in audit trail if authenticated
    if user_id and user_email:
        try:
            with SessionLocal() as db:
                audit_svc = AuditService(AuditRepository(db))
                audit_svc.log_event(
                    usuario_id=user_id,
                    usuario_email=user_email,
                    rol_en_momento=user_role or "Compliance_Officer",
                    tipo_accion="Cierre_Sesion",
                    entidad_objeto="Sesion",
                    registro_id=user_id,
                    version_registro=1,
                    justificacion_operativa=reason,
                )
                db.commit()
        except Exception:
            pass

    st.session_state["is_authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["email"] = None
    st.session_state["nombres_completos"] = None
    st.session_state["rol"] = None
    st.session_state["last_activity_time"] = time.time()


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return dictionary with current user credentials."""
    init_session()
    if not st.session_state.get("is_authenticated"):
        return None
    return {
        "user_id": st.session_state["user_id"],
        "email": st.session_state["email"],
        "nombres_completos": st.session_state["nombres_completos"],
        "rol": st.session_state["rol"],
    }


def can_write() -> bool:
    """Return False if user is Compliance_Officer (Read-only under RBAC)."""
    init_session()
    rol = st.session_state.get("rol")
    if not rol or rol == "Compliance_Officer":
        return False
    return True


def is_head_of_ta() -> bool:
    """Return True if user has Head_of_Talent_Acquisition role."""
    init_session()
    return st.session_state.get("rol") == "Head_of_Talent_Acquisition"


def has_role(allowed_roles: List[str]) -> bool:
    """Check if current user's role is in the authorized list."""
    init_session()
    return st.session_state.get("rol") in allowed_roles


def enforce_write_permission(action_name: str = "esta acción") -> bool:
    """Check write permissions; if denied, displays warning and audits security event.

    Returns:
        bool: True if write allowed, False if blocked.
    """
    if can_write():
        return True

    user = get_current_user()
    msg = "Acceso denegado: su rol solo posee permisos de consulta y auditoría."
    st.error(f"🚫 {msg}")

    if user:
        try:
            with SessionLocal() as db:
                audit_svc = AuditService(AuditRepository(db))
                audit_svc.log_event(
                    usuario_id=user["user_id"],
                    usuario_email=user["email"],
                    rol_en_momento=user["rol"],
                    tipo_accion="Acceso_Denegado",
                    entidad_objeto="Operacion",
                    registro_id="write_blocked",
                    version_registro=1,
                    justificacion_operativa=f"Intento de ejecucion de {action_name} sin permisos de escritura.",
                )
                db.commit()
        except Exception:
            pass

    return False
