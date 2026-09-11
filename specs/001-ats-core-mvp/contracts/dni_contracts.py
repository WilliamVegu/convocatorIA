"""
Contratos de Interfaz y Esquemas Pydantic: Identidad DNI Nacional y Soporte Offline
Módulo: specs/001-ats-core-mvp/contracts/dni_contracts.py
Feature: 001-ats-core-mvp
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TipoDocumentoEnum(str, Enum):
    DNI = "DNI"
    CE = "CE"
    PASAPORTE = "Pasaporte"


class EstadoIdentidadEnum(str, Enum):
    VALIDADO_OFICIALMENTE = "Validado_Oficialmente"
    PENDIENTE_REGULARIZACION = "Pendiente_Regularizacion"
    CAPTURA_MANUAL_OBSERVADA = "Captura_Manual_Observada"


class DNIRequest(BaseModel):
    """Solicitud de consulta de documento nacional de identidad."""
    model_config = ConfigDict(str_strip_whitespace=True)

    dni: str = Field(
        ...,
        description="Número de DNI peruano de exactamente 8 dígitos numéricos.",
        examples=["76128709", "46753314"]
    )

    @field_validator("dni")
    @classmethod
    def validate_dni_format(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 8:
            raise ValueError("El DNI peruano debe contener exactamente 8 dígitos numéricos.")
        return v


class DNIResponseData(BaseModel):
    """Datos oficiales de identidad validados desde caché local o APIsPERU."""
    model_config = ConfigDict(str_strip_whitespace=True)

    dni: str = Field(..., min_length=8, max_length=8)
    nombres: str = Field(..., min_length=1, description="Nombres de pila oficiales")
    apellido_paterno: str = Field(..., min_length=1, description="Primer apellido oficial")
    apellido_materno: str = Field(default="", description="Segundo apellido oficial")
    fecha_nacimiento: Optional[date] = Field(default=None, description="Fecha de nacimiento para cálculo de edad")
    ubigeo: Optional[str] = Field(default=None, max_length=6, description="Código ubigeo INEI de 6 dígitos")
    distrito: Optional[str] = Field(default=None, description="Distrito de residencia oficial")
    direccion: Optional[str] = Field(default=None, description="Dirección domiciliaria registrada")

    @property
    def nombres_completos(self) -> str:
        partes = [self.nombres, self.apellido_paterno]
        if self.apellido_materno:
            partes.append(self.apellido_materno)
        return " ".join(partes)


class DNIValidationResult(BaseModel):
    """Resultado unificado de la resolución de identidad con trazabilidad de origen."""
    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool = Field(..., description="Indica si la resolución fue exitosa")
    fuente_origen: str = Field(
        ...,
        description="Fuente de donde se obtuvo la identidad: 'CACHE_LOCAL', 'APISPERU_LIVE', 'OFFLINE_MANUAL', 'NOT_FOUND'"
    )
    datos: Optional[DNIResponseData] = Field(default=None, description="Datos de identidad resueltos")
    estado_identidad: EstadoIdentidadEnum = Field(
        default=EstadoIdentidadEnum.VALIDADO_OFICIALMENTE,
        description="Estado asignado a la ficha del candidato"
    )
    regularizacion_pendiente: bool = Field(
        default=False,
        description="Indica si debe encolarse para regularización asíncrona"
    )
    mensaje_error: Optional[str] = Field(default=None, description="Mensaje explicativo ante error o indisponibilidad")
    timestamp_consulta: datetime = Field(default_factory=datetime.utcnow)


class DNICacheEntry(BaseModel):
    """Estructura de persistencia en la tabla local cache_dni_reniec."""
    dni: str = Field(..., min_length=8, max_length=8)
    nombres: str
    apellido_paterno: str
    apellido_materno: str = ""
    fecha_nacimiento: Optional[date] = None
    ubigeo: Optional[str] = None
    distrito: Optional[str] = None
    direccion: Optional[str] = None
    cached_at: datetime = Field(default_factory=datetime.utcnow)


class DNIProviderPort(ABC):
    """
    Puerto Hexagonal para el proveedor de validación de identidad DNI.
    Garantiza el desacoplamiento entre los adaptadores de red y el dominio.
    """

    @abstractmethod
    def lookup_dni(self, dni: str) -> DNIValidationResult:
        """
        Resuelve los datos de un DNI siguiendo la cascada:
        1. Almacén / Caché local SQLite.
        2. Servicio APIsPERU HTTP Live.
        3. Degradación elegante a captura asistida offline.
        """
        pass

    @abstractmethod
    def save_to_cache(self, entry: DNICacheEntry) -> None:
        """Persiste una entrada en la caché local para futuras operaciones offline."""
        pass
