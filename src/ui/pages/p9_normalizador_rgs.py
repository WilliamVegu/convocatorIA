"""RGS Requirement Normalizer and Boolean Search generator page."""
from __future__ import annotations

import streamlit as st

from src.services.rgs_normalizer_service import RGSNormalizerService
from src.services.cooling_pool_service import CoolingPoolService
from src.adapters.persistence.database import SessionLocal
from src.ui.session import get_current_user, navigate_to
from src.ui.theme import render_pipeline_stepper


SAMPLE_MESSAGES = {
    "BCP Java Backend": (
        "Hola equipo, el líder de arquitectura de BCP necesita con urgencia cubrir 2 posiciones "
        "de desarrollador backend senior. Requisitos indispensables: al menos 5 años con Java 17, "
        "Spring Boot 3, microservicios, Kafka y base de datos Oracle o PostgreSQL. "
        "Deseable que conozca AWS y Docker/Kubernetes. Presupuesto máximo autorizado S/. 9,500 bruto mensual. "
        "Modalidad de trabajo híbrida con 2 días presenciales en la sede de La Molina. Urgente."
    ),
    "Entel Data Engineer": (
        "Buen día, para la cuenta Entel requerimos un Data Engineer con 3 a 4 años de experiencia sólida. "
        "Must have: Python, SQL avanzado, Apache Spark y construcción de pipelines ETL/ELT. "
        "Nice to have: Airflow, GCP (BigQuery) y Databricks. Tarifa máxima estimada S/. 8,000 bruto. "
        "Esquema 100% remoto desde cualquier parte de Perú."
    ),
    "Falabella DevOps": (
        "Necesitamos para Falabella Digital un especialista DevOps. Requisitos obligatorios: "
        "Docker, Kubernetes en producción, CI/CD con GitLab y Linux. Requisitos deseables: "
        "Terraform, AWS y monitoreo con Prometheus/Grafana. Salario hasta S/. 11,000 según evaluación técnica. "
        "Modalidad híbrida en San Isidro."
    ),
}


