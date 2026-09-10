<!--
Sync Impact Report:
- Version change: template -> 1.0.0
- Ratified: 2026-09-10
- Principles defined:
  1. I. Human-in-the-Loop Supremacy (Supervisión Humana Innegociable)
  2. II. Zero Web-Scraping & Legal Platform Compliance (Cumplimiento Legal y Anti-Scraping)
  3. III. Relational Single Source of Truth (Erradicación de Hojas de Cálculo)
  4. IV. Deduplicación Algorítmica y Control del Proveedor Externo
  5. V. IA Ética, Explicable y Desprovista de Atributos Protegidos
- Added sections:
  - Architecture & Data Integrity Standards (Arquitectura en 7 Capas y Esquema PostgreSQL)
  - Spec-Driven Development Workflow & Quality Gates
- Governance: Procedimiento formal de enmiendas, versionado semántico y auditoría.
-->

# ATS TCS Constitution

## Core Principles

### I. Human-in-the-Loop Supremacy (Supervisión Humana Innegociable)
The system MUST ensure that AI models operate strictly in an assistive and structural capacity. Under no circumstances shall AI autonomously discard candidates, generate job offers, execute mass contact campaigns, or make hiring decisions. The phone screening call (and its 7 validation objectives: availability, technical validation, CTC expectation, interest, work modality, commute viability, and candidate impression) MUST be conducted 100% by human recruiters.

### II. Zero Web-Scraping & Legal Platform Compliance
The system MUST NOT implement browser automation, headless browser crawlers, or unofficial screen scrapers targeting LinkedIn Recruiter or any third-party job portal. All external platform interoperability MUST occur exclusively through official partner APIs (e.g., LinkedIn RSC, Apply Connect) or authorized file imports/exports (XLSX, CSV, PDF). System operations MUST strictly adhere to vendor quotas, including LinkedIn's 300 export limit per user/month on 1-Click Export.

### III. Relational Single Source of Truth (Erradicación de Hojas de Cálculo)
The system MUST eradicate the multi-sheet manual Excel ecosystem (specifically `BD GENERAL FY27` and its 11 sheets) and enforce a normalized relational schema in PostgreSQL. Phone numbers MUST be normalized and stored strictly under the canonical E.164 format (`+519XXXXXXXX`). Age MUST be dynamically calculated via `AGE(fecha_nacimiento)` and NEVER manually hardcoded or offset. Financial formulas (CTC Factor 1.56) MUST include division-by-zero guards to prevent corrupted states (`#DIV/0!`).

### IV. Deduplicación Algorítmica y Control del Proveedor Externo
The system MUST provide real-time multi-criteria deduplication upon candidate entry (exact match by document ID, email, and normalized phone; fuzzy matching on full name to eliminate typo/accent variations). The system MUST automatically generate periodic Exclusion Reports for external recruitment agencies (Adecco) prior to sourcing cycles, preventing duplicated efforts and redundant candidate contact.

### V. IA Ética, Explicable y Desprovista de Atributos Protegidos
AI matching, ranking, and scoring modules MUST provide explainable justifications (*Fit & Gaps* analysis) detailing which requirements are met and which are missing against the Job Description. AI scoring algorithms MUST NEVER consider or process protected demographic attributes (age, gender, marital status, home address, or photo) as screening or filtering criteria. AI-generated historical discard summaries MUST be concise and auditable.

## Architecture & Data Integrity Standards

### Seven-Layer Decoupled Architecture
All application components MUST adhere to the 7-layer architecture:
1. **Intake Layer**: Standardized web intake for job descriptions (RGS/JD) with strict skill taxonomy.
2. **Authorized Data Layer**: Centralized PostgreSQL database and encrypted candidate CV document store.
3. **TCS AI Engine**: Resume parsing, semantic embeddings, and explainable scoring modules.
4. **Orchestration & Workflow Layer**: Event-driven state machine managing status lifecycles, SLAs, and ownership.
5. **Official Connectors Layer**: File ingestors (Adecco sheets) and standard export adapters.
6. **Security & Governance Layer**: Role-Based Access Control (RBAC), SSO authentication, audit logging, and encryption at rest and in transit.
7. **Analytics & Funnel Layer**: Real-time metrics dashboard tracking the 17-variable recruitment funnel and operational savings.

### Data Normalization Schema
The database MUST map the 28 columns of the legacy operational Excel into 5 core normalized entities:
* `candidatos`: Core identity, document number (UNIQUE), E.164 phone (UNIQUE), email (UNIQUE), calculated age, TCS alumni status.
* `postulaciones_procesos`: Process lifecycle, candidate ID (FK), client account, RGS/vacancy ID, recruiter ID (FK), source (Adecco, Offshore, BYB, LinkedIn), fiscal quarter, and status.
* `evaluacion_financiera_ctc`: CTC calculations with standard factor 1.56, requested salary, budgeted salary, and safe budget variance percentages.
* `compliance_verificaciones`: Background check (BGC) statuses, credit bureau check (Equifax) audit, and compliance timestamps.
* `screening_tecnico`: Recruiter call feedback, technical competency notes, and structured screening records.

## Spec-Driven Development Workflow & Quality Gates

### Spec-Driven Development Lifecycle
Development MUST follow the official GitHub Spec Kit workflow:
1. **Specification First**: No production code may be created without an approved feature specification (`spec.md`) defining user requirements and acceptance criteria.
2. **Architecture & Technical Plan**: Technical details, schemas, and API contracts MUST be isolated within `plan.md`.
3. **Atomic Task Breakdown**: Tasks in `tasks.md` MUST be granular, sequenced, and independently testable.
4. **Verification Gates**: Every module MUST provide automated unit and integration tests validating all acceptance criteria before being marked complete.

## Governance

This Constitution supersedes any temporary operational practice or unapproved design pattern. Any proposed amendment to this Constitution requires formal documentation of intent, impact analysis, and approval.
- **MAJOR version bump**: Redefinition or removal of any core principle or legal compliance rule.
- **MINOR version bump**: Addition of new principles, architectural layers, or significant workflow expansions.
- **PATCH version bump**: Wording clarifications, typo fixes, or non-semantic adjustments.

**Version**: 1.0.0 | **Ratified**: 2026-09-10 | **Last Amended**: 2026-09-10
