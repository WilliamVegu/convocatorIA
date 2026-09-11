# Tasks: ATS Core MVP (Erradicación de Fricción Manual y Gestión Centralizada)

**Input**: Design documents from `specs/001-ats-core-mvp/`  
**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required for user stories), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)  
**Methodology**: Test-Driven Development (TDD) - Las pruebas unitarias y de integración se definen primero para fallar antes de la implementación de cada componente.  
**Organization**: Tareas agrupadas por fases de infraestructura y ordenadas por dependencias estrictas de historias de usuario (US6 → US1 → US2 → US5 → US3 → US4) para garantizar entrega incremental y testing autónomo.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecución en paralelo permitida (archivos independientes, sin bloqueos de dependencias).
- **[Story]**: Etiqueta de historia de usuario (`[US1]`, `[US2]`, `[US3]`, `[US4]`, `[US5]`, `[US6]`).
- Todas las descripciones contienen rutas exactas de archivos y citas textuales de restricciones normativas y de base de datos.

---

## Phase 1: Setup del Proyecto y Entorno (Shared Infrastructure)

**Purpose**: Inicialización del entorno de desarrollo, paquetes de la arquitectura hexagonal, dependencias y configuración transversal.

- [ ] T001 Inicializar la estructura completa de paquetes Python del proyecto creando los directorios y archivos `__init__.py` en `src/domain/`, `src/ports/`, `src/adapters/persistence/repositories/`, `src/adapters/identity/`, `src/adapters/cv_parser/`, `src/adapters/adecco/`, `src/adapters/security/`, `src/services/`, `src/ui/pages/`, `tests/unit/`, `tests/integration/`, `scripts/` y `data/` según la arquitectura hexagonal definida en [plan.md](plan.md).
- [ ] T002 [P] Definir el archivo de dependencias de producción y desarrollo en `requirements.txt` especificando versiones mínimas verificadas (`streamlit>=1.38.0`, `sqlalchemy>=2.0.30`, `pydantic>=2.8.0`, `openpyxl>=3.1.2`, `pandas>=2.2.0`, `pypdf>=4.3.0`, `bcrypt>=4.1.0`, `rapidfuzz>=3.9.0`, `requests>=2.32.0`, `python-dotenv>=1.0.1`, `pytest>=8.2.0`, `pytest-cov`, `langchain>=0.2.14`, `langchain-google-genai>=1.0.8`, `langchain-xai>=0.1.1`).
- [ ] T003 [P] Crear el módulo de configuración y carga de entorno en `src/config.py` con validación para `DATABASE_URL` (default `sqlite:///ats_demo.db`), `APISPERU_TOKEN`, `APISPERU_BASE_URL` (`https://dniruc.apisperu.com/api/v1/dni`), `GEMINI_API_KEY`, `GROK_API_KEY`, `SECRET_KEY`, `SESSION_TIMEOUT_MINUTES=30`, y crear el archivo plantilla `.env.example` en la raíz del repositorio.
- [ ] T004 [P] Implementar el módulo centralizado de logging estructurado en `src/logger.py` con formato ISO 8601, rotación de archivos (`ats_system.log`) y salida estándar formateada para consola corporativa.

---

## Phase 2: Infraestructura y Persistencia de Base de Datos (Foundational Prerequisites)

**Purpose**: Capa relacional centralizada que erradica las 11 pestañas de `BD GENERAL FY27` y sirve de soporte bloqueante para todas las historias de usuario.

**⚠️ CRITICAL**: Ninguna historia de usuario puede persistir datos sin la finalización de esta fase fundacional.

