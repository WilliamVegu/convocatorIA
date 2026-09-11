"""Alumni TCS catalog and Boomerang detection interface page."""
from __future__ import annotations

import uuid
from datetime import date
import streamlit as st

from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.services.audit_service import AuditService
from src.services.alumni_service import AlumniService
from src.services.candidate_service import normalize_full_name
from src.ui.session import get_current_user, enforce_write_permission
from src.ui.theme import render_badge


def render_alumni_page() -> None:
    """Render Alumni TCS catalog, rehire eligibility status and registration form."""
    st.markdown("## 🟣 Catálogo Alumni TCS Perú (Candidatos Boomerang)")
    st.caption("Detección de ex-colaboradores para capitalizar su curva de aprendizaje y bloquear el pago de comisiones indebidas a agencias.")

    tab_cat, tab_reg = st.tabs(["📚 Catálogo de Ex-Colaboradores", "➕ Registrar Ex-Colaborador (Alumni)"])

    with tab_cat:
        _render_catalogo_alumni()

    with tab_reg:
        _render_registro_alumni()


def _render_catalogo_alumni() -> None:
    """Busqueda y visualizacion de alumni."""
    q_search = st.text_input("Buscar por DNI, Correo Histórico o Nombres:", key="alumni_search_q").strip()

    with SessionLocal() as db:
        alm_repo = AlumniRepository(db)
        if q_search:
            # Check by DNI first, then search by name
            if q_search.isdigit() and len(q_search) == 8:
                single = alm_repo.get_by_dni(q_search)
                alumni_list = [single] if single else []
            else:
                alumni_list = alm_repo.search_by_normalized_name(normalize_full_name(q_search))
        else:
            alumni_list = alm_repo.list_all(limit=100)

        if not alumni_list:
            st.info("No se encontraron registros de ex-colaboradores con el criterio ingresado.")
            return

        rows = []
        for a in alumni_list:
            b_type = "green" if a.estatus_recontratacion == "Rehire_Eligible" else "red"
            rows.append({
                "DNI": a.numero_documento,
                "Nombres Completos": a.nombres_completos,
                "Email Corporativo": a.email_corporativo_historico or "N/A",
                "Última Cuenta": a.ultima_cuenta_proyecto or "N/A",
                "Ingreso": str(a.fecha_ingreso or ""),
                "Cese": str(a.fecha_cese),
                "Motivo Desvinculación": a.motivo_desvinculacion or "N/A",
                "Estatus Recontratación": a.estatus_recontratacion,
            })

        st.dataframe(rows, use_container_width=True)


def _render_registro_alumni() -> None:
    """Formulario para agregar un ex-colaborador al catalogo."""
    user = get_current_user() or {}
    user_id = user.get("user_id", "usr-demo")
    user_email = user.get("email", "demo@tcs.com")
    user_role = user.get("rol", "Senior_Technical_Recruiter")

    with st.form("form_nuevo_alumni"):
        c1, c2 = st.columns(2)
        with c1:
            dni = st.text_input("DNI del Ex-Colaborador (8 dígitos)", max_chars=8).strip()
            nombres = st.text_input("Nombres y Apellidos Completos").strip()
            email_hist = st.text_input("Email Corporativo Histórico (@tcs.com)").strip().lower()
            cuenta = st.text_input("Última Cuenta / Proyecto Asignado (Ej. BCP Home Banking)").strip()

        with c2:
            fecha_ing = st.date_input("Fecha de Ingreso", value=date(2021, 1, 1))
            fecha_ces = st.date_input("Fecha de Cese / Desvinculación", value=date(2024, 1, 1))
            motivo = st.selectbox(
                "Motivo de Desvinculación:",
                ["Renuncia Voluntaria - Mejor Oferta", "Fin de Proyecto / Contrato", "Mutuo Disenso", "Despido / Falta Grave", "Otro"],
            )
            estatus_labels = {
                "Rehire_Eligible": "Elegible para Recontratación (Rehire_Eligible)",
                "Do_Not_Rehire": "No Recontratable (Do_Not_Rehire)",
                "Requiere_Aprobacion_RRHH": "Requiere Aprobación RRHH (Requiere_Aprobacion_RRHH)",
            }
            estatus = st.selectbox(
                "Estatus de Recontratabilidad:",
                ["Rehire_Eligible", "Do_Not_Rehire", "Requiere_Aprobacion_RRHH"],
                format_func=lambda x: estatus_labels.get(x, x),
            )

        notas_comp = st.text_area("Notas u Observaciones de Compliance:")

        submit = st.form_submit_button("Guardar Registro Alumni", type="primary", use_container_width=True)

        if submit:
            if not enforce_write_permission("Registrar Alumni"):
                return

            if not dni or len(dni) != 8 or not nombres:
                st.error("DNI de 8 dígitos y Nombres Completos son obligatorios.")
                return

            try:
                with SessionLocal() as db:
                    alm_repo = AlumniRepository(db)
                    audit_repo = AuditRepository(db)
                    audit_svc = AuditService(audit_repo)

                    alm_id = f"alm-{uuid.uuid4()}"
                    alm_repo.create(
                        alumni_id=alm_id,
                        tipo_documento="DNI",
                        numero_documento=dni,
                        nombres_completos=nombres,
                        nombres_normalizado=normalize_full_name(nombres),
                        email_corporativo_historico=email_hist or None,
                        fecha_ingreso=fecha_ing,
                        fecha_cese=fecha_ces,
                        ultima_cuenta_proyecto=cuenta or None,
                        motivo_desvinculacion=motivo,
                        estatus_recontratacion=estatus,
                    )

                    audit_svc.record_mutation(
                        usuario_id=user_id,
                        usuario_email=user_email,
                        rol_en_momento=user_role,
                        tipo_accion="Creacion",
                        entidad_objeto="HistorialAlumni",
                        registro_id=alm_id,
                        version_registro=1,
                        valores_nuevos={"dni": dni, "nombres": nombres, "estatus": estatus},
                        justificacion="Registro manual en catalogo alumni TCS",
                    )
                    db.commit()

                    st.success(f"✅ Ex-colaborador {nombres} registrado exitosamente en el catálogo Alumni.")
            except Exception as e:
                st.error(f"Error al registrar alumni: {e}")
