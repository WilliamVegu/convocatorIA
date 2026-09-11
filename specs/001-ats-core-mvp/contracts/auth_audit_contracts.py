"""
Contratos de Interfaz y Esquemas Pydantic: Autenticación, RBAC y Bitácora Inmutable de Auditoría
Módulo: specs/001-ats-core-mvp/contracts/auth_audit_contracts.py
Feature: 001-ats-core-mvp
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RolUsuarioEnum(str, Enum):
    HEAD_OF_TALENT_ACQUISITION = "Head_of_Talent_Acquisition"
    SENIOR_TECHNICAL_RECRUITER = "Senior_Technical_Recruiter"
    ACCOUNT_RECRUITMENT_COORDINATOR = "Account_Recruitment_Coordinator"
    COMPLIANCE_OFFICER = "Compliance_Officer"


class EstadoCuentaEnum(str, Enum):
    ACTIVA = "Activa"
    SUSPENDIDA = "Suspendida"
    BLOQUEADA_POR_INTENTOS = "Bloqueada_Por_Intentos"


class TipoAccionAuditoriaEnum(str, Enum):
    CREACION = "Creacion"
    MODIFICACION = "Modificacion"
    CARGA_ARCHIVO = "Carga_Archivo"
    EXPORTACION = "Exportacion"
    TRANSICION_ESTADO = "Transicion_Estado"
    AUTENTICACION = "Autenticacion"
    ACCESO_DENEGADO = "Acceso_Denegado"
    MODIFICACION_ROL = "Modificacion_Rol"
    DESBLOQUEO_MANUAL = "Desbloqueo_Manual"
    FALLO_CARGA = "Fallo_Carga"


class EntidadAuditoriaEnum(str, Enum):
    CANDIDATO = "Candidato"
    POSTULACION = "Postulacion"
    SCREENING = "Screening"
    EVALUACION_CTC = "Evaluacion_CTC"
    COMPLIANCE = "Compliance"
    DOCUMENTO_CV = "Documento_CV"
    PLANILLA_ADECCO = "Planilla_Adecco"
    REPORTE_CARTERA_EXCLUSIONES = "Reporte_Cartera_Exclusiones"
    USUARIO = "Usuario"


class UserRegistrationRequest(BaseModel):
    """Solicitud de alta de nuevo usuario en el sistema ATS."""
    model_config = ConfigDict(str_strip_whitespace=True)

    nombres_completos: str = Field(..., min_length=5, max_length=150)
    email: str = Field(..., description="Correo corporativo oficial institucional (@tcs.com)")
    password: str = Field(..., min_length=8, description="Contraseña robusta de acceso")

    @field_validator("email")
    @classmethod
    def validate_tcs_domain(cls, v: str) -> str:
        v = v.lower().strip()
        if not v.endswith("@tcs.com"):
            raise ValueError("El registro corporativo exige obligatoriamente una cuenta con dominio institucional '@tcs.com'.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not any(c.isupper() for c in v):
            raise ValueError("La contraseña debe incluir al menos una letra mayúscula.")
        if not any(c.islower() for c in v):
            raise ValueError("La contraseña debe incluir al menos una letra minúscula.")
        if not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe incluir al menos un número.")
        if not any(not c.isalnum() for c in v):
            raise ValueError("La contraseña debe incluir al menos un carácter especial (ej. !@#$%^&*).")
        return v


class UserLoginRequest(BaseModel):
    """Solicitud de inicio de sesión de usuario."""
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., description="Correo institucional")
    password: str = Field(..., description="Contraseña confidencial")


class UserResponseDTO(BaseModel):
    """Transferencia de datos pública del usuario (sin hash de contraseña)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str
    nombres_completos: str
    email: str
    rol: RolUsuarioEnum
    estado_cuenta: EstadoCuentaEnum
    ultimo_login: Optional[datetime] = None
    created_at: datetime


class UserRoleUpdateRequest(BaseModel):
    """Solicitud de elevación o cambio de rol autorizada por Head of Talent Acquisition."""
    model_config = ConfigDict(str_strip_whitespace=True)

    usuario_objetivo_id: str
    nuevo_rol: RolUsuarioEnum
    autorizado_por_user_id: str
    justificacion_operativa: str = Field(
        ...,
        min_length=10,
        description="Motivo administrativo de la asignación de permisos"
    )


