# Implementation Plan: ATS Core MVP (Erradicación de Fricción Manual y Gestión Centralizada)

**Branch**: `001-ats-core-mvp` | **Date**: 2026-09-10 | **Spec**: [specs/001-ats-core-mvp/spec.md](spec.md)  
**Input**: Feature specification from `specs/001-ats-core-mvp/spec.md`  
**Artifacts**: [research.md](research.md) | [data-model.md](data-model.md) | [quickstart.md](quickstart.md) | [contracts/](contracts/)  

---

## Summary

El proyecto **ATS Core MVP** erradica las 35 horas semanales de dolor operativo del equipo de Selección de TCS Perú (25h de registro manual de candidatos, 5h de actualización de estados y 5h de cruce manual de planillas con Adecco) mediante un sistema web corporativo estructurado bajo **Arquitectura Hexagonal (Puertos y Adaptadores)**.

El sistema implementa:
1. **Ficha Única de Candidato**: Autollenado instantáneo por DNI (<5ms desde caché local SQLite o servicio APIsPERU en tiempo real), cálculo dinámico de edad (eliminando el bug de 127 años), normalización canónica a formato E.164 (`+519XXXXXXXX`), botón interactivo de 1-clic hacia WhatsApp Web con mensaje protocolar, detección preventiva de duplicados y registro estructurado de las 7 dimensiones de la llamada humana de screening con alertas geográficas de conmutación.
2. **Extracción Estructurada de CVs y CUL**: Desacoplada mediante LangChain con soporte multi-proveedor para Google Gemini (`gemini-2.5-flash`) y xAI Grok (`grok-2`), estructurada mediante esquemas Pydantic v2 y blindada con un extractor heurístico local 100% offline (`pypdf` + regex), censurando todo atributo demográfico protegido (Principio V).
3. **Validador Masivo de Planillas de Adecco**: Ingesta tolerante a variaciones de encabezados (alias semánticos) con semáforo algorítmico instantáneo (🔴 Duplicado activo o exclusión permanente, 🟡 Reactivable >180 días, 🟢 Limpio/Inédito), detección cruzada de ex-colaboradores TCS (🟣 Insignia Boomerang) para evitar pago de comisiones indebidas, e importación atómica en lote.
4. **Generador a Demanda de Reporte de Cartera y Exclusiones**: Descarga en 1-clic con la estructura uniforme de exactamente **5 columnas oficiales** bajo estricta anonimización de la Ley N° 29733 (censura de remuneraciones, tarifas de clientes, teléfonos, correos y notas privadas).
5. **Simulador Financiero CTC (Factor 1.56)**: Basado en el régimen laboral privado peruano (D.L. 728) con conversión de neto a bruto (~21%), semáforo de viabilidad presupuestal y guardas matemáticas estrictas que garantizan una tasa de 0.00% del error `#DIV/0!`.
6. **Autenticación, RBAC y Bitácora Inmutable**: Control de acceso con 4 roles corporativos (`Head_of_Talent_Acquisition`, `Senior_Technical_Recruiter`, `Account_Recruitment_Coordinator`, `Compliance_Officer`), política de contraseñas, rol por defecto de mínimo privilegio, bloqueo por intentos fallidos y bitácora de auditoría *append-only* que asocia de forma obligatoria cada mutación, subida de archivos o exportación al usuario autenticado.

---

## Technical Context

- **Language/Version**: Python 3.12 (compatible con Python 3.11+).
- **Primary Dependencies**:
  * **Frontend / UI**: `streamlit>=1.38.0`, `openpyxl>=3.1.2`, `pandas>=2.2.0`.
  * **Persistencia & Validación**: `sqlalchemy>=2.0.30`, `pydantic>=2.8.0`, `python-dotenv>=1.0.1`.
  * **Seguridad & Hashing**: `bcrypt>=4.1.0` / `passlib[bcrypt]>=1.7.4`.
  * **Deduplicación & Parsing**: `rapidfuzz>=3.9.0`, `pypdf>=4.3.0`, `requests>=2.32.0`.
  * **Motor IA (Opcional)**: `langchain>=0.2.14`, `langchain-google-genai>=1.0.8`, `langchain-xai>=0.1.1`.
