"""Mass Adecco spreadsheet validation, traffic lights, and atomic batch intake page."""
from __future__ import annotations

import streamlit as st

from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.adecco_repository import AdeccoRepository
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.services.deduplication_service import DeduplicationService
from src.services.alumni_service import AlumniService
from src.services.audit_service import AuditService
from src.services.adecco_service import AdeccoService
from src.ui.session import get_current_user, enforce_write_permission
from src.ui.theme import render_badge


def render_validador_adecco_page() -> None:
    """Render Adecco spreadsheet dropzone, semaphore metrics and atomic import."""
    st.markdown("## 📊 Validador Masivo de Planillas Externas (Adecco)")
    st.caption("Ingesta tolerante a alias, categorización algorítmica <100ms/fila y prevención de duplicados/comisiones indebidas.")

    user = get_current_user() or {}
    user_id = user.get("user_id", "usr-demo")
    user_email = user.get("email", "demo@tcs.com")
    user_role = user.get("rol", "Senior_Technical_Recruiter")

    if "adecco_eval_result" not in st.session_state:
        st.session_state["adecco_eval_result"] = None

    uploaded_file = st.file_uploader(
        "Arrastre y suelte la planilla de candidatos enviada por Adecco (.xlsx, .csv)",
        type=["xlsx", "xls", "csv"],
    )

    if uploaded_file is not None:
        c_btn, c_info = st.columns([1, 3])
        with c_btn:
            if st.button("⚡ Procesar Planilla Masiva", type="primary", use_container_width=True):
                try:
                    file_bytes = uploaded_file.getvalue()
                    with SessionLocal() as db:
                        cand_repo = CandidatoRepository(db)
                        post_repo = PostulacionRepository(db)
                        adecco_repo = AdeccoRepository(db)
                        alumni_repo = AlumniRepository(db)
                        audit_repo = AuditRepository(db)

                        dedup_svc = DeduplicationService(cand_repo)
                        alumni_svc = AlumniService(alumni_repo)
                        audit_svc = AuditService(audit_repo)

                        adecco_svc = AdeccoService(
                            candidato_repo=cand_repo,
                            postulacion_repo=post_repo,
                            adecco_repo=adecco_repo,
                            dedup_service=dedup_svc,
                            alumni_service=alumni_svc,
                            audit_service=audit_svc,
                        )

                        res = adecco_svc.evaluate_spreadsheet(
                            file_bytes=file_bytes,
                            filename=uploaded_file.name,
                            actor_user_id=user_id,
                            actor_email=user_email,
                            actor_role=user_role,
                        )
                        db.commit()

                        st.session_state["adecco_eval_result"] = res
                        st.success(f"✅ Planilla evaluada en {res['tiempo_procesamiento_ms']:.1f} ms.")
                except Exception as e:
                    st.error(f"Error procesando archivo de Adecco: {e}")

    eval_data = st.session_state.get("adecco_eval_result")
    if eval_data:
        st.markdown("---")
        st.markdown("#### 🚦 Semáforo de Evaluación de Planilla")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Total Procesados", eval_data["total_filas"])
        with c2:
            st.metric("🔴 Duplicados / Excluidos", eval_data["total_rojos"])
        with c3:
            st.metric("🟡 Reactivables (>180d)", eval_data["total_amarillos"])
        with c4:
            st.metric("🟢 Inéditos / Limpios", eval_data["total_verdes"])
        with c5:
            st.metric("🟣 Alumni TCS Detectados", eval_data["total_alumni"])

        st.markdown("#### Detalle Fila por Fila")
        rows = []
        for item in eval_data["items"]:
            sem = item.get("color_semaforo") or item.get("semaforo", "Verde")
            badge_type = "red" if sem == "Rojo" else ("yellow" if sem == "Amarillo" else ("purple" if sem == "Purpura" else "green"))
            rows.append({
                "Fila": item.get("fila_index", item.get("fila_original")),
                "Semáforo": sem,
                "DNI / Doc": item.get("documento"),
                "Nombres": item.get("nombres"),
                "Teléfono": item.get("telefono"),
                "Puesto": item.get("perfil"),
                "Alumni TCS": "🟣 Sí" if item.get("is_alumni") or item.get("es_alumni") else "No",
                "Dictamen / Causa": item.get("detalle_clasificacion") or item.get("motivo_dictamen"),
            })

        st.dataframe(rows, use_container_width=True)

        # Import section
        st.markdown("---")
        st.markdown("#### 📥 Ingesta Atómica de Candidatos Limpios")
        green_items = [i for i in eval_data["items"] if (i.get("color_semaforo") or i.get("semaforo")) == "Verde"]

        if green_items:
            c_cl, c_rgs, c_perf = st.columns(3)
            with c_cl:
                import_cliente = st.selectbox("Cliente Destino:", ["BCP", "BBVA", "Interbank", "Entel", "Falabella"])
            with c_rgs:
                import_rgs = st.text_input("RGS Vacante:", value="RGS-ADECCO-BATCH-01")
            with c_perf:
                import_perfil = st.text_input("Perfil Técnico:", value="Ingeniero de Software")

            btn_label = f"Importar Candidatos Limpios ({len(green_items)})"
            if st.button(btn_label, type="primary", use_container_width=True):
                if not enforce_write_permission("Importar Planilla Adecco"):
                    return

                try:
                    with SessionLocal() as db:
                        cand_repo = CandidatoRepository(db)
                        post_repo = PostulacionRepository(db)
                        adecco_repo = AdeccoRepository(db)
                        alumni_repo = AlumniRepository(db)
                        audit_repo = AuditRepository(db)

                        dedup_svc = DeduplicationService(cand_repo)
                        alumni_svc = AlumniService(alumni_repo)
                        audit_svc = AuditService(audit_repo)

                        adecco_svc = AdeccoService(
                            candidato_repo=cand_repo,
                            postulacion_repo=post_repo,
                            adecco_repo=adecco_repo,
                            dedup_service=dedup_svc,
                            alumni_service=alumni_svc,
                            audit_service=audit_svc,
                        )

                        imported = adecco_svc.import_clean_candidates(
                            lote_id=eval_data["lote_id"],
                            items_to_import=green_items,
                            actor_user_id=user_id,
                            actor_email=user_email,
                            actor_role=user_role,
                            cliente_cuenta=import_cliente,
                            rgs_vacante_id=import_rgs,
                            perfil_tecnico=import_perfil,
                        )
                        db.commit()

                        st.success(f"🎉 Éxito: {imported} candidatos limpios importados atómicamente a la base de datos corporativa.")
                        st.session_state["adecco_eval_result"] = None
                except Exception as e:
                    st.error(f"Error durante importación atómica: {e}")
        else:
            st.info("No hay candidatos con semáforo verde para importar en este lote.")
