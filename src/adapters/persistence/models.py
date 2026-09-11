"""SQLAlchemy 2.0 ORM Models for ATS Core MVP."""
from __future__ import annotations

from datetime import datetime, date, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def current_utc_time():
    return datetime.now(timezone.utc)


class UsuarioModel(Base):
    __tablename__ = "usuarios_rbac"

    id = Column(String(36), primary_key=True)
    nombres_completos = Column(String(150), nullable=False)
    email = Column(String(120), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(String(40), nullable=False, default="Compliance_Officer")
    estado_cuenta = Column(String(25), nullable=False, default="Activa")
    intentos_fallidos = Column(Integer, nullable=False, default=0)
    bloqueado_hasta = Column(DateTime, nullable=True)
    ultimo_login = Column(DateTime, nullable=True)
    autorizado_por_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="SET NULL", name="fk_usuarios_autorizador"),
        nullable=True,
    )
    record_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=current_utc_time)
    updated_at = Column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)

    __table_args__ = (
        CheckConstraint(
            "rol IN ('Head_of_Talent_Acquisition', 'Senior_Technical_Recruiter', 'Account_Recruitment_Coordinator', 'Compliance_Officer')",
            name="chk_usuario_rol",
        ),
        CheckConstraint(
            "estado_cuenta IN ('Activa', 'Suspendida', 'Bloqueada_Por_Intentos')",
            name="chk_usuario_estado",
        ),
    )


class HistorialAlumniModel(Base):
    __tablename__ = "historial_alumni_tcs"

    id = Column(String(36), primary_key=True)
    tipo_documento = Column(String(15), nullable=False, default="DNI")
    numero_documento = Column(String(20), nullable=False, unique=True, index=True)
    nombres_completos = Column(String(200), nullable=False)
    nombres_normalizado = Column(String(200), nullable=False, index=True)
    email_corporativo_historico = Column(String(120), nullable=True)
    fecha_ingreso = Column(Date, nullable=True)
    fecha_cese = Column(Date, nullable=False)
    ultima_cuenta_proyecto = Column(String(100), nullable=True)
    motivo_desvinculacion = Column(String(150), nullable=True)
    estatus_recontratacion = Column(String(35), nullable=False, default="Rehire_Eligible")
    created_at = Column(DateTime, nullable=False, default=current_utc_time)
    updated_at = Column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)

    __table_args__ = (
        CheckConstraint(
            "estatus_recontratacion IN ('Rehire_Eligible', 'Do_Not_Rehire', 'Requiere_Aprobacion_RRHH')",
            name="chk_alumni_recontratacion",
        ),
    )


