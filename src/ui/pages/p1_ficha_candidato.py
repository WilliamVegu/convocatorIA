"""Ficha Única de Candidato page for ATS TCS Perú (Consolidating 28 attributes)."""
from __future__ import annotations

import datetime
from datetime import date
from typing import Optional, Dict, Any
import streamlit as st

from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.identity.apisperu_adapter import APIsPeruDNIAdapter
from src.adapters.cv_parser.heuristic_extractor import HeuristicCVExtractor
from src.services.candidate_service import CandidateService
from src.services.audit_service import AuditService
from src.services.alumni_service import AlumniService
from src.domain.value_objects import TelefonoE164, DocumentoIdentidad
from src.ui.session import get_current_user, enforce_write_permission
from src.ui.theme import render_badge


def render_ficha_candidato_page() -> None:
    """Render Ficha Única de Candidato interface with two tabs."""
    st.markdown("## 📋 Ficha Única de Candidato")
    st.caption("Consolidación integral de 28 atributos operativos, autollenado por DNI, normalización E.164 y detección Boomerang.")

    tab_nuevo, tab_cartera = st.tabs(["➕ Nuevo Registro / Ficha", "🔍 Cartera de Candidatos Registrados"])

    with tab_nuevo:
        _render_formulario_registro()

    with tab_cartera:
        _render_cartera_candidatos()