class SessionPayload(BaseModel):
    """Estado de la sesión autenticada activa en el cliente web Streamlit."""
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str
    nombres_completos: str
    email: str
    rol: RolUsuarioEnum
    session_token: str
    login_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def can_mutate(self) -> bool:
        """Determina si el rol tiene privilegios de escritura en el pipeline."""
        return self.rol in [
            RolUsuarioEnum.HEAD_OF_TALENT_ACQUISITION,
            RolUsuarioEnum.SENIOR_TECHNICAL_RECRUITER,
            RolUsuarioEnum.ACCOUNT_RECRUITMENT_COORDINATOR,
        ]

    def is_admin(self) -> bool:
        """Determina si el usuario tiene privilegios administrativos globales."""
        return self.rol == RolUsuarioEnum.HEAD_OF_TALENT_ACQUISITION


class AuditLogEntryCreate(BaseModel):
    """Estructura obligatoria para asentar un evento inmutable en la bitácora."""
    model_config = ConfigDict(str_strip_whitespace=True)

    usuario_id: str
    usuario_email: str
    rol_en_momento: RolUsuarioEnum
    tipo_accion: TipoAccionAuditoriaEnum
    entidad_objeto: EntidadAuditoriaEnum
    registro_id: str
    version_registro: Optional[int] = None
    valores_previos_json: Optional[Dict[str, Any]] = None
    valores_nuevos_json: Optional[Dict[str, Any]] = None
    justificacion_operativa: Optional[str] = None
    ip_address: str = "127.0.0.1"
    session_id: Optional[str] = None
    nombre_archivo_adjunto: Optional[str] = None
    hash_integridad_sha256: Optional[str] = None


class AuditLogEntryDTO(BaseModel):
    """Visualización y consulta forense de un evento histórico de auditoría."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str
    timestamp: datetime
    usuario_id: str
    usuario_email: str
    rol_en_momento: RolUsuarioEnum
    tipo_accion: TipoAccionAuditoriaEnum
    entidad_objeto: EntidadAuditoriaEnum
    registro_id: str
    version_registro: Optional[int] = None
    valores_previos_json: Optional[Dict[str, Any]] = None
    valores_nuevos_json: Optional[Dict[str, Any]] = None
    justificacion_operativa: Optional[str] = None
    ip_address: Optional[str] = None
    nombre_archivo_adjunto: Optional[str] = None
    hash_integridad_sha256: Optional[str] = None


class AuditSearchFilter(BaseModel):
    """Criterios de filtrado avanzado para la consola central de auditoría."""
    model_config = ConfigDict(str_strip_whitespace=True)

    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    usuario_id: Optional[str] = None
    usuario_email: Optional[str] = None
    entidad_objeto: Optional[EntidadAuditoriaEnum] = None
    tipo_accion: Optional[TipoAccionAuditoriaEnum] = None
    registro_id: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class AuthServicePort(ABC):
    """Puerto Hexagonal para el servicio de autenticación y gestión de acceso."""

    @abstractmethod
    def register_user(self, request: UserRegistrationRequest) -> UserResponseDTO:
        """Registra un usuario corporativo con rol inicial Compliance_Officer."""
        pass

    @abstractmethod
    def authenticate(self, request: UserLoginRequest) -> SessionPayload:
        """Valida credenciales, controla bloqueos y emite sesión autenticada."""
        pass

    @abstractmethod
    def update_user_role(self, request: UserRoleUpdateRequest) -> UserResponseDTO:
        """Eleva o modifica el rol operativo auditando el evento."""
        pass

    @abstractmethod
    def unlock_user_account(self, admin_user_id: str, target_user_id: str, justification: str) -> None:
        """Desbloquea administrativamente una cuenta bloqueada por intentos fallidos."""
        pass


class AuditLogRepositoryPort(ABC):
    """Puerto para el repositorio append-only de auditoría e inmutabilidad."""

    @abstractmethod
    def log_event(self, entry: AuditLogEntryCreate) -> str:
        """Registra un nuevo evento inmutable en la bitácora y devuelve el id generado."""
        pass

    @abstractmethod
    def search_logs(self, filters: AuditSearchFilter) -> List[AuditLogEntryDTO]:
        """Consulta y filtra eventos históricos para auditorías y Ley 29733."""
        pass