class CandidatoModel(Base):
    __tablename__ = "candidatos"

    id = Column(String(36), primary_key=True)
    tipo_documento = Column(String(15), nullable=False, default="DNI")
    numero_documento = Column(String(20), nullable=False, unique=True, index=True)
    nombres = Column(String(100), nullable=False)
    apellido_paterno = Column(String(100), nullable=False)
    apellido_materno = Column(String(100), nullable=True, default="")
    nombres_completos_normalizado = Column(String(255), nullable=False, index=True)
    telefono_e164 = Column(String(20), nullable=False, unique=True, index=True)
    email = Column(String(120), nullable=False, unique=True, index=True)
    fecha_nacimiento = Column(Date, nullable=True)
    ubigeo = Column(String(6), nullable=True)
    departamento = Column(String(50), nullable=True, default="Lima")
    provincia = Column(String(50), nullable=True, default="Lima")
    distrito_residencia = Column(String(100), nullable=True)
    direccion_residencia = Column(String(255), nullable=True)
    is_tcs_alumni = Column(Boolean, nullable=False, default=False)
    alumni_id = Column(
        String(36),
        ForeignKey("historial_alumni_tcs.id", ondelete="SET NULL", name="fk_candidato_alumni"),
        nullable=True,
    )
    estado_identidad = Column(String(40), nullable=False, default="Validado_Oficialmente")
    regularizacion_pendiente = Column(Boolean, nullable=False, default=False)
    cv_documento_url = Column(String(500), nullable=True)
    cv_hash_sha256 = Column(String(64), nullable=True)
    cv_resumen_tecnico = Column(Text, nullable=True)
    cv_anios_experiencia = Column(Float, nullable=True)
    cv_idiomas_json = Column(Text, nullable=True)
    record_version = Column(Integer, nullable=False, default=1)
    created_by_user_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="RESTRICT", name="fk_candidato_creador"),
        nullable=False,
    )
    updated_by_user_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="SET NULL", name="fk_candidato_modificador"),
        nullable=True,
    )
    created_at = Column(DateTime, nullable=False, default=current_utc_time)
    updated_at = Column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)

    @property
    def nombres_completos(self) -> str:
        parts = [self.nombres, self.apellido_paterno]
        if self.apellido_materno:
            parts.append(self.apellido_materno)
        return " ".join(parts)

    def calcular_edad(self, referencia: Optional[date] = None) -> Optional[int]:
        if not self.fecha_nacimiento:
            return None
        today = referencia or date.today()
        edad = today.year - self.fecha_nacimiento.year
        if (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            edad -= 1
        return edad

    __table_args__ = (
        CheckConstraint("tipo_documento IN ('DNI', 'CE', 'Pasaporte')", name="chk_candidato_doc_tipo"),
        CheckConstraint(
            "estado_identidad IN ('Validado_Oficialmente', 'Pendiente_Regularizacion', 'Captura_Manual_Observada')",
            name="chk_candidato_identidad",
        ),
    )


class PostulacionModel(Base):
    __tablename__ = "postulaciones_procesos"

    id = Column(String(36), primary_key=True)
    candidato_id = Column(
        String(36),
        ForeignKey("candidatos.id", ondelete="RESTRICT", name="fk_postulacion_candidato"),
        nullable=False,
        index=True,
    )
    cliente_cuenta = Column(String(100), nullable=False, index=True)
    rgs_vacante_id = Column(String(50), nullable=False)
    perfil_tecnico = Column(String(120), nullable=False)
    reclutador_asignado_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="RESTRICT", name="fk_postulacion_reclutador"),
        nullable=False,
        index=True,
    )
    fuente_origen = Column(String(50), nullable=False)
    trimestre_fiscal = Column(String(10), nullable=False)
    estado_embudo = Column(String(40), nullable=False, default="Nuevo", index=True)
    motivo_cierre_tipo = Column(String(30), nullable=True)
    motivo_cierre_detalle = Column(Text, nullable=True)
    fecha_cierre_descarte = Column(DateTime, nullable=True)
    disponibilidad_incorporacion = Column(String(30), nullable=True)
    observaciones = Column(Text, nullable=True)
    record_version = Column(Integer, nullable=False, default=1)
    created_by_user_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="RESTRICT", name="fk_postulacion_creador"),
        nullable=False,
    )
    updated_by_user_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="SET NULL", name="fk_postulacion_modificador"),
        nullable=True,
    )
    created_at = Column(DateTime, nullable=False, default=current_utc_time)
    updated_at = Column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)

    __table_args__ = (
        CheckConstraint(
            "fuente_origen IN ('Adecco', 'LinkedIn_Oficial', 'BYB_Referido', 'Offshore', 'Directo_Alumni', 'Bolsa_Web')",
            name="chk_postulacion_fuente",
        ),
        CheckConstraint(
            "motivo_cierre_tipo IS NULL OR motivo_cierre_tipo IN ('Temporal_No_Excluyente', 'Excluyente_Permanente', 'Contratacion_Exitosa', 'Desistimiento')",
            name="chk_postulacion_motivo",
        ),
        CheckConstraint(
            "estado_embudo IN ('Nuevo', 'Screening_Telefonico', 'Pendiente_Entrevistas', 'Pendiente_Envio_Cliente', 'Entrevista_Cliente', 'Oferta_Economica', 'Oferta_Aceptada', 'Contratado', 'Descartado_Tecnico', 'Descartado_Economico', 'Descartado_Compliance', 'Desistio')",
            name="chk_postulacion_estado",
        ),
    )


