# Data Model & Relational Schema: ATS Core MVP

**Feature**: `001-ats-core-mvp` | **Date**: 2026-09-10 | **Status**: Approved  
**Database Dialect**: SQLAlchemy 2.0 (SQLite 3.35+ with WAL mode / PostgreSQL 15+)  

---

## 1. Architectural Principles of the Data Layer

1. **Relational Single Source of Truth**: Reemplaza definitivamente la dispersión de las 11 pestañas del libro de cálculo `BD GENERAL FY27` mediante un esquema de 10 entidades normalizadas en 3FN (Tercera Forma Normal).
2. **Normalización Estricta de Identidad**: Teléfonos móviles en estándar canónico internacional E.164 (`+519XXXXXXXX`), documentos de identidad únicos (DNI de 8 dígitos para ciudadanos peruanos, CE o Pasaporte para extranjeros), y correos electrónicos normalizados en minúsculas.
3. **Cálculo Dinámico sin Atributos Obsoletos**: La edad se calcula en tiempo de ejecución o consulta a partir de `fecha_nacimiento`, erradicando el almacenamiento de números estáticos y previniendo el error histórico de los 127 años.
4. **Control de Concurrencia Optimista**: Las tablas maestras sujetas a edición concurrente (`candidatos`, `postulaciones_procesos`, `usuarios_rbac`) incluyen la columna `record_version INTEGER NOT NULL DEFAULT 1`.
5. **Trazabilidad e Inmutabilidad de Auditoría**: Toda mutación, subida documental, cálculo financiero, validación masiva y exportación genera un registro inmutable en `bitacora_auditoria` vinculado de forma indisociable al `usuario_id` autenticado.

---

## 2. Entity Relationship Diagram (Conceptual)

```text
[usuarios_rbac] 1───────* [candidatos] 1───────* [postulaciones_procesos] 1───────1 [screening_tecnico]
       │                         │                         │
       │                         │                         ├───────1 [evaluacion_financiera_ctc]
       │                         │                         │
       │                         │                         └───────1 [compliance_verificaciones]
       │                         │
       │                         * (detección)
       │                  [historial_alumni_tcs]
       │
       ├───────* [lotes_planilla_adecco]
       │
       ├───────* [reportes_cartera_exclusiones]
       │
       └───────* [bitacora_auditoria] (append-only)

[cache_dni_reniec] (almacén de identidades / resiliencia offline)
```

---

## 3. Entity Specifications & Field Dictionaries

### 3.1. `usuarios_rbac` (Operadores y Cuentas Corporativas)
Representa a los miembros del equipo de Selección autorizados para operar el sistema bajo políticas de control de acceso basado en roles.

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `id` | `VARCHAR(36)` | NO | UUIDv4 | Llave primaria única del operador. |
| `nombres_completos` | `VARCHAR(150)` | NO | - | Nombres y apellidos oficiales del colaborador. |
| `email` | `VARCHAR(120)` | NO | - | Correo corporativo institucional único (dominio `@tcs.com`). `UNIQUE`. |
| `hashed_password` | `VARCHAR(255)` | NO | - | Hash criptográfico seguro con salt (Bcrypt / Argon2id). |
| `rol` | `VARCHAR(40)` | NO | `'Compliance_Officer'` | Rol RBAC: `Head_of_Talent_Acquisition`, `Senior_Technical_Recruiter`, `Account_Recruitment_Coordinator`, `Compliance_Officer`. |
| `estado_cuenta` | `VARCHAR(25)` | NO | `'Activa'` | Estado de la cuenta: `Activa`, `Suspendida`, `Bloqueada_Por_Intentos`. |
| `intentos_fallidos` | `INTEGER` | NO | `0` | Contador de fallos consecutivos de autenticación (bloqueo al 5to intento). |
| `bloqueado_hasta` | `TIMESTAMP` | SÍ | `NULL` | Fecha/hora UTC hasta la cual rige el bloqueo automático preventivo (15 min). |
| `ultimo_login` | `TIMESTAMP` | SÍ | `NULL` | Marca de tiempo UTC del último inicio de sesión exitoso. |
| `autorizado_por_id` | `VARCHAR(36)` | SÍ | `NULL` | FK a `usuarios_rbac(id)`. Head of Talent Acquisition que elevó o modificó el rol. |
| `record_version` | `INTEGER` | NO | `1` | Versión para control de concurrencia optimista. |
| `created_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de creación del usuario. |
| `updated_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de última actualización. |

---

