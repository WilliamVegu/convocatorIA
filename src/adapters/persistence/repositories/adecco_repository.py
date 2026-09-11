"""Repository for Adecco batch uploads and exclusion report logs in SQLAlchemy 2.0."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.adapters.persistence.models import LoteAdeccoModel, ReporteExclusionesModel


class AdeccoRepository:
    """Repository handling persistence for LoteAdeccoModel and ReporteExclusionesModel."""

    def __init__(self, session: Session):
        self.session = session

    def create_lote(
        self,
        lote_id: str,
        usuario_carga_id: str,
        nombre_archivo_original: str,
        hash_archivo_sha256: str,
        total_filas: int,
        cantidad_rojos_duplicados: int,
        cantidad_amarillos_reactivables: int,
        cantidad_verdes_limpios: int,
        cantidad_alumni_detectados: int,
        estado_procesamiento: str = "Completado",
        nombre_proveedor: str = "Adecco",
    ) -> LoteAdeccoModel:
        lote = LoteAdeccoModel(
            id=lote_id,
            nombre_proveedor=nombre_proveedor,
            fecha_hora_carga=datetime.now(timezone.utc),
            usuario_carga_id=usuario_carga_id,
            nombre_archivo_original=nombre_archivo_original,
            hash_archivo_sha256=hash_archivo_sha256,
            total_filas=total_filas,
            cantidad_rojos_duplicados=cantidad_rojos_duplicados,
            cantidad_amarillos_reactivables=cantidad_amarillos_reactivables,
            cantidad_verdes_limpios=cantidad_verdes_limpios,
            cantidad_alumni_detectados=cantidad_alumni_detectados,
            estado_procesamiento=estado_procesamiento,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(lote)
        self.session.flush()
        return lote

    def get_lote_by_id(self, lote_id: str) -> Optional[LoteAdeccoModel]:
        return self.session.execute(
            select(LoteAdeccoModel).where(LoteAdeccoModel.id == lote_id)
        ).scalar_one_or_none()

    def list_lotes(self, limit: int = 50) -> List[LoteAdeccoModel]:
        stmt = (
            select(LoteAdeccoModel)
            .order_by(LoteAdeccoModel.fecha_hora_carga.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def create_reporte_exclusion(
        self,
        reporte_id: str,
        usuario_solicitante_id: str,
        hash_archivo_sha256: str,
        total_registros: int,
        filtro_cuenta: Optional[str] = None,
        periodo_vigencia_dias: int = 180,
        destinatario: str = "Adecco",
    ) -> ReporteExclusionesModel:
        reporte = ReporteExclusionesModel(
            id=reporte_id,
            destinatario=destinatario,
            fecha_hora_generacion=datetime.now(timezone.utc),
            usuario_solicitante_id=usuario_solicitante_id,
            filtro_cuenta_cliente=filtro_cuenta,
            total_registros_exportados=total_registros,
            periodo_vigencia_dias=periodo_vigencia_dias,
            hash_archivo_sha256=hash_archivo_sha256,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(reporte)
        self.session.flush()
        return reporte

    def list_reportes(self, limit: int = 50) -> List[ReporteExclusionesModel]:
        stmt = (
            select(ReporteExclusionesModel)
            .order_by(ReporteExclusionesModel.fecha_hora_generacion.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())
