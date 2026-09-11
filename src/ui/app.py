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
    st.sidebar.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #334155;'/>", unsafe_allow_html=True)

    nav_options = [
        "📋 Ficha Única de Candidato",
        "📞 Screening Telefónico (HITL)",
        "💰 Simulador Financiero CTC",
        "📊 Validador Masivo Adecco",
        "🔒 Reporte de Exclusiones (Ley 29733)",
        "🟣 Catálogo Alumni TCS",
        "🛡️ Auditoría & Métricas del Embudo",
    ]

    # Show User Management exclusively to Head of TA
    if is_head_of_ta():
        nav_options.append("👥 Gestión de Usuarios y Roles")

    selected_page = st.sidebar.radio("Navegación:", nav_options)

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        logout(reason="Cierre de sesión voluntario por el usuario")
        st.rerun()

    # Route to selected page
    if selected_page == "📋 Ficha Única de Candidato":
        render_ficha_candidato_page()
    elif selected_page == "📞 Screening Telefónico (HITL)":
        render_screening_page()
    elif selected_page == "💰 Simulador Financiero CTC":
        render_simulador_ctc_page()
    elif selected_page == "📊 Validador Masivo Adecco":
        render_validador_adecco_page()
    elif selected_page == "🔒 Reporte de Exclusiones (Ley 29733)":
        render_reporte_exclusion_page()
    elif selected_page == "🟣 Catálogo Alumni TCS":
        render_alumni_page()
    elif selected_page == "🛡️ Auditoría & Métricas del Embudo":
        render_consola_auditoria_page()
    elif selected_page == "👥 Gestión de Usuarios y Roles":
        render_gestion_usuarios_page()


if __name__ == "__main__":
    main()