def _render_formulario_registro() -> None:
    """Formulario reactivo de registro de candidato."""
    user = get_current_user() or {}
    user_id = user.get("user_id", "usr-demo")
    user_email = user.get("email", "demo@tcs.com")
    user_role = user.get("rol", "Senior_Technical_Recruiter")
    user_name = user.get("nombres_completos", "Reclutador TCS")

    # Session storage for intermediate lookup results
    if "dni_lookup_data" not in st.session_state:
        st.session_state["dni_lookup_data"] = {}
    if "cv_parsed_data" not in st.session_state:
        st.session_state["cv_parsed_data"] = {}

    st.markdown("#### 1. Identidad Nacional y Consulta Ciudadana (DNI / APIsPERU)")
    col_dni, col_btn = st.columns([3, 1])

    with col_dni:
        dni_input = st.text_input("Número de DNI (8 dígitos)", max_chars=8, placeholder="Ej. 76128709", key="dni_input_field").strip()

    with col_btn:
        st.write("")
        st.write("")
        if st.button("🔎 Validar DNI", use_container_width=True):
            if not dni_input or len(dni_input) != 8 or not dni_input.isdigit():
                st.error("El DNI debe tener exactamente 8 dígitos numéricos.")
            else:
                try:
                    with SessionLocal() as db:
                        cand_repo = CandidatoRepository(db)
                        dni_adapter = APIsPeruDNIAdapter(cand_repo)
                        res = dni_adapter.resolve_dni(dni_input)
                        st.session_state["dni_lookup_data"] = res
                        st.success(f"DNI {dni_input} validado exitosamente ({res.get('fuente_resolucion', 'Local')})")
                except Exception as e:
                    st.error(f"Error consultando DNI: {e}")

    dni_data = st.session_state.get("dni_lookup_data", {})

    # Automatic Boomerang check for this DNI
    if dni_input and len(dni_input) == 8:
        with SessionLocal() as db:
            alm_repo = AlumniRepository(db)
            alm_svc = AlumniService(alm_repo)
            boomerang = alm_svc.detect_boomerang(dni=dni_input)
            if boomerang.get("es_boomerang"):
                badge_type = "green" if boomerang.get("elegible_recontratacion") else "red"
                st.markdown(
                    f"""
                    <div style="background-color: #F3E8FF; border-left: 5px solid #9B59B6; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                        <span style="font-weight: 700; color: #7E22CE;">🟣 CANDIDATO BOOMERANG DETECTADO:</span> Ex-colaborador TCS Perú<br/>
                        <b>Cuenta / Proyecto anterior:</b> {boomerang.get('ultima_cuenta_proyecto', 'N/A')} ({boomerang.get('fecha_ingreso', '')} al {boomerang.get('fecha_cese', '')})<br/>
                        <b>Estatus Recontratación:</b> {render_badge(boomerang.get('estatus_recontratacion', ''), badge_type)} | <i>{boomerang.get('motivo_desvinculacion', '')}</i><br/>
                        <small style="color: #6B21A8;">⚠️ Alerta de Ahorro: Este candidato es patrimonio TCS. No procede pago de comisión externa de agencia.</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Personal data fields
    c1, c2, c3 = st.columns(3)
    with c1:
        nombres = st.text_input("Nombres", value=dni_data.get("nombres", "")).strip()
    with c2:
        ape_paterno = st.text_input("Apellido Paterno", value=dni_data.get("apellido_paterno", "")).strip()
    with c3:
        ape_materno = st.text_input("Apellido Materno", value=dni_data.get("apellido_materno", "")).strip()

    c4, c5, c6 = st.columns(3)
    with c4:
        # Dynamic Birth Date & Age
        raw_bdate = dni_data.get("fecha_nacimiento")
        default_bdate = date(1995, 1, 1)
        if isinstance(raw_bdate, str) and len(raw_bdate) == 10:
            try:
                default_bdate = datetime.date.fromisoformat(raw_bdate)
            except Exception:
                pass
        elif isinstance(raw_bdate, date):
            default_bdate = raw_bdate

        fecha_nac = st.date_input("Fecha de Nacimiento", value=default_bdate, min_value=date(1940, 1, 1), max_value=date.today())

        # Dynamic age calculation (zero 127 years bug!)
        today = date.today()
        edad_calculada = today.year - fecha_nac.year - ((today.month, today.day) < (fecha_nac.month, fecha_nac.day))
        st.caption(f"🎂 **Edad calculada en runtime:** {edad_calculada} años")

    with c5:
        distrito = st.text_input("Distrito de Residencia (Lima)", value=dni_data.get("distrito", "Santiago de Surco")).strip()
    with c6:
        ubigeo = st.text_input("Ubigeo", value=dni_data.get("ubigeo", "150140")).strip()

    st.markdown("#### 2. Contacto & Canal Directo WhatsApp Web")
    col_tel, col_email = st.columns(2)
    with col_tel:
        telefono_raw = st.text_input("Teléfono Móvil (9 dígitos)", placeholder="Ej. 989322088").strip()
        e164_val = ""
        wa_url = ""
        if telefono_raw:
            try:
                e164_obj = TelefonoE164(telefono_raw)
                e164_val = str(e164_obj)
                st.caption(f"✅ Formato E.164 canónico: `{e164_val}`")
                candidato_display = nombres or "estimado/a"
                msg_proto = (
                    f"Hola {candidato_display}, te saluda {user_name} del equipo de Selección de TCS Perú. "
                    "Te contacto para coordinar una breve conversación sobre oportunidades profesionales."
                )
                wa_url = e164_obj.to_whatsapp_url(mensaje_personalizado=msg_proto)
            except Exception as e:
                st.caption(f"⚠️ Teléfono pendiente de validación: {e}")

        if wa_url:
            st.markdown(
                f'<a href="{wa_url}" target="_blank" style="text-decoration: none;">'
                f'<button style="background-color: #25D366; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: 600; cursor: pointer;">'
                f'💬 Iniciar WhatsApp Web</button></a>',
                unsafe_allow_html=True,
            )

    with col_email:
        email = st.text_input("Correo Electrónico Personal", placeholder="ejemplo@gmail.com").strip().lower()

    st.markdown("#### 3. Carga y Análisis Asistido de Currículum Vitae (CV)")
    uploaded_cv = st.file_uploader("Adjuntar CV en formato PDF", type=["pdf"])
    if uploaded_cv is not None:
        if st.button("📄 Extraer Datos con IA / Heurística"):
            try:
                extractor = HeuristicCVExtractor()
                content = uploaded_cv.getvalue()
                parsed = extractor.extract_from_pdf(content)
                st.session_state["cv_parsed_data"] = parsed
                st.success("✅ CV analizado exitosamente mediante motor heurístico local.")
            except Exception as e:
                st.error(f"Error procesando CV: {e}")

    cv_info = st.session_state.get("cv_parsed_data", {})
    if cv_info:
        st.info(f"**Habilidades detectadas:** {', '.join(cv_info.get('habilidades_tecnicas', [])) or 'No detectadas'}")
        st.info(f"**Años de experiencia estimados:** {cv_info.get('anios_experiencia_estimados', 'N/A')}")
        st.info(f"**Idiomas detectados:** {cv_info.get('idiomas', {})}")

    st.markdown("#### 4. Postulación Inicial y Perfil Vacante")
    cp1, cp2, cp3 = st.columns(3)
    with cp1:
        cliente = st.selectbox(
            "Cuenta / Cliente Asignado",
            ["BCP", "BBVA", "Interbank", "Entel", "Falabella", "Rimac", "TCS Internal", "Otro"],
        )
    with cp2:
        perfil = st.selectbox(
            "Perfil Solicitado",
            ["Desarrollador Java Senior", "Data Engineer", "DevOps Specialist", "Full Stack Developer", "Cloud Architect", "Scrum Master", "QA Automation"],
        )
    with cp3:
        modalidad = st.selectbox("Modalidad Requerida", ["Híbrido", "Remoto", "Presencial"])

    cp4, cp5 = st.columns(2)
    with cp4:
        salario_pretendido = st.number_input("Expectativa Salarial Bruta (S/.)", min_value=0.0, value=6500.0, step=100.0)
    with cp5:
        fuente = st.selectbox("Fuente de Reclutamiento", ["LinkedIn Recruiter", "Referido Interno", "Bumeran", "Adecco", "Web Corporativa TCS"])

    st.markdown("---")
    if st.button("💾 Guardar Ficha y Postulación", type="primary", use_container_width=True):
        if not enforce_write_permission("Guardar Candidato"):
            return

        if not dni_input or not nombres or not ape_paterno or not telefono_raw or not email:
            st.error("Por favor complete los campos obligatorios: DNI, Nombres, Apellido Paterno, Teléfono y Correo.")
            return

        try:
            with SessionLocal() as db:
                cand_repo = CandidatoRepository(db)
                post_repo = PostulacionRepository(db)
                alumni_repo = AlumniRepository(db)
                audit_repo = AuditRepository(db)
                audit_svc = AuditService(audit_repo)
                dni_adapter = APIsPeruDNIAdapter(cand_repo)
                cand_svc = CandidateService(cand_repo, dni_adapter, audit_svc, alumni_repo)

                # Create candidate
                cand = cand_svc.create_candidate(
                    actor_user_id=user_id,
                    actor_email=user_email,
                    actor_role=user_role,
                    tipo_documento="DNI",
                    numero_documento=dni_input,
                    nombres=nombres,
                    apellido_paterno=ape_paterno,
                    apellido_materno=ape_materno,
                    telefono_raw=telefono_raw,
                    email=email,
                    fecha_nacimiento=fecha_nac,
                    ubigeo=ubigeo,
                    distrito_residencia=distrito,
                    cv_resumen_tecnico=cv_info.get("resumen_ejecutivo", ""),
                    cv_anios_experiencia=cv_info.get("anios_experiencia_estimados"),
                    cv_idiomas_json=cv_info.get("idiomas"),
                )

                # Map fuente to DB constraint
                fuentes_map = {
                    "LinkedIn Recruiter": "LinkedIn_Oficial",
                    "Referido Interno": "BYB_Referido",
                    "Bumeran": "Bolsa_Web",
                    "Adecco": "Adecco",
                    "Web Corporativa TCS": "Bolsa_Web",
                }
                fuente_db = fuentes_map.get(fuente, "LinkedIn_Oficial")

                # Create associated postulacion
                post_id = f"post-{cand.id[5:]}"
                post_repo.create_postulacion(
                    postulacion_id=post_id,
                    candidato_id=cand.id,
                    cliente_cuenta=cliente,
                    rgs_vacante_id=f"RGS-2026-{cliente[:3].upper()}-01",
                    perfil_tecnico=perfil,
                    reclutador_asignado_id=user_id,
                    fuente_origen=fuente_db,
                    trimestre_fiscal="FY27-Q1",
                    created_by_user_id=user_id,
                    estado_embudo="Nuevo",
                    observaciones=f"Modalidad: {modalidad}. Pretensión: S/. {salario_pretendido}",
                )

                db.commit()
                st.success(f"🎉 Candidato {nombres} {ape_paterno} y postulación registrados exitosamente con ID `{cand.id}`.")
                st.session_state["dni_lookup_data"] = {}
                st.session_state["cv_parsed_data"] = {}
        except Exception as e:
            st.error(f"Error al guardar candidato: {e}")


def _render_cartera_candidatos() -> None:
    """Explorador y búsqueda de cartera de candidatos con auditoría."""
    st.markdown("#### Búsqueda de Candidatos en Cartera")
    q_search = st.text_input("Filtrar por DNI, Nombres o Correo", key="cand_search_filter").strip()

    with SessionLocal() as db:
        cand_repo = CandidatoRepository(db)
        post_repo = PostulacionRepository(db)
        audit_repo = AuditRepository(db)

        if q_search:
            candidatos = cand_repo.search_by_name(q_search)
        else:
            candidatos = cand_repo.list_all(limit=50)

        if not candidatos:
            st.info("No se encontraron candidatos con los criterios especificados.")
            return

        # Build table records
        table_rows = []
        for c in candidatos:
            posts = post_repo.get_by_candidato(c.id)
            ultimo_cliente = posts[0].cliente_cuenta if posts else "Sin postulación"
            ultimo_estado = posts[0].estado_embudo if posts else "N/A"
            table_rows.append({
                "ID": c.id,
                "DNI": c.numero_documento,
                "Candidato": c.nombres_completos,
                "Edad": f"{c.calcular_edad or 'N/A'} años",
                "Teléfono E.164": c.telefono_e164,
                "Distrito": c.distrito_residencia or "N/A",
                "Alumni TCS": "🟣 Sí" if c.is_tcs_alumni else "No",
                "Cliente": ultimo_cliente,
                "Estado Embudo": ultimo_estado,
            })

        st.dataframe(table_rows, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📜 Línea de Tiempo & Trazabilidad de Auditoría")
        cand_ids = [c.id for c in candidatos]
        selected_cid = st.selectbox("Seleccione un Candidato para inspeccionar su historial inmutable:", cand_ids)

        if selected_cid:
            audit_events = audit_repo.list_by_entity("Candidato", selected_cid)
            if not audit_events:
                st.caption("Sin eventos de auditoría registrados para este candidato.")
            else:
                for ev in audit_events:
                    st.markdown(
                        f"**{ev.timestamp.strftime('%Y-%m-%d %H:%M:%S')}** — "
                        f"Acción: `{ev.tipo_accion}` por `{ev.usuario_email}` ({ev.rol_en_momento}) | "
                        f"Detalle: *{ev.justificacion_operativa}*"
                    )
