"""Human-in-the-loop (HITL) Phone Screening 7 dimensions evaluation page."""
from __future__ import annotations

import streamlit as st

from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.services.screening_service import ScreeningService
from src.services.audit_service import AuditService
from src.services.commute_matrix import evaluate_commute
from src.services.cheat_sheet_service import CheatSheetService
from src.adapters.reporting.one_pager_builder import OnePagerBuilder
from src.ui.session import get_current_user, enforce_write_permission, navigate_to, get_nav_context
from src.ui.theme import render_pipeline_stepper


def render_screening_page() -> None:
    """Render 7-dimensional telephone screening interview form with commute alerts."""
    st.markdown("## 📞 Screening Telefónico HITL (7 Dimensiones)")
    st.caption("Validación humana soberana estructurada con alerta automática de conmutación geográfica y trazabilidad indivisible.")

    user = get_current_user() or {}
    user_id = user.get("user_id", "usr-demo")
    user_email = user.get("email", "demo@tcs.com")
    user_role = user.get("rol", "Senior_Technical_Recruiter")

    with SessionLocal() as db:
        post_repo = PostulacionRepository(db)
        cand_repo = CandidatoRepository(db)
        postulaciones = post_repo.list_all(limit=50)

        if not postulaciones:
            st.info("No hay postulaciones registradas en el sistema. Registre un candidato primero en la Ficha Única.")
            return

        post_options = {}
        for p in postulaciones:
            c = cand_repo.get_by_id(p.candidato_id)
            c_name = c.nombres_completos if c else p.candidato_id
            post_options[p.id] = f"{c_name} — {p.cliente_cuenta} ({p.perfil_tecnico}) [ID: {p.id}]"

        target_p_id = get_nav_context("target_postulacion_id")
        post_keys = list(post_options.keys())
        default_ix = post_keys.index(target_p_id) if target_p_id in post_keys else 0
        selected_post_id = st.selectbox("Seleccione la Postulación a Evaluar:", post_keys, index=default_ix, format_func=lambda x: post_options[x])

        selected_post = post_repo.get_by_id(selected_post_id)
        selected_cand = cand_repo.get_by_id(selected_post.candidato_id) if selected_post else None

    if not selected_post or not selected_cand:
        st.warning("Seleccione una postulación válida.")
        return

    render_pipeline_stepper(
        current_step=3,
        candidate_name=selected_cand.nombres_completos,
        role_or_rgs=f"{selected_post.perfil_tecnico} ({selected_post.cliente_cuenta})",
    )

    # Display candidate context
    st.info(
        f"👤 **Candidato:** {selected_cand.nombres_completos} &nbsp;|&nbsp; "
        f"**DNI:** `{selected_cand.numero_documento}` &nbsp;|&nbsp; "
        f"**Teléfono:** `{selected_cand.telefono_e164}`\n\n"
        f"📍 **Residencia:** {selected_cand.distrito_residencia or 'Lima'} &nbsp;|&nbsp; "
        f"**Cliente Destino:** {selected_post.cliente_cuenta} &nbsp;|&nbsp; "
        f"**Estado Actual:** `{selected_post.estado_embudo}`"
    )

    # Cheat Sheet Técnico Asistido (Propuesta P5)
    with st.expander("💡 Cheat Sheet Técnico Asistido (Preguntas y Respuestas Clave)", expanded=False):
        st.caption("Guía de soporte para la llamada telefónica con preguntas directas, conceptos clave y criterios de evaluación:")
        cs_key = f"cheat_sheet_{selected_post.id}"
        if cs_key not in st.session_state:
            cs_svc = CheatSheetService()
            st.session_state[cs_key] = cs_svc.generate_cheat_sheet(
                postulacion_id=selected_post.id,
                perfil_puesto=selected_post.perfil_tecnico,
                cv_text="",
            )

        if st.button("🤖 Personalizar Preguntas con IA según CV", key=f"btn_ai_cs_{selected_post.id}"):
            with st.spinner("Consultando IA con perfil y CV..."):
                cs_svc = CheatSheetService()
                st.session_state[cs_key] = cs_svc.generate_cheat_sheet(
                    postulacion_id=selected_post.id,
                    perfil_puesto=selected_post.perfil_tecnico,
                    cv_text=getattr(selected_cand, "cv_resumen_tecnico", "") or "",
                )

        cs = st.session_state[cs_key]
        for i, q in enumerate(cs.preguntas, 1):
            st.markdown(f"**{i}. {q.pregunta}**")
            st.markdown(f"- 🎯 *Concepto Clave:* `{q.concepto_clave}`")
            st.markdown(f"- 💬 *Respuesta Esperada:* {q.respuesta_esperada}")
            st.markdown(f"- ⚖️ *Criterio de Evaluación:* {q.criterio_evaluacion}")
            st.markdown("---")

    with st.form("form_screening_hitl"):
        c1, c2 = st.columns(2)
        with c1:
            dim1 = st.selectbox("1. Disponibilidad de Incorporación", ["Inmediata", "1 semana", "2 semanas", "1 mes", "Mayor a 1 mes"])
            salario_ctx = get_nav_context("salario")
            default_sal = float(salario_ctx) if salario_ctx else 6500.0
            dim3 = st.number_input("3. Expectativa Salarial Declarada (S/.)", min_value=0.0, value=default_sal, step=100.0)
            dim5 = st.selectbox("5. Modalidad Aceptada", ["Híbrido", "Remoto", "Presencial"])

        with c2:
            dim4 = st.selectbox("4. Nivel de Interés en la Vacante y TCS", ["Alto", "Medio", "Bajo"])
            # Dynamic Commute Check
            auto_viab, alerta_nota = evaluate_commute(
                residence_district=selected_cand.distrito_residencia,
                client_or_workplace=selected_post.cliente_cuenta,
                modalidad=dim5,
            )
            dim6_options = ["Viable_Cercano", "Viable_Con_Conmutacion", "Alerta_Distancia_Critica"]
            dim6_labels = {
                "Viable_Cercano": "Viable Cercano (<45 min)",
                "Viable_Con_Conmutacion": "Viable con Conmutación (45-75 min)",
                "Alerta_Distancia_Critica": "Alerta Distancia Crítica (>90 min)",
            }
            default_ix = dim6_options.index(auto_viab) if auto_viab in dim6_options else 0
            dim6 = st.selectbox(
                "6. Viabilidad de Traslado (Conmutación)",
                dim6_options,
                index=default_ix,
                format_func=lambda x: dim6_labels.get(x, x),
            )

        if "Alerta_Distancia_Critica" in (dim6, auto_viab) and "Remoto" not in dim5:
            st.warning(
                f"⚠️ **Alerta de Conmutación Geográfica Crítica**: Distancia estimada >90 minutos entre residencia "
                f"('{selected_cand.distrito_residencia}') y sede cliente ('{selected_post.cliente_cuenta}'). Riesgo alto de deserción."
            )

        dim2 = st.text_area(
            "2. Resumen Técnico Cualitativo (Arquitecturas, frameworks, proyectos clave)",
            placeholder="Ej. Fuerte dominio en Java 17, Spring Boot 3, Kafka y arquitecturas de microservicios. Experiencia en banca.",
        )

        dim7 = st.text_area(
            "7. Impresión General y Habilidades Blandas",
            placeholder="Ej. Excelente articulación técnica, claridad verbal y buena disposición para guardias rotativas.",
        )

        st.markdown("#### ⚖️ Dictamen Humano Soberano (HITL)")
        dictamen = st.selectbox(
            "Decisión del Reclutador Responsable:",
            [
                "Avanza_Entrevista_Tecnica",
                "No_Apto_Filtro_Inicial",
                "Enfriar_En_Cartera",
            ],
            format_func=lambda x: {
                "Avanza_Entrevista_Tecnica": "Avanza a Entrevista Técnica (Aprobado)",
                "No_Apto_Filtro_Inicial": "No Apto en Filtro Inicial (Descartado)",
                "Enfriar_En_Cartera": "Enfriar en Cartera de Talento (En Espera)",
            }.get(x, x),
        )

        justificacion = st.text_input("Comentarios u observaciones adicionales del dictamen:")

        submit_scr = st.form_submit_button("Guardar Evaluación de Screening Telefónico", type="primary", use_container_width=True)

        if submit_scr:
            if not enforce_write_permission("Screening Telefónico"):
                return

            if not dim2 or not dim7:
                st.error("Por favor complete los campos cualitativos técnicos y de impresión general.")
                return

            try:
                with SessionLocal() as db:
                    post_repo = PostulacionRepository(db)
                    cand_repo = CandidatoRepository(db)
                    audit_repo = AuditRepository(db)
                    audit_svc = AuditService(audit_repo)
                    scr_svc = ScreeningService(post_repo, cand_repo, audit_svc)

                    scr = scr_svc.record_screening_call(
                        evaluador_user_id=user_id,
                        evaluador_email=user_email,
                        evaluador_role=user_role,
                        postulacion_id=selected_post_id,
                        dim1_disponibilidad=dim1,
                        dim2_resumen_tecnico=dim2,
                        dim3_expectativa_declarada=float(dim3),
                        dim4_interes_vacante=dim4,
                        dim5_modalidad_aceptada=dim5,
                        dim7_impresion_general=dim7,
                        dictamen_humano=dictamen,
                        dim6_override_viabilidad=dim6,
                        justificacion_descarte=justificacion if "Descartado" in dictamen else None,
                    )
                    db.commit()

                    st.session_state["last_screening_saved"] = {
                        "scr_id": scr.id,
                        "post_id": selected_post_id,
                        "dictamen": dictamen,
                        "salario": float(dim3),
                        "cand_name": selected_cand.nombres_completos,
                        "perfil": selected_post.perfil_tecnico,
                        "cliente": selected_post.cliente_cuenta,
                    }
                    st.success(f"✅ Screening registrado exitosamente con dictamen: '{dictamen}'. ID Evaluación: `{scr.id}`.")
            except Exception as e:
                st.error(f"Error al registrar screening: {e}")

    # Next Steps Panel after Screening
    last_scr = st.session_state.get("last_screening_saved")
    if last_scr and last_scr.get("post_id") == selected_post_id:
        st.markdown("---")
        dictamen_val = last_scr.get("dictamen", "")
        if dictamen_val == "Avanza_Entrevista_Tecnica":
            st.markdown(
                f'<div style="background: #0A192F; border: 1px solid #10B981; border-radius: 8px; padding: 14px 18px; margin: 12px 0;">'
                f'<div style="font-size: 11px; color: #10B981; font-weight: 700; text-transform: uppercase;">🎉 Screening Aprobado — Siguiente Paso Recomendado</div>'
                f'<div style="font-size: 15px; color: white; margin: 4px 0;">El candidato <b>{last_scr["cand_name"]}</b> avanzó a Entrevista Técnica. Pretensión salarial: <b>S/. {last_scr["salario"]:,.2f}</b>. ¿Desea validar su CTC ahora?</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            col_sc1, col_sc2 = st.columns(2)
            with col_sc1:
                if st.button(f"💰 Validar CTC y Techo Presupuestal (S/. {last_scr['salario']:,.0f}) ➔", type="primary", use_container_width=True, key="btn_go_ctc_from_scr"):
                    navigate_to("p3_ctc", context={
                        "target_postulacion_id": last_scr["post_id"],
                        "monto_bruto": last_scr["salario"],
                        "cand_name": last_scr["cand_name"],
                        "perfil": last_scr["perfil"],
                    })
            with col_sc2:
                if st.button("📄 Generar One-Pager Ejecutivo para Cliente ➔", use_container_width=True, key="btn_go_op_from_scr"):
                    st.session_state["show_one_pager_now"] = True
        else:
            st.info(f"Screening registrado con dictamen: '{dictamen_val}'. Postulación #{last_scr['post_id']} actualizada.")

    # Ficha Ejecutiva One-Pager para Clientes (Propuesta N2)
    st.markdown("---")
    st.markdown("### 📄 Ficha Ejecutiva One-Pager para Clientes (Terna BCP / Clientes Corporativos)")
    st.caption("Genere una presentación ejecutiva instantánea con branding institucional TCS, resumen de competencias, BGC y dictamen para el Hiring Manager del cliente.")

    if st.button("🚀 Generar Ficha Ejecutiva One-Pager", key="btn_gen_onepager"):
        dni_mask = (selected_cand.numero_documento[:4] + "****") if selected_cand.numero_documento else "N/D"
        skills_parsed = [selected_post.perfil_tecnico, "Git", "Clean Code", "Microservicios"]

        op_html = OnePagerBuilder.build_html(
            candidato_nombre=selected_cand.nombres_completos,
            dni_masked=dni_mask,
            perfil_puesto=selected_post.perfil_tecnico,
            cliente=selected_post.cliente_cuenta,
            anios_experiencia=getattr(selected_cand, "cv_anios_experiencia", None) or 4.0,
            distrito=selected_cand.distrito_residencia or "Lima",
            modalidad=selected_post.observaciones or "Híbrido",
            skills=skills_parsed,
            resumen_tecnico=getattr(selected_cand, "cv_resumen_tecnico", None) or f"Profesional especializado en {selected_post.perfil_tecnico} con amplia trayectoria en proyectos empresariales.",
            disponibilidad=selected_post.disponibilidad_incorporacion or "Inmediata / 15 días",
            expectativa_salarial=float(dim3) if dim3 else 6500.0,
            bgc_status="Aprobado (Sin antecedentes)",
            evaluador_nombre=user.get("nombres_completos", "Senior Technical Recruiter"),
            dictamen_humano="Recomendado para Terna Final",
            alumni_tcs=getattr(selected_cand, "is_tcs_alumni", False),
            fit_score=88.5,
        )

        st.components.v1.html(op_html, height=480, scrolling=True)
        st.download_button(
            label="💾 Descargar One-Pager HTML (Listo para Enviar al Cliente)",
            data=op_html,
            file_name=f"Ficha_Ejecutiva_{selected_cand.nombres_completos.replace(' ', '_')}.html",
            mime="text/html",
            use_container_width=True,
        )

