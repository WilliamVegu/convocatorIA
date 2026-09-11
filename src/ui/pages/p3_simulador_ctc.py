"""Financial simulator CTC Factor 1.56 under D.L. 728 regime with zero #DIV/0! guards."""
from __future__ import annotations

from typing import Optional
import streamlit as st

from src.services.ctc_calculator_service import CTCCalculatorService
from src.services.ctc_service import CTCService
from src.services.salary_radar_service import SalaryRadarService
from src.services.audit_service import AuditService
from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.ui.session import get_current_user, enforce_write_permission, is_head_of_ta, get_nav_context, navigate_to
from src.ui.theme import render_badge, render_pipeline_stepper
from src.adapters.reporting.one_pager_builder import OnePagerBuilder


def render_simulador_ctc_page() -> None:
    """Render financial Cost-to-Company simulator interface."""
    st.markdown("## 💰 Simulador Financiero CTC (Factor 1.56 D.L. 728)")
    st.caption("Cálculo actuarial de Costo Empresa con conversión Neto/Bruto y guardas matemáticas contra errores de división por cero.")

    user = get_current_user() or {}
    user_id = user.get("user_id", "usr-demo")
    user_email = user.get("email", "demo@tcs.com")
    user_role = user.get("rol", "Senior_Technical_Recruiter")

    target_p_id = get_nav_context("target_postulacion_id")
    cand_name_ctx = get_nav_context("cand_name", "")
    perfil_ctx = get_nav_context("perfil", "")
    monto_bruto_ctx = get_nav_context("monto_bruto")

    role_display = perfil_ctx or "Validación Presupuestal Factor 1.56"
    render_pipeline_stepper(
        current_step=4,
        candidate_name=cand_name_ctx,
        role_or_rgs=role_display,
    )

    c_calc, c_post = st.columns([3, 2])

    with c_calc:
        st.markdown("#### 1. Parámetros de Simulación Salarial")
        tipo_salario = st.radio("Modalidad de Expectativa Salarial:", ["Bruto", "Neto"], horizontal=True)

        default_monto = float(monto_bruto_ctx) if monto_bruto_ctx else 5000.0
        monto_input = st.number_input(
            "Monto Mensual Declarado por el Candidato (S/.)",
            min_value=0.0,
            value=default_monto,
            step=100.0,
            format="%.2f",
        )

        presupuesto_input = st.number_input(
            "Presupuesto Mensual Asignado al Rol (S/.) [Dejar en 0 si no está definido]",
            min_value=0.0,
            value=10000.0,
            step=500.0,
            format="%.2f",
        )

        presupuesto_val: Optional[float] = presupuesto_input if presupuesto_input > 0 else None

        perfiles_bench = ["Desarrollador Java", "Data Engineer", "DevOps Specialist", "Full Stack Developer", "Cloud Architect", "QA Automation", "Scrum Master"]
        p_bench_ix = 0
        if perfil_ctx:
            for i, pb in enumerate(perfiles_bench):
                if pb.lower() in perfil_ctx.lower():
                    p_bench_ix = i
                    break

        r_col1, r_col2 = st.columns(2)
        with r_col1:
            perfil_select = st.selectbox(
                "Perfil Técnico a Benchmarcar:",
                perfiles_bench,
                index=p_bench_ix,
            )
        with r_col2:
            seniority_select = st.selectbox(
                "Seniority Requerido:",
                ["Junior", "Semi-Senior", "Senior", "Lead"],
                index=2,
            )

        calculator = CTCCalculatorService()
        calc_result = calculator.calculate(
            tipo_expectativa=tipo_salario,
            monto_declarado=float(monto_input),
            ctc_presupuestado=presupuesto_val,
            factor_ctc=1.56,
        )

        st.markdown("#### 2. Resultados del Costo Empresa (CTC)")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(
                "Salario Bruto Proyectado",
                f"S/. {calc_result['salario_bruto_mensual']:,.2f}",
                delta="Factor Neto / 0.79" if tipo_salario == "Neto" else None,
            )
        with m2:
            st.metric(
                "CTC Calculado (1.56)",
                f"S/. {calc_result['ctc_solicitado']:,.2f}",
            )
        with m3:
            var_pct = calc_result.get("variacion_porcentual")
            var_str = f"{var_pct:+.2f}%" if var_pct is not None else "N/A"
            st.metric(
                "Variación Presupuestal",
                var_str,
            )

        # Semaphore card
        semaforo = calc_result.get("semaforo_presupuestal", calc_result.get("semaforo_viabilidad", "Pendiente_Presupuesto"))
        badge_type = "green" if semaforo == "Dentro_Presupuesto" else (
            "yellow" if semaforo == "Requiere_Aprobacion" else (
                "red" if semaforo == "Fuera_Banda" else "gray"
            )
        )
        sem_display = semaforo.replace('_', ' ')
        if semaforo == "Dentro_Presupuesto":
            st.success(f"✅ **Estado de Viabilidad Presupuestal:** `{sem_display}` — *Dentro del techo presupuestado del cliente.*")
        elif semaforo == "Requiere_Aprobacion":
            st.warning(f"⚠️ **Estado de Viabilidad Presupuestal:** `{sem_display}` — *Variación entre 0% y 10%. Requiere aprobación de excepción por Head of TA.*")
        elif semaforo == "Fuera_Banda":
            st.error(f"🚫 **Estado de Viabilidad Presupuestal:** `{sem_display}` — *Variación superior al 10%. Fuera de banda presupuestal.*")
        else:
            st.info(f"ℹ️ **Estado de Viabilidad Presupuestal:** `{sem_display}` — *Guardas matemáticas activas: 0.00% riesgo de error #DIV/0! ante presupuestos vacíos.*")

        # Atypical salary warnings
        warn_atipico = calc_result.get("advertencia_rango_atipico")
        if warn_atipico:
            st.warning(f"⚠️ {warn_atipico}")
        for warn in calc_result.get("advertencias_rango", []):
            st.warning(f"⚠️ {warn}")

        # Propuesta P22: Radar Salarial Tech y Benchmarking Local (Lima 2026)
        st.markdown("---")
        st.markdown("##### 📊 Radar Salarial Tech y Benchmarking Local (Lima 2026)")
        st.caption("Contraste en tiempo real contra percentiles P25, P50 (mediana) y P75 del mercado IT local:")
        radar_svc = SalaryRadarService()
        radar_result = radar_svc.evaluate_salary(
            perfil_puesto=perfil_select,
            salario_pretendido=calc_result["salario_bruto_mensual"],
            seniority=seniority_select,
        )

        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("P25 (Bajo Mercado)", f"S/. {radar_result.p25:,.0f}")
        with r2:
            st.metric("P50 (Mediana Lima)", f"S/. {radar_result.p50:,.0f}")
        with r3:
            st.metric("P75 (Banda Alta)", f"S/. {radar_result.p75:,.0f}")

        st.info(f"🎯 **Posicionamiento en Mercado:** {radar_result.posicion_mercado}")

    with c_post:
        st.markdown("#### 3. Asociar Evaluación a Postulación")
        with SessionLocal() as db:
            post_repo = PostulacionRepository(db)
            cand_repo = CandidatoRepository(db)
            postulaciones = post_repo.list_all(limit=50)

            post_map = {}
            for p in postulaciones:
                c = cand_repo.get_by_id(p.candidato_id)
                name = c.nombres_completos if c else p.candidato_id
                post_map[p.id] = f"{name} ({p.cliente_cuenta})"

        if not post_map:
            st.caption("No hay postulaciones registradas en base de datos.")
            return

        p_keys = list(post_map.keys())
        default_ix = p_keys.index(target_p_id) if target_p_id in p_keys else 0
        selected_p_id = st.selectbox("Postulación:", p_keys, index=default_ix, format_func=lambda x: post_map[x])

        if st.button("💾 Guardar Simulación en la Postulación", type="primary", use_container_width=True):
            if not enforce_write_permission("Guardar CTC"):
                return

            try:
                with SessionLocal() as db:
                    post_repo = PostulacionRepository(db)
                    audit_repo = AuditRepository(db)
                    audit_svc = AuditService(audit_repo)
                    ctc_svc = CTCService(post_repo, audit_svc)

                    eval_ctc = ctc_svc.evaluate_and_persist_ctc(
                        actor_user_id=user_id,
                        actor_email=user_email,
                        actor_role=user_role,
                        postulacion_id=selected_p_id,
                        tipo_expectativa=tipo_salario,
                        monto_declarado=float(monto_input),
                        ctc_presupuestado=presupuesto_val,
                        factor_ctc=1.56,
                    )
                    db.commit()
                    st.session_state["last_ctc_saved"] = {
                        "post_id": selected_p_id,
                        "semaforo": semaforo,
                        "salario": calc_result['salario_bruto_mensual'],
                    }
                    st.success(f"✅ Evaluación CTC registrada con ID: `{eval_ctc.id}`.")
            except Exception as e:
                st.error(f"Error al guardar evaluación CTC: {e}")

        # Head of TA Approval section if special approval needed
        if semaforo in {"Requiere_Aprobacion", "Fuera_Banda", "Requiere_Aprobacion_Especial"}:
            st.markdown("---")
            st.markdown("##### ✍️ Trámite de Excepción Salarial")
            if is_head_of_ta():
                just_aprob = st.text_input("Justificación de Aprobación por Head of TA:")
                if st.button("Aprobar Excepción Salarial", use_container_width=True):
                    try:
                        with SessionLocal() as db:
                            post_repo = PostulacionRepository(db)
                            audit_repo = AuditRepository(db)
                            audit_svc = AuditService(audit_repo)
                            ctc_svc = CTCService(post_repo, audit_svc)

                            # Find latest CTC eval for this post
                            evals = post_repo.get_ctc_evals(selected_p_id)
                            if evals:
                                ctc_svc.approve_ctc_exception(
                                    approver_user_id=user_id,
                                    approver_email=user_email,
                                    approver_role=user_role,
                                    postulacion_id=selected_p_id,
                                    justification=just_aprob or "Aprobación de excepción por Head of TA.",
                                )
                                db.commit()
                                st.session_state["last_ctc_saved"] = {
                                    "post_id": selected_p_id,
                                    "semaforo": "Aprobado_Por_Excepcion",
                                    "salario": calc_result['salario_bruto_mensual'],
                                }
                                st.success("🎉 Excepción presupuestal aprobada y auditada.")
                            else:
                                st.warning("Guarde primero la simulación antes de aprobar la excepción.")
                    except Exception as e:
                        st.error(f"Error aprobando excepción: {e}")
            else:
                st.info("ℹ️ La aprobación de esta excepción salarial está restringida al rol `Head_of_Talent_Acquisition`.")

    # Terna One-Pager generation after CTC validation
    last_ctc = st.session_state.get("last_ctc_saved")
    if last_ctc and last_ctc.get("post_id") == selected_p_id:
        st.markdown("---")
        st.markdown(
            f'<div style="background: #0A192F; border: 1px solid #38BDF8; border-radius: 8px; padding: 14px 18px; margin: 12px 0;">'
            f'<div style="font-size: 11px; color: #38BDF8; font-weight: 700; text-transform: uppercase;">🚀 Siguiente Paso: Presentación de Terna al Cliente</div>'
            f'<div style="font-size: 15px; color: white; margin: 4px 0;">La viabilidad financiera para <b>{post_map.get(selected_p_id, '')}</b> ha sido registrada. ¿Desea generar la Ficha Ejecutiva One-Pager para el Delivery / Cliente?</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("📄 Generar Ficha Ejecutiva One-Pager para Cliente ➔", type="primary", use_container_width=True, key="btn_open_op_ctc"):
            st.session_state["show_one_pager_in_ctc"] = True

    if st.session_state.get("show_one_pager_in_ctc"):
        st.markdown("---")
        st.markdown("### 📄 Ficha Ejecutiva One-Pager (Terna para Cliente)")
        with SessionLocal() as db:
            post_repo = PostulacionRepository(db)
            cand_repo = CandidatoRepository(db)
            p_obj = post_repo.get_by_id(selected_p_id)
            c_obj = cand_repo.get_by_id(p_obj.candidato_id) if p_obj else None

        if p_obj and c_obj:
            dni_mask = (c_obj.numero_documento[:4] + "****") if c_obj.numero_documento else "N/D"
            import json
            skills_parsed = []
            if c_obj.skills_extraidas:
                try:
                    skills_parsed = json.loads(c_obj.skills_extraidas) if isinstance(c_obj.skills_extraidas, str) else list(c_obj.skills_extraidas)
                except Exception:
                    skills_parsed = [s.strip() for s in str(c_obj.skills_extraidas).split(",") if s.strip()]
            if not skills_parsed:
                skills_parsed = [p_obj.perfil_tecnico, "Git", "Clean Code", "Metodologías Ágiles"]

            op_html = OnePagerBuilder.build_html(
                candidato_nombre=c_obj.nombres_completos,
                dni_masked=dni_mask,
                perfil_puesto=p_obj.perfil_tecnico,
                cliente=p_obj.cliente_cuenta,
                anios_experiencia=c_obj.anios_experiencia_total or 4.0,
                distrito=c_obj.distrito_residencia or "Lima",
                modalidad=p_obj.modalidad_contrato or "Híbrido",
                skills=skills_parsed,
                resumen_tecnico=c_obj.resumen_cv or f"Profesional especializado en {p_obj.perfil_tecnico} con sólida trayectoria en proyectos empresariales.",
                disponibilidad="Inmediata / 15 días",
                expectativa_salarial=calc_result["salario_bruto_mensual"],
                bgc_status="Aprobado (Sin antecedentes)" if not c_obj.alerta_fraude else "En Verificación",
                evaluador_nombre=user.get("nombres_completos", "Senior Technical Recruiter"),
                dictamen_humano="Recomendado para Terna Final",
                alumni_tcs=getattr(c_obj, "alumni_tcs", False),
                fit_score=88.5,
            )

            st.components.v1.html(op_html, height=480, scrolling=True)
            st.download_button(
                label="💾 Descargar One-Pager HTML para Hiring Manager",
                data=op_html,
                file_name=f"Ficha_Ejecutiva_{c_obj.nombres_completos.replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True,
                key="btn_dl_op_ctc",
            )
