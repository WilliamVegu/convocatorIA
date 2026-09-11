"""Central Live Audit Console and 17-Variable Funnel Metrics Dashboard."""
from __future__ import annotations

import json
from typing import Optional
import streamlit as st
from sqlalchemy import select, func

from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.persistence.models import (
    CandidatoModel,
    PostulacionModel,
    ScreeningModel,
    LotePlanillaAdeccoModel,
    HistorialAlumniModel,
    BitacoraAuditoriaModel,
)


def render_consola_auditoria_page() -> None:
    """Render central audit console and recruitment funnel metrics dashboard."""
    st.markdown("## 🛡️ Consola Central de Auditoría & Tablero de Métricas")
    st.caption("Pista de auditoría relacional append-only inmutable bajo Ley N° 29733 y seguimiento cuantitativo de las 17 variables del embudo.")

    tab_auditoria, tab_metricas = st.tabs(["📜 Consola de Auditoría en Vivo", "📈 Tablero de Métricas del Embudo"])

    with tab_auditoria:
        _render_consola_auditoria()

    with tab_metricas:
        _render_tablero_metricas()


def _render_consola_auditoria() -> None:
    """Visualizador de bitácora con filtros e inspector de diferencias JSON."""
    st.markdown("#### Filtros de Auditoría")
    c1, c2, c3 = st.columns(3)

    with c1:
        f_user = st.text_input("Filtrar por Correo de Usuario:", placeholder="ej. carla.soto@tcs.com").strip()
    with c2:
        f_entidad = st.selectbox(
            "Entidad Objeto:",
            ["Todas", "Candidato", "Postulacion", "Screening", "Evaluacion_CTC", "Compliance", "Documento_CV", "Planilla_Adecco", "Reporte_Cartera_Exclusiones", "Usuario"],
        )
    with c3:
        f_accion = st.selectbox(
            "Tipo de Acción:",
            ["Todas", "Creacion", "Modificacion", "Carga_Archivo", "Exportacion", "Transicion_Estado", "Autenticacion", "Acceso_Denegado", "Modificacion_Rol", "Desbloqueo_Manual", "Fallo_Carga"],
        )

    entidad_param = None if f_entidad == "Todas" else f_entidad
    accion_param = None if f_accion == "Todas" else f_accion
    user_param = f_user if f_user else None

    with SessionLocal() as db:
        audit_repo = AuditRepository(db)
        logs = audit_repo.filter_logs(
            usuario_email=user_param,
            entidad_objeto=entidad_param,
            tipo_accion=accion_param,
            limit=100,
        )

        if not logs:
            st.info("No se encontraron registros de auditoría que coincidan con los filtros.")
            return

        table_data = []
        for l in logs:
            table_data.append({
                "ID": l.id,
                "Fecha / Hora (UTC)": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "Usuario": l.usuario_email,
                "Rol al Momento": l.rol_en_momento,
                "Acción": l.tipo_accion,
                "Entidad": l.entidad_objeto,
                "Registro ID": l.registro_id,
                "Justificación Operativa": l.justificacion_operativa or "",
            })

        st.dataframe(table_data, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🔍 Inspector de Diferencias JSON (Valores Anteriores vs Nuevos)")
        log_ids = [l.id for l in logs]
        log_map = {
            l.id: f"#{l.id} | {l.timestamp.strftime('%H:%M:%S')} — {l.tipo_accion} en {l.entidad_objeto} ({l.usuario_email})"
            for l in logs
        }
        selected_log_id = st.selectbox(
            "Seleccione un ID de evento de auditoría para inspeccionar:",
            log_ids,
            format_func=lambda lid: log_map.get(lid, str(lid)),
        )

        if selected_log_id:
            selected_entry = audit_repo.get_by_id(selected_log_id)
            if selected_entry:
                c_prev, c_new = st.columns(2)
                with c_prev:
                    st.markdown("**Valores Anteriores (Estado previo):**")
                    if selected_entry.valores_previos_json:
                        try:
                            parsed_prev = json.loads(selected_entry.valores_previos_json)
                            st.json(parsed_prev)
                        except Exception:
                            st.code(selected_entry.valores_previos_json, language="json")
                    else:
                        st.caption("*(Sin valores previos — Creación o evento puntual)*")

                with c_new:
                    st.markdown("**Valores Nuevos (Estado resultante):**")
                    if selected_entry.valores_nuevos_json:
                        try:
                            parsed_new = json.loads(selected_entry.valores_nuevos_json)
                            st.json(parsed_new)
                        except Exception:
                            st.code(selected_entry.valores_nuevos_json, language="json")
                    else:
                        st.caption("*(Sin valores nuevos declarados)*")


def _render_tablero_metricas() -> None:
    """Tablero de métricas del embudo de selección (17 variables) y horas ahorradas."""
    st.markdown("#### 📊 Monitoreo de las 17 Variables del Embudo de Reclutamiento")

    with SessionLocal() as db:
        # Funnel counts
        total_candidatos = db.execute(select(func.count(CandidatoModel.id))).scalar() or 0
        total_alumni = db.execute(select(func.count(CandidatoModel.id)).where(CandidatoModel.is_tcs_alumni.is_(True))).scalar() or 0
        total_postulaciones = db.execute(select(func.count(PostulacionModel.id))).scalar() or 0

        # Stages
        p_nuevo = db.execute(select(func.count(PostulacionModel.id)).where(PostulacionModel.estado_embudo == "Nuevo")).scalar() or 0
        p_screening = db.execute(select(func.count(PostulacionModel.id)).where(PostulacionModel.estado_embudo == "Screening_Telefonico")).scalar() or 0
        p_pend_entrev = db.execute(select(func.count(PostulacionModel.id)).where(PostulacionModel.estado_embudo == "Pendiente_Entrevistas")).scalar() or 0
        p_entrev_cliente = db.execute(select(func.count(PostulacionModel.id)).where(PostulacionModel.estado_embudo == "Entrevista_Cliente")).scalar() or 0
        p_oferta_econ = db.execute(select(func.count(PostulacionModel.id)).where(PostulacionModel.estado_embudo == "Oferta_Economica")).scalar() or 0
        p_oferta_acept = db.execute(select(func.count(PostulacionModel.id)).where(PostulacionModel.estado_embudo == "Oferta_Aceptada")).scalar() or 0
        p_contratado = db.execute(select(func.count(PostulacionModel.id)).where(PostulacionModel.estado_embudo == "Contratado")).scalar() or 0
        p_descartado = db.execute(select(func.count(PostulacionModel.id)).where(PostulacionModel.estado_embudo.like("Descartado%"))).scalar() or 0

        # Screenings
        total_screenings = db.execute(select(func.count(ScreeningModel.id))).scalar() or 0
        total_lotes_adecco = db.execute(select(func.count(LotePlanillaAdeccoModel.id))).scalar() or 0

        # Calculations
        tasa_scr_entrev = (p_pend_entrev / total_screenings * 100) if total_screenings > 0 else 0.0
        tasa_of_cont = (p_contratado / p_oferta_econ * 100) if p_oferta_econ > 0 else 0.0

        # Operational Hours Saved calculation (vs 35 h/sem baseline)
        # Proceso 1 (Registro): ~15 min (0.25h) manual per candidate saved
        # Proceso 2 (Actualización de estados): ~10 min (0.17h) per screening saved
        # Proceso 3 (Cruce con Adecco): ~5 hours per batch
        horas_ahorradas_registro = total_candidatos * 0.25
        horas_ahorradas_screening = total_screenings * 0.17
        horas_ahorradas_adecco = total_lotes_adecco * 5.0
        total_horas_ahorradas = horas_ahorradas_registro + horas_ahorradas_screening + horas_ahorradas_adecco

    st.markdown("##### 1. Métricas de Impacto Operativo (Erradicación de las 35 Horas Semanales)")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Candidatos Registrados", total_candidatos)
    with m2:
        st.metric("Candidatos Boomerang Detectados", total_alumni, delta="Patrimonio TCS (Cero comisión)")
    with m3:
        st.metric("Planillas Adecco Validadas", total_lotes_adecco)
    with m4:
        st.metric("Horas Operativas Ahorradas", f"{total_horas_ahorradas:.1f} hrs", delta="Ahorro vs 35h/sem AS-IS")

    st.markdown("##### 2. Distribución del Embudo de Postulaciones")
    c_e1, c_e2, c_e3, c_e4 = st.columns(4)
    with c_e1:
        st.metric("Postulaciones Totales", total_postulaciones)
        st.metric("1. Nuevos / Por Evaluar", p_nuevo)
    with c_e2:
        st.metric("2. Screening Telefónico", p_screening)
        st.metric("3. Aprobados a Entrevista", p_pend_entrev)
    with c_e3:
        st.metric("4. Entrevista con Cliente", p_entrev_cliente)
        st.metric("5. Oferta Económica", p_oferta_econ)
    with c_e4:
        st.metric("6. Contratados Efectivos", p_contratado)
        st.metric("Descartados / En Cartera", p_descartado)

    st.markdown("##### 3. Tasas de Conversión y Eficiencia")
    tc1, tc2 = st.columns(2)
    with tc1:
        st.metric("Tasa de Conversión: Screening ➡️ Entrevista Técnica", f"{tasa_scr_entrev:.1f}%")
    with tc2:
        st.metric("Efectividad: Oferta Económica ➡️ Contratación", f"{tasa_of_cont:.1f}%")
