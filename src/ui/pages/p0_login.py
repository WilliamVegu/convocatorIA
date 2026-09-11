"""Corporate login and user registration page for TCS ATS Core MVP."""
from __future__ import annotations

import streamlit as st
from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.user_repository import UserRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.ui.session import login_user
from src.domain.exceptions import AuthenticationError, InvalidDomainError, WeakPasswordError, AccountLockedError


def render_login_page() -> None:
    """Render dual-tab login & registration interface with 1-click demo buttons."""
    st.markdown("### 🔐 Acceso al Sistema de Adquisición de Talento")
    st.markdown("Por favor ingrese sus credenciales corporativas `@tcs.com` o utilice un perfil demo.")

    tab_login, tab_register = st.tabs(["🔑 Iniciar Sesión", "📝 Registro Corporativo"])

    with tab_login:
        with st.form("form_login"):
            email_input = st.text_input("Correo Corporativo", placeholder="usuario@tcs.com").strip()
            password_input = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar al ATS", use_container_width=True)

            if submitted:
                if not email_input or not password_input:
                    st.error("Por favor complete todos los campos.")
                else:
                    try:
                        with SessionLocal() as db:
                            user_repo = UserRepository(db)
                            audit_repo = AuditRepository(db)
                            audit_svc = AuditService(audit_repo)
                            auth_svc = AuthService(user_repo, audit_svc)

                            auth_res = auth_svc.authenticate(email_input, password_input)
                            db.commit()

                            login_user(
                                user_id=auth_res.get("usuario_id") or auth_res.get("id"),
                                email=auth_res["email"],
                                nombres_completos=auth_res["nombres_completos"],
                                rol=auth_res["rol"],
                            )
                            st.success(f"Bienvenido/a, {auth_res['nombres_completos']} ({auth_res['rol']})")
                            st.rerun()
                    except AuthenticationError as e:
                        st.error(f"Error de autenticación: {e}")
                    except AccountLockedError as e:
                        st.error(f"Cuenta bloqueada: {e}")
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")

        # Quick Access 1-Click Demo Section
        st.markdown("---")
        st.markdown("#### ⚡ Acceso Rápido de Evaluación (Roles Demo)")
        st.caption("Seleccione un rol institucional precargado para ingresar con 1 solo clic (Password: Password123!):")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if st.button("👑 Head of TA (Admin)", use_container_width=True, help="admin.ta@tcs.com"):
                _quick_login("admin.ta@tcs.com", "Password123!")

        with c2:
            if st.button("🎯 Senior Recruiter", use_container_width=True, help="recruiter.lead@tcs.com"):
                _quick_login("recruiter.lead@tcs.com", "Password123!")

        with c3:
            if st.button("📋 Coordinator", use_container_width=True, help="coordinator.tcs@tcs.com"):
                _quick_login("coordinator.tcs@tcs.com", "Password123!")

        with c4:
            if st.button("🛡️ Compliance Officer", use_container_width=True, help="compliance.officer@tcs.com"):
                _quick_login("compliance.officer@tcs.com", "Password123!")

    with tab_register:
        st.markdown("##### Crear Cuenta Institucional")
        st.caption(
            "Toda cuenta nueva se registra bajo el principio de menor privilegio con el rol "
            "`Compliance_Officer` (Solo Lectura). El Head of TA puede elevar el rol posteriormente."
        )

        with st.form("form_register"):
            reg_names = st.text_input("Nombres y Apellidos", placeholder="Ej. Carla Soto Mendoza").strip()
            reg_email = st.text_input("Correo Institucional (@tcs.com)", placeholder="carla.soto@tcs.com").strip()
            reg_password = st.text_input(
                "Contraseña (mínimo 8 caracteres, 1 mayúscula, 1 número y 1 carácter especial)",
                type="password",
            )
            reg_submitted = st.form_submit_button("Registrar Cuenta", use_container_width=True)

            if reg_submitted:
                if not reg_names or not reg_email or not reg_password:
                    st.error("Por favor complete todos los campos de registro.")
                else:
                    try:
                        with SessionLocal() as db:
                            user_repo = UserRepository(db)
                            audit_repo = AuditRepository(db)
                            audit_svc = AuditService(audit_repo)
                            auth_svc = AuthService(user_repo, audit_svc)

                            res = auth_svc.register_user(
                                nombres_completos=reg_names,
                                email=reg_email,
                                password=reg_password,
                            )
                            db.commit()

                            st.success(
                                f"✅ Cuenta creada exitosamente para {res['nombres_completos']}. "
                                f"Rol asignado: `{res['rol']}`. Proceda a iniciar sesión en la pestaña anterior."
                            )
                    except InvalidDomainError as e:
                        st.error(f"Dominio inválido: {e}")
                    except WeakPasswordError as e:
                        st.error(f"Contraseña débil: {e}")
                    except Exception as e:
                        st.error(f"Error al registrar: {e}")


def _quick_login(email: str, password: str) -> None:
    """Helper to perform quick 1-click evaluation login."""
    try:
        with SessionLocal() as db:
            user_repo = UserRepository(db)
            audit_repo = AuditRepository(db)
            audit_svc = AuditService(audit_repo)
            auth_svc = AuthService(user_repo, audit_svc)

            auth_res = auth_svc.authenticate(email, password)
            db.commit()

            login_user(
                user_id=auth_res.get("usuario_id") or auth_res.get("id"),
                email=auth_res["email"],
                nombres_completos=auth_res["nombres_completos"],
                rol=auth_res["rol"],
            )
            st.rerun()
    except Exception as e:
        st.error(f"Error en acceso rápido: {e}")
