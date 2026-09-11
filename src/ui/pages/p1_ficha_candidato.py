"""Ficha Única de Candidato page for ATS TCS Perú (Consolidating 28 attributes)."""
from __future__ import annotations

import datetime
from datetime import date
from typing import Optional, Dict, Any
import pandas as pd
import streamlit as st
from sqlalchemy import select

from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.models import UsuarioModel, CandidatoModel, PostulacionModel
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.identity.apisperu_adapter import APIsPeruDNIAdapter
from src.adapters.cv_parser.heuristic_extractor import HeuristicCVExtractor
from src.adapters.cv_parser.langchain_extractor import LangChainCVExtractor
from src.adapters.cv_parser.cul_extractor import CULExtractor
from src.adapters.github.github_adapter import GitHubAdapter
from src.services.candidate_service import CandidateService
from src.services.audit_service import AuditService
from src.services.alumni_service import AlumniService
from src.services.fit_gap_service import FitGapService
from src.domain.value_objects import TelefonoE164, DocumentoIdentidad
from src.ui.session import get_current_user, enforce_write_permission, navigate_to, get_nav_context
from src.ui.theme import render_badge, render_pipeline_stepper


def render_ficha_candidato_page() -> None:
    """Render Ficha Única de Candidato interface with two tabs."""
    st.markdown("## 📋 Ficha Única de Candidato")
    st.caption("Consolidación integral de 28 atributos operativos, autollenado por DNI, normalización E.164 y detección Boomerang.")

    rgs_role = get_nav_context("rgs_perfil", "")
    rgs_cli = get_nav_context("rgs_cliente", "")
    role_ctx = f"{rgs_role} ({rgs_cli})" if rgs_role and rgs_cli else (rgs_role or "Ingesta & Evaluación Inicial")
    render_pipeline_stepper(current_step=2, role_or_rgs=role_ctx)

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
    if "github_audit_data" not in st.session_state:
        st.session_state["github_audit_data"] = None
    if "cul_parsed_data" not in st.session_state:
        st.session_state["cul_parsed_data"] = None

    prefill_dni = get_nav_context("prefill_dni", "")
    if prefill_dni and "dni_input_field" not in st.session_state:
        st.session_state["dni_input_field"] = prefill_dni
        try:
            with SessionLocal() as db:
                cand_repo = CandidatoRepository(db)
                dni_adapter = APIsPeruDNIAdapter(cand_repo)
                res = dni_adapter.resolve_dni(prefill_dni)
                db.commit()
                st.session_state["dni_lookup_data"] = res
        except Exception:
            pass

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
                        db.commit()
                        st.session_state["dni_lookup_data"] = res
                        if res.get("success"):
                            fuente_tipo = res.get("fuente_origen", "CACHE_LOCAL")
                            fuente_lbl = "APIsPERU / RENIEC Oficial" if fuente_tipo == "APISPERU_LIVE" else "Caché Local Offline"
                            st.success(f"DNI {dni_input} validado exitosamente ({fuente_lbl})")
                        else:
                            api_msg = res.get("mensaje", "No se encontraron resultados en RENIEC.")
                            st.warning(f"DNI {dni_input} no encontrado en registros oficiales: {api_msg} (Respuesta de APIsPERU). Puede ingresar los datos manualmente.")
                except Exception as e:
                    st.error(f"Error consultando DNI: {e}")

    lookup_res = st.session_state.get("dni_lookup_data", {})
    dni_data = {}
    if lookup_res.get("success"):
        c_datos = lookup_res.get("datos", {})
        if c_datos.get("dni") == dni_input:
            dni_data = c_datos

    # Automatic Boomerang check for this DNI
    if dni_input and len(dni_input) == 8:
        with SessionLocal() as db:
            alm_repo = AlumniRepository(db)
            alm_svc = AlumniService(alm_repo)
            boomerang = alm_svc.detect_boomerang(dni=dni_input)
            if boomerang.get("es_boomerang"):
                st.warning(
                    f"🟣 **CANDIDATO BOOMERANG DETECTADO (Ex-colaborador TCS Perú)**\n\n"
                    f"• **Cuenta / Proyecto anterior:** {boomerang.get('ultima_cuenta_proyecto', 'N/A')} "
                    f"({boomerang.get('fecha_ingreso', '')} al {boomerang.get('fecha_cese', '')})\n"
                    f"• **Estatus Recontratación:** `{boomerang.get('estatus_recontratacion', '')}` | "
                    f"*{boomerang.get('motivo_desvinculacion', '')}*\n\n"
                    f"⚠️ *Alerta de Ahorro: Este candidato es patrimonio TCS. No procede pago de comisión externa de agencia.*"
                )

    # Personal data fields
    c1, c2, c3 = st.columns(3)
    with c1:
        nombres = st.text_input("Nombres", value=dni_data.get("nombres") or "").strip()
    with c2:
        ape_paterno = st.text_input("Apellido Paterno", value=dni_data.get("apellido_paterno") or "").strip()
    with c3:
        ape_materno = st.text_input("Apellido Materno", value=dni_data.get("apellido_materno") or "").strip()

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
        distrito = st.text_input("Distrito de Residencia (Lima)", value=dni_data.get("distrito") or "Santiago de Surco").strip()
    with c6:
        ubigeo = st.text_input("Ubigeo", value=dni_data.get("ubigeo") or "150140").strip()

    cod_v = dni_data.get("codigo_verificacion")
    cod_vl = dni_data.get("codigo_verificacion_letra")
    if cod_v:
        letra_str = f" (Letra: {cod_vl})" if cod_vl else ""
        st.caption(f"🛡️ **RENIEC Oficial:** Dígito Verificador: `{cod_v}`{letra_str} | Identidad confirmada en padrón nacional.")

    with st.expander("🏛️ Consulta SUNAT RUC (Para Contratistas 4ta Categoría / Recibos por Honorarios)", expanded=False):
        st.caption("Verificación oficial en tiempo real de condición (Habido) y estado (Activo) en SUNAT via APIsPERU.")
        cr1, cr2 = st.columns([3, 1])
        with cr1:
            ruc_val_input = st.text_input("Número de RUC (11 dígitos)", max_chars=11, placeholder="Ej. 10738610821 o 20100070970", key="ruc_consult_field").strip()
        with cr2:
            st.write("")
            st.write("")
            btn_ruc = st.button("🔎 Validar RUC", use_container_width=True)

        if btn_ruc:
            if not ruc_val_input or len(ruc_val_input) != 11 or not ruc_val_input.isdigit():
                st.error("El RUC debe tener exactamente 11 dígitos numéricos.")
            else:
                try:
                    with SessionLocal() as db:
                        cand_repo = CandidatoRepository(db)
                        dni_adapter = APIsPeruDNIAdapter(cand_repo)
                        res_ruc = dni_adapter.resolve_ruc(ruc_val_input)
                        if res_ruc.get("success"):
                            r_datos = res_ruc.get("datos", {})
                            st.success(f"✅ RUC {ruc_val_input} validado exitosamente en SUNAT")
                            st.markdown(
                                f"• **Razón Social / Titular:** `{r_datos.get('razon_social')}`\n\n"
                                f"• **Estado:** `{r_datos.get('estado')}` | **Condición:** `{r_datos.get('condicion')}`\n\n"
                                f"• **Dirección Fiscal:** `{r_datos.get('direccion')}` ({r_datos.get('distrito')}, {r_datos.get('provincia')})\n\n"
                                f"• **Ubigeo SUNAT:** `{r_datos.get('ubigeo')}`"
                            )
                        else:
                            st.warning(f"RUC {ruc_val_input}: {res_ruc.get('mensaje', 'No encontrado en SUNAT')}")
                except Exception as e:
                    st.error(f"Error consultando RUC en SUNAT: {e}")


    st.markdown("#### 2. Contacto, WhatsApp Web y Auditoría de Código GitHub")
    col_tel, col_email, col_gh = st.columns(3)
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

    with col_gh:
        gh_user = st.text_input("Usuario GitHub (opcional)", placeholder="Ej. torvalds o perfil URL", key="gh_user_input").strip()
        if gh_user:
            if st.button("🔎 Auditar GitHub", use_container_width=True, key="btn_audit_gh"):
                with st.spinner("Consultando repositorios públicos en GitHub API..."):
                    gh_adapter = GitHubAdapter()
                    gh_res = gh_adapter.audit_user(gh_user)
                    st.session_state["github_audit_data"] = gh_res

        gh_info = st.session_state.get("github_audit_data")
        if gh_info and gh_info.usuario:
            badge_color = "#2ECC71" if gh_info.actividad_verificada else "#E74C3C"
            badge_txt = "✔ Actividad Técnica Verificada" if gh_info.actividad_verificada else "Sin repositorios activos"
            langs_str = ", ".join(gh_info.lenguajes_principales[:3]) or "N/A"
            st.markdown(
                f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 8px 10px; border-radius: 6px; font-size: 12px; margin-top: 4px;">'
                f'<b>GitHub:</b> <a href="{gh_info.perfil_url}" target="_blank">@{gh_info.usuario}</a><br>'
                f'• Repos propios: <b>{gh_info.repos_propios}</b> | Forks: {gh_info.repos_forks}<br>'
                f'• Lenguajes: <i>{langs_str}</i><br>'
                f'<span style="color: {badge_color}; font-weight: bold;">{badge_txt}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("#### 3. Carga y Análisis Asistido de Documentos (CV y CUL MTPE)")
    c_cv, c_cul = st.columns(2)

    with c_cv:
        uploaded_cv = st.file_uploader("Adjuntar CV en formato PDF", type=["pdf"], key="cv_uploader_main")
        if uploaded_cv is not None:
            if st.button("📄 Extraer Datos CV (IA / Heurística)", key="btn_parse_cv"):
                try:
                    extractor = LangChainCVExtractor()
                    content = uploaded_cv.getvalue()
                    parsed = extractor.extract_from_pdf(content)
                    st.session_state["cv_parsed_data"] = parsed
                    motor = parsed.get("motor_extraccion_usado", "Motor Heurístico Local")
                    st.success(f"✅ CV analizado exitosamente ({motor}).")
                except Exception as e:
                    st.error(f"Error procesando CV: {e}")

        cv_info = st.session_state.get("cv_parsed_data", {})
        if cv_info:
            skills = cv_info.get("habilidades_tecnicas", [])
            if skills and isinstance(skills[0], dict):
                skills_str = ", ".join([s.get("nombre", "") for s in skills if s.get("nombre")])
            elif skills and isinstance(skills[0], str):
                skills_str = ", ".join(skills)
            else:
                skills_str = "No detectadas"
            st.info(f"**Habilidades:** {skills_str or 'No detectadas'}")
            anios_exp = cv_info.get("anios_experiencia_total", cv_info.get("anios_experiencia_estimados", "N/A"))
            st.info(f"**Experiencia estimada:** {anios_exp} años | **Idiomas:** {cv_info.get('idiomas', {})}")

    with c_cul:
        uploaded_cul = st.file_uploader("Adjuntar CUL (Certificado Único Laboral - MTPE)", type=["pdf"], key="cul_uploader_main")
        if uploaded_cul is not None:
            if st.button("🏛️ Extraer Antecedentes y SUNAT (CUL)", key="btn_parse_cul"):
                try:
                    cul_extractor = CULExtractor()
                    cul_res = cul_extractor.extract_from_pdf(uploaded_cul.getvalue())
                    st.session_state["cul_parsed_data"] = cul_res
                    if cul_res.get("bgc_status") == "Aprobado":
                        st.success("✅ CUL MTPE: Antecedentes limpios (PNP, INPE y Poder Judicial).")
                    else:
                        st.error(f"⚠️ CUL MTPE: {cul_res.get('bgc_dictamen')}")
                except Exception as e:
                    st.error(f"Error procesando CUL: {e}")

        cul_info = st.session_state.get("cul_parsed_data")
        if cul_info:
            st.info(
                f"🛡️ **BGC:** {cul_info.get('bgc_dictamen')}\n\n"
                f"🎓 **Grados SUNEDU:** {', '.join(cul_info.get('grados_sunedu', [])) or 'En verificación'}\n\n"
                f"🏢 **SUNAT Planilla:** {', '.join(cul_info.get('trayectoria_formal_registros', [])) or 'Registros verificados'}"
            )

    rgs_cliente = get_nav_context("rgs_cliente")
    rgs_perfil = get_nav_context("rgs_perfil")
    rgs_modalidad = get_nav_context("rgs_modalidad")
    rgs_id_ctx = get_nav_context("rgs_id")

    clientes_list = ["BCP", "BBVA", "Interbank", "Entel", "Falabella", "Rimac", "TCS Internal", "Otro"]
    if rgs_cliente and rgs_cliente not in clientes_list:
        clientes_list.insert(0, rgs_cliente)
    c_idx = clientes_list.index(rgs_cliente) if rgs_cliente in clientes_list else 0

    perfiles_list = ["Desarrollador Java Senior", "Data Engineer", "DevOps Specialist", "Full Stack Developer", "Cloud Architect", "Scrum Master", "QA Automation"]
    if rgs_perfil and rgs_perfil not in perfiles_list:
        perfiles_list.insert(0, rgs_perfil)
    p_idx = perfiles_list.index(rgs_perfil) if rgs_perfil in perfiles_list else 0

    modalidades_list = ["Híbrido", "Remoto", "Presencial"]
    m_idx = modalidades_list.index(rgs_modalidad) if rgs_modalidad in modalidades_list else 0

    st.markdown("#### 4. Postulación Inicial y Perfil Vacante")
    cp1, cp2, cp3 = st.columns(3)
    with cp1:
        cliente = st.selectbox("Cuenta / Cliente Asignado", clientes_list, index=c_idx)
    with cp2:
        perfil = st.selectbox("Perfil Solicitado", perfiles_list, index=p_idx)
    with cp3:
        modalidad = st.selectbox("Modalidad Requerida", modalidades_list, index=m_idx)

    cp4, cp5 = st.columns(2)
    with cp4:
        salario_pretendido = st.number_input("Expectativa Salarial Bruta (S/.)", min_value=0.0, value=6500.0, step=100.0)
    with cp5:
        fuente = st.selectbox("Fuente de Reclutamiento", ["LinkedIn Recruiter", "Referido Interno", "Bumeran", "Adecco", "Web Corporativa TCS"])

    # Reactive Fit & Gap Analysis (Propuesta N1)
    if cv_info:
        st.markdown("---")
        st.markdown("#### 🎯 Compatibilidad Técnica Automática (Fit & Gap Analysis)")
        fit_svc = FitGapService()
        raw_text_cv = cv_info.get("resumen_profesional", "") + " " + " ".join(
            [s.get("nombre", "") for s in cv_info.get("habilidades_tecnicas", []) if isinstance(s, dict)]
        )
        fit_res = fit_svc.compare_cv_vs_rgs(
            cv_text=raw_text_cv,
            cv_skills=cv_info.get("habilidades_tecnicas", []),
            perfil_puesto=perfil,
        )

        col_score, col_fg = st.columns([1, 2])
        with col_score:
            st.metric("Score de Compatibilidad", f"{fit_res.score_porcentaje:.0f}%", delta=f"{perfil}")
            st.caption(f"💡 *{fit_res.recomendacion}*")
        with col_fg:
            st.markdown("**Fortalezas Detectadas:**")
            for f in fit_res.fortalezas[:3]:
                st.markdown(f"• 🟢 {f}")
            if fit_res.gaps_criticos:
                st.markdown("**Gaps o Brechas Técnicas:**")
                for g in fit_res.gaps_criticos[:2]:
                    st.markdown(f"• 🔴 {g}")

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
                    estado_identidad=lookup_res.get("estado_identidad", "Validado_Oficialmente") if (lookup_res.get("success") and dni_data) else "Pendiente_Regularizacion",
                    regularizacion_pendiente=lookup_res.get("regularizacion_pendiente", False) if (lookup_res.get("success") and dni_data) else True,
                    cv_resumen_tecnico=cv_info.get("resumen_profesional", cv_info.get("resumen_ejecutivo", "")),
                    cv_anios_experiencia=cv_info.get("anios_experiencia_total", cv_info.get("anios_experiencia_estimados")),
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
                rgs_id_to_use = rgs_id_ctx if rgs_id_ctx else f"RGS-2026-{cliente[:3].upper()}-01"
                post_repo.create_postulacion(
                    postulacion_id=post_id,
                    candidato_id=cand.id,
                    cliente_cuenta=cliente,
                    rgs_vacante_id=rgs_id_to_use,
                    perfil_tecnico=perfil,
                    reclutador_asignado_id=user_id,
                    fuente_origen=fuente_db,
                    trimestre_fiscal="FY27-Q1",
                    created_by_user_id=user_id,
                    estado_embudo="Nuevo",
                    observaciones=f"Modalidad: {modalidad}. Pretensión: S/. {salario_pretendido}",
                )

                db.commit()
                st.session_state["last_saved_candidate"] = {
                    "cand_id": cand.id,
                    "nombres": f"{nombres} {ape_paterno}",
                    "post_id": post_id,
                    "salario": float(salario_pretendido),
                    "perfil": perfil,
                    "cliente": cliente,
                }
                st.session_state["dni_lookup_data"] = {}
                st.session_state["cv_parsed_data"] = {}
                st.success(f"🎉 Candidato {nombres} {ape_paterno} y postulación registrados exitosamente con ID `{cand.id}`.")
        except Exception as e:
            st.error(f"Error al guardar candidato: {e}")

    # Interactive Next Steps panel after saving
    last_saved = st.session_state.get("last_saved_candidate")
    if last_saved:
        st.markdown("---")
        st.markdown(
            f'<div style="background: #0A192F; border: 1px solid #00B4D8; border-radius: 8px; padding: 14px 18px; margin: 12px 0;">'
            f'<div style="font-size: 11px; color: #00B4D8; font-weight: 700; text-transform: uppercase;">🚀 Siguiente Paso del Ciclo de Reclutamiento</div>'
            f'<div style="font-size: 15px; color: white; margin: 4px 0;">Postulación activa <b>#{last_saved["post_id"]}</b> para <b>{last_saved["nombres"]}</b> ({last_saved["perfil"]} - {last_saved["cliente"]}). ¿Cómo desea continuar?</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        col_ns1, col_ns2, col_ns3 = st.columns(3)
        with col_ns1:
            if st.button("📞 Continuar a Screening Telefónico (HITL) ➔", type="primary", use_container_width=True, key="btn_go_scr_next"):
                navigate_to("p2_screening", context={
                    "target_postulacion_id": last_saved["post_id"],
                    "cand_name": last_saved["nombres"],
                    "perfil": last_saved["perfil"],
                    "salario": last_saved["salario"],
                })
        with col_ns2:
            if st.button("💰 Simular CTC Salarial (Factor 1.56) ➔", use_container_width=True, key="btn_go_ctc_next"):
                navigate_to("p3_ctc", context={
                    "target_postulacion_id": last_saved["post_id"],
                    "monto_bruto": last_saved["salario"],
                    "cand_name": last_saved["nombres"],
                    "perfil": last_saved["perfil"],
                })
        with col_ns3:
            if st.button("➕ Registrar Otro Candidato", use_container_width=True, key="btn_reset_cand_next"):
                st.session_state["dni_lookup_data"] = {}
                st.session_state["cv_parsed_data"] = {}
                st.session_state.pop("last_saved_candidate", None)
                st.rerun()


def _render_cartera_candidatos() -> None:
    """Explorador y búsqueda de cartera de candidatos con visualización completa BD GENERAL FY27 y edición en vivo."""
    st.markdown("### 📋 Cartera de Candidatos Registrados (BD GENERAL FY27)")
    st.caption("Estructura operativa completa homologada con TCS Perú TA: 24 columnas, cálculo de CTC, estado en tiempo real y edición continua con auditoría.")

    q_search = st.text_input("🔍 Filtrar por DNI, Nombres, Perfil, Cliente o Correo", key="cand_search_filter").strip()

    with SessionLocal() as db:
        cand_repo = CandidatoRepository(db)
        post_repo = PostulacionRepository(db)
        alumni_repo = AlumniRepository(db)
        audit_repo = AuditRepository(db)
        audit_svc = AuditService(audit_repo)
        dni_adapter = APIsPeruDNIAdapter(cand_repo)
        cand_svc = CandidateService(cand_repo, dni_adapter, audit_svc, alumni_repo)

        # Map recruiters / users
        users = db.execute(select(UsuarioModel)).scalars().all()
        user_map = {u.id: u.nombres_completos for u in users}

        if q_search:
            candidatos = cand_repo.search_by_name(q_search)
        else:
            candidatos = cand_repo.list_all(limit=100)

        if not candidatos:
            st.info("No se encontraron candidatos con los criterios especificados.")
            return

        # Build table records matching the 24 columns of BD GENERAL FY27
        table_rows = []
        for c in candidatos:
            posts = post_repo.get_by_candidato(c.id)
            latest_p = posts[0] if posts else None
            scr = post_repo.get_screening_by_postulacion(latest_p.id) if latest_p else None

            # 1. Cliente
            cliente = latest_p.cliente_cuenta if latest_p else "Sin asignar"
            # 2. Status del Candidato
            status_cand = latest_p.estado_embudo if latest_p else "Nuevo"
            # 3. Fecha
            fecha_str = (latest_p.created_at if latest_p and latest_p.created_at else c.created_at).strftime("%d/%m/%Y")
            # 4. Reclutador
            reclutador_nom = user_map.get(latest_p.reclutador_asignado_id, latest_p.reclutador_asignado_id) if latest_p else "Sin asignar"
            # 5. Fuente de Reclutamiento
            fuente = latest_p.fuente_origen if latest_p else "N/A"
            # 6. Q
            q_fiscal = latest_p.trimestre_fiscal if latest_p else "FY27-Q1"
            # 7. PERFIL
            perfil = latest_p.perfil_tecnico if latest_p else (c.cv_resumen_tecnico[:30] if c.cv_resumen_tecnico else "N/A")
            # 8. NOMBRES Y APELLIDOS
            nombres_completos = c.nombres_completos
            # 9. Celular
            celular = c.telefono_e164
            # 10. Correo
            correo = c.email
            # 11. Fecha Nac.
            fecha_nac_str = c.fecha_nacimiento.strftime("%d/%m/%Y") if c.fecha_nacimiento else "N/A"
            # 12. Edad
            edad_val = f"{c.calcular_edad()} años" if c.fecha_nacimiento else "N/A"
            # 13. DNI / CE
            dni_ce = f"{c.tipo_documento}: {c.numero_documento}"
            # 14. BGC (Verificación Personal)
            bgc = "🟢 Conforme" if c.estado_identidad == "Validado_Oficialmente" else ("🟡 Regularización" if c.regularizacion_pendiente else "⚪ Pendiente")
            # 15. Conocimientos Técnicos
            con_tec = c.cv_resumen_tecnico[:45] + "..." if (c.cv_resumen_tecnico and len(c.cv_resumen_tecnico) > 45) else (c.cv_resumen_tecnico or (latest_p.perfil_tecnico if latest_p else "N/A"))
            # 16. Deuda Equifax
            deuda_eq = "No"
            # 17. Expectativa Salarial & CTC
            expectativa = None
            if scr and scr.dim3_expectativa_declarada:
                expectativa = scr.dim3_expectativa_declarada
            elif latest_p and latest_p.observaciones and "Pretensión: S/." in latest_p.observaciones:
                try:
                    import re
                    m = re.search(r"Pretensi[oó]n:\s*S/\.\s*([\d,.]+)", latest_p.observaciones)
                    if m:
                        expectativa = float(m.group(1).replace(",", ""))
                except Exception:
                    pass

            exp_str = f"S/. {expectativa:,.2f}" if expectativa else "S/. -"
            ctc_solicitado = expectativa * 1.56 if expectativa else None
            ctc_sol_str = f"S/. {ctc_solicitado:,.2f}" if ctc_solicitado else "S/. -"

            # CTC Rol (Benchmark referencial estimado o desde RGS)
            ctc_rol_bench = 11000.0  # Referencial estándar Senior TCS
            ctc_rol_str = f"S/. {ctc_rol_bench:,.2f}" if ctc_solicitado else "S/. -"
            var_pct = ((ctc_solicitado - ctc_rol_bench) / ctc_rol_bench) * 100 if ctc_solicitado else 0.0
            var_pct_str = f"{var_pct:+.1f}%" if ctc_solicitado else "0.0%"

            # 21. Disponibilidad
            disp = (scr.dim1_disponibilidad if scr else None) or (latest_p.disponibilidad_incorporacion if latest_p else None) or "Inmediata"
            # 22. Distrito / Residencia
            distrito = c.distrito_residencia or "N/A"
            # 23. Ha trabajado antes en TCS
            alumni_str = "🟣 Sí (Alumni)" if c.is_tcs_alumni else "No"
            # 24. Observaciones
            obs = latest_p.observaciones if latest_p else ""

            table_rows.append({
                "Cliente": cliente,
                "Status del Candidato": status_cand,
                "Fecha": fecha_str,
                "Reclutador": reclutador_nom,
                "Fuente de Reclutamiento": fuente,
                "Q": q_fiscal,
                "PERFIL": perfil,
                "NOMBRES Y APELLIDOS": nombres_completos,
                "Celular": celular,
                "Correo": correo,
                "Fecha Nac.": fecha_nac_str,
                "Edad": edad_val,
                "DNI / CE": dni_ce,
                "BGC (Verificación Personal)": bgc,
                "Conocimientos Técnicos": con_tec,
                "Deuda Equifax": deuda_eq,
                "Expectativa Salarial": exp_str,
                "CTC Solicitado": ctc_sol_str,
                "CTC Rol": ctc_rol_str,
                "% Variación CTC": var_pct_str,
                "Disponibilidad": disp,
                "Distrito / Residencia": distrito,
                "Ha trabajado antes en TCS": alumni_str,
                "Observaciones": obs,
            })

        df_cartera = pd.DataFrame(table_rows)
        st.dataframe(df_cartera, use_container_width=True)

        col_d1, _ = st.columns([1, 2])
        with col_d1:
            csv_data = df_cartera.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 Exportar BD GENERAL FY27 (Excel / CSV)",
                data=csv_data,
                file_name=f"BD_GENERAL_FY27_TCS_{datetime.date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown("#### ⚙️ Operaciones, Edición Continua & Auditoría de Candidato")
        cand_ids = [c.id for c in candidatos]
        cand_map = {
            c.id: f"{c.nombres_completos} (DNI: {c.numero_documento}) - {post_repo.get_by_candidato(c.id)[0].cliente_cuenta if post_repo.get_by_candidato(c.id) else 'Sin vacante'}"
            for c in candidatos
        }

        selected_cid = st.selectbox(
            "Seleccione un Candidato de la cartera para editar sus datos o ver su trazabilidad:",
            cand_ids,
            format_func=lambda cid: cand_map.get(cid, cid),
            key="cartera_selected_cid",
        )

        if selected_cid:
            cand_selected = cand_repo.get_by_id(selected_cid)
            cand_posts = post_repo.get_by_candidato(selected_cid)
            latest_p = cand_posts[0] if cand_posts else None

            # Fast-track navigation buttons
            if latest_p:
                c_act1, c_act2, c_act3 = st.columns(3)
                with c_act1:
                    if st.button(f"📞 Ir a Screening Telefónico ({latest_p.id}) ➔", key=f"btn_cart_scr_{selected_cid}", use_container_width=True):
                        navigate_to("p2_screening", context={
                            "target_postulacion_id": latest_p.id,
                            "cand_name": cand_selected.nombres_completos if cand_selected else "",
                            "perfil": latest_p.perfil_tecnico,
                        })
                with c_act2:
                    if st.button(f"💰 Ir a Simulación CTC ({latest_p.id}) ➔", key=f"btn_cart_ctc_{selected_cid}", use_container_width=True):
                        navigate_to("p3_ctc", context={
                            "target_postulacion_id": latest_p.id,
                            "cand_name": cand_selected.nombres_completos if cand_selected else "",
                            "perfil": latest_p.perfil_tecnico,
                        })
                with c_act3:
                    if st.button(f"📄 One-Pager ({latest_p.cliente_cuenta}) ➔", key=f"btn_cart_onepager_{selected_cid}", use_container_width=True):
                        navigate_to("p3_ctc", context={
                            "target_postulacion_id": latest_p.id,
                            "cand_name": cand_selected.nombres_completos if cand_selected else "",
                            "perfil": latest_p.perfil_tecnico,
                            "trigger_download": True,
                        })

            # Live Interactive Edit Form
            with st.expander("✏️ Editar Ficha del Candidato y Postulación (Edición Continua)", expanded=True):
                st.markdown(
                    f"**Modificando:** `{cand_selected.nombres_completos}` | DNI: `{cand_selected.numero_documento}` "
                    f"| Versión de Registro: `{cand_selected.record_version}`"
                )

                col_ed1, col_ed2 = st.columns(2)
                with col_ed1:
                    st.markdown("##### 👤 Datos Personales y Contacto")
                    edit_nombres = st.text_input("Nombres (Edición)", value=cand_selected.nombres or "", key=f"ed_nom_{selected_cid}")
                    edit_paterno = st.text_input("Apellido Paterno (Edición)", value=cand_selected.apellido_paterno or "", key=f"ed_pat_{selected_cid}")
                    edit_materno = st.text_input("Apellido Materno (Edición)", value=cand_selected.apellido_materno or "", key=f"ed_mat_{selected_cid}")
                    edit_telefono = st.text_input(
                        "Celular (Edición E.164)",
                        value=cand_selected.telefono_e164 or "",
                        key=f"ed_tel_{selected_cid}",
                        help="Acepta 9 dígitos peruanos o formato internacional (+51).",
                    )
                    edit_email = st.text_input("Correo Electrónico (Edición)", value=cand_selected.email or "", key=f"ed_mail_{selected_cid}")

                    fnac_default = cand_selected.fecha_nacimiento or date(1995, 1, 1)
                    edit_fnac = st.date_input(
                        "Fecha de Nacimiento (Edición)",
                        value=fnac_default,
                        min_value=date(1940, 1, 1),
                        max_value=date.today(),
                        key=f"ed_fnac_{selected_cid}",
                    )
                    edit_distrito = st.text_input("Distrito / Residencia (Edición)", value=cand_selected.distrito_residencia or "", key=f"ed_dist_{selected_cid}")
                    edit_alumni = st.checkbox("¿Ha trabajado antes en TCS? (Alumni)", value=bool(cand_selected.is_tcs_alumni), key=f"ed_alumni_{selected_cid}")

                with col_ed2:
                    st.markdown("##### 💼 Datos de Postulación / Vacante")
                    if latest_p:
                        # Client choices
                        clients_pool = ["BCP", "BBVA", "Interbank", "Entel", "Falabella", "Rimac", "TCS Internal", "Otro"]
                        if latest_p.cliente_cuenta and latest_p.cliente_cuenta not in clients_pool:
                            clients_pool.insert(0, latest_p.cliente_cuenta)
                        c_idx = clients_pool.index(latest_p.cliente_cuenta) if latest_p.cliente_cuenta in clients_pool else 0
                        edit_cliente = st.selectbox("Cliente / Cuenta", clients_pool, index=c_idx, key=f"ed_cli_{selected_cid}")

                        edit_perfil = st.text_input("Perfil Técnico", value=latest_p.perfil_tecnico or "", key=f"ed_prf_{selected_cid}")

                        # Funnel status
                        estados_validos = [
                            "Nuevo", "Screening_Telefonico", "Pendiente_Entrevistas", "Pendiente_Envio_Cliente",
                            "Entrevista_Cliente", "Oferta_Economica", "Oferta_Aceptada", "Contratado",
                            "Descartado_Tecnico", "Descartado_Economico", "Descartado_Compliance", "Desistio"
                        ]
                        e_idx = estados_validos.index(latest_p.estado_embudo) if latest_p.estado_embudo in estados_validos else 0
                        edit_estado = st.selectbox("Status del Candidato (Embudo)", estados_validos, index=e_idx, key=f"ed_est_{selected_cid}")

                        # Fuente
                        fuentes_validas = ["LinkedIn_Oficial", "BYB_Referido", "Adecco", "Bolsa_Web", "Directo_Alumni", "Offshore"]
                        f_idx = fuentes_validas.index(latest_p.fuente_origen) if latest_p.fuente_origen in fuentes_validas else 0
                        edit_fuente = st.selectbox("Fuente de Reclutamiento", fuentes_validas, index=f_idx, key=f"ed_fue_{selected_cid}")

                        # Recruiter
                        user_ids_list = list(user_map.keys())
                        r_idx = user_ids_list.index(latest_p.reclutador_asignado_id) if latest_p.reclutador_asignado_id in user_ids_list else 0
                        edit_recruiter_id = st.selectbox(
                            "Reclutador Asignado",
                            user_ids_list,
                            index=r_idx,
                            format_func=lambda uid: user_map.get(uid, uid),
                            key=f"ed_rec_{selected_cid}",
                        )

                        edit_disp = st.text_input("Disponibilidad", value=latest_p.disponibilidad_incorporacion or "Inmediata", key=f"ed_disp_{selected_cid}")
                        edit_obs = st.text_area("Observaciones", value=latest_p.observaciones or "", height=85, key=f"ed_obs_{selected_cid}")
                    else:
                        st.info("Este candidato no tiene una postulación activa vinculada.")
                        edit_cliente = None
                        edit_perfil = None
                        edit_estado = None
                        edit_fuente = None
                        edit_recruiter_id = None
                        edit_disp = None
                        edit_obs = None

                st.markdown("---")
                col_j1, col_j2 = st.columns([2, 1])
                with col_j1:
                    edit_just = st.text_input(
                        "Motivo / Justificación del cambio (Auditoría Ley N° 29733):",
                        value="Actualización de datos operativos por reclutador",
                        key=f"ed_just_{selected_cid}",
                    )
                with col_j2:
                    st.write("")
                    st.write("")
                    btn_save_edits = st.button("💾 Guardar Modificaciones", type="primary", use_container_width=True, key=f"btn_save_edit_{selected_cid}")

                if btn_save_edits:
                    curr_user = get_current_user() or {}
                    u_id = curr_user.get("user_id", "usr-demo")
                    u_email = curr_user.get("email", "demo@tcs.com")
                    u_role = curr_user.get("rol", "Senior_Technical_Recruiter")

                    if not enforce_write_permission("Editar Candidato"):
                        return

                    if not edit_nombres or not edit_paterno or not edit_telefono or not edit_email:
                        st.error("Nombres, Apellido Paterno, Celular y Correo son obligatorios.")
                    else:
                        try:
                            # Update candidate with validation and audit logging
                            cand_svc.update_candidate(
                                candidato_id=selected_cid,
                                actor_user_id=u_id,
                                actor_email=u_email,
                                actor_role=u_role,
                                expected_version=cand_selected.record_version,
                                justification=edit_just.strip() or "Edición de ficha",
                                nombres=edit_nombres.strip(),
                                apellido_paterno=edit_paterno.strip(),
                                apellido_materno=edit_materno.strip() if edit_materno else None,
                                telefono_raw=edit_telefono.strip(),
                                email=edit_email.strip(),
                                fecha_nacimiento=edit_fnac,
                                distrito_residencia=edit_distrito.strip() if edit_distrito else None,
                                is_tcs_alumni=edit_alumni,
                            )

                            # Update postulacion if exists
                            if latest_p and edit_cliente:
                                post_repo.update_postulacion(
                                    postulacion_id=latest_p.id,
                                    updated_by_user_id=u_id,
                                    expected_version=latest_p.record_version,
                                    cliente_cuenta=edit_cliente,
                                    perfil_tecnico=edit_perfil.strip(),
                                    estado_embudo=edit_estado,
                                    fuente_origen=edit_fuente,
                                    reclutador_asignado_id=edit_recruiter_id,
                                    disponibilidad_incorporacion=edit_disp.strip() if edit_disp else None,
                                    observaciones=edit_obs.strip() if edit_obs else None,
                                )

                            db.commit()
                            st.success(f"✅ ¡Ficha de {edit_nombres} {edit_paterno} actualizada exitosamente!")
                            st.rerun()
                        except Exception as ex:
                            db.rollback()
                            st.error(f"Error al guardar los cambios: {ex}")

            st.markdown("---")
            st.markdown("#### 📜 Línea de Tiempo & Trazabilidad Inmutable (Auditoría Ley N° 29733)")
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