class ScreeningModel(Base):
    __tablename__ = "screening_tecnico"

    id = Column(String(36), primary_key=True)
    postulacion_id = Column(
        String(36),
        ForeignKey("postulaciones_procesos.id", ondelete="CASCADE", name="fk_screening_postulacion"),
        nullable=False,
        unique=True,
    )
    evaluador_user_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="RESTRICT", name="fk_screening_evaluador"),
        nullable=False,
    )
    fecha_hora_llamada = Column(DateTime, nullable=False, default=current_utc_time)
    dim1_disponibilidad = Column(String(30), nullable=False)
    dim2_resumen_tecnico = Column(Text, nullable=False)
    dim3_expectativa_declarada = Column(Float, nullable=False)
    dim4_interes_vacante = Column(String(20), nullable=False)
    dim5_modalidad_aceptada = Column(String(20), nullable=False)
    dim6_viabilidad_traslado = Column(String(25), nullable=False)
    dim6_alerta_distancia_nota = Column(String(255), nullable=True)
    dim7_impresion_general = Column(Text, nullable=False)
    dictamen_humano = Column(String(35), nullable=False)
    created_at = Column(DateTime, nullable=False, default=current_utc_time)
    updated_at = Column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)

    __table_args__ = (
        CheckConstraint(
            "dim5_modalidad_aceptada IN ('Híbrido', 'Remoto', 'Presencial')",
            name="chk_screening_modalidad",
        ),
        CheckConstraint(
            "dictamen_humano IN ('Avanza_Entrevista_Tecnica', 'No_Apto_Filtro_Inicial', 'Enfriar_En_Cartera')",
            name="chk_screening_dictamen",
        ),
    )


class EvaluacionCTCModel(Base):
    __tablename__ = "evaluacion_financiera_ctc"

    id = Column(String(36), primary_key=True)
    postulacion_id = Column(
        String(36),
        ForeignKey("postulaciones_procesos.id", ondelete="CASCADE", name="fk_ctc_postulacion"),
        nullable=False,
        unique=True,
    )
    tipo_expectativa = Column(String(10), nullable=False, default="Bruto")
    monto_declarado = Column(Float, nullable=False)
    salario_bruto_mensual = Column(Float, nullable=False)
    factor_ctc = Column(Float, nullable=False, default=1.56)
    ctc_solicitado = Column(Float, nullable=False)
    ctc_presupuestado = Column(Float, nullable=True)
    variacion_porcentual = Column(Float, nullable=True)
    semaforo_presupuestal = Column(String(35), nullable=False, default="Pendiente_Presupuesto")
    requiere_aprobacion = Column(Boolean, nullable=False, default=False)
    aprobado_por_user_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="SET NULL", name="fk_ctc_aprobador"),
        nullable=True,
    )
    justificacion_aprobacion = Column(Text, nullable=True)
    evaluado_por_user_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="RESTRICT", name="fk_ctc_evaluador"),
        nullable=False,
    )
    created_at = Column(DateTime, nullable=False, default=current_utc_time)
    updated_at = Column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)

    __table_args__ = (
        CheckConstraint("tipo_expectativa IN ('Bruto', 'Neto')", name="chk_ctc_tipo"),
        CheckConstraint(
            "semaforo_presupuestal IN ('Dentro_Presupuesto', 'Requiere_Aprobacion', 'Fuera_Banda', 'Pendiente_Presupuesto')",
            name="chk_ctc_semaforo",
        ),
    )


class ComplianceModel(Base):
    __tablename__ = "compliance_verificaciones"

    id = Column(String(36), primary_key=True)
    postulacion_id = Column(
        String(36),
        ForeignKey("postulaciones_procesos.id", ondelete="CASCADE", name="fk_compliance_postulacion"),
        nullable=False,
        unique=True,
    )
    estado_bgc = Column(String(30), nullable=False, default="Pendiente")
    fecha_solicitud_bgc = Column(DateTime, nullable=True)
    fecha_cierre_bgc = Column(DateTime, nullable=True)
    consulta_equifax_realizada = Column(Boolean, nullable=False, default=False)
    tiene_deuda_castigada_banca = Column(Boolean, nullable=False, default=False)
    es_elegible_compliance = Column(Boolean, nullable=False, default=True)
    notas_compliance = Column(Text, nullable=True)
    verificado_por_user_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="SET NULL", name="fk_compliance_verificador"),
        nullable=True,
    )
    created_at = Column(DateTime, nullable=False, default=current_utc_time)
    updated_at = Column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)

    __table_args__ = (
        CheckConstraint(
            "estado_bgc IN ('Pendiente', 'En_Proceso', 'Aprobado', 'Observado_No_Apto')",
            name="chk_compliance_bgc",
        ),
    )