- [ ] T005 [P] Implementar el gestor agnóstico de conexiones y fábrica de sesiones SQLAlchemy 2.0 en `src/adapters/persistence/database.py` con soporte para SQLite WAL (`journal_mode = WAL`, `foreign_keys = ON`, `busy_timeout = 5000`) y conmutación transparente a PostgreSQL 15+ a través de `DATABASE_URL`.
- [ ] T006 Implementar los modelos ORM de SQLAlchemy 2.0 en `src/adapters/persistence/models.py` para las 10 entidades funcionales y la tabla auxiliar de caché, transcribiendo las restricciones verbatim de [data-model.md](data-model.md):
  - `usuarios_rbac`: `id VARCHAR(36) PRIMARY KEY`, `nombres_completos VARCHAR(150) NOT NULL`, `email VARCHAR(120) NOT NULL UNIQUE`, `hashed_password VARCHAR(255) NOT NULL`, `rol VARCHAR(40) NOT NULL DEFAULT 'Compliance_Officer'` con restricción de check de roles (`Head_of_Talent_Acquisition`, `Senior_Technical_Recruiter`, `Account_Recruitment_Coordinator`, `Compliance_Officer`), `estado_cuenta VARCHAR(25) NOT NULL DEFAULT 'Activa'`, `intentos_fallidos INTEGER NOT NULL DEFAULT 0`, `bloqueado_hasta TIMESTAMP NULL`, `ultimo_login TIMESTAMP NULL`, `autorizado_por_id VARCHAR(36) NULL FK usuarios_rbac(id)`, `record_version INTEGER NOT NULL DEFAULT 1`.
  - `candidatos`: `id VARCHAR(36) PRIMARY KEY`, `tipo_documento VARCHAR(15) NOT NULL DEFAULT 'DNI'`, `numero_documento VARCHAR(20) NOT NULL UNIQUE`, `nombres VARCHAR(100) NOT NULL`, `apellido_paterno VARCHAR(100) NOT NULL`, `apellido_materno VARCHAR(100) NULL DEFAULT ''`, `nombres_completos_normalizado VARCHAR(255) NOT NULL`, `telefono_e164 VARCHAR(20) NOT NULL UNIQUE`, `email VARCHAR(120) NOT NULL UNIQUE`, `fecha_nacimiento DATE NULL`, `ubigeo VARCHAR(6) NULL`, `departamento VARCHAR(50) NULL DEFAULT 'Lima'`, `provincia VARCHAR(50) NULL DEFAULT 'Lima'`, `distrito_residencia VARCHAR(100) NULL`, `direccion_residencia VARCHAR(255) NULL`, `is_tcs_alumni BOOLEAN NOT NULL DEFAULT 0`, `alumni_id VARCHAR(36) NULL FK historial_alumni_tcs(id)`, `estado_identidad VARCHAR(40) NOT NULL DEFAULT 'Validado_Oficialmente'`, `regularizacion_pendiente BOOLEAN NOT NULL DEFAULT 0`, `cv_documento_url VARCHAR(500) NULL`, `cv_hash_sha256 VARCHAR(64) NULL`, `cv_resumen_tecnico TEXT NULL`, `cv_anios_experiencia REAL NULL`, `cv_idiomas_json JSON NULL`, `record_version INTEGER NOT NULL DEFAULT 1`, `created_by_user_id VARCHAR(36) NOT NULL FK usuarios_rbac(id)`, `updated_by_user_id VARCHAR(36) NULL FK usuarios_rbac(id)`.
  - `postulaciones_procesos`: `id VARCHAR(36) PRIMARY KEY`, `candidato_id VARCHAR(36) NOT NULL FK candidatos(id) ON DELETE RESTRICT`, `cliente_cuenta VARCHAR(100) NOT NULL`, `rgs_vacante_id VARCHAR(50) NOT NULL`, `perfil_tecnico VARCHAR(120) NOT NULL`, `reclutador_asignado_id VARCHAR(36) NOT NULL FK usuarios_rbac(id) ON DELETE RESTRICT`, `fuente_origen VARCHAR(50) NOT NULL CHECK IN ('Adecco', 'LinkedIn_Oficial', 'BYB_Referido', 'Offshore', 'Directo_Alumni', 'Bolsa_Web')`, `trimestre_fiscal VARCHAR(10) NOT NULL`, `estado_embudo VARCHAR(40) NOT NULL DEFAULT 'Nuevo'` con check de estados de embudo, `motivo_cierre_tipo VARCHAR(30) NULL CHECK IN ('Temporal_No_Excluyente', 'Excluyente_Permanente', 'Contratacion_Exitosa', 'Desistimiento')`, `motivo_cierre_detalle TEXT NULL`, `fecha_cierre_descarte TIMESTAMP NULL`, `record_version INTEGER NOT NULL DEFAULT 1`, `created_by_user_id VARCHAR(36) NOT NULL FK usuarios_rbac(id)`.
  - `screening_tecnico`: `id VARCHAR(36) PRIMARY KEY`, `postulacion_id VARCHAR(36) NOT NULL UNIQUE FK postulaciones_procesos(id) ON DELETE CASCADE`, `evaluador_user_id VARCHAR(36) NOT NULL FK usuarios_rbac(id) ON DELETE RESTRICT`, `fecha_hora_llamada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`, `dim1_disponibilidad VARCHAR(30) NOT NULL`, `dim2_resumen_tecnico TEXT NOT NULL`, `dim3_expectativa_declarada REAL NOT NULL`, `dim4_interes_vacante VARCHAR(20) NOT NULL`, `dim5_modalidad_aceptada VARCHAR(20) NOT NULL CHECK IN ('Híbrido', 'Remoto', 'Presencial')`, `dim6_viabilidad_traslado VARCHAR(25) NOT NULL`, `dim6_alerta_distancia_nota VARCHAR(255) NULL`, `dim7_impresion_general TEXT NOT NULL`, `dictamen_humano VARCHAR(35) NOT NULL CHECK IN ('Avanza_Entrevista_Tecnica', 'No_Apto_Filtro_Inicial', 'Enfriar_En_Cartera')`.
  - `evaluacion_financiera_ctc`: `id VARCHAR(36) PRIMARY KEY`, `postulacion_id VARCHAR(36) NOT NULL UNIQUE FK postulaciones_procesos(id) ON DELETE CASCADE`, `tipo_expectativa VARCHAR(10) NOT NULL DEFAULT 'Bruto' CHECK IN ('Bruto', 'Neto')`, `monto_declarado REAL NOT NULL`, `salario_bruto_mensual REAL NOT NULL`, `factor_ctc REAL NOT NULL DEFAULT 1.56`, `ctc_solicitado REAL NOT NULL`, `ctc_presupuestado REAL NULL`, `variacion_porcentual REAL NULL`, `semaforo_presupuestal VARCHAR(35) NOT NULL DEFAULT 'Pendiente_Presupuesto' CHECK IN ('Dentro_Presupuesto', 'Requiere_Aprobacion', 'Fuera_Banda', 'Pendiente_Presupuesto')`, `requiere_aprobacion BOOLEAN NOT NULL DEFAULT 0`, `aprobado_por_user_id VARCHAR(36) NULL FK usuarios_rbac(id)`, `justificacion_aprobacion TEXT NULL`, `evaluado_por_user_id VARCHAR(36) NOT NULL FK usuarios_rbac(id)`.
  - `compliance_verificaciones`: `id VARCHAR(36) PRIMARY KEY`, `postulacion_id VARCHAR(36) NOT NULL UNIQUE FK postulaciones_procesos(id) ON DELETE CASCADE`, `estado_bgc VARCHAR(30) NOT NULL DEFAULT 'Pendiente' CHECK IN ('Pendiente', 'En_Proceso', 'Aprobado', 'Observado_No_Apto')`, `fecha_solicitud_bgc TIMESTAMP NULL`, `fecha_cierre_bgc TIMESTAMP NULL`, `consulta_equifax_realizada BOOLEAN NOT NULL DEFAULT 0`, `tiene_deuda_castigada_banca BOOLEAN NOT NULL DEFAULT 0`, `es_elegible_compliance BOOLEAN NOT NULL DEFAULT 1`, `notas_compliance TEXT NULL`, `verificado_por_user_id VARCHAR(36) NULL FK usuarios_rbac(id)`.
  - `historial_alumni_tcs`: `id VARCHAR(36) PRIMARY KEY`, `tipo_documento VARCHAR(15) NOT NULL DEFAULT 'DNI'`, `numero_documento VARCHAR(20) NOT NULL UNIQUE`, `nombres_completos VARCHAR(200) NOT NULL`, `nombres_normalizado VARCHAR(200) NOT NULL`, `email_corporativo_historico VARCHAR(120) NULL`, `fecha_ingreso DATE NULL`, `fecha_cese DATE NOT NULL`, `ultima_cuenta_proyecto VARCHAR(100) NULL`, `motivo_desvinculacion VARCHAR(150) NULL`, `estatus_recontratacion VARCHAR(35) NOT NULL DEFAULT 'Rehire_Eligible' CHECK IN ('Rehire_Eligible', 'Do_Not_Rehire', 'Requiere_Aprobacion_RRHH')`.
  - `lotes_planilla_adecco`: `id VARCHAR(36) PRIMARY KEY`, `nombre_proveedor VARCHAR(60) NOT NULL DEFAULT 'Adecco'`, `fecha_hora_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`, `usuario_carga_id VARCHAR(36) NOT NULL FK usuarios_rbac(id)`, `nombre_archivo_original VARCHAR(255) NOT NULL`, `hash_archivo_sha256 VARCHAR(64) NOT NULL`, `total_filas INTEGER NOT NULL DEFAULT 0`, `cantidad_rojos_duplicados INTEGER NOT NULL DEFAULT 0`, `cantidad_amarillos_reactivables INTEGER NOT NULL DEFAULT 0`, `cantidad_verdes_limpios INTEGER NOT NULL DEFAULT 0`, `cantidad_alumni_detectados INTEGER NOT NULL DEFAULT 0`, `estado_procesamiento VARCHAR(30) NOT NULL DEFAULT 'Completado'`.
  - `reportes_cartera_exclusiones`: `id VARCHAR(36) PRIMARY KEY`, `destinatario VARCHAR(60) NOT NULL DEFAULT 'Adecco'`, `fecha_hora_generacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`, `usuario_solicitante_id VARCHAR(36) NOT NULL FK usuarios_rbac(id)`, `filtro_cuenta_cliente VARCHAR(100) NULL`, `total_registros_exportados INTEGER NOT NULL DEFAULT 0`, `periodo_vigencia_dias INTEGER NOT NULL DEFAULT 180`, `hash_archivo_sha256 VARCHAR(64) NOT NULL`.
  - `bitacora_auditoria`: `id VARCHAR(36) PRIMARY KEY`, `timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`, `usuario_id VARCHAR(36) NOT NULL FK usuarios_rbac(id)`, `usuario_email VARCHAR(120) NOT NULL`, `rol_en_momento VARCHAR(40) NOT NULL`, `tipo_accion VARCHAR(35) NOT NULL`, `entidad_objeto VARCHAR(40) NOT NULL`, `registro_id VARCHAR(36) NOT NULL`, `version_registro INTEGER NULL`, `valores_previos_json TEXT NULL`, `valores_nuevos_json TEXT NULL`, `justificacion_operativa TEXT NULL`, `ip_address VARCHAR(45) NULL DEFAULT '127.0.0.1'`, `session_id VARCHAR(64) NULL`, `nombre_archivo_adjunto VARCHAR(255) NULL`, `hash_integridad_sha256 VARCHAR(64) NULL`.
  - `cache_dni_reniec`: `dni VARCHAR(8) PRIMARY KEY`, `nombres VARCHAR(100) NOT NULL`, `apellido_paterno VARCHAR(100) NOT NULL`, `apellido_materno VARCHAR(100) NULL DEFAULT ''`, `fecha_nacimiento DATE NULL`, `ubigeo VARCHAR(6) NULL`, `distrito VARCHAR(100) NULL`, `direccion VARCHAR(255) NULL`, `cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`.
