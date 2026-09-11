"""Pure domain entities for ATS Core MVP decoupled from ORM persistence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, Any, Dict, List


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Usuario:
    """User account entity with RBAC."""

    id: str
    nombres_completos: str
    email: str
    hashed_password: str
    rol: str = "Compliance_Officer"
    estado_cuenta: str = "Activa"
    intentos_fallidos: int = 0
    bloqueado_hasta: Optional[datetime] = None
    ultimo_login: Optional[datetime] = None
    autorizado_por_id: Optional[str] = None
    record_version: int = 1
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def is_locked(self) -> bool:
        if self.estado_cuenta == "Bloqueada_Por_Intentos":
            if self.bloqueado_hasta and self.bloqueado_hasta > datetime.now(timezone.utc):
                return True
        return False

    def can_mutate(self) -> bool:
        return self.rol in {
            "Head_of_Talent_Acquisition",
            "Senior_Technical_Recruiter",
            "Account_Recruitment_Coordinator",
        }

    def is_admin(self) -> bool:
        return self.rol == "Head_of_Talent_Acquisition"


@dataclass
class Candidato:
    """Centralized candidate identity profile."""

    id: str
    tipo_documento: str
    numero_documento: str
    nombres: str
    apellido_paterno: str
    nombres_completos_normalizado: str
    telefono_e164: str
    email: str
    created_by_user_id: str
    apellido_materno: str = ""
    fecha_nacimiento: Optional[date] = None
    ubigeo: Optional[str] = None
    departamento: str = "Lima"
    provincia: str = "Lima"
    distrito_residencia: Optional[str] = None
    direccion_residencia: Optional[str] = None
    is_tcs_alumni: bool = False
    alumni_id: Optional[str] = None
    estado_identidad: str = "Validado_Oficialmente"
    regularizacion_pendiente: bool = False
    cv_documento_url: Optional[str] = None
    cv_hash_sha256: Optional[str] = None
    cv_resumen_tecnico: Optional[str] = None
    cv_anios_experiencia: Optional[float] = None
    cv_idiomas_json: Optional[Any] = None
    record_version: int = 1
    updated_by_user_id: Optional[str] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    @property
    def nombres_completos(self) -> str:
        parts = [self.nombres, self.apellido_paterno]
        if self.apellido_materno:
            parts.append(self.apellido_materno)
        return " ".join(parts)

    def calcular_edad(self, referencia: Optional[date] = None) -> Optional[int]:
        """Dynamically compute age without fixed leap year offsets or static assumptions."""
        if not self.fecha_nacimiento:
            return None
        today = referencia or date.today()
        edad = today.year - self.fecha_nacimiento.year
        if (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            edad -= 1
        return edad


@dataclass
class Postulacion:
    """Candidate job application process lifecycle."""

    id: str
    candidato_id: str
    cliente_cuenta: str
    rgs_vacante_id: str
    perfil_tecnico: str
    reclutador_asignado_id: str
    fuente_origen: str
    trimestre_fiscal: str
    created_by_user_id: str
    estado_embudo: str = "Nuevo"
    motivo_cierre_tipo: Optional[str] = None
    motivo_cierre_detalle: Optional[str] = None
    fecha_cierre_descarte: Optional[datetime] = None
    disponibilidad_incorporacion: Optional[str] = None
    observaciones: Optional[str] = None
    record_version: int = 1
    updated_by_user_id: Optional[str] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class ScreeningTecnico:
    """Qualitative human screening call evidence (7 dimensions)."""

    id: str
    postulacion_id: str
    evaluador_user_id: str
    dim1_disponibilidad: str
    dim2_resumen_tecnico: str
    dim3_expectativa_declarada: float
    dim4_interes_vacante: str
    dim5_modalidad_aceptada: str
    dim6_viabilidad_traslado: str
    dim7_impresion_general: str
    dictamen_humano: str
    dim6_alerta_distancia_nota: Optional[str] = None
    fecha_hora_llamada: datetime = field(default_factory=utc_now)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class EvaluacionCTC:
    """Financial compensation simulation with Factor 1.56."""

    id: str
    postulacion_id: str
    monto_declarado: float
    salario_bruto_mensual: float
    ctc_solicitado: float
    evaluado_por_user_id: str
    tipo_expectativa: str = "Bruto"
    factor_ctc: float = 1.56
    ctc_presupuestado: Optional[float] = None
    variacion_porcentual: Optional[float] = None
    semaforo_presupuestal: str = "Pendiente_Presupuesto"
    requiere_aprobacion: bool = False
    aprobado_por_user_id: Optional[str] = None
    justificacion_aprobacion: Optional[str] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class ComplianceVerificacion:
    """Background check and institutional risk verification."""

    id: str
    postulacion_id: str
    estado_bgc: str = "Pendiente"
    fecha_solicitud_bgc: Optional[datetime] = None
    fecha_cierre_bgc: Optional[datetime] = None
    consulta_equifax_realizada: bool = False
    tiene_deuda_castigada_banca: bool = False
    es_elegible_compliance: bool = True
    notas_compliance: Optional[str] = None
    verificado_por_user_id: Optional[str] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class HistorialAlumni:
    """Ex-collaborator historical registry (TCS Peru Alumni)."""

    id: str
    tipo_documento: str
    numero_documento: str
    nombres_completos: str
    nombres_normalizado: str
    fecha_cese: date
    email_corporativo_historico: Optional[str] = None
    fecha_ingreso: Optional[date] = None
    ultima_cuenta_proyecto: Optional[str] = None
    motivo_desvinculacion: Optional[str] = None
    estatus_recontratacion: str = "Rehire_Eligible"
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class LoteAdecco:
    """Mass spreadsheet upload audit log for Adecco."""

    id: str
    usuario_carga_id: str
    nombre_archivo_original: str
    hash_archivo_sha256: str
    nombre_proveedor: str = "Adecco"
    total_filas: int = 0
    cantidad_rojos_duplicados: int = 0
    cantidad_amarillos_reactivables: int = 0
    cantidad_verdes_limpios: int = 0
    cantidad_alumni_detectados: int = 0
    estado_procesamiento: str = "Completado"
    fecha_hora_carga: datetime = field(default_factory=utc_now)
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class ReporteExclusiones:
    """Official 5-column portfolio and exclusion report audit."""

    id: str
    usuario_solicitante_id: str
    hash_archivo_sha256: str
    destinatario: str = "Adecco"
    filtro_cuenta_cliente: Optional[str] = None
    total_registros_exportados: int = 0
    periodo_vigencia_dias: int = 180
    fecha_hora_generacion: datetime = field(default_factory=utc_now)
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class RegistroAuditoria:
    """Immutable append-only audit trail entry."""

    id: str
    usuario_id: str
    usuario_email: str
    rol_en_momento: str
    tipo_accion: str
    entidad_objeto: str
    registro_id: str
    version_registro: Optional[int] = None
    valores_previos_json: Optional[str] = None
    valores_nuevos_json: Optional[str] = None
    justificacion_operativa: Optional[str] = None
    ip_address: str = "127.0.0.1"
    session_id: Optional[str] = None
    nombre_archivo_adjunto: Optional[str] = None
    hash_integridad_sha256: Optional[str] = None
    timestamp: datetime = field(default_factory=utc_now)