- **Storage**:
  * **Local / Lab**: SQLite local (`ats_demo.db`) con soporte WAL (`journal_mode=WAL`) y llaves foráneas forzadas (`PRAGMA foreign_keys = ON`).
  * **Producción Corporativa**: PostgreSQL 15+ mediante conmutación transparente vía `DATABASE_URL` en `.env` sin alteración del código de dominio.
- **Testing**: `pytest>=8.2.0`, `pytest-cov`, `pytest-mock` para suites unitarias, de contratos y de integración.
- **Target Platform**: Estaciones de trabajo corporativas y servidores en entornos restringidos de laboratorio (Windows 11 / Linux / macOS). Cero dependencias de Node.js, Docker o npm.
- **Project Type**: Aplicación Web empresarial en Python Streamlit con Arquitectura Hexagonal desacoplada en capas (Domain, Ports, Adapters, Services, UI).
- **Performance Goals**:
  * Resolución de DNI desde caché local: $< 5\text{ ms}$.
  * Validación masiva de Adecco: $< 100\text{ ms}$ por fila ($< 2\text{ s}$ para planillas de 50 filas).
  * Generación a demanda de reporte de cartera y exclusiones: $< 2\text{ s}$.
  * Cálculo dinámico de variación financiera CTC: $< 1\text{ ms}$ con $0.00\%$ errores `#DIV/0!`.
- **Constraints**:
  * **Supervisión Humana Innegociable (Principio I)**: Ningún modelo de IA descarta candidatos ni toma decisiones de contratación de manera autónoma.
  * **Anti-Scraping Estricto (Principio II)**: Cero automatización o scraping sobre LinkedIn Recruiter. Operación exclusiva sobre datos propios e importaciones oficiales autorizadas.
  * **Privacidad Ley N° 29733**: Prohibición de incluir teléfonos, correos o montos salariales en el reporte entregado a agencias externas.
  * **Inmutabilidad de Auditoría**: Estructura *append-only*; prohibidas operaciones `UPDATE` o `DELETE` sobre la bitácora histórica.
  * **Resiliencia Offline**: Continuidad operativa garantizada mediante caché local de identidad y modo de captura asistida ante ausencia de red.
- **Scale/Scope**: 10 entidades relacionales, 6 historias de usuario completas, 4 roles RBAC, soporte de >10,000 registros históricos y auditoría forense granular.

---

## Constitution Check

*GATE: Evaluation against the 5 principles of `.specify/memory/constitution.md`.*

| Principio Constitucional | Estado | Evidencia de Cumplimiento Técnico en el Plan |
|--------------------------|--------|----------------------------------------------|
| **I. Human-in-the-Loop Supremacy (Supervisión Humana Innegociable)** | **PASS** | Los modelos de IA (Gemini/Grok/Heurístico) operan estrictamente en modo asistente de extracción estructurada. La llamada de screening (7 dimensiones) y cualquier decisión de avance, rechazo o contratación es ejecutada soberanamente por un reclutador humano autenticado y registrada en `screening_tecnico` y `bitacora_auditoria`. |
| **II. Zero Web-Scraping & Legal Platform Compliance** | **PASS** | El sistema no incluye drivers Selenium, Playwright, Puppeteer ni scrapers headless. La ingesta de datos de candidatos externos se efectúa exclusivamente mediante importación de archivos autorizados (XLSX, CSV, PDF) y la API de APIsPERU. |
| **III. Relational Single Source of Truth (Erradicación de Hojas de Cálculo)** | **PASS** | Se reemplazan las 11 pestañas del Excel `BD GENERAL FY27` por 10 tablas normalizadas en SQLAlchemy 2.0. Teléfonos en formato canónico E.164 (`+519XXXXXXXX`), edad calculada dinámicamente desde `fecha_nacimiento` (cero cálculo estático de 127 años), y fórmulas CTC con guardas contra `#DIV/0!`. |
| **IV. Deduplicación Algorítmica y Control del Proveedor Externo** | **PASS** | Módulo `DeduplicationService` con cotejo exacto (DNI, teléfono, email) y fonético (Double Metaphone + Token Sort Ratio $\ge 85\%$). Generador a demanda de reporte de exclusión de 5 columnas oficiales para Adecco bajo Ley 29733. |
| **V. IA Ética, Explicable y Desprovista de Atributos Protegidos** | **PASS** | Los contratos Pydantic (`CVExtractionResult`) y prompts censuran explícitamente atributos protegidos (edad, género, estado civil, dirección domiciliaria o fotografías). La extracción se enfoca exclusivamente en habilidades técnicas, experiencia comprobable, educación y certificaciones. |

