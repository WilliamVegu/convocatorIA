"""Financial simulator CTC Factor 1.56 under D.L. 728 regime with zero #DIV/0! guards."""
from __future__ import annotations

from typing import Optional
import streamlit as st

from src.services.ctc_calculator_service import CTCCalculatorService
from src.services.ctc_service import CTCService
from src.services.audit_service import AuditService
from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.ui.session import get_current_user, enforce_write_permission, is_head_of_ta
from src.ui.theme import render_badge


def render_simulador_ctc_page() -> None:
    """Render financial Cost-to-Company simulator interface."""
    st.markdown("## 💰 Simulador Financiero CTC (Factor 1.56 D.L. 728)")
    st.caption("Cálculo actuarial de Costo Empresa con conversión Neto/Bruto y guardas matemáticas contra errores de división por cero.")

    user = get_current_user() or {}
    user_id = user.get("user_id", "usr-demo")
    user_email = user.get("email", "demo@tcs.com")
    user_role = user.get("rol", "Senior_Technical_Recruiter")

    c_calc, c_post = st.columns([3, 2])

    with c_calc:
        st.markdown("#### 1. Parámetros de Simulación Salarial")
        tipo_salario = st.radio("Modalidad de Expectativa Salarial:", ["Bruto", "Neto"], horizontal=True)

        monto_input = st.number_input(
            "Monto Mensual Declarado por el Candidato (S/.)",
            min_value=0.0,
            value=5000.0,
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
        semaforo = calc_result["semaforo_viabilidad"]
        badge_type = "green" if semaforo == "Dentro_de_Presupuesto" else (
            "yellow" if semaforo == "Requiere_Aprobacion_Especial" else (
                "red" if semaforo == "Fuera_de_Banda" else "gray"
            )
        )
        st.markdown(
            f"""
            <div style="padding: 12px; border-radius: 8px; border: 1px solid #CBD5E1; background: #FFFFFF; margin-top: 10px;">
                <b>Estado de Viabilidad Presupuestal:</b> {render_badge(semaforo.replace('_', ' '), badge_type)}<br/>
                <small style="color: #64748B;">Guardas matemáticas activas: 0.00% riesgo de error #DIV/0! ante presupuestos vacíos o nulos.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Atypical salary warnings
        for warn in calc_result.get("advertencias_rango", []):
            st.warning(f"⚠️ {warn}")

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

        selected_p_id = st.selectbox("Postulación:", list(post_map.keys()), format_func=lambda x: post_map[x])

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
                    st.success(f"✅ Evaluación CTC registrada con ID: `{eval_ctc.id}`.")
            except Exception as e:
                st.error(f"Error al guardar evaluación CTC: {e}")

        # Head of TA Approval section if special approval needed
        if semaforo == "Requiere_Aprobacion_Especial":
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
                                ctc_svc.approve_exception(
                                    approver_user_id=user_id,
                                    approver_email=user_email,
                                    approver_role=user_role,
                                    evaluacion_ctc_id=evals[0].id,
                                    justificacion=just_aprob or "Aprobación de excepción por Head of TA.",
                                )
                                db.commit()
                                st.success("🎉 Excepción presupuestal aprobada y auditada.")
                    except Exception as e:
                        st.error(f"Error aprobando excepción: {e}")
            else:
                st.info("ℹ️ La aprobación de esta excepción salarial está restringida al rol `Head_of_Talent_Acquisition`.")
