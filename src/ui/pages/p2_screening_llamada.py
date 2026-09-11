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
from src.ui.session import get_current_user, enforce_write_permission


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

        selected_post_id = st.selectbox("Seleccione la Postulación a Evaluar:", list(post_options.keys()), format_func=lambda x: post_options[x])

        selected_post = post_repo.get_by_id(selected_post_id)
        selected_cand = cand_repo.get_by_id(selected_post.candidato_id) if selected_post else None

    if not selected_post or not selected_cand:
        st.warning("Seleccione una postulación válida.")
        return

    # Display candidate context
    st.markdown(
        f"""
        <div style="background-color: #F1F5F9; border-left: 4px solid #0076CE; padding: 10px; border-radius: 4px; margin-bottom: 16px;">
            <b>Candidato:</b> {selected_cand.nombres_completos} | <b>DNI:</b> {selected_cand.numero_documento} | <b>Teléfono:</b> {selected_cand.telefono_e164}<br/>
            <b>Residencia:</b> {selected_cand.distrito_residencia or 'Lima'} | <b>Cliente Destino:</b> {selected_post.cliente_cuenta} | <b>Estado Actual:</b> `{selected_post.estado_embudo}`
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_screening_hitl"):
        c1, c2 = st.columns(2)
        with c1:
            dim1 = st.selectbox("1. Disponibilidad de Incorporación", ["Inmediata", "1 semana", "2 semanas", "1 mes", "Mayor a 1 mes"])
            dim3 = st.number_input("3. Expectativa Salarial Declarada (S/.)", min_value=0.0, value=6500.0, step=100.0)
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

                    st.success(f"✅ Screening registrado exitosamente con dictamen: '{dictamen}'. ID Evaluación: `{scr.id}`.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al registrar screening: {e}")
