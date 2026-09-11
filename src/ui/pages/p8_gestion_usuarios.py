"""User administration and role elevation management page (Restricted to Head of TA)."""
from __future__ import annotations

import streamlit as st
from sqlalchemy import select

from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.user_repository import UserRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.persistence.models import UsuarioModel
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.ui.session import get_current_user, is_head_of_ta
from src.domain.exceptions import InsufficientPermissionsError


def render_gestion_usuarios_page() -> None:
    """Render user administration, role promotion, and account unlock interface."""
    st.markdown("## 👥 Panel de Administración de Usuarios y Roles (RBAC)")
    st.caption("Control de accesos corporativos exclusivo para Head of Talent Acquisition bajo principio de mínimo privilegio.")

    user = get_current_user() or {}
    user_id = user.get("user_id", "")
    user_email = user.get("email", "")
    user_role = user.get("rol", "")

    # Strict RBAC Guard
    if not is_head_of_ta():
        st.error("🚫 **Acceso Restringido**: Esta sección está reservada exclusivamente para el `Head_of_Talent_Acquisition`.")
        try:
            with SessionLocal() as db:
                audit_repo = AuditRepository(db)
                audit_svc = AuditService(audit_repo)
                audit_svc.record_security_event(
                    usuario_id=user_id or "anon",
                    usuario_email=user_email or "anon@tcs.com",
                    rol_en_momento=user_role or "Compliance_Officer",
                    tipo_accion="Acceso_Denegado",
                    justificacion="Intento no autorizado de ingreso al Panel de Gestión de Usuarios",
                )
                db.commit()
        except Exception:
            pass
        return

    with SessionLocal() as db:
        user_repo = UserRepository(db)
        audit_repo = AuditRepository(db)
        audit_svc = AuditService(audit_repo)
        auth_svc = AuthService(user_repo, audit_svc)

        all_users = db.execute(select(UsuarioModel).order_by(UsuarioModel.created_at.desc())).scalars().all()

        st.markdown("#### 1. Directorio de Operadores Corporativos")
        user_table = []
        for u in all_users:
            user_table.append({
                "ID": u.id,
                "Nombres Completos": u.nombres_completos,
                "Email Corporativo": u.email,
                "Rol Actual": u.rol,
                "Estado de Cuenta": u.estado_cuenta,
                "Intentos Fallidos": u.intentos_fallidos,
                "Versión": u.record_version,
            })
        st.dataframe(user_table, use_container_width=True)

        st.markdown("---")
        c_elev, c_unlock = st.columns(2)

        with c_elev:
            st.markdown("#### 2. Elevación o Modificación de Rol")
            target_map = {u.id: f"{u.nombres_completos} ({u.email}) [Rol: {u.rol}]" for u in all_users}
            target_uid = st.selectbox("Seleccione Usuario a Modificar:", list(target_map.keys()), format_func=lambda x: target_map[x])

            new_rol = st.selectbox(
                "Nuevo Rol a Asignar:",
                [
                    "Senior_Technical_Recruiter",
                    "Account_Recruitment_Coordinator",
                    "Compliance_Officer",
                    "Head_of_Talent_Acquisition",
                ],
            )

            justificacion = st.text_input(
                "Justificación Operativa Obligatoria:",
                placeholder="Ej. Asignación a célula de selección de banca BCP",
            ).strip()

            if st.button("👑 Aplicar Cambio de Rol", type="primary", use_container_width=True):
                target_user = user_repo.get_by_id(target_uid)
                if not target_user:
                    st.error("Usuario no encontrado.")
                elif not justificacion:
                    st.error("Debe ingresar una justificación formal para el cambio de rol.")
                else:
                    try:
                        res = auth_svc.change_user_role(
                            admin_user_id=user_id,
                            target_user_id=target_uid,
                            new_role=new_rol,
                            justification=justificacion,
                            expected_version=target_user.record_version,
                        )
                        db.commit()
                        st.success(f"✅ Rol de {target_user.nombres_completos} actualizado a `{new_rol}` exitosamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al modificar rol: {e}")

        with c_unlock:
            st.markdown("#### 3. Desbloqueo y Reactivación de Cuenta")
            locked_users = [u for u in all_users if u.intentos_fallidos > 0 or u.estado_cuenta != "Activa"]

            if locked_users:
                locked_map = {u.id: f"{u.nombres_completos} ({u.email}) - {u.estado_cuenta}" for u in locked_users}
                locked_uid = st.selectbox("Usuario Bloqueado / Con Intentos:", list(locked_map.keys()), format_func=lambda x: locked_map[x])

                if st.button("🔓 Desbloquear Cuenta y Restablecer Intentos", use_container_width=True):
                    try:
                        auth_svc.unlock_user_account(
                            admin_user_id=user_id,
                            target_user_id=locked_uid,
                            justification=f"Desbloqueo manual de cuenta ejecutado por Head of TA ({user_email})",
                        )
                        db.commit()
                        st.success("✅ Cuenta desbloqueada y contador de intentos reiniciado a cero.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al desbloquear cuenta: {e}")
            else:
                st.info("No hay cuentas bloqueadas ni con intentos fallidos registrados.")
