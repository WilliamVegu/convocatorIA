"""Exclusion and portfolio report application service under Ley N° 29733."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import select

from src.adapters.adecco.exclusion_exporter import ExclusionReportExporter
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.adecco_repository import AdeccoRepository
from src.services.audit_service import AuditService
from src.ports.contracts import CarteraExclusionRow5Col
from src.adapters.persistence.models import PostulacionModel, CandidatoModel


class ExclusionReportService:
    """Service compiling active talent portfolio and exclusion records for Adecco."""

    def __init__(
        self,
        candidato_repo: CandidatoRepository,
        postulacion_repo: PostulacionRepository,
        adecco_repo: AdeccoRepository,
        audit_service: AuditService,
        exporter: Optional[ExclusionReportExporter] = None,
    ):
        self.candidato_repo = candidato_repo
        self.postulacion_repo = postulacion_repo
        self.adecco_repo = adecco_repo
        self.audit_service = audit_service
        self.exporter = exporter or ExclusionReportExporter()

    def generate_exclusion_report(
        self,
        actor_user_id: str,
        actor_email: str,
        actor_role: str,
        cliente_cuenta: Optional[str] = None,
        periodo_vigencia_dias: int = 180,
    ) -> Dict[str, Any]:
        """Generate official 5-column Excel report strictly omitting contact and remuneration data."""
        session = self.postulacion_repo.session
        stmt = select(PostulacionModel, CandidatoModel).join(
            CandidatoModel, PostulacionModel.candidato_id == CandidatoModel.id
        )

        if cliente_cuenta and cliente_cuenta.strip():
            stmt = stmt.where(PostulacionModel.cliente_cuenta == cliente_cuenta.strip())

        results = session.execute(stmt).all()
        now_utc = datetime.now(timezone.utc)
        rows_5col: List[CarteraExclusionRow5Col] = []

        for post, cand in results:
            vigencia = "Exclusión Permanente"
            estado_label = post.estado_embudo.replace("_", " ")

            if post.estado_embudo in {
                "Nuevo",
                "Screening_Telefonico",
                "Pendiente_Entrevistas",
                "Pendiente_Envio_Cliente",
                "Entrevista_Cliente",
                "Oferta_Economica",
                "Oferta_Aceptada",
                "Contratado",
            }:
                vigencia = "En Proceso Activo"
                estado_label = "Activo en Proceso"
            elif post.motivo_cierre_tipo == "Excluyente_Permanente":
                vigencia = "Exclusión Permanente (Compliance)"
                estado_label = "No Recontratable"
            else:
                # Temporal descarte
                fecha_cierre = post.fecha_cierre_descarte or post.updated_at
                if fecha_cierre.tzinfo is None:
                    fecha_cierre = fecha_cierre.replace(tzinfo=timezone.utc)

                dias_transcurridos = (now_utc - fecha_cierre).days
                if dias_transcurridos < periodo_vigencia_dias:
                    fecha_fin = fecha_cierre + timedelta(days=periodo_vigencia_dias)
                    vigencia = f"Hasta {fecha_fin.strftime('%d/%m/%Y')}"
                    estado_label = "Descarte Temporal"
                else:
                    # >180 days, no longer excluded for other vacancies
                    continue

            row = CarteraExclusionRow5Col(
                dni=cand.numero_documento,
                nombres_y_apellidos=cand.nombres_completos,
                perfil=post.perfil_tecnico,
                vigencia_exclusion=vigencia,
                estado=estado_label,
            )
            rows_5col.append(row)

        excel_bytes = self.exporter.export_to_excel(rows_5col, cuenta_cliente=cliente_cuenta)
        file_hash = hashlib.sha256(excel_bytes).hexdigest()
        reporte_id = f"rep-{uuid.uuid4()}"

        # Persist audit record in reportes_cartera_exclusiones
        self.adecco_repo.create_reporte_exclusion(
            reporte_id=reporte_id,
            usuario_solicitante_id=actor_user_id,
            hash_archivo_sha256=file_hash,
            total_registros=len(rows_5col),
            filtro_cuenta=cliente_cuenta,
            periodo_vigencia_dias=periodo_vigencia_dias,
        )

        # Audit export event
        self.audit_service.record_export(
            usuario_id=actor_user_id,
            usuario_email=actor_email,
            rol_en_momento=actor_role,
            entidad_objeto="Reporte_Cartera_Exclusiones",
            registro_id=reporte_id,
            hash_sha256=file_hash,
        )

        date_str = now_utc.strftime("%Y%m%d_%H%M")
        suffix = f"_{cliente_cuenta}" if cliente_cuenta else "_Consolidado"
        filename = f"Cartera_Exclusiones_Adecco_{date_str}{suffix}.xlsx"

        return {
            "reporte_id": reporte_id,
            "filename": filename,
            "excel_bytes": excel_bytes,
            "hash_sha256": file_hash,
            "total_registros": len(rows_5col),
            "cuenta_filtrada": cliente_cuenta,
            "rows": rows_5col,
        }