- [ ] T007 Implementar la lógica de creación DDL y triggers SQL de inmutabilidad en `src/adapters/persistence/ddl.py`, instalando `trg_prevent_update_bitacora` y `trg_prevent_delete_bitacora` para abortar físicamente cualquier intento de `UPDATE` o `DELETE` sobre `bitacora_auditoria`.
- [ ] T008 Implementar el inicializador y seeder de bootstrap administrativo en `src/adapters/persistence/seed.py`, creando el usuario fundacional `usr-admin-bootstrap-001` (`admin.ta@tcs.com`, `Head_of_Talent_Acquisition`, hash de `Password123!`) y el primer asiento de auditoría en `bitacora_auditoria`.
- [ ] T009 [P] Implementar las clases de excepciones tipadas del dominio en `src/domain/exceptions.py` (`EntityNotFoundError`, `DuplicateEntityError`, `OptimisticLockError`, `AuthenticationError`, `AccountLockedError`, `InsufficientPermissionsError`, `AuditIntegrityError`, `FinancialValidationError`).
- [ ] T010 [P] Implementar los objetos de valor (Value Objects) inmutables en `src/domain/value_objects.py` (`TelefonoE164`, `DocumentoIdentidad`, `EmailCorporativo`, `PorcentajeVariacion`, `MonedaPEN`).

**Checkpoint**: Base de datos, esquemas relacionales, triggers de inmutabilidad y usuario administrador inicial listos y verificables con `pytest tests/contract/test_database_ddl.py`.

---

## Phase 3: Implementación de Historias de Usuario (Metodología TDD)

### Phase 3.1: User Story 6 - Autenticación, RBAC y Bitácora Inmutable (Priority: P1)

**Goal**: Proveer autenticación segura con bcrypt, restricción de dominios `@tcs.com`, asignación inicial del rol de mínimo privilegio (`Compliance_Officer`), bloqueo preventivo por 5 intentos fallidos, elevación formal de roles por `Head_of_Talent_Acquisition` y trazabilidad append-only transversal.

**Independent Test**: Registrar una cuenta `@tcs.com`, verificar que inicia con rol `Compliance_Officer` en modo solo lectura, comprobar que al intentar mutar datos se bloquea y se asienta `Acceso_Denegado`, elevar el rol con el usuario admin y verificar que cada mutación asienta en `bitacora_auditoria` con usuario, timestamp y deltas JSON.

#### Tests para User Story 6 (TDD - Escribir primero y verificar fallo)

- [ ] T011 [P] [US6] Escribir pruebas unitarias de hashing bcrypt, validación de contraseñas complejas y bloqueo de cuentas en `tests/unit/test_rbac_security.py`.
- [ ] T012 [P] [US6] Escribir pruebas de integración para la inmutabilidad física y no repudiación de `bitacora_auditoria` en `tests/integration/test_audit_immutability.py`.

#### Implementación para User Story 6

- [ ] T013 [P] [US6] Definir las interfaces abstractas de puertos en `src/ports/auth_port.py` (`AuthPort`) y `src/ports/audit_port.py` (`AuditPort`).
- [ ] T014 [P] [US6] Implementar el hasher de contraseñas con bcrypt en `src/adapters/security/password_hasher.py` (`hash_password`, `verify_password`, validación de 8+ caracteres, mayúscula, minúscula, número y símbolo).
- [ ] T015 [P] [US6] Implementar el repositorio de usuarios corporativos en `src/adapters/persistence/repositories/user_repository.py` (`get_by_email`, `get_by_id`, `create_user`, `update_user_role`, `increment_failed_attempts`, `reset_failed_attempts`, `lock_account_until`).
- [ ] T016 [P] [US6] Implementar el repositorio append-only de auditoría en `src/adapters/persistence/repositories/audit_repository.py` (`append_log`, `list_logs`, `filter_logs` con filtros por usuario, entidad, tipo de acción y fechas; sin métodos de actualización o borrado).
- [ ] T017 [US6] Implementar el servicio de aplicación `AuthService` en `src/services/auth_service.py` (registro restringido a `@tcs.com`, rol default `Compliance_Officer`, bloqueo tras 5 intentos fallidos por 15 minutos, verificación de credenciales, y delegación de elevación de roles).
- [ ] T018 [US6] Implementar el servicio de auditoría `AuditService` en `src/services/audit_service.py` (`record_mutation`, `record_file_upload`, `record_export`, `record_security_event` persistiendo el usuario actor, rol, entidad, deltas JSON antes/después y justificación).