### 3.2. `candidatos` (Ficha Única de Identidad Centralizada)
Entidad maestra que consolida los datos de identidad, residencia y contacto de la persona física.

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `id` | `VARCHAR(36)` | NO | UUIDv4 | Llave primaria del candidato. |
| `tipo_documento` | `VARCHAR(15)` | NO | `'DNI'` | Tipo de documento: `DNI` (8 dígitos), `CE` (Carné de Extranjería), `Pasaporte`. |
| `numero_documento` | `VARCHAR(20)` | NO | - | Número de documento oficial. `UNIQUE`. Índice único. |
| `nombres` | `VARCHAR(100)` | NO | - | Nombres de pila oficiales. |
| `apellido_paterno` | `VARCHAR(100)` | NO | - | Primer apellido oficial. |
| `apellido_materno` | `VARCHAR(100)` | SÍ | `''` | Segundo apellido oficial (vacío en extranjeros con un solo apellido). |
| `nombres_completos_normalizado` | `VARCHAR(255)` | NO | - | Nombres en mayúsculas sin tildes ni partículas ("DE", "LA") para deduplicación. |
| `telefono_e164` | `VARCHAR(20)` | NO | - | Teléfono móvil en formato canónico estricto E.164 (`+519XXXXXXXX`). `UNIQUE`. |
| `email` | `VARCHAR(120)` | NO | - | Correo electrónico principal en minúsculas. `UNIQUE`. |
| `fecha_nacimiento` | `DATE` | SÍ | `NULL` | Fecha de nacimiento oficial para cálculo dinámico de edad. |
| `ubigeo` | `VARCHAR(6)` | SÍ | `NULL` | Código postal/geográfico INEI de 6 dígitos. |
| `departamento` | `VARCHAR(50)` | SÍ | `'Lima'` | Departamento de residencia. |
| `provincia` | `VARCHAR(50)` | SÍ | `'Lima'` | Provincia de residencia. |
| `distrito_residencia` | `VARCHAR(100)` | SÍ | `NULL` | Distrito de residencia para la alerta de viabilidad de transporte geográfico. |
| `direccion_residencia` | `VARCHAR(255)` | SÍ | `NULL` | Dirección censurada/opcional (no expuesta a terceros). |
| `is_tcs_alumni` | `BOOLEAN` | NO | `FALSE` | Bandera que indica si es ex-colaborador TCS (Boomerang). |
| `alumni_id` | `VARCHAR(36)` | SÍ | `NULL` | FK opcional a `historial_alumni_tcs(id)`. |
| `estado_identidad` | `VARCHAR(40)` | NO | `'Validado_Oficialmente'` | `Validado_Oficialmente`, `Pendiente_Regularizacion`, `Captura_Manual_Observada`. |
| `regularizacion_pendiente` | `BOOLEAN` | NO | `FALSE` | Bandera para la cola de sincronización asíncrona de DNI offline. |
| `cv_documento_url` | `VARCHAR(500)` | SÍ | `NULL` | Ruta o URI al archivo de CV almacenado. |
| `cv_hash_sha256` | `VARCHAR(64)` | SÍ | `NULL` | Hash SHA-256 para integridad documental y trazabilidad. |
| `cv_resumen_tecnico` | `TEXT` | SÍ | `NULL` | Habilidades y tecnologías extraídas por LangChain o parser heurístico. |
| `cv_anios_experiencia` | `FLOAT` | SÍ | `NULL` | Años estimados de experiencia profesional extraídos. |
| `cv_idiomas_json` | `JSON` | SÍ | `NULL` | Estructura JSON con idiomas y niveles declarados. |
| `record_version` | `INTEGER` | NO | `1` | Control de concurrencia optimista. |
| `created_by_user_id` | `VARCHAR(36)` | NO | - | FK a `usuarios_rbac(id)`. Reclutador autor de la creación. |
| `updated_by_user_id` | `VARCHAR(36)` | SÍ | `NULL` | FK a `usuarios_rbac(id)`. Último usuario en mutar el registro. |
| `created_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de creación del registro. |
| `updated_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de última actualización. |

---

### 3.3. `postulaciones_procesos` (Ciclo de Vida de Postulación en Embudo)
Modela la participación de un candidato en un requerimiento específico de una cuenta cliente.

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `id` | `VARCHAR(36)` | NO | UUIDv4 | Llave primaria de la postulación. |
| `candidato_id` | `VARCHAR(36)` | NO | - | FK a `candidatos(id)`. Relación N:1 con eliminación restringida (`RESTRICT`). |
| `cliente_cuenta` | `VARCHAR(100)` | NO | - | Nombre de la cuenta cliente (e.g. `BCP`, `Banco Falabella`, `Entel`, `TCS Interno`). |
| `rgs_vacante_id` | `VARCHAR(50)` | NO | - | Código RGS o identificador corporativo de la vacante. |
| `perfil_tecnico` | `VARCHAR(120)` | NO | - | Rol técnico requerido (e.g. `Senior Java Backend Developer`, `DevOps Specialist`). |
| `reclutador_asignado_id` | `VARCHAR(36)` | NO | - | FK a `usuarios_rbac(id)`. Senior Technical Recruiter responsable. |
| `fuente_origen` | `VARCHAR(50)` | NO | - | Canal de atracción: `Adecco`, `LinkedIn_Oficial`, `BYB_Referido`, `Offshore`, `Directo_Alumni`. |
| `trimestre_fiscal` | `VARCHAR(10)` | NO | - | Trimestre fiscal TCS: `FY27-Q1`, `FY27-Q2`, `FY27-Q3`, `FY27-Q4`. |
| `estado_embudo` | `VARCHAR(40)` | NO | `'Nuevo'` | Ver matriz de estados: `Nuevo`, `Screening_Telefonico`, `Pendiente_Entrevistas`, `Pendiente_Envio_Cliente`, `Entrevista_Cliente`, `Oferta_Economica`, `Oferta_Aceptada`, `Contratado`, `Descartado_Tecnico`, `Descartado_Economico`, `Descartado_Compliance`, `Desistio`. |
| `motivo_cierre_tipo` | `VARCHAR(30)` | SÍ | `NULL` | Categoría de descarte: `Temporal_No_Excluyente`, `Excluyente_Permanente`, `Contratacion_Exitosa`, `Desistimiento`. |
| `motivo_cierre_detalle` | `TEXT` | SÍ | `NULL` | Justificación detallada obligatoria en descartes. |
| `fecha_cierre_descarte` | `TIMESTAMP` | SÍ | `NULL` | Fecha de cierre para el cálculo de los 180 días de reactivación. |
| `observaciones` | `TEXT` | SÍ | `NULL` | Notas operativas generales de la postulación. |
| `record_version` | `INTEGER` | NO | `1` | Control de concurrencia optimista. |
| `created_by_user_id` | `VARCHAR(36)` | NO | - | FK a `usuarios_rbac(id)`. |
| `updated_by_user_id` | `VARCHAR(36)` | SÍ | `NULL` | FK a `usuarios_rbac(id)`. |
| `created_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de creación de la postulación. |
| `updated_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de última modificación. |

---