*Resultado del Gate*: **APROBADO SIN EXCEPCIONES**. No se registran violaciones constitucionales.

---

## Project Structure

### Documentation (Feature Directory: `specs/001-ats-core-mvp/`)

```text
specs/001-ats-core-mvp/
├── plan.md              # Plan técnico maestro de implementación (este documento)
├── research.md          # Decisiones de ingeniería y análisis de alternativas (Fase 0)
├── data-model.md        # Esquema relacional DDL de las 10 entidades y tablas auxiliares (Fase 1)
├── quickstart.md        # Guía de validación con escenarios ejecutables paso a paso (Fase 1)
├── contracts/           # Contratos de interfaz tipados y esquemas Pydantic v2 (Fase 1)
│   ├── __init__.py
│   ├── dni_contracts.py
│   ├── cv_parser_contracts.py
│   ├── adecco_contracts.py
│   ├── ctc_contracts.py
│   └── auth_audit_contracts.py
└── checklists/
    └── requirements.md  # Lista de verificación de requisitos del sistema
```

### Source Code Layout (Repository Root: `src/`)

```text
src/
├── domain/                      # Capa 1: Entidades de Dominio Puras y Reglas de Negocio
│   ├── __init__.py
│   ├── entities.py              # Clases de dominio (Candidato, Postulacion, Screening, CTC, etc.)
│   ├── exceptions.py            # Excepciones de negocio (DuplicateError, OptimisticLockError, etc.)
│   └── value_objects.py         # Teléfono E.164, DocumentoIdentidad, PorcentajeVariacion
│
├── ports/                       # Capa 2: Interfaces Abstractas y Contratos Hexagonales
│   ├── __init__.py
│   ├── dni_port.py              # Puerto de resolución de identidad DNI
│   ├── cv_parser_port.py        # Puerto de extracción documental (LangChain / Heurístico)
│   ├── adecco_port.py           # Puerto de validación de planillas y generación de exclusiones
│   ├── ctc_port.py              # Puerto de cálculo de compensaciones CTC
│   ├── auth_port.py             # Puerto de autenticación y RBAC
│   └── audit_port.py            # Puerto de bitácora inmutable de auditoría
│
├── adapters/                    # Capa 3: Adaptadores de Infraestructura Externa
│   ├── __init__.py
│   ├── persistence/             # Base de datos relacional SQLAlchemy 2.0
│   │   ├── __init__.py
│   │   ├── database.py          # Engine, SessionLocal, Base declarativa, soporte SQLite/PostgreSQL
│   │   ├── models.py            # Modelos ORM de las 10 entidades funcionales
│   │   └── repositories/        # Repositorios concretos (CandidatoRepo, AuditRepo, UserRepo, etc.)
│   │       ├── __init__.py
│   │       ├── candidato_repository.py
│   │       ├── postulacion_repository.py
│   │       ├── user_repository.py
│   │       └── audit_repository.py
│   ├── identity/                # Adaptador DNI (APIsPERU + Caché Local SQLite)
│   │   ├── __init__.py
│   │   └── apisperu_adapter.py
│   ├── cv_parser/               # Adaptadores de extracción de currículos
│   │   ├── __init__.py
│   │   ├── langchain_extractor.py # Adaptador LangChain para Google Gemini y xAI Grok
│   │   └── heuristic_extractor.py # Fallback heurístico local 100% offline con pypdf
│   ├── adecco/                  # Adaptador de planillas de proveedores
│   │   ├── __init__.py
│   │   ├── excel_validator.py   # Ingestor semántico con alias mapping
│   │   └── exclusion_exporter.py # Exportador de 5 columnas bajo Ley 29733
│   └── security/                # Criptografía y contraseñas
│       ├── __init__.py
│       └── password_hasher.py   # Bcrypt con salt aleatorio
│
├── services/                    # Capa 4: Casos de Uso y Servicios de Aplicación Orquestados
│   ├── __init__.py
│   ├── candidate_service.py     # Alta de ficha, autollenado DNI, normalización E.164, auditoría
│   ├── screening_service.py     # Registro de las 7 dimensiones de screening telefónico
│   ├── ctc_calculator_service.py# Simulador de Costo Empresa Factor 1.56 con guardas matemáticas
│   ├── deduplication_service.py # Deduplicador multicriterio (exacto + Double Metaphone)
│   ├── adecco_service.py        # Orquestación de ingesta masiva y semáforo 🔴/🟡/🟢
│   ├── auth_service.py          # Autenticación, bloqueo por intentos, gestión de roles RBAC
│   └── audit_service.py         # Registro atómico append-only y consulta forense
│
├── ui/                          # Capa 5: Interfaz de Usuario Web en Streamlit
│   ├── __init__.py
│   ├── app.py                   # Punto de entrada principal y enrutador de páginas
│   ├── session.py               # Gestión de estado de sesión (`st.session_state`) y guardas RBAC
│   ├── theme.py                 # Inyección de estilos CSS corporativos TCS y renderizado de logo
│   └── pages/                   # Módulos funcionales en pestañas/páginas
│       ├── __init__.py
│       ├── p1_ficha_candidato.py  # Ficha Única, DNI, WhatsApp, CV Upload, Alertas Geográficas
│       ├── p2_screening_llamada.py# Registro de validación humana de las 7 dimensiones
│       ├── p3_simulador_ctc.py    # Simulador financiero con Factor 1.56 y guardas #DIV/0!
│       ├── p4_validador_adecco.py # Ingesta de planillas masivas con semáforo y detección Boomerang
│       ├── p5_reporte_exclusion.py# Generador a demanda de reporte de 5 columnas (Ley 29733)
│       ├── p6_alumni_tcs.py       # Catálogo corporativo de ex-colaboradores (Boomerang)
│       ├── p7_consola_auditoria.py# Consola central de auditoría global y trazabilidad forense
│       └── p8_gestion_usuarios.py # Administración y elevación de roles (Head of TA)
│
└── config.py                    # Carga y validación de variables de entorno (.env)

tests/
├── conftest.py                  # Fixtures compartidos, base de datos SQLite en memoria
├── unit/                        # Pruebas unitarias de servicios y lógica de dominio
│   ├── test_ctc_calculator.py   # Pruebas de Factor 1.56, neto a bruto y guardas #DIV/0!
│   ├── test_deduplication.py    # Pruebas de Double Metaphone, token sort y remoción de partículas
│   ├── test_e164_normalizer.py  # Pruebas de normalización telefónica y enlace WhatsApp
│   ├── test_age_calculator.py   # Pruebas de cálculo dinámico de edad (cero candidatos 127 años)
│   └── test_rbac_security.py    # Pruebas de roles, contraseñas y permisos mínimos
├── contract/                    # Pruebas de contratos Pydantic y puertos
│   ├── test_dni_contracts.py
│   ├── test_cv_contracts.py
│   ├── test_adecco_contracts.py
│   └── test_ctc_contracts.py
└── integration/                 # Pruebas de integración end-to-end con base de datos
    ├── test_candidate_lifecycle.py
    ├── test_adecco_batch_import.py
    └── test_audit_immutability.py
```