**Checkpoint**: Autenticación, RBAC y auditoría plenamente funcionales. Todas las historias posteriores inyectarán `AuditService` y `AuthService`.

---

### Phase 3.2: User Story 1 - Ficha Única de Candidato, DNI, E.164, CV Parsing y Screening Humano (Priority: P1) 🎯 MVP

**Goal**: Erradicar las 25 horas semanales de transcripción manual en `BD GENERAL FY27` mediante la Ficha Única: autollenado por DNI (<5ms desde caché local o APIsPERU), cálculo dinámico de edad (erradicando los 127 años del Excel), normalización canónica E.164 (`+519XXXXXXXX`), enlace interactivo a WhatsApp Web con mensaje protocolar, extracción estructurada de CVs con LangChain Gemini/Grok y fallback heurístico local `pypdf`, alerta de conmutación geográfica y registro de las 7 dimensiones de la llamada humana.

**Independent Test**: Registrar a un candidato ingresando DNI `76128709`, verificar autollenado y cálculo de edad real, ingresar teléfono `989322088` verificando conversión a `+51989322088` y botón WhatsApp, cargar un CV en PDF verificando extracción estructurada censurando atributos protegidos, y registrar las 7 dimensiones de la llamada con alerta geográfica de traslado.

#### Tests para User Story 1 (TDD - Escribir primero y verificar fallo)

- [ ] T019 [P] [US1] Escribir pruebas unitarias de normalización telefónica canónica E.164 y generación de URLs de WhatsApp Web en `tests/unit/test_e164_normalizer.py`.
- [ ] T020 [P] [US1] Escribir pruebas unitarias de cálculo dinámico de edad sin año bisiesto ni offsets estáticos en `tests/unit/test_age_calculator.py`.
- [ ] T021 [P] [US1] Escribir pruebas unitarias del extractor heurístico local de CVs en `tests/unit/test_cv_heuristic_parser.py`.

#### Implementación para User Story 1

- [ ] T022 [P] [US1] Definir las interfaces de puertos para DNI (`DNIPort`) en `src/ports/dni_port.py` y extractor de CVs (`CVParserPort`) en `src/ports/cv_parser_port.py`.
- [ ] T023 [P] [US1] Implementar el adaptador de identidad nacional en `src/adapters/identity/apisperu_adapter.py` consultando en primer orden `cache_dni_reniec`, en segundo orden el endpoint de APIsPERU (`https://dniruc.apisperu.com/api/v1/dni/`), persistiendo resultados en caché, y degradando a captura manual con marca `Pendiente_Regularizacion` ante fallas de red.
- [ ] T024 [P] [US1] Implementar el extractor heurístico local 100% offline basado en `pypdf` y diccionarios de habilidades tecnológicas en `src/adapters/cv_parser/heuristic_extractor.py`.
- [ ] T025 [P] [US1] Implementar el extractor LangChain multi-proveedor (soporte dual para `ChatGoogleGenerativeAI` con `gemini-2.5-flash` y `ChatXAI` con `grok-2` usando structured outputs Pydantic) en `src/adapters/cv_parser/langchain_extractor.py`.
- [ ] T026 [P] [US1] Implementar el repositorio de candidatos en `src/adapters/persistence/repositories/candidato_repository.py` (`get_by_id`, `get_by_dni`, `get_by_phone`, `get_by_email`, `create`, `update` con control de concurrencia optimista `record_version`).
- [ ] T027 [P] [US1] Implementar el repositorio de postulaciones y screening en `src/adapters/persistence/repositories/postulacion_repository.py` (`create_postulacion`, `update_postulacion_status`, `create_screening`, `get_screening_by_postulacion`).
- [ ] T028 [P] [US1] Implementar la matriz de distancias y cálculo de alerta geográfica de conmutación en `src/services/commute_matrix.py` (evaluando distrito de residencia vs. sede cliente, e.g. VMT a La Molina >90 min emitiendo `Alerta_Distancia_Critica`).
- [ ] T029 [US1] Implementar el servicio de aplicación `CandidateService` en `src/services/candidate_service.py` (orquestación de consulta DNI, cálculo de edad, normalización E.164, prevención de duplicados exactos, parsing de CV y registro de auditoría).
- [ ] T030 [US1] Implementar el servicio de aplicación `ScreeningService` en `src/services/screening_service.py` (registro de las 7 dimensiones humanas, alerta geográfica de traslado, dictamen soberano HITL y vinculación obligatoria al evaluador autenticado).

**Checkpoint**: Ficha Única, DNI, WhatsApp, CV Parsing y Screening Humano completados e independientemente verificables.

---

### Phase 3.3: User Story 2 - Validador Masivo de Planillas de Adecco con Semáforo Algorítmico (Priority: P2)

**Goal**: Erradicar las 5 horas semanales de cotejo manual de planillas con Adecco (Proceso 3) mediante ingesta tolerante a alias de encabezados, semáforo algorítmico instantáneo (🔴 Duplicado activo o exclusión permanente, 🟡 Reactivable >180 días con causa subsanable, 🟢 Inédito) e importación atómica en lote.

**Independent Test**: Cargar una planilla de prueba de 20 registros, verificar la clasificación exacta de cada fila en los colores del semáforo con su justificación en <5 segundos, y confirmar la importación de perfiles limpios verificando el registro de auditoría del lote.

#### Tests para User Story 2 (TDD - Escribir primero y verificar fallo)

- [ ] T031 [P] [US2] Escribir pruebas unitarias de deduplicación fonética y similitud de cadenas (Double Metaphone y Token Sort Ratio >=85%) en `tests/unit/test_deduplication.py`.
- [ ] T032 [P] [US2] Escribir pruebas de integración de ingesta masiva e importación atómica de lotes en `tests/integration/test_adecco_batch_import.py`.

#### Implementación para User Story 2

- [ ] T033 [P] [US2] Implementar el servicio de deduplicación multicriterio en `src/services/deduplication_service.py` (cotejo exacto DNI/email/E.164, remoción de partículas en nombres y similitud fonética con `rapidfuzz`).
- [ ] T034 [P] [US2] Definir el puerto de procesamiento de planillas externas (`AdeccoPort`) en `src/ports/adecco_port.py`.
- [ ] T035 [P] [US2] Implementar el adaptador de ingesta Excel con mapeo semántico de alias (`Móvil`/`Celular` → `telefono_raw`, `DNI`/`Documento` → `documento_raw`, `Puesto`/`Perfil` → `perfil_raw`) en `src/adapters/adecco/excel_validator.py`.
- [ ] T036 [US2] Implementar el servicio de aplicación `AdeccoService` en `src/services/adecco_service.py` (evaluación algorítmica de planillas, reglas de semáforo 🔴/🟡/🟢, detección de causas de exclusión permanente, importación atómica en lote y registro en `lotes_planilla_adecco` y `bitacora_auditoria`).