### 3.4. `screening_tecnico` (Registro Cualitativo de Llamada Humana - 7 Dimensiones)
Captura la evidencia estructurada de la llamada humana conducida por la reclutadora técnica, garantizando el principio HITL.

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `id` | `VARCHAR(36)` | NO | UUIDv4 | Llave primaria de la evaluación de screening. |
| `postulacion_id` | `VARCHAR(36)` | NO | - | FK a `postulaciones_procesos(id)`. `UNIQUE`. Relación 1:1. |
| `evaluador_user_id` | `VARCHAR(36)` | NO | - | FK a `usuarios_rbac(id)`. Reclutador que condujo la llamada. |
| `fecha_hora_llamada` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha y hora en que se efectuó la comunicación. |
| `dim1_disponibilidad` | `VARCHAR(30)` | NO | - | Dimensión 1: `Inmediata`, `1_semana`, `2_semanas`, `1_mes`, `Mayor_a_1_mes`. |
| `dim2_resumen_tecnico` | `TEXT` | NO | - | Dimensión 2: Resumen de competencias técnicas validadas verbalmente. |
| `dim3_expectativa_declarada` | `FLOAT` | NO | - | Dimensión 3: Monto salarial mensual comunicado por el candidato en PEN. |
| `dim4_interes_vacante` | `VARCHAR(20)` | NO | - | Dimensión 4: Nivel de motivación e interés: `Alto`, `Medio`, `Bajo`. |
| `dim5_modalidad_aceptada` | `VARCHAR(20)` | NO | - | Dimensión 5: Aceptación de modelo de trabajo: `Híbrido`, `Remoto`, `Presencial`. |
| `dim6_viabilidad_traslado` | `VARCHAR(25)` | NO | - | Dimensión 6: Viabilidad geográfica: `Viable_Cercano`, `Viable_Con_Conmutacion`, `Alerta_Distancia_Critica`. |
| `dim6_alerta_distancia_nota` | `VARCHAR(255)` | SÍ | `NULL` | Detalle de la alerta geográfica (ej. "Reside en VMT, sede BCP La Molina >90min"). |
| `dim7_impresion_general` | `TEXT` | NO | - | Dimensión 7: Impresión general sobre comunicación, actitud y fit cultural. |
| `dictamen_humano` | `VARCHAR(35)` | NO | - | Dictamen humano soberano: `Avanza_Entrevista_Tecnica`, `No_Apto_Filtro_Inicial`, `Enfriar_En_Cartera`. |
| `created_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de creación del registro de screening. |
| `updated_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de última modificación. |

---

### 3.5. `evaluacion_financiera_ctc` (Cálculo Financiero con Factor 1.56 y Guardas)
Gobierna la simulación de Costo Empresa bajo el Régimen Laboral Privado Peruano (D.L. 728).

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `id` | `VARCHAR(36)` | NO | UUIDv4 | Llave primaria de la evaluación financiera. |
| `postulacion_id` | `VARCHAR(36)` | NO | - | FK a `postulaciones_procesos(id)`. `UNIQUE`. Relación 1:1. |
| `tipo_expectativa` | `VARCHAR(10)` | NO | `'Bruto'` | Modalidad ingresada: `'Bruto'` o `'Neto'`. |
| `monto_declarado` | `FLOAT` | NO | - | Valor numérico comunicado en la llamada en Soles (PEN). |
| `salario_bruto_mensual` | `FLOAT` | NO | - | Salario bruto resultante (si era Neto, se aplica conversión inversa `/ 0.79`). |
| `factor_ctc` | `FLOAT` | NO | `1.56` | Factor estándar de cargas sociales según D.L. 728. |
| `ctc_solicitado` | `FLOAT` | NO | - | Costo Empresa calculado: `salario_bruto_mensual * 1.56`. |
| `ctc_presupuestado` | `FLOAT` | SÍ | `NULL` | Techo presupuestal autorizado para la vacante en PEN. |
| `variacion_porcentual` | `FLOAT` | SÍ | `NULL` | Variación porcentual contra el presupuesto. Nulo si presupuesto $\le 0$. |
| `semaforo_presupuestal` | `VARCHAR(35)` | NO | `'Pendiente_Presupuesto'` | `Dentro_Presupuesto` ($\le 0\%$), `Requiere_Aprobacion` ($>0\% \text{ y } \le 10\%$), `Fuera_Banda` ($>10\%$), `Pendiente_Presupuesto`. |
| `requiere_aprobacion` | `BOOLEAN` | NO | `FALSE` | Verdadero si la variación excede el presupuesto autorizado. |
| `aprobado_por_user_id` | `VARCHAR(36)` | SÍ | `NULL` | FK a `usuarios_rbac(id)`. Head of Talent Acquisition que aprueba la excepción. |
| `justificacion_aprobacion` | `TEXT` | SÍ | `NULL` | Justificación obligatoria para autorizaciones salariales fuera de banda. |
| `evaluado_por_user_id` | `VARCHAR(36)` | NO | - | FK a `usuarios_rbac(id)`. Reclutador que ejecutó la simulación. |
| `created_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de creación del registro. |
| `updated_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de última modificación. |

---

### 3.6. `compliance_verificaciones` (Auditoría de Riesgos y Filtros Institucionales)
Gestiona el estado de antecedentes laborales, policiales y riesgo crediticio bancario.

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `id` | `VARCHAR(36)` | NO | UUIDv4 | Llave primaria de verificación de compliance. |
| `postulacion_id` | `VARCHAR(36)` | NO | - | FK a `postulaciones_procesos(id)`. `UNIQUE`. Relación 1:1. |
| `estado_bgc` | `VARCHAR(30)` | NO | `'Pendiente'` | Background Check: `Pendiente`, `En_Proceso`, `Aprobado`, `Observado_No_Apto`. |
| `fecha_solicitud_bgc` | `TIMESTAMP` | SÍ | `NULL` | Fecha de inicio del trámite de BGC con proveedor. |
| `fecha_cierre_bgc` | `TIMESTAMP` | SÍ | `NULL` | Fecha de resolución del BGC. |
| `consulta_equifax_realizada`| `BOOLEAN` | NO | `FALSE` | Indica si se consultó el buró crediticio. |
| `tiene_deuda_castigada_banca`| `BOOLEAN` | NO | `FALSE` | Indica si registra deuda castigada incompatible con cuentas financieras. |
| `es_elegible_compliance` | `BOOLEAN` | NO | `TRUE` | Bandera general de aptitud para contratación. |
| `notas_compliance` | `TEXT` | SÍ | `NULL` | Notas reservadas del oficial de cumplimiento. |
| `verificado_por_user_id` | `VARCHAR(36)` | SÍ | `NULL` | FK a `usuarios_rbac(id)`. Oficial de cumplimiento o reclutador. |
| `created_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de creación. |
| `updated_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de última actualización. |