class LoteAdeccoModel(Base):
    __tablename__ = "lotes_planilla_adecco"

    id = Column(String(36), primary_key=True)
    nombre_proveedor = Column(String(60), nullable=False, default="Adecco")
    fecha_hora_carga = Column(DateTime, nullable=False, default=current_utc_time)
    usuario_carga_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="RESTRICT", name="fk_lote_usuario"),
        nullable=False,
    )
    nombre_archivo_original = Column(String(255), nullable=False)
    hash_archivo_sha256 = Column(String(64), nullable=False)
    total_filas = Column(Integer, nullable=False, default=0)
    cantidad_rojos_duplicados = Column(Integer, nullable=False, default=0)
    cantidad_amarillos_reactivables = Column(Integer, nullable=False, default=0)
    cantidad_verdes_limpios = Column(Integer, nullable=False, default=0)
    cantidad_alumni_detectados = Column(Integer, nullable=False, default=0)
    estado_procesamiento = Column(String(30), nullable=False, default="Completado")
    created_at = Column(DateTime, nullable=False, default=current_utc_time)


class ReporteExclusionesModel(Base):
    __tablename__ = "reportes_cartera_exclusiones"

    id = Column(String(36), primary_key=True)
    destinatario = Column(String(60), nullable=False, default="Adecco")
    fecha_hora_generacion = Column(DateTime, nullable=False, default=current_utc_time)
    usuario_solicitante_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="RESTRICT", name="fk_reporte_usuario"),
        nullable=False,
    )
    filtro_cuenta_cliente = Column(String(100), nullable=True)
    total_registros_exportados = Column(Integer, nullable=False, default=0)
    periodo_vigencia_dias = Column(Integer, nullable=False, default=180)
    hash_archivo_sha256 = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=current_utc_time)


class BitacoraAuditoriaModel(Base):
    __tablename__ = "bitacora_auditoria"

    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=current_utc_time, index=True)
    usuario_id = Column(
        String(36),
        ForeignKey("usuarios_rbac.id", ondelete="RESTRICT", name="fk_auditoria_usuario"),
        nullable=False,
        index=True,
    )
    usuario_email = Column(String(120), nullable=False)
    rol_en_momento = Column(String(40), nullable=False)
    tipo_accion = Column(String(35), nullable=False)
    entidad_objeto = Column(String(40), nullable=False)
    registro_id = Column(String(36), nullable=False)
    version_registro = Column(Integer, nullable=True)
    valores_previos_json = Column(Text, nullable=True)
    valores_nuevos_json = Column(Text, nullable=True)
    justificacion_operativa = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True, default="127.0.0.1")
    session_id = Column(String(64), nullable=True)
    nombre_archivo_adjunto = Column(String(255), nullable=True)
    hash_integridad_sha256 = Column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_auditoria_entidad", "entidad_objeto", "registro_id"),
    )


class CacheDNIReniecModel(Base):
    __tablename__ = "cache_dni_reniec"

    dni = Column(String(8), primary_key=True, index=True)
    nombres = Column(String(100), nullable=False)
    apellido_paterno = Column(String(100), nullable=False)
    apellido_materno = Column(String(100), nullable=True, default="")
    fecha_nacimiento = Column(Date, nullable=True)
    ubigeo = Column(String(6), nullable=True)
    distrito = Column(String(100), nullable=True)
    direccion = Column(String(255), nullable=True)
    cached_at = Column(DateTime, nullable=False, default=current_utc_time)


# Aliases for model names matching SQL tables and alternative imports
LotePlanillaAdeccoModel = LoteAdeccoModel
ReporteCarteraExclusionesModel = ReporteExclusionesModel
ScreeningTecnicoModel = ScreeningModel
EvaluacionFinancieraCTCModel = EvaluacionCTCModel
ComplianceVerificacionesModel = ComplianceModel