**Checkpoint**: Ingesta masiva y semáforo de Adecco operativos e integrables.

---

### Phase 3.4: User Story 5 - Detección Automática de Candidatos Boomerang (Alumni TCS) (Priority: P5)

**Goal**: Identificar automáticamente si un candidato laboró previamente en TCS Perú mediante DNI, correo corporativo histórico o reconciliación fonética, desplegando un distintivo púrpura (🟣 "Ex-Colaborador TCS"), visualizando su estatus de recontratabilidad y bloqueando el pago de comisiones indebidas a agencias externas.

**Independent Test**: Consultar un candidato que figure en `historial_alumni_tcs`, comprobar que se despliega la insignia Boomerang con los datos del último proyecto y estatus `Rehire_Eligible`, o advertencia de compliance si es `Do_Not_Rehire`.

#### Tests para User Story 5 (TDD - Escribir primero y verificar fallo)

- [ ] T037 [P] [US5] Escribir pruebas unitarias de coincidencia exacta y fonética contra el catálogo Alumni en `tests/unit/test_boomerang_detection.py`.

#### Implementación para User Story 5

- [ ] T038 [P] [US5] Implementar el repositorio corporativo de alumni en `src/adapters/persistence/repositories/alumni_repository.py` (`get_by_dni`, `get_by_email`, `search_by_normalized_name`, `list_all`).
- [ ] T039 [US5] Implementar el servicio `AlumniService` en `src/services/alumni_service.py` (detección automática de ex-colaboradores, validación de condiciones de salida y emisión del dictamen Boomerang).

**Checkpoint**: Detección Boomerang operativa tanto en la Ficha Única como en el Validador Masivo de Adecco.

---

### Phase 3.5: User Story 3 - Generador a Demanda de Reporte de Cartera y Exclusiones para Adecco (Priority: P3)

**Goal**: Generar y descargar en 1-clic el reporte oficial para Adecco con exactamente 5 columnas (`DNI`, `Nombres y Apellidos`, `Perfil`, `Vigencia de Exclusión`, `Estado`), garantizando el estricto cumplimiento de la Ley N° 29733 mediante la censura absoluta de salarios, teléfonos, correos y notas privadas.

**Independent Test**: Generar el reporte oficial en Excel, verificar que contiene exactamente las 5 columnas acordadas, 0.00% presencia de datos de contacto o remuneraciones, opción de filtrado por cuenta cliente y registro de auditoría de la exportación.

#### Tests para User Story 3 (TDD - Escribir primero y verificar fallo)

- [ ] T040 [P] [US3] Escribir pruebas unitarias de anonimización estricta bajo Ley N° 29733 (censura de correos, teléfonos y montos monetarios) en `tests/unit/test_exclusion_report_censorship.py`.

#### Implementación para User Story 3

- [ ] T041 [P] [US3] Implementar el exportador de 5 columnas oficiales en `src/adapters/adecco/exclusion_exporter.py` utilizando `openpyxl`/`pandas` con estilos y anchos de columna corporativos.
- [ ] T042 [US3] Implementar el servicio de aplicación `ExclusionReportService` en `src/services/exclusion_report_service.py` (compilación de cartera activa y exclusiones temporales <180 días, soporte de filtro por cliente o consolidado, manejo de reporte vacío limpio y registro en `reportes_cartera_exclusiones`).

**Checkpoint**: Reporte de 5 columnas para Adecco generado a demanda con censura legal verificada.

---

### Phase 3.6: User Story 4 - Simulador Financiero CTC Factor 1.56 con Guardas Matemáticas (Priority: P4)

**Goal**: Simulación precisa de Costo Empresa bajo el régimen laboral peruano D.L. 728 con Factor 1.56, conversión de neto a bruto (`/ 0.79`), semáforo de viabilidad presupuestal y guardas matemáticas estrictas que garantizan 0.00% de errores `#DIV/0!`.

**Independent Test**: Ingresar salario bruto de S/. 5,000 con presupuesto S/. 10,000 obteniendo CTC S/. 7,800 (-22.00% 🟢); salario neto de S/. 5,000 obteniendo bruto proyectado S/. 6,329.11 y CTC S/. 9,873.41 (-1.27% 🟢); y presupuesto 0 o vacío obteniendo estado "Pendiente de Presupuesto" sin error matemático.

#### Tests para User Story 4 (TDD - Escribir primero y verificar fallo)

- [ ] T043 [P] [US4] Escribir pruebas unitarias exhaustivas de cálculo CTC Factor 1.56, conversión neto a bruto con tasa 21% y guardas de división por cero en `tests/unit/test_ctc_calculator.py`.

#### Implementación para User Story 4

- [ ] T044 [P] [US4] Definir el puerto de compensaciones laborales (`CTCPort`) en `src/ports/ctc_port.py`.
- [ ] T045 [US4] Implementar el servicio de cálculo financiero `CTCCalculatorService` en `src/services/ctc_calculator_service.py` (multiplicador 1.56, conversión neto/bruto, guarda contra presupuesto $\le 0$, semáforo de 3 niveles y advertencia de rangos atípicos).

**Checkpoint**: Todas las historias de usuario de dominio (US6, US1, US2, US5, US3, US4) implementadas y testeadas en capas de Dominio, Puertos, Adaptadores y Servicios.

---

## Phase 4: Frontend Streamlit con Branding Oficial TCS

**Purpose**: Presentación visual integrada mediante interfaz web interactiva en Python Streamlit con identidad corporativa de TCS y control de acceso.