---

## Complexity Tracking

| Decisión de Diseño | Justificación | Alternativa Descartada y Razón de Rechazo |
|--------------------|---------------|------------------------------------------|
| **Arquitectura Hexagonal en 5 Capas** | Desacopla la lógica de negocio (cálculos CTC, deduplicación, reglas de exclusión) de los detalles de infraestructura (Streamlit, SQLite/PostgreSQL, APIs externas). Permite probar el 100% de la lógica sin levantar la interfaz web. | **Script monolítico en Streamlit (`app.py` único)**: Produce acoplamiento extremo, dificulta pruebas automatizadas de regresión y viola principios de mantenibilidad empresarial. |
| **SQLAlchemy 2.0 con Repositorio Agnóstico** | Permite operar de forma inmediata en SQLite local durante laboratorios y evaluaciones locales, y conmutar a PostgreSQL en producción modificando solo `.env`. | **Consultas Raw SQL con `sqlite3`**: Código no tipado, riesgo de inyección SQL y requeriría reescribir consultas al pasar a PostgreSQL. |
| **Deduplicación Fonética (Double Metaphone + Token Sort)** | En Perú es común la inversión de nombres y apellidos ("Huanca, Alonso" vs "Alonso Huanca") y partículas ("De la Cruz"). El cotejo fonético con umbral del 85% resuelve falsos negativos. | **Coincidencia Exacta de Cadenas**: Fracasa en más del 40% de los candidatos duplicados que provienen de LinkedIn o planillas con orden alterado. |
| **Fallback Heurístico Local para Extracción de CVs** | Garantiza que el sistema funcione al 100% sin conexión a internet o cuando no se configuran llaves de API para Gemini o Grok. | **Dependencia estricta de APIs LLM externas**: Interrumpiría el registro de candidatos si se agota la cuota o si hay caída de red corporativa. |
| **Bitácora de Auditoría Append-Only en Tabla Relacional** | Asegura que cada mutación quede vinculada a un usuario de forma no repudiable para cumplir la Ley N° 29733 y los controles internos de TCS. | **Registro en archivos de texto plano (`.log`)**: No permite filtrado relacional, cruces con entidades ni exportación estructurada en la UI de auditoría. |

