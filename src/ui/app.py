"""Main Streamlit application router and navigation for ATS TCS Perú."""
from __future__ import annotations

import os
import streamlit as st

from src.adapters.persistence.database import init_db, SessionLocal
from src.adapters.persistence.seed import seed_database
from src.ui.theme import apply_theme, render_header
from src.ui.session import (
    init_session,
    check_session_timeout,
    get_current_user,
    logout,
    is_head_of_ta,
)
from src.ui.pages.p0_login import render_login_page
from src.ui.pages.p1_ficha_candidato import render_ficha_candidato_page
from src.ui.pages.p2_screening_llamada import render_screening_page
from src.ui.pages.p3_simulador_ctc import render_simulador_ctc_page
from src.ui.pages.p4_validador_adecco import render_validador_adecco_page
from src.ui.pages.p5_reporte_exclusion import render_reporte_exclusion_page
from src.ui.pages.p6_alumni_tcs import render_alumni_page
from src.ui.pages.p7_consola_auditoria import render_consola_auditoria_page
from src.ui.pages.p8_gestion_usuarios import render_gestion_usuarios_page
from src.ui.pages.p9_normalizador_rgs import render_normalizador_rgs_page


def main() -> None:
    """Primary application entry point."""
    st.set_page_config(
        page_title="ATS TCS Perú - Talent Acquisition",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize Database and Bootstrap Seed
    try:
        init_db()
        with SessionLocal() as db:
            seed_database(db)
            db.commit()
    except Exception:
        pass

    apply_theme()
    init_session()

    # Session inactivity check
    is_active = check_session_timeout()
    current_user = get_current_user()

    if not is_active or not current_user:
        render_header()
        render_login_page()
        return

    # Authenticated user interface
    render_header(current_user=current_user)

    # Sidebar Navigation Menu
    logo_path = "assets/tcs_logo.png"
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)
    st.sidebar.markdown("### 🏢 Menú de Operaciones")
    st.sidebar.markdown(f"👤 **{current_user['nombres_completos']}**")
    rol_display = current_user['rol'].replace('_', ' ')
    st.sidebar.markdown(f"<span class='tcs-badge tcs-badge-blue'>{rol_display}</span>", unsafe_allow_html=True)
    st.sidebar.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #334155;'/>", unsafe_allow_html=True)

    nav_options = [
        "1. 📝 Requerimiento RGS a JD",
        "2. 📋 Ficha Única de Candidato",
        "3. 📞 Screening Telefónico (HITL)",
        "4. 💰 Simulador Financiero CTC",
        "5. 📊 Validador Masivo Adecco",
        "6. 🔒 Reporte de Exclusiones (Ley 29733)",
        "7. 🟣 Catálogo Alumni TCS",
        "8. 🛡️ Consola de Auditoría & Métricas",
    ]

    # Show User Management exclusively to Head of TA
    if is_head_of_ta():
        nav_options.append("9. 👥 Gestión de Usuarios y Roles")

    # Determine default index based on current session state
    from src.ui.session import NAV_PAGE_KEYS, CANONICAL_PAGE_MAP

    current_key = st.session_state.get("current_page", "p9_rgs")
    target_label = NAV_PAGE_KEYS.get(current_key)
    current_active = st.session_state.get("active_nav_page")

    if target_label in nav_options:
        default_index = nav_options.index(target_label)
    elif current_active in nav_options:
        default_index = nav_options.index(current_active)
    else:
        default_index = 0

    selected_page = st.sidebar.radio("Etapas del Proceso:", nav_options, index=default_index)
    canonical_key = CANONICAL_PAGE_MAP.get(selected_page, "p9_rgs")
    st.session_state["current_page"] = canonical_key
    st.session_state["active_nav_page"] = selected_page

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        logout(reason="Cierre de sesión voluntario por el usuario")
        st.rerun()

    # Route to selected page via canonical key
    if canonical_key == "p9_rgs":
        render_normalizador_rgs_page()
    elif canonical_key == "p1_ficha":
        render_ficha_candidato_page()
    elif canonical_key == "p2_screening":
        render_screening_page()
    elif canonical_key == "p3_ctc":
        render_simulador_ctc_page()
    elif canonical_key == "p4_adecco":
        render_validador_adecco_page()
    elif canonical_key == "p5_exclusiones":
        render_reporte_exclusion_page()
    elif canonical_key == "p6_alumni":
        render_alumni_page()
    elif canonical_key == "p7_auditoria":
        render_consola_auditoria_page()
    elif canonical_key == "p8_usuarios":
        render_gestion_usuarios_page()


if __name__ == "__main__":
    main()