- [ ] T046 Implementar el gestor de estado de sesión, autenticación y guardas RBAC en `src/ui/session.py` (persistencia en `st.session_state` de `user_id`, `email`, `rol`, expiración por inactividad a los 30 minutos y verificadores de permisos por rol).
- [ ] T047 [P] Implementar el tema corporativo TCS en `src/ui/theme.py` inyectando estilos CSS (Deep Navy `#0A192F`, Vibrant Blue `#0076CE`, Cyan Accent `#00B4D8`, Magenta Accent `#E91E63`, semáforos `#2ECC71`, `#F1C40F`, `#E74C3C`, `#9B59B6`), renderizado del logo oficial `assets/tcs_logo.png` y badges de estado.
- [ ] T048 Implementar la pantalla de Login corporativo en `src/ui/pages/p0_login.py` (formulario de inicio de sesión con correo `@tcs.com`, pestaña de registro institucional con asignación de `Compliance_Officer`, y botones de acceso rápido de 1-clic para roles demo: Head of TA, Senior Recruiter, Coordinator y Compliance Officer).
- [ ] T049 Implementar la vista de Ficha Única de Candidato en `src/ui/pages/p1_ficha_candidato.py` (formulario reactivo con autollenado por DNI, normalización E.164, botón interactivo de WhatsApp Web, subida de CV con parsing asistido, detección preventiva de duplicados y badge Boomerang).
- [ ] T050 Implementar la vista de Screening Telefónico HITL en `src/ui/pages/p2_screening_llamada.py` (formulario estructurado de las 7 dimensiones, alerta visual de conmutación geográfica de transporte y registro del dictamen humano con autoría indivisible).
- [ ] T051 Implementar la vista del Simulador Financiero CTC en `src/ui/pages/p3_simulador_ctc.py` (selectores Bruto/Neto, cálculo reactivo en vivo de Factor 1.56, tarjetas de métricas, semáforo presupuestal y trámite de excepciones salariales).
- [ ] T052 Implementar la vista del Validador de Planillas de Adecco en `src/ui/pages/p4_validador_adecco.py` (arrastrar y soltar archivo Excel/CSV, tarjetas ejecutivas del semáforo 🔴/🟡/🟢 y 🟣 Boomerang, tabla interactiva con filtros e importación atómica de candidatos limpios).
- [ ] T053 Implementar la vista de Generación de Reporte de Cartera y Exclusiones en `src/ui/pages/p5_reporte_exclusion.py` (selector de cliente o consolidado general, visualización previa de las 5 columnas censuradas y botón de descarga directa en Excel).
- [ ] T054 Implementar la vista del Catálogo Alumni TCS en `src/ui/pages/p6_alumni_tcs.py` (búsqueda de ex-colaboradores, consulta de estatus de recontratabilidad y registro de nuevos alumni).
- [ ] T055 Implementar la Consola Central de Auditoría en vivo en `src/ui/pages/p7_consola_auditoria.py` (tabla interactiva con refresco en vivo, filtros por usuario, entidad, acción y fechas, inspector de diferencias JSON y botón de exportación).
- [ ] T056 Implementar el Panel de Administración de Usuarios y Roles en `src/ui/pages/p8_gestion_usuarios.py` (restringido a `Head_of_Talent_Acquisition`, listado de operadores, elevación de roles RBAC con justificación obligatoria y desbloqueo de cuentas).
- [ ] T057 Implementar el punto de entrada principal y enrutador en `src/ui/app.py` y el script lanzador de raíz en `src/app.py` (menú de navegación por pestañas condicionales según el rol RBAC, barra superior con identificación de usuario y botón de cierre de sesión).

---

## Phase 5: Datos Semilla de Demostración y Lanzador de 1-Clic

**Purpose**: Suministro de datos de prueba hiper-realistas y lanzador para una experiencia demo impecable sin configuración manual.

- [ ] T058 [P] Generar el archivo de personas sintéticas peruanas calibradas en `data/demo_personas.json` (DNIs válidos de 8 dígitos, fechas de nacimiento, distritos de Lima y perfiles de competencias para precargar en la caché local de DNI).
- [ ] T059 [P] Generar la planilla de prueba de Adecco calibrada en `data/Adecco_Semana_37.xlsx` con 20 filas estructuradas con alias de columnas (`Móvil`, `DNI / CE`, `Puesto`) conteniendo casos para 🔴 duplicados activos, 🟡 reactivables >180 días, 🟢 inéditos limpios y 🟣 alumni TCS.
- [ ] T060 [P] Crear el script de carga de datos históricos representativos de `BD GENERAL FY27` en `scripts/seed_historical_data.py` para poblar el pool corporativo con >100 candidatos y casos de prueba del quickstart.
- [ ] T061 [P] Crear el script lanzador unificado de 1-clic para Windows en `run_demo.bat` (verificación de Python, activación de `.venv`, instalación de dependencias faltantes, ejecución del bootstrap seed y apertura automática de Streamlit en el navegador).

---

## Phase 6: Verificación de Integración y Tests End-to-End

**Purpose**: Verificación formal automatizada del 100% de los flujos del sistema y cumplimiento de criterios de aceptación.

- [ ] T062 [P] Implementar la suite de pruebas de integración del ciclo de vida del candidato en `tests/integration/test_candidate_lifecycle.py` (alta de ficha, validación DNI, normalización E.164, screening de 7 dimensiones, cálculo CTC y auditoría).
- [ ] T063 [P] Implementar la suite de pruebas de integración de control de acceso y seguridad en `tests/integration/test_rbac_integration.py` (bloqueo de escritura a Compliance Officer, elevación autorizada por Head of TA y auditoría de permisos).
- [ ] T064 Implementar la suite de validación de los 6 escenarios del quickstart en `tests/integration/test_quickstart_scenarios.py` (verificando secuencialmente Escenarios 1 al 6 de [quickstart.md](quickstart.md)).
- [ ] T065 Ejecutar la suite completa de pruebas unitarias, de contratos y de integración (`pytest tests/ -v --cov=src`), verificando el paso del 100% de los tests y emitiendo el reporte consolidado de cobertura.

---

## Dependencies & Execution Order

### Phase Dependencies

```text
[Phase 1: Setup]
       │
       ▼
[Phase 2: Foundational & DB Infrastructure] ──(BLOCKS ALL USER STORIES)
       │
       ├────────────────────────┬────────────────────────┐
       ▼                        ▼                        ▼
[Phase 3.1: US6 Auth/Audit]    [Phase 3.2: US1 Ficha]   [Phase 3.4: US5 Boomerang]
       │                                │                        │
       ▼                                ▼                        │
[Phase 3.3: US2 Validador Adecco] ◄─────┴────────────────────────┘
       │
       ├────────────────────────┐
       ▼                        ▼
[Phase 3.5: US3 Exclusiones]   [Phase 3.4: US4 Simulador CTC]
       │                        │
       └────────────────────────┘
                    │
                    ▼
[Phase 4: Frontend Streamlit & UI]
                    │
                    ▼
[Phase 5: Datos Semilla & Launcher]
                    │
                    ▼
[Phase 6: Verificación de Integración & E2E]
```

### User Story Dependencies

1. **User Story 6 (Auth & Audit - P1)**: Depende de Phase 2. Es el cimiento de autoría para todas las demás historias.
2. **User Story 1 (Ficha Única - P1 🎯 MVP)**: Depende de US6 para auditar la creación de candidatos y screening.
3. **User Story 2 (Validador Adecco - P2)**: Depende de US1 (repositorio de candidatos para deduplicar) y US5 (catálogo alumni).
4. **User Story 5 (Boomerang Alumni - P5)**: Depende de Phase 2. Puede implementarse en paralelo con US1 y enriquece a US1 y US2.
5. **User Story 3 (Reporte Exclusiones - P3)**: Depende de US1 y US2 (cartera de candidatos y estados de postulación).
6. **User Story 4 (Simulador CTC - P4)**: Depende de US1 (postulaciones de candidatos y expectativas salariales).