---

### 3.7. `historial_alumni_tcs` (Catálogo de Ex-Colaboradores TCS Perú)
Repositorio histórico corporativo para la detección automática de candidatos Boomerang.

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `id` | `VARCHAR(36)` | NO | UUIDv4 | Llave primaria del registro Alumni. |
| `tipo_documento` | `VARCHAR(15)` | NO | `'DNI'` | Tipo de documento (`DNI`, `CE`, `Pasaporte`). |
| `numero_documento` | `VARCHAR(20)` | NO | - | Número de documento de identidad. `UNIQUE`. Índice único. |
| `nombres_completos` | `VARCHAR(200)` | NO | - | Nombres y apellidos completos. |
| `nombres_normalizado` | `VARCHAR(200)` | NO | - | Versión normalizada en mayúsculas sin preposiciones para reconciliación fonética. |
| `email_corporativo_historico`| `VARCHAR(120)` | SÍ | `NULL` | Antiguo correo corporativo `@tcs.com`. |
| `fecha_ingreso` | `DATE` | SÍ | `NULL` | Fecha de alta histórica en TCS. |
| `fecha_cese` | `DATE` | NO | - | Fecha de salida de la compañía. |
| `ultima_cuenta_proyecto` | `VARCHAR(100)` | SÍ | `NULL` | Última cuenta cliente o proyecto en que prestó servicios. |
| `motivo_desvinculacion` | `VARCHAR(150)` | SÍ | `NULL` | Motivo de cese registrado por RRHH. |
| `estatus_recontratacion` | `VARCHAR(35)` | NO | `'Rehire_Eligible'` | Condición corporativa: `Rehire_Eligible`, `Do_Not_Rehire`, `Requiere_Aprobacion_RRHH`. |
| `created_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de inserción en el catálogo. |
| `updated_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de actualización. |

---

### 3.8. `lotes_planilla_adecco` (Auditoría de Ingesta Masiva de Proveedor)
Audita cada lote de candidatos externos procesado mediante el validador semántico de planillas.

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `id` | `VARCHAR(36)` | NO | UUIDv4 | Llave primaria del lote de ingesta. |
| `nombre_proveedor` | `VARCHAR(60)` | NO | `'Adecco'` | Nombre de la agencia proveedora de talentos. |
| `fecha_hora_carga` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Marca de tiempo UTC de la carga del archivo. |
| `usuario_carga_id` | `VARCHAR(36)` | NO | - | FK a `usuarios_rbac(id)`. Reclutadora que procesó el archivo. |
| `nombre_archivo_original` | `VARCHAR(255)` | NO | - | Nombre del archivo Excel/CSV cargado. |
| `hash_archivo_sha256` | `VARCHAR(64)` | NO | - | Hash SHA-256 para verificación de integridad y prevención de doble carga. |
| `total_filas` | `INTEGER` | NO | `0` | Total de filas procesadas con datos válidos. |
| `cantidad_rojos_duplicados`| `INTEGER` | NO | `0` | Perfiles clasificados como Duplicado Activo / Exclusión Permanente. |
| `cantidad_amarillos_reactivables`| `INTEGER`| NO | `0` | Perfiles clasificados como Reactivables (>180 días con motivo no excluyente). |
| `cantidad_verdes_limpios` | `INTEGER` | NO | `0` | Perfiles inéditos limpios listos para importación. |
| `cantidad_alumni_detectados`| `INTEGER`| NO | `0` | Perfiles identificados como ex-colaboradores TCS (alerta Boomerang). |
| `estado_procesamiento` | `VARCHAR(30)` | NO | `'Completado'` | `Completado`, `Importado_Parcial`, `Fallido_Rollback`. |
| `created_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de auditoría del lote. |

---

### 3.9. `reportes_cartera_exclusiones` (Auditoría de Descargas bajo Ley 29733)
Registra cada generación y descarga del reporte de exclusión entregado al proveedor externo.

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `id` | `VARCHAR(36)` | NO | UUIDv4 | Llave primaria del evento de reporte. |
| `destinatario` | `VARCHAR(60)` | NO | `'Adecco'` | Nombre de la agencia externa receptora. |
| `fecha_hora_generacion` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Marca de tiempo UTC exacta de la descarga. |
| `usuario_solicitante_id` | `VARCHAR(36)` | NO | - | FK a `usuarios_rbac(id)`. Reclutador o Head autor de la descarga. |
| `filtro_cuenta_cliente` | `VARCHAR(100)` | SÍ | `NULL` | Cuenta filtrada (e.g. `BCP`) o `NULL` para reporte general consolidado. |
| `total_registros_exportados`| `INTEGER`| NO | `0` | Cantidad total de candidatos censurados incluidos en las 5 columnas. |
| `periodo_vigencia_dias` | `INTEGER` | NO | `180` | Ventana de exclusión normativa en días. |
| `hash_archivo_sha256` | `VARCHAR(64)` | NO | - | Hash de integridad del archivo generado. |
| `created_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha de creación del registro. |

---

