"""
Contratos de Interfaz y Esquemas Pydantic: Extracción Estructurada de CVs y CUL (LangChain / Heurístico)
Módulo: specs/001-ats-core-mvp/contracts/cv_parser_contracts.py
Feature: 001-ats-core-mvp
"""

from abc import ABC, abstractmethod
from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IdiomaNivelEnum(str, Enum):
    BASICO = "Básico (A1-A2)"
    INTERMEDIO = "Intermedio (B1-B2)"
    AVANZADO = "Avanzado (C1-C2)"
    NATIVO = "Nativo"


class ModalidadLaboralEnum(str, Enum):
    HIBRIDO = "Híbrido"
    REMOTO = "Remoto"
    PRESENCIAL = "Presencial"


class NivelSeniorityEnum(str, Enum):
    TRAINEE = "Trainee"
    JUNIOR = "Junior (1-2 años)"
    SEMI_SENIOR = "Semi-Senior (3-4 años)"
    SENIOR = "Senior (5+ años)"
    LEAD_ARCHITECT = "Lead / Architect (8+ años)"


class HabilidadTecnica(BaseModel):
    """Competencia tecnológica o herramienta extraída del documento."""
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(..., description="Nombre canónico de la tecnología (ej. Java, React, Docker)")
    categoria: str = Field(default="General", description="Backend, Frontend, Cloud, DevOps, Base de Datos, IA/Data")
    anios_experiencia: Optional[float] = Field(default=None, description="Años estimados de uso")


class ExperienciaLaboral(BaseModel):
    """Posición laboral previa declarada en el currículo."""
    model_config = ConfigDict(str_strip_whitespace=True)

    puesto: str = Field(..., description="Cargo o título del rol desempeñado")
    empresa: str = Field(..., description="Nombre de la empresa o cliente")
    fecha_inicio: Optional[str] = Field(default=None, description="Mes/Año de inicio")
    fecha_fin: Optional[str] = Field(default=None, description="Mes/Año de término o 'Actualidad'")
    descripcion_responsabilidades: Optional[str] = Field(default=None, description="Resumen de funciones desempeñadas")
    tecnologias_utilizadas: List[str] = Field(default_factory=list, description="Lista de herramientas empleadas")


class EducacionCertificacion(BaseModel):
    """Formación académica formal o certificación técnica obtenida."""
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(..., description="Grado académico o nombre de la certificación (ej. AWS Certified Solutions Architect)")
    institucion: str = Field(..., description="Universidad, instituto o entidad emisora")
    anio_obtencion: Optional[int] = Field(default=None, description="Año de graduación o expedición")


class CULDataExtracted(BaseModel):
    """
    Datos estructurados extraídos del Certificado Único Laboral (CUL - MTPE Perú).
    Censura explícitamente antecedentes sensibles y extrae trayectoria formal.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    tiene_antecedentes_penales_policiales: bool = Field(
        default=False,
        description="Indica si el documento oficial consigna observaciones penales o policiales"
    )
    trayectoria_formal_registros: List[str] = Field(
        default_factory=list,
        description="Resumen de empleadores formales y periodos declarados ante MTPE/EsSalud"
    )
    fecha_emision_cul: Optional[date] = Field(default=None, description="Fecha de expedición del certificado")


class CVExtractionResult(BaseModel):
    """
    Resultado global de la extracción documental estructurada.
    ESTRICTAMENTE DESPROVISTO de atributos protegidos (edad, género, estado civil, dirección exacta o fotos).
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    resumen_profesional: str = Field(
        ...,
        description="Síntesis técnica del perfil profesional orientado al rol"
    )
    seniority_estimado: NivelSeniorityEnum = Field(
        default=NivelSeniorityEnum.SEMI_SENIOR,
        description="Nivel de experiencia global calculado a partir de la trayectoria"
    )
    anios_experiencia_total: float = Field(
        ...,
        ge=0.0,
        description="Suma total estimada de años de ejercicio laboral técnico"
    )
    habilidades_tecnicas: List[HabilidadTecnica] = Field(
        default_factory=list,
        description="Listado de tecnologías, librerías, nubes y lenguajes identificados"
    )
    experiencias_laborales: List[ExperienciaLaboral] = Field(
        default_factory=list,
        description="Historial cronológico de empleos"
    )
    certificaciones_educacion: List[EducacionCertificacion] = Field(
        default_factory=list,
        description="Certificaciones técnicas y grados universitarios"
    )
    idiomas: List[dict] = Field(
        default_factory=list,
        description="Idiomas y nivel de dominio (ej. [{'idioma': 'Inglés', 'nivel': 'Intermedio (B1-B2)'}])"
    )
    enlaces_profesionales: List[str] = Field(
        default_factory=list,
        description="URLs a perfiles públicos relevantes (GitHub, GitLab, Portfolio)"
    )
    cul_datos: Optional[CULDataExtracted] = Field(
        default=None,
        description="Datos opcionales si el archivo adjunto era un CUL oficial"
    )
    motor_extraccion_usado: str = Field(
        ...,
        description="'GEMINI_LANGCHAIN', 'GROK_LANGCHAIN' o 'HEURISTICO_LOCAL_PYPDF'"
    )


class CVUploadMetadata(BaseModel):
    """Metadatos de integridad y custodia para el archivo adjunto."""
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_archivo_original: str
    tamanio_bytes: int
    hash_sha256: str
    mime_type: str
    subido_por_user_id: str
    fecha_subida: str


class CVParserPort(ABC):
    """
    Puerto Hexagonal para el motor de parsing documental.
    Permite intercambiar entre Gemini, Grok y el extractor heurístico local sin impacto en la UI.
    """

    @abstractmethod
    def parse_document(self, file_bytes: bytes, file_name: str) -> CVExtractionResult:
        """
        Procesa el archivo binario (PDF o DOCX) y devuelve la estructura fuertemente tipada.
        """
        pass