### Parallel Opportunities

- **Phase 1**: `T002`, `T003`, `T004` pueden ejecutarse en paralelo tras `T001`.
- **Phase 2**: `T005`, `T009`, `T010` pueden ejecutarse en paralelo con la definición de modelos en `T006`.
- **Phase 3 (TDD Tests)**: Las pruebas `T011`, `T012`, `T019`, `T020`, `T021`, `T031`, `T037`, `T040`, `T043` pueden redactarse en paralelo.
- **Phase 3 (Servicios y Adaptadores)**: Los adaptadores `T014`, `T015`, `T023`, `T024`, `T025`, `T033`, `T035`, `T038`, `T041` son independientes a nivel de archivo.
- **Phase 4**: `T047` (CSS y Branding) puede construirse en paralelo con las páginas de UI.
- **Phase 5**: `T058`, `T059`, `T060`, `T061` pueden desarrollarse en paralelo.

---

## Parallel Example: User Story 1 (Ficha Única MVP)

```bash
# Redactar pruebas unitarias en paralelo:
Task T019: "tests/unit/test_e164_normalizer.py"
Task T020: "tests/unit/test_age_calculator.py"
Task T021: "tests/unit/test_cv_heuristic_parser.py"

# Implementar adaptadores y puertos en paralelo:
Task T022: "src/ports/dni_port.py" y "src/ports/cv_parser_port.py"
Task T023: "src/adapters/identity/apisperu_adapter.py"
Task T024: "src/adapters/cv_parser/heuristic_extractor.py"
Task T025: "src/adapters/cv_parser/langchain_extractor.py"
Task T026: "src/adapters/persistence/repositories/candidato_repository.py"
Task T027: "src/adapters/persistence/repositories/postulacion_repository.py"
```

---

## Implementation Strategy

### MVP First (Fase 1 + Fase 2 + US6 + US1)

1. Completar **Phase 1 (Setup)** y **Phase 2 (Foundational & DB)**.
2. Implementar **US6 (Autenticación y Auditoría)** para garantizar que cada acción tenga autoría no repudiable.
3. Implementar **US1 (Ficha Única de Candidato y Screening HITL)**.
4. **STOP & VALIDATE**: Ejecutar `tests/integration/test_candidate_lifecycle.py` y probar la Ficha Única en Streamlit (`p1_ficha_candidato.py` y `p2_screening_llamada.py`).
5. Con esto se erradican inmediatamente **25 de las 35 horas semanales** de sobrecarga operativa (Proceso 1).

### Incremental Delivery

1. **Incremento 1 (MVP)**: Ficha Única + DNI + WhatsApp + CV Parsing + Screening Humano (US1 + US6).
2. **Incremento 2 (Proveedores)**: Validador Masivo de Adecco con semáforo 🔴/🟡/🟢 + Detección Boomerang (US2 + US5). Erradica 5 horas semanales adicionales (Proceso 3).
3. **Incremento 3 (Regulación & Finanzas)**: Reporte oficial de 5 columnas bajo Ley 29733 (US3) + Simulador CTC 1.56 sin `#DIV/0!` (US4). Erradica fricciones salariales y riesgos legales.
4. **Incremento 4 (Consolidación Demo)**: Consola de auditoría, panel administrativo de roles, datasets de prueba y script `run_demo.bat`.

---

## Traceability & Requirements Mapping Table