### 3.10. `bitacora_auditoria` (Trazabilidad Inmutable Append-Only)
Tabla de auditoría obligatoria donde cada mutación operativa, ingesta documental y evento de seguridad queda asentado de manera no repudiable.

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `id` | `VARCHAR(36)` | NO | UUIDv4 | Llave primaria inmutable del evento de auditoría. |
| `timestamp` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Marca de tiempo con zona horaria UTC. |
| `usuario_id` | `VARCHAR(36)` | NO | - | FK a `usuarios_rbac(id)`. Usuario autor de la operación. |
| `usuario_email` | `VARCHAR(120)` | NO | - | Correo corporativo del actor para auditoría forense rápida. |
| `rol_en_momento` | `VARCHAR(40)` | NO | - | Rol del usuario en el instante exacto de la acción. |
| `tipo_accion` | `VARCHAR(35)` | NO | - | Acción ejecutada: `Creacion`, `Modificacion`, `Carga_Archivo`, `Exportacion`, `Transicion_Estado`, `Autenticacion`, `Acceso_Denegado`, `Modificacion_Rol`, `Desbloqueo_Manual`, `Fallo_Carga`. |
| `entidad_objeto` | `VARCHAR(40)` | NO | - | Entidad afectada: `Candidato`, `Postulacion`, `Screening`, `Evaluacion_CTC`, `Compliance`, `Documento_CV`, `Planilla_Adecco`, `Reporte_Cartera_Exclusiones`, `Usuario`. |
| `registro_id` | `VARCHAR(36)` | NO | - | Identificador del registro mutado o consultado. |
| `version_registro` | `INTEGER` | SÍ | `NULL` | Versión del registro involucrado (concurrencia optimista). |
| `valores_previos_json` | `JSON` | SÍ | `NULL` | Diccionario JSON de atributos previos a la mutación. |
| `valores_nuevos_json` | `JSON` | SÍ | `NULL` | Diccionario JSON de los nuevos atributos resultantes. |
| `justificacion_operativa`| `TEXT` | SÍ | `NULL` | Justificación obligatoria en descartes y excepciones salariales. |
| `ip_address` | `VARCHAR(45)` | SÍ | `'127.0.0.1'` | Dirección IP del cliente u operador. |
| `session_id` | `VARCHAR(64)` | SÍ | `NULL` | Identificador de la sesión web activa. |
| `nombre_archivo_adjunto` | `VARCHAR(255)` | SÍ | `NULL` | Nombre original del documento cargado (si aplica). |
| `hash_integridad_sha256` | `VARCHAR(64)` | SÍ | `NULL` | Hash de integridad del documento o lote procesado. |

---

### 3.11. `cache_dni_reniec` (Tabla Auxiliar de Caché Local de Identidades)
Permite el autollenado instantáneo (<5ms) sin consumir cuotas externas y habilita la operación 100% offline.

| Columna | Tipo SQL | Nulo | Default | Restricción / Descripción |
|---------|----------|------|---------|---------------------------|
| `dni` | `VARCHAR(8)` | NO | - | Llave primaria. DNI peruano de 8 dígitos. |
| `nombres` | `VARCHAR(100)` | NO | - | Nombres oficiales devueltos por APIsPERU. |
| `apellido_paterno` | `VARCHAR(100)` | NO | - | Primer apellido oficial. |
| `apellido_materno` | `VARCHAR(100)` | SÍ | `''` | Segundo apellido oficial. |
| `fecha_nacimiento` | `DATE` | SÍ | `NULL` | Fecha de nacimiento para cálculo dinámico de edad. |
| `ubigeo` | `VARCHAR(6)` | SÍ | `NULL` | Código postal / Ubigeo INEI de 6 dígitos. |
| `distrito` | `VARCHAR(100)` | SÍ | `NULL` | Distrito de residencia. |
| `direccion` | `VARCHAR(255)` | SÍ | `NULL` | Dirección de domicilio oficial. |
| `cached_at` | `TIMESTAMP` | NO | `CURRENT_TIMESTAMP` | Fecha/hora UTC en que se guardó en la caché local. |

---

## 4. State Transitions & Lifecycle Matrices

### 4.1. Ciclo de Vida de Postulación (`postulaciones_procesos.estado_embudo`)

```text
[Nuevo] ───(Asignación)───> [Screening_Telefonico] ───(Aprobación Reclutador)───> [Pendiente_Entrevistas]
   │                               │                                                    │
   │ (Descarte)                    │ (Descarte)                                         │ (Avanza)
   ▼                               ▼                                                    ▼
[Descartado_Tecnico /        [Descartado_Tecnico /                             [Pendiente_Envio_Cliente]
 Descartado_Economico /       Descartado_Economico /                                    │
 Desistio]                    Desistio]                                                 ▼
                                                                                [Entrevista_Cliente]
                                                                                        │
                                                                                        ▼
                                                                                [Oferta_Economica]
                                                                                        │
                                                                                        ▼
                                                                                [Oferta_Aceptada]
                                                                                        │
                                                                                        ▼
                                                                                  [Contratado]
```

### 4.2. Semáforo Financiero Presupuestal (`evaluacion_financiera_ctc.semaforo_presupuestal`)

| Condición Matemática | Estado Semáforo | Color UI | Acción del Reclutador |
|----------------------|-----------------|----------|-----------------------|
| $\text{CTC Presupuestado} \le 0 \lor \text{NULL}$ | `Pendiente_Presupuesto` | ⚪ Gris | Alerta informativa. No emite error `#DIV/0!`. |
| $\text{Variación} \le 0.00\%$ | `Dentro_Presupuesto` | 🟢 Verde | Oferta financieramente viable. Continuar proceso. |
| $0.00\% < \text{Variación} \le 10.00\%$ | `Requiere_Aprobacion` | 🟡 Ámbar | Requiere autorización formal de Head of Talent Acquisition. |
| $\text{Variación} > 10.00\%$ | `Fuera_Banda` | 🔴 Rojo | Descarte económico o renegociación mandatoria. |

### 4.3. Semáforo de Validación Masiva Adecco