---

## Phase 0 & Phase 1 Execution Verification

- [x] **Phase 0 (Research)**: Documentado completamente en `specs/001-ats-core-mvp/research.md`. Se resolvieron todas las incógnitas técnicas sobre frontend Streamlit, persistencia SQLite/Postgres, DNI APIsPERU con resiliencia offline, extracción dual LangChain (Gemini/Grok) con fallback heurístico, patrón `IAfinanciero`, deduplicación fonética, semáforo de Adecco, reporte de 5 columnas bajo Ley 29733, fórmula CTC 1.56 y seguridad RBAC.
- [x] **Phase 1 (Data Model & Schema)**: Documentado en `specs/001-ats-core-mvp/data-model.md`. Incluye diccionario de datos y DDL relacional para las 10 entidades funcionales y la tabla auxiliar de caché, con llaves foráneas, restricciones de unicidad e índices.
- [x] **Phase 1 (Interface Contracts & Pydantic Schemas)**: Creados y compilados sin errores en `specs/001-ats-core-mvp/contracts/`:
  * `dni_contracts.py`
  * `cv_parser_contracts.py`
  * `adecco_contracts.py`
  * `ctc_contracts.py`
  * `auth_audit_contracts.py`
- [x] **Phase 1 (Quickstart & Validation Guide)**: Documentado en `specs/001-ats-core-mvp/quickstart.md`, detallando 6 escenarios secuenciales reproducibles que cubren el 100% de las historias de usuario de `spec.md`.
- [x] **Constitution Gate Re-evaluation**: Verificado post-diseño; todos los artefactos cumplen estrictamente los 5 principios de la Constitución.
