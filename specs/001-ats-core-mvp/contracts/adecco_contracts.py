"""
Contratos de Interfaz y Esquemas Pydantic: Validador Adecco y Reporte de Exclusión (Ley 29733)
Módulo: specs/001-ats-core-mvp/contracts/adecco_contracts.py
Feature: 001-ats-core-mvp
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SemaforoClasificacionEnum(str, Enum):
    ROJO_DUPLICADO_ACTIVO = "Rojo_Duplicado_Activo"
    ROJO_EXCLUSION_PERMANENTE = "Rojo_Exclusion_Permanente"
    AMARILLO_REACTIVABLE = "Amarillo_Reactivable"
    VERDE_LIMPIO = "Verde_Limpio"


class MotivoExclusionEnum(str, Enum):
    PROCESO_ACTIVO = "En proceso activo en cuenta cliente"
    DESCARTE_RECIENTE_MENOR_180D = "Descartado hace menos de 180 días"
    EXCLUSION_BGC_NO_APTO = "No apto en verificación personal BGC"
    EXCLUSION_ETICA_FRAUDE = "Falta ética o falsedad documental"
    EXCLUSION_DEUDA_CASTIGADA = "Deuda castigada bancaria excluyente"
    DO_NOT_REHIRE_TCS = "Ex-colaborador TCS no recontratable"
    REACTIVABLE_SALARIO = "Cierre previo por expectativa salarial (>180 días)"
    REACTIVABLE_CUPO = "Cierre previo por vacante cancelada/cubierta (>180 días)"
    INEDITO = "Sin antecedentes registrados"


class AdeccoRowRaw(BaseModel):
    """Fila cruda leída de la planilla de Adecco con tolerancia a alias de cabeceras."""
    model_config = ConfigDict(str_strip_whitespace=True)

    documento_raw: Optional[str] = Field(default=None, description="DNI, CE o Pasaporte digitado en la planilla")
    nombres_raw: Optional[str] = Field(default=None, description="Nombres o Nombres y Apellidos")
    apellidos_raw: Optional[str] = Field(default=None, description="Apellidos (si vienen en columna separada)")
    telefono_raw: Optional[str] = Field(default=None, description="Teléfono, Móvil o Celular")
    email_raw: Optional[str] = Field(default=None, description="Correo electrónico")
    perfil_raw: Optional[str] = Field(default=None, description="Rol o perfil técnico propuesto")
    pretension_raw: Optional[str] = Field(default=None, description="Monto comunicado a la agencia (si viene)")


class AdeccoNormalizedCandidate(BaseModel):
    """Candidato normalizado a partir de la fila de Adecco para cotejo algorítmico."""
    model_config = ConfigDict(str_strip_whitespace=True)

    fila_numero: int
    tipo_documento: str = "DNI"
    numero_documento: Optional[str] = None
    nombres_completos: str
    nombres_completos_normalizado: str
    telefono_e164: Optional[str] = None
    email: Optional[str] = None
    perfil_propuesto: str


class AdeccoValidationItemResult(BaseModel):
    """Resultado de la evaluación individual de una fila de la planilla de Adecco."""
    model_config = ConfigDict(str_strip_whitespace=True)

    fila_numero: int
    candidato_normalizado: AdeccoNormalizedCandidate
    clasificacion: SemaforoClasificacionEnum
    motivo_detalle: str
    es_alumni_tcs: bool = False
    alumni_estatus_recontratacion: Optional[str] = None
    reclutador_responsable: Optional[str] = None
    cuenta_asociada: Optional[str] = None
    candidato_existente_id: Optional[str] = None
    score_similitud_fonetica: float = 0.0


class AdeccoBatchSummary(BaseModel):
    """Resumen cuantitativo del procesamiento del lote de Adecco."""
    model_config = ConfigDict(str_strip_whitespace=True)

    lote_id: str
    nombre_archivo: str
    total_filas_leidas: int
    total_rojos_duplicados: int
    total_amarillos_reactivables: int
    total_verdes_limpios: int
    total_alumni_detectados: int
    items: List[AdeccoValidationItemResult]
    tiempo_procesamiento_ms: float
    procesado_por_user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CarteraExclusionRow5Col(BaseModel):
    """
    Estructura estricta y obligatoria de 5 columnas para el reporte entregado a Adecco.
    Garantiza el 100% de cumplimiento de la Ley N° 29733 (cero teléfonos, correos o sueldos).
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    dni: str = Field(..., description="Columna 1: DNI del candidato en cartera")
    nombres_y_apellidos: str = Field(..., description="Columna 2: Nombres y apellidos completos")
    perfil: str = Field(..., description="Columna 3: Especialidad o rol profesional")
    vigencia_exclusion: str = Field(..., description="Columna 4: Plazo hasta el cual rige la exclusión (ej. 'Hasta 15/12/2026' o 'Permanente')")
    estado: str = Field(..., description="Columna 5: Estado formal de exclusión (ej. 'En Proceso Activo', 'Cartera Excluida', 'Exclusión Institucional')")


class CarteraExclusionExportRequest(BaseModel):
    """Parámetros de generación del reporte de cartera y exclusiones a demanda."""
    model_config = ConfigDict(str_strip_whitespace=True)

    usuario_solicitante_id: str
    filtro_cuenta_cliente: Optional[str] = Field(default=None, description="Cuenta específica o None para general")
    formato: str = Field(default="xlsx", description="'xlsx' o 'csv'")


class AdeccoProcessorPort(ABC):
    """Puerto para el procesamiento y validación algorítmica de planillas de proveedores."""

    @abstractmethod
    def process_spreadsheet(self, file_bytes: bytes, file_name: str, user_id: str) -> AdeccoBatchSummary:
        """Procesa una planilla electrónica y devuelve el resumen con código semafórico."""
        pass

    @abstractmethod
    def import_clean_candidates(self, lote_id: str, clean_items: List[AdeccoValidationItemResult], user_id: str) -> int:
        """Importa masivamente los candidatos verdes hacia la base relacional en una transacción atómica."""
        pass


class ExclusionReportGeneratorPort(ABC):
    """Puerto para la generación del reporte oficial de exclusión de 5 columnas bajo Ley 29733."""

    @abstractmethod
    def generate_report_5col(self, request: CarteraExclusionExportRequest) -> bytes:
        """Compila los candidatos en cartera y exclusión y genera el archivo binario descargable (.xlsx)."""
        pass