def render_normalizador_rgs_page() -> None:
    """Render RGS Requirement Normalizer and Boolean search generator interface."""
    st.markdown("## 📝 Normalizador de Requerimientos (RGS a JD)")
    st.caption("Transformación algorítmica de mensajes desestructurados en perfiles homologados y cadenas booleanas para Hiring Assistant.")

    norm_res_existing = st.session_state.get("normalized_rgs")
    role_label = norm_res_existing.titulo_puesto if norm_res_existing else "Definición y Sourcing"
    render_pipeline_stepper(current_step=1, role_or_rgs=role_label)

    user = get_current_user() or {}
    user_name = user.get("nombres_completos", "Reclutador TCS")

    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown("#### 1. Ingesta de Solicitud de Vacante (Correo o Teams)")

        ejemplo_sel = st.selectbox(
            "Cargar Ejemplo Rápido de Demostración:",
            ["(Personalizado / Escribir texto)", "BCP Java Backend", "Entel Data Engineer", "Falabella DevOps"],
        )

        initial_text = ""
        if ejemplo_sel in SAMPLE_MESSAGES:
            initial_text = SAMPLE_MESSAGES[ejemplo_sel]

        raw_input = st.text_area(
            "Texto sin estructurar del Requerimiento:",
            value=initial_text,
            height=200,
            placeholder="Pegue aquí el correo del Delivery Manager o mensaje de Teams con la necesidad del cliente...",
        )

        c_cl, c_btn = st.columns([2, 1])
        with c_cl:
            cliente_sug = st.selectbox("Cliente Principal:", ["BCP", "BBVA", "Interbank", "Entel", "Falabella", "Rimac"])
        with c_btn:
            st.write("")
            st.write("")
            btn_norm = st.button("🚀 Normalizar con IA", type="primary", use_container_width=True)

    # State storage for normalization
    if "normalized_rgs" not in st.session_state:
        st.session_state["normalized_rgs"] = None

    if btn_norm:
        if not raw_input or len(raw_input.strip()) < 15:
            st.error("Por favor ingrese un texto descriptivo del requerimiento (mínimo 15 caracteres).")
        else:
            with st.spinner("Normalizando perfil, extrayendo requisitos y generando sintaxis booleana..."):
                normalizer = RGSNormalizerService()
                res = normalizer.normalize_raw_text(raw_input, cliente_sugerido=cliente_sug)
                st.session_state["normalized_rgs"] = res
                st.success("✅ Requerimiento normalizado exitosamente.")

    norm_res = st.session_state.get("normalized_rgs")

    with c_right:
        st.markdown("#### 2. Job Description Parametrizado (Estructurado)")
        if not norm_res:
            st.info("Pegue el requerimiento a la izquierda y presione 'Normalizar con IA' para estructurar la vacante.")
        else:
            st.markdown(
                f'<div style="background: #0A192F; color: white; padding: 14px 18px; border-radius: 8px; margin-bottom: 14px;">'
                f'<div style="font-size: 11px; color: #00B4D8; text-transform: uppercase; font-weight: 700;">ID REQUERIMIENTO: {norm_res.rgs_id}</div>'
                f'<div style="font-size: 18px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">{norm_res.titulo_puesto}</div>'
                f'<div style="font-size: 13px; color: #94A3B8;">Cliente: <b>{norm_res.cliente}</b> &nbsp;|&nbsp; Modalidad: <b>{norm_res.modalidad_sugerida}</b></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Salary band
            st.markdown(f"💰 **Banda Salarial Sugerida:** `{norm_res.banda_salarial_pen}`")

            # Must have and Nice to have
            st.markdown("##### Requisitos Obligatorios (Must-Have 70%):")
            must_chips = "".join([f'<span style="background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; padding: 3px 8px; border-radius: 10px; font-size: 12px; margin: 2px; display: inline-block;">✔ {m}</span>' for m in norm_res.must_have])
            st.markdown(must_chips, unsafe_allow_html=True)

            st.markdown("##### Requisitos Deseables (Nice-to-Have 30%):")
            nice_chips = "".join([f'<span style="background: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; padding: 3px 8px; border-radius: 10px; font-size: 12px; margin: 2px; display: inline-block;">✦ {n}</span>' for n in norm_res.nice_to_have])
            st.markdown(nice_chips, unsafe_allow_html=True)

            # Boolean Search box for LinkedIn Recruiter
            st.markdown("---")
            st.markdown("##### 🔎 Cadena Booleana para LinkedIn Recruiter / Hiring Assistant:")
            st.code(norm_res.cadena_booleana_linkedin, language="sql")
            st.caption("📋 *Copie y pegue esta cadena booleana en el buscador de LinkedIn Recruiter para asegurar precisión algorítmica.*")

            # Next step action: Open Ficha Única pre-populating vacancy parameters
            st.markdown("---")
            st.markdown("##### 🚀 Siguiente Paso del Flujo:")
            if st.button("📋 Crear Ficha de Candidato con este RGS ➔", type="primary", use_container_width=True, key="btn_goto_ficha_from_rgs"):
                navigate_to("p1_ficha", context={
                    "rgs_cliente": norm_res.cliente,
                    "rgs_perfil": norm_res.titulo_puesto,
                    "rgs_modalidad": norm_res.modalidad_sugerida,
                    "rgs_id": norm_res.rgs_id,
                    "rgs_must_have": norm_res.must_have,
                    "rgs_nice_to_have": norm_res.nice_to_have,
                    "rgs_banda": norm_res.banda_salarial_pen,
                })

    # Bottom section: Cooling Pool Candidates proactive detection
    if norm_res:
        st.markdown("---")
        st.markdown("### 🔔 Candidatos Históricos Enfriados Detectados (Reactivador Proactivo)")
        st.caption("Candidatos evaluados en meses anteriores que no ingresaron por presupuesto o vacante cerrada y que ahora calzan con este RGS:")

        cooling_svc = CoolingPoolService(SessionLocal)
        reactivables = cooling_svc.find_reactivable_candidates(
            perfil_tecnico=norm_res.titulo_puesto,
            presupuesto_max_bruto=9500.0,
            dias_minimos_enfriamiento=90,
        )

        if not reactivables:
            st.info("No se registran candidatos enfriados en la base histórica para esta combinación técnica específica.")
        else:
            for r in reactivables:
                col_i1, col_i2 = st.columns([3, 1])
                with col_i1:
                    st.markdown(
                        f"👤 **{r['nombres_completos']}** &nbsp;|&nbsp; DNI: `{r['numero_documento']}` &nbsp;|&nbsp; Tel: `{r['telefono_e164']}`\n\n"
                        f"• *Perfil previo:* {r['perfil_historico']} ({r['cliente_anterior']}) &nbsp;|&nbsp; "
                        f"• *Inactivo hace:* **{r['dias_inactivo']} días**\n\n"
                        f"💡 *{r['motivo_sugerencia']}*"
                    )
                with col_i2:
                    st.write("")
                    if st.button(f"👤 Abrir Ficha", key=f"btn_recontact_{r['candidato_id']}", use_container_width=True):
                        navigate_to("p1_ficha", context={
                            "prefill_dni": r["numero_documento"],
                            "rgs_cliente": norm_res.cliente,
                            "rgs_perfil": norm_res.titulo_puesto,
                            "rgs_modalidad": norm_res.modalidad_sugerida,
                            "rgs_id": norm_res.rgs_id,
                        })
                st.markdown("---")