| Tipo de Coincidencia Histórica | Clasificación | Insignia | Acción de Ingesta |
|--------------------------------|---------------|----------|-------------------|
| Proceso activo en curso O descarte $<180$ días | `Rojo_Duplicado_Activo` | 🔴 Rojo | Excluido de importación. Muestra reclutador a cargo. |
| Descarte histórico permanente (BGC, ética, no recontratable) | `Rojo_Exclusion_Permanente` | 🔴 Rojo | Excluido definitivamente. Bloqueado para siempre. |
| Descarte $>180$ días por motivo subsanable (salario, vacante cerrada) | `Amarillo_Reactivable` | 🟡 Amarillo | Habilita opción de reactivación hacia nueva vacante. |
| Sin antecedentes de documento, teléfono, correo ni fonética | `Verde_Limpio` | 🟢 Verde | Importación limpia en lote a bandeja de entrada. |
| Documento o fonética coincide con `historial_alumni_tcs` | `Alumni_TCS_Boomerang` | 🟣 Púrpura | Alerta Boomerang: canalizar por reclutamiento directo sin comisión. |

---

## 5. Formal Relational DDL (SQL Script)

A continuación se detalla el script DDL ejecutable estándar, 100% compatible con SQLite 3.35+ y conmutable a PostgreSQL 15+:

```sql
-- Habilitar integridad referencial en SQLite
PRAGMA foreign_keys = ON;

-- 1. TABLA: usuarios_rbac
CREATE TABLE IF NOT EXISTS usuarios_rbac (
    id VARCHAR(36) PRIMARY KEY,
    nombres_completos VARCHAR(150) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    rol VARCHAR(40) NOT NULL DEFAULT 'Compliance_Officer',
    estado_cuenta VARCHAR(25) NOT NULL DEFAULT 'Activa',
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta TIMESTAMP NULL,
    ultimo_login TIMESTAMP NULL,
    autorizado_por_id VARCHAR(36) NULL,
    record_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuarios_autorizador FOREIGN KEY (autorizado_por_id) REFERENCES usuarios_rbac(id) ON DELETE SET NULL,
    CONSTRAINT chk_usuario_rol CHECK (rol IN ('Head_of_Talent_Acquisition', 'Senior_Technical_Recruiter', 'Account_Recruitment_Coordinator', 'Compliance_Officer')),
    CONSTRAINT chk_usuario_estado CHECK (estado_cuenta IN ('Activa', 'Suspendida', 'Bloqueada_Por_Intentos'))
);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios_rbac(email);

-- 2. TABLA: historial_alumni_tcs
CREATE TABLE IF NOT EXISTS historial_alumni_tcs (
    id VARCHAR(36) PRIMARY KEY,
    tipo_documento VARCHAR(15) NOT NULL DEFAULT 'DNI',
    numero_documento VARCHAR(20) NOT NULL UNIQUE,
    nombres_completos VARCHAR(200) NOT NULL,
    nombres_normalizado VARCHAR(200) NOT NULL,
    email_corporativo_historico VARCHAR(120) NULL,
    fecha_ingreso DATE NULL,
    fecha_cese DATE NOT NULL,
    ultima_cuenta_proyecto VARCHAR(100) NULL,
    motivo_desvinculacion VARCHAR(150) NULL,
    estatus_recontratacion VARCHAR(35) NOT NULL DEFAULT 'Rehire_Eligible',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_alumni_recontratacion CHECK (estatus_recontratacion IN ('Rehire_Eligible', 'Do_Not_Rehire', 'Requiere_Aprobacion_RRHH'))
);
CREATE INDEX IF NOT EXISTS idx_alumni_documento ON historial_alumni_tcs(numero_documento);
CREATE INDEX IF NOT EXISTS idx_alumni_nombres_norm ON historial_alumni_tcs(nombres_normalizado);

-- 3. TABLA: candidatos
CREATE TABLE IF NOT EXISTS candidatos (
    id VARCHAR(36) PRIMARY KEY,
    tipo_documento VARCHAR(15) NOT NULL DEFAULT 'DNI',
    numero_documento VARCHAR(20) NOT NULL UNIQUE,
    nombres VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100) NULL DEFAULT '',
    nombres_completos_normalizado VARCHAR(255) NOT NULL,
    telefono_e164 VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    fecha_nacimiento DATE NULL,
    ubigeo VARCHAR(6) NULL,
    departamento VARCHAR(50) NULL DEFAULT 'Lima',
    provincia VARCHAR(50) NULL DEFAULT 'Lima',
    distrito_residencia VARCHAR(100) NULL,
    direccion_residencia VARCHAR(255) NULL,
    is_tcs_alumni BOOLEAN NOT NULL DEFAULT 0,
    alumni_id VARCHAR(36) NULL,
    estado_identidad VARCHAR(40) NOT NULL DEFAULT 'Validado_Oficialmente',
    regularizacion_pendiente BOOLEAN NOT NULL DEFAULT 0,
    cv_documento_url VARCHAR(500) NULL,
    cv_hash_sha256 VARCHAR(64) NULL,
    cv_resumen_tecnico TEXT NULL,
    cv_anios_experiencia REAL NULL,
    cv_idiomas_json TEXT NULL,
    record_version INTEGER NOT NULL DEFAULT 1,
    created_by_user_id VARCHAR(36) NOT NULL,
    updated_by_user_id VARCHAR(36) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_candidato_alumni FOREIGN KEY (alumni_id) REFERENCES historial_alumni_tcs(id) ON DELETE SET NULL,
    CONSTRAINT fk_candidato_creador FOREIGN KEY (created_by_user_id) REFERENCES usuarios_rbac(id) ON DELETE RESTRICT,
    CONSTRAINT fk_candidato_modificador FOREIGN KEY (updated_by_user_id) REFERENCES usuarios_rbac(id) ON DELETE SET NULL,
    CONSTRAINT chk_candidato_doc_tipo CHECK (tipo_documento IN ('DNI', 'CE', 'Pasaporte')),
    CONSTRAINT chk_candidato_identidad CHECK (estado_identidad IN ('Validado_Oficialmente', 'Pendiente_Regularizacion', 'Captura_Manual_Observada'))
);
CREATE INDEX IF NOT EXISTS idx_candidatos_documento ON candidatos(numero_documento);
CREATE INDEX IF NOT EXISTS idx_candidatos_telefono ON candidatos(telefono_e164);
CREATE INDEX IF NOT EXISTS idx_candidatos_email ON candidatos(email);
CREATE INDEX IF NOT EXISTS idx_candidatos_nombres_norm ON candidatos(nombres_completos_normalizado);

-- 4. TABLA: postulaciones_procesos
CREATE TABLE IF NOT EXISTS postulaciones_procesos (
    id VARCHAR(36) PRIMARY KEY,
    candidato_id VARCHAR(36) NOT NULL,
    cliente_cuenta VARCHAR(100) NOT NULL,
    rgs_vacante_id VARCHAR(50) NOT NULL,
    perfil_tecnico VARCHAR(120) NOT NULL,
    reclutador_asignado_id VARCHAR(36) NOT NULL,
    fuente_origen VARCHAR(50) NOT NULL,
    trimestre_fiscal VARCHAR(10) NOT NULL,
    estado_embudo VARCHAR(40) NOT NULL DEFAULT 'Nuevo',
    motivo_cierre_tipo VARCHAR(30) NULL,
    motivo_cierre_detalle TEXT NULL,
    fecha_cierre_descarte TIMESTAMP NULL,
    disponibilidad_incorporacion VARCHAR(30) NULL,
    observaciones TEXT NULL,
    record_version INTEGER NOT NULL DEFAULT 1,
    created_by_user_id VARCHAR(36) NOT NULL,
    updated_by_user_id VARCHAR(36) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_postulacion_candidato FOREIGN KEY (candidato_id) REFERENCES candidatos(id) ON DELETE RESTRICT,
    CONSTRAINT fk_postulacion_reclutador FOREIGN KEY (reclutador_asignado_id) REFERENCES usuarios_rbac(id) ON DELETE RESTRICT,
    CONSTRAINT fk_postulacion_creador FOREIGN KEY (created_by_user_id) REFERENCES usuarios_rbac(id) ON DELETE RESTRICT,
    CONSTRAINT fk_postulacion_modificador FOREIGN KEY (updated_by_user_id) REFERENCES usuarios_rbac(id) ON DELETE SET NULL,
    CONSTRAINT chk_postulacion_fuente CHECK (fuente_origen IN ('Adecco', 'LinkedIn_Oficial', 'BYB_Referido', 'Offshore', 'Directo_Alumni', 'Bolsa_Web')),
    CONSTRAINT chk_postulacion_motivo CHECK (motivo_cierre_tipo IS NULL OR motivo_cierre_tipo IN ('Temporal_No_Excluyente', 'Excluyente_Permanente', 'Contratacion_Exitosa', 'Desistimiento'))
);
CREATE INDEX IF NOT EXISTS idx_postulaciones_candidato ON postulaciones_procesos(candidato_id);
CREATE INDEX IF NOT EXISTS idx_postulaciones_cliente ON postulaciones_procesos(cliente_cuenta);
CREATE INDEX IF NOT EXISTS idx_postulaciones_estado ON postulaciones_procesos(estado_embudo);
CREATE INDEX IF NOT EXISTS idx_postulaciones_reclutador ON postulaciones_procesos(reclutador_asignado_id);

-- 5. TABLA: screening_tecnico
CREATE TABLE IF NOT EXISTS screening_tecnico (
    id VARCHAR(36) PRIMARY KEY,
    postulacion_id VARCHAR(36) NOT NULL UNIQUE,
    evaluador_user_id VARCHAR(36) NOT NULL,
    fecha_hora_llamada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dim1_disponibilidad VARCHAR(30) NOT NULL,
    dim2_resumen_tecnico TEXT NOT NULL,
    dim3_expectativa_declarada REAL NOT NULL,
    dim4_interes_vacante VARCHAR(20) NOT NULL,
    dim5_modalidad_aceptada VARCHAR(20) NOT NULL,
    dim6_viabilidad_traslado VARCHAR(25) NOT NULL,
    dim6_alerta_distancia_nota VARCHAR(255) NULL,
    dim7_impresion_general TEXT NOT NULL,
    dictamen_humano VARCHAR(35) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_screening_postulacion FOREIGN KEY (postulacion_id) REFERENCES postulaciones_procesos(id) ON DELETE CASCADE,
    CONSTRAINT fk_screening_evaluador FOREIGN KEY (evaluador_user_id) REFERENCES usuarios_rbac(id) ON DELETE RESTRICT,
    CONSTRAINT chk_screening_modalidad CHECK (dim5_modalidad_aceptada IN ('Híbrido', 'Remoto', 'Presencial')),
    CONSTRAINT chk_screening_dictamen CHECK (dictamen_humano IN ('Avanza_Entrevista_Tecnica', 'No_Apto_Filtro_Inicial', 'Enfriar_En_Cartera'))
);

-- 6. TABLA: evaluacion_financiera_ctc
CREATE TABLE IF NOT EXISTS evaluacion_financiera_ctc (
    id VARCHAR(36) PRIMARY KEY,
    postulacion_id VARCHAR(36) NOT NULL UNIQUE,
    tipo_expectativa VARCHAR(10) NOT NULL DEFAULT 'Bruto',
    monto_declarado REAL NOT NULL,
    salario_bruto_mensual REAL NOT NULL,
    factor_ctc REAL NOT NULL DEFAULT 1.56,
    ctc_solicitado REAL NOT NULL,
    ctc_presupuestado REAL NULL,
    variacion_porcentual REAL NULL,
    semaforo_presupuestal VARCHAR(35) NOT NULL DEFAULT 'Pendiente_Presupuesto',
    requiere_aprobacion BOOLEAN NOT NULL DEFAULT 0,
    aprobado_por_user_id VARCHAR(36) NULL,
    justificacion_aprobacion TEXT NULL,
    evaluado_por_user_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ctc_postulacion FOREIGN KEY (postulacion_id) REFERENCES postulaciones_procesos(id) ON DELETE CASCADE,
    CONSTRAINT fk_ctc_aprobador FOREIGN KEY (aprobado_por_user_id) REFERENCES usuarios_rbac(id) ON DELETE SET NULL,
    CONSTRAINT fk_ctc_evaluador FOREIGN KEY (evaluado_por_user_id) REFERENCES usuarios_rbac(id) ON DELETE RESTRICT,
    CONSTRAINT chk_ctc_tipo CHECK (tipo_expectativa IN ('Bruto', 'Neto')),
    CONSTRAINT chk_ctc_semaforo CHECK (semaforo_presupuestal IN ('Dentro_Presupuesto', 'Requiere_Aprobacion', 'Fuera_Banda', 'Pendiente_Presupuesto'))
);

-- 7. TABLA: compliance_verificaciones
CREATE TABLE IF NOT EXISTS compliance_verificaciones (
    id VARCHAR(36) PRIMARY KEY,
    postulacion_id VARCHAR(36) NOT NULL UNIQUE,
    estado_bgc VARCHAR(30) NOT NULL DEFAULT 'Pendiente',
    fecha_solicitud_bgc TIMESTAMP NULL,
    fecha_cierre_bgc TIMESTAMP NULL,
    consulta_equifax_realizada BOOLEAN NOT NULL DEFAULT 0,
    tiene_deuda_castigada_banca BOOLEAN NOT NULL DEFAULT 0,
    es_elegible_compliance BOOLEAN NOT NULL DEFAULT 1,
    notas_compliance TEXT NULL,
    verificado_por_user_id VARCHAR(36) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_compliance_postulacion FOREIGN KEY (postulacion_id) REFERENCES postulaciones_procesos(id) ON DELETE CASCADE,
    CONSTRAINT fk_compliance_verificador FOREIGN KEY (verificado_por_user_id) REFERENCES usuarios_rbac(id) ON DELETE SET NULL,
    CONSTRAINT chk_compliance_bgc CHECK (estado_bgc IN ('Pendiente', 'En_Proceso', 'Aprobado', 'Observado_No_Apto'))
);

-- 8. TABLA: lotes_planilla_adecco
CREATE TABLE IF NOT EXISTS lotes_planilla_adecco (
    id VARCHAR(36) PRIMARY KEY,
    nombre_proveedor VARCHAR(60) NOT NULL DEFAULT 'Adecco',
    fecha_hora_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_carga_id VARCHAR(36) NOT NULL,
    nombre_archivo_original VARCHAR(255) NOT NULL,
    hash_archivo_sha256 VARCHAR(64) NOT NULL,
    total_filas INTEGER NOT NULL DEFAULT 0,
    cantidad_rojos_duplicados INTEGER NOT NULL DEFAULT 0,
    cantidad_amarillos_reactivables INTEGER NOT NULL DEFAULT 0,
    cantidad_verdes_limpios INTEGER NOT NULL DEFAULT 0,
    cantidad_alumni_detectados INTEGER NOT NULL DEFAULT 0,
    estado_procesamiento VARCHAR(30) NOT NULL DEFAULT 'Completado',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lote_usuario FOREIGN KEY (usuario_carga_id) REFERENCES usuarios_rbac(id) ON DELETE RESTRICT
);

-- 9. TABLA: reportes_cartera_exclusiones
CREATE TABLE IF NOT EXISTS reportes_cartera_exclusiones (
    id VARCHAR(36) PRIMARY KEY,
    destinatario VARCHAR(60) NOT NULL DEFAULT 'Adecco',
    fecha_hora_generacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_solicitante_id VARCHAR(36) NOT NULL,
    filtro_cuenta_cliente VARCHAR(100) NULL,
    total_registros_exportados INTEGER NOT NULL DEFAULT 0,
    periodo_vigencia_dias INTEGER NOT NULL DEFAULT 180,
    hash_archivo_sha256 VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reporte_usuario FOREIGN KEY (usuario_solicitante_id) REFERENCES usuarios_rbac(id) ON DELETE RESTRICT
);

-- 10. TABLA: bitacora_auditoria (APPEND-ONLY)
CREATE TABLE IF NOT EXISTS bitacora_auditoria (
    id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_id VARCHAR(36) NOT NULL,
    usuario_email VARCHAR(120) NOT NULL,
    rol_en_momento VARCHAR(40) NOT NULL,
    tipo_accion VARCHAR(35) NOT NULL,
    entidad_objeto VARCHAR(40) NOT NULL,
    registro_id VARCHAR(36) NOT NULL,
    version_registro INTEGER NULL,
    valores_previos_json TEXT NULL,
    valores_nuevos_json TEXT NULL,
    justificacion_operativa TEXT NULL,
    ip_address VARCHAR(45) NULL DEFAULT '127.0.0.1',
    session_id VARCHAR(64) NULL,
    nombre_archivo_adjunto VARCHAR(255) NULL,
    hash_integridad_sha256 VARCHAR(64) NULL,
    CONSTRAINT fk_auditoria_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios_rbac(id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_auditoria_timestamp ON bitacora_auditoria(timestamp);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON bitacora_auditoria(usuario_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_entidad ON bitacora_auditoria(entidad_objeto, registro_id);

-- TABLA AUXILIAR: cache_dni_reniec (Resiliencia Offline)
CREATE TABLE IF NOT EXISTS cache_dni_reniec (
    dni VARCHAR(8) PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100) NULL DEFAULT '',
    fecha_nacimiento DATE NULL,
    ubigeo VARCHAR(6) NULL,
    distrito VARCHAR(100) NULL,
    direccion VARCHAR(255) NULL,
    cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cache_dni ON cache_dni_reniec(dni);
```