| ID Tarea | Fase / Story | Componente Afectado | Ruta de Archivo | Requisito Cubierto |
|:---------|:-------------|:-------------------|:----------------|:-------------------|
| `T001` | Phase 1: Setup | Project Layout | `src/` | Estructura Hexagonal |
| `T002` | Phase 1: Setup | Dependencies | `requirements.txt` | Python 3.12 stack |
| `T003` | Phase 1: Setup | Configuration | `src/config.py`, `.env.example` | Variables de entorno |
| `T004` | Phase 1: Setup | Logging | `src/logger.py` | Logger estructurado |
| `T005` | Phase 2: DB | Persistence Engine | `src/adapters/persistence/database.py` | SQLite WAL / Postgres |
| `T006` | Phase 2: DB | ORM Entities | `src/adapters/persistence/models.py` | 10 tablas relacionales |
| `T007` | Phase 2: DB | Immutability DDL | `src/adapters/persistence/ddl.py` | Triggers append-only |
| `T008` | Phase 2: DB | Bootstrap Seeder | `src/adapters/persistence/seed.py` | Admin bootstrap |
| `T009` | Phase 2: DB | Domain Exceptions | `src/domain/exceptions.py` | Excepciones de negocio |
| `T010` | Phase 2: DB | Value Objects | `src/domain/value_objects.py` | Objetos de valor |
| `T011` | Phase 3.1: US6 | Security Unit Tests | `tests/unit/test_rbac_security.py` | Pruebas RBAC TDD |
| `T012` | Phase 3.1: US6 | Audit Integration Tests | `tests/integration/test_audit_immutability.py` | Pruebas Auditoría TDD |
| `T013` | Phase 3.1: US6 | Ports | `src/ports/auth_port.py`, `src/ports/audit_port.py` | Puertos Auth y Audit |
| `T014` | Phase 3.1: US6 | Cryptography | `src/adapters/security/password_hasher.py` | Hashing Bcrypt |
| `T015` | Phase 3.1: US6 | User Repository | `src/adapters/persistence/repositories/user_repository.py` | Gestión de usuarios |
| `T016` | Phase 3.1: US6 | Audit Repository | `src/adapters/persistence/repositories/audit_repository.py` | Repositorio append-only |
| `T017` | Phase 3.1: US6 | Auth Service | `src/services/auth_service.py` | RBAC y bloqueo cuentas |
| `T018` | Phase 3.1: US6 | Audit Service | `src/services/audit_service.py` | Trazabilidad integral |
| `T019` | Phase 3.2: US1 | E.164 Tests | `tests/unit/test_e164_normalizer.py` | Pruebas E.164 TDD |
| `T020` | Phase 3.2: US1 | Age Tests | `tests/unit/test_age_calculator.py` | Pruebas Edad TDD |
| `T021` | Phase 3.2: US1 | CV Parser Tests | `tests/unit/test_cv_heuristic_parser.py` | Pruebas Parser TDD |
| `T022` | Phase 3.2: US1 | Ports | `src/ports/dni_port.py`, `src/ports/cv_parser_port.py` | Puertos DNI y CV |
| `T023` | Phase 3.2: US1 | Identity Adapter | `src/adapters/identity/apisperu_adapter.py` | APIsPERU y Caché |
| `T024` | Phase 3.2: US1 | Heuristic Extractor | `src/adapters/cv_parser/heuristic_extractor.py` | Fallback offline pypdf |
| `T025` | Phase 3.2: US1 | LangChain Extractor | `src/adapters/cv_parser/langchain_extractor.py` | Gemini / Grok Parser |
| `T026` | Phase 3.2: US1 | Candidate Repo | `src/adapters/persistence/repositories/candidato_repository.py` | Persistencia Candidatos |
| `T027` | Phase 3.2: US1 | Process Repo | `src/adapters/persistence/repositories/postulacion_repository.py` | Persistencia Procesos |
| `T028` | Phase 3.2: US1 | Commute Domain | `src/services/commute_matrix.py` | Alerta Geográfica |
| `T029` | Phase 3.2: US1 | Candidate Service | `src/services/candidate_service.py` | Ficha Única |
| `T030` | Phase 3.2: US1 | Screening Service | `src/services/screening_service.py` | Screening 7D HITL |
| `T031` | Phase 3.3: US2 | Deduplication Tests | `tests/unit/test_deduplication.py` | Pruebas Fonéticas TDD |
| `T032` | Phase 3.3: US2 | Batch Import Tests | `tests/integration/test_adecco_batch_import.py` | Pruebas Ingesta TDD |
| `T033` | Phase 3.3: US2 | Deduplication Service | `src/services/deduplication_service.py` | Cotejo fonético |
| `T034` | Phase 3.3: US2 | Adecco Port | `src/ports/adecco_port.py` | Puerto Proveedores |
| `T035` | Phase 3.3: US2 | Excel Ingestor | `src/adapters/adecco/excel_validator.py` | Mapeo de alias Excel |
| `T036` | Phase 3.3: US2 | Adecco Service | `src/services/adecco_service.py` | Semáforo 🔴/🟡/🟢 |
| `T037` | Phase 3.4: US5 | Boomerang Tests | `tests/unit/test_boomerang_detection.py` | Pruebas Alumni TDD |
| `T038` | Phase 3.4: US5 | Alumni Repo | `src/adapters/persistence/repositories/alumni_repository.py` | Persistencia Alumni |
| `T039` | Phase 3.4: US5 | Alumni Service | `src/services/alumni_service.py` | Detección Boomerang |
| `T040` | Phase 3.5: US3 | Censorship Tests | `tests/unit/test_exclusion_report_censorship.py` | Pruebas Ley 29733 TDD |
| `T041` | Phase 3.5: US3 | Exclusion Exporter | `src/adapters/adecco/exclusion_exporter.py` | Excel 5 columnas |
| `T042` | Phase 3.5: US3 | Exclusion Service | `src/services/exclusion_report_service.py` | Reporte a demanda |
| `T043` | Phase 3.6: US4 | CTC Calculator Tests | `tests/unit/test_ctc_calculator.py` | Pruebas CTC TDD |
| `T044` | Phase 3.6: US4 | CTC Port | `src/ports/ctc_port.py` | Puerto Compensaciones |
| `T045` | Phase 3.6: US4 | CTC Service | `src/services/ctc_calculator_service.py` | Factor 1.56 y guardas |
| `T046` | Phase 4: UI | Session Manager | `src/ui/session.py` | Sesión y RBAC UI |
| `T047` | Phase 4: UI | Theme & Styling | `src/ui/theme.py` | TCS CSS e identidad |
| `T048` | Phase 4: UI | Login View | `src/ui/pages/p0_login.py` | Login y 1-clic demo |
| `T049` | Phase 4: UI | Ficha Candidato View | `src/ui/pages/p1_ficha_candidato.py` | Ficha Única UI |
| `T050` | Phase 4: UI | Screening View | `src/ui/pages/p2_screening_llamada.py` | Screening 7D UI |
| `T051` | Phase 4: UI | CTC Simulator View | `src/ui/pages/p3_simulador_ctc.py` | Simulador CTC UI |
| `T052` | Phase 4: UI | Adecco View | `src/ui/pages/p4_validador_adecco.py` | Validador Adecco UI |
| `T053` | Phase 4: UI | Exclusions View | `src/ui/pages/p5_reporte_exclusion.py` | Reporte Exclusiones UI |
| `T054` | Phase 4: UI | Alumni View | `src/ui/pages/p6_alumni_tcs.py` | Catálogo Alumni UI |
| `T055` | Phase 4: UI | Audit Console View | `src/ui/pages/p7_consola_auditoria.py` | Consola Auditoría UI |
| `T056` | Phase 4: UI | User Management View | `src/ui/pages/p8_gestion_usuarios.py` | Gestión de Usuarios UI |
| `T057` | Phase 4: UI | Main App Router | `src/ui/app.py`, `src/app.py` | Navegación Streamlit |
| `T058` | Phase 5: Demo | Seed Personas | `data/demo_personas.json` | Dataset DNI local |
| `T059` | Phase 5: Demo | Seed Adecco Excel | `data/Adecco_Semana_37.xlsx` | Planilla calibrada |
| `T060` | Phase 5: Demo | Historical Seeder | `scripts/seed_historical_data.py` | Poblado inicial BD |
| `T061` | Phase 5: Demo | Unified Launcher | `run_demo.bat` | Script 1-clic demo |
| `T062` | Phase 6: E2E | Lifecycle Integration | `tests/integration/test_candidate_lifecycle.py` | Test integración Ficha |
| `T063` | Phase 6: E2E | RBAC Integration | `tests/integration/test_rbac_integration.py` | Test integración RBAC |
| `T064` | Phase 6: E2E | Quickstart Validation | `tests/integration/test_quickstart_scenarios.py` | Test 6 escenarios |
| `T065` | Phase 6: E2E | Full Test Suite | `tests/` | Cobertura total pytest |

---

## Notes

- **Formato Estricto**: Cada tarea comienza con `- [ ]`, seguida de su ID secuencial (`T001` a `T065`), indicador opcional `[P]`, etiqueta de historia (para historias de usuario `[US1]`, `[US2]`, `[US3]`, `[US4]`, `[US5]`, `[US6]`) y descripción precisa con ruta de archivo.
- **TDD Riguroso**: En cada fase de historia de usuario, las tareas de redacción de pruebas preceden a las tareas de implementación.
- **Inmutabilidad de Auditoría**: Cualquier mutación física de `bitacora_auditoria` está bloqueada a nivel de base de datos por los triggers `trg_prevent_update_bitacora` y `trg_prevent_delete_bitacora`.
- **Cero Web Scraping (Principio II)**: Cero navegadores headless o scrapers de LinkedIn; interoperabilidad exclusiva vía archivos autorizados y API REST oficial de APIsPERU.
- **Supervisión Humana (Principio I)**: Ningún modelo de IA descarta candidatos ni toma decisiones; las 7 dimensiones y el dictamen de screening son 100% de autoría y ejecución humana.
