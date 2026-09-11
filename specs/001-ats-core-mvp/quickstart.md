# Quickstart & Validation Guide: ATS Core MVP

**Feature**: `001-ats-core-mvp` | **Date**: 2026-09-10 | **Status**: Approved  
**Documentation**: [spec.md](spec.md) | [research.md](research.md) | [data-model.md](data-model.md) | [contracts/](contracts/)  

---

## 1. Prerequisites & Environment Setup

### 1.1. System Requirements
- **Python**: Version 3.11+ (verified compatible with 3.12.x).
- **OS**: Windows / Linux / macOS (Zero Node.js, zero Docker, zero npm required).
- **Assets**: Verified presence of official logo in `assets/tcs_logo.png`.

### 1.2. Virtual Environment Setup
Execute the following commands in PowerShell from the repository root:

```powershell
# Create virtual environment if not already present
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install runtime dependencies
pip install streamlit sqlalchemy pydantic openpyxl pandas pypdf bcrypt rapidfuzz requests python-dotenv

# Optional AI engine dependencies
pip install langchain langchain-google-genai langchain-xai
```

### 1.3. Environment Configuration (`.env`)
Create or verify the `.env` file in the project root:

```env
# Database Configuration (Agnostic SQLite WAL for Local / Lab)
DATABASE_URL=sqlite:///ats_demo.db

# National Identity API (APIsPERU free tier token)
APISPERU_TOKEN=demo_token_or_real_key
APISPERU_BASE_URL=https://dniruc.apisperu.com/api/v1/dni

# AI Providers (Optional - fallback heurístico local activo por defecto)
GEMINI_API_KEY=
GROK_API_KEY=

# Security & Sessions
SECRET_KEY=tcs_secret_key_ats_core_mvp_2026
SESSION_TIMEOUT_MINUTES=30
```

---

## 2. Launching the Application

Run the Streamlit application (via entry point launcher):

```powershell
streamlit run src/app.py
# O alternativamente: streamlit run src/ui/app.py
```

Expected output:
```text
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

---

## 3. End-to-End Validation Scenarios

The following 6 sequential scenarios validate 100% of the User Stories, Acceptance Scenarios, and Success Criteria from [spec.md](spec.md).

### Scenario 1: Authentication, RBAC and Default Least-Privilege Role (User Story 6)
**Objective**: Prove that accounts are created with `@tcs.com` validation, initial role `Compliance_Officer` (read-only), and administrative elevation by `Head_of_Talent_Acquisition`.

1. **Step 1.1**: In the login screen, switch to the "Registro Corporativo" tab.
2. **Step 1.2**: Enter:
   - Nombres: `Carla Soto Mendoza`
   - Email: `carla.soto@tcs.com`
   - Contraseña: `Password123!` (exige mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número y 1 carácter especial)
3. **Step 1.3**: Click "Registrar Cuenta".
   - **Expected Outcome**: Account created with status `Activa` and default role `Compliance_Officer`.
4. **Step 1.4**: Log in with `carla.soto@tcs.com`.
   - **Expected Outcome**: Logged in successfully. Notice the UI header badge indicates `[Rol: Compliance_Officer (Solo Lectura)]`.
5. **Step 1.5**: Attempt to click "Nuevo Candidato" or edit any candidate field.
   - **Expected Outcome**: Action is prevented. Toast warning appears: *"Acceso denegado: su rol solo posee permisos de consulta y auditoría"*. A security event `Acceso_Denegado` is recorded in `bitacora_auditoria`.
6. **Step 1.6**: Log in as the pre-seeded bootstrap admin `admin.ta@tcs.com` (password: `Password123!`, con rol `Head_of_Talent_Acquisition` inicializado en la base de datos) and access "Panel de Usuarios".
7. **Step 1.7**: Elevate `carla.soto@tcs.com` to `Senior_Technical_Recruiter` providing justification: *"Asignación a célula de selección de banca BCP"*.
   - **Expected Outcome**: Role elevated. Audit log confirms `Modificacion_Rol` linked to the Head of TA.

---

### Scenario 2: Candidate Registration, DNI Autofill & E.164 Normalization (User Story 1 & 5)
**Objective**: Prove instant DNI resolution, dynamic age calculation (no 127 years bug), canonical phone formatting, and Boomerang detection.

1. **Step 2.1**: Log in as `carla.soto@tcs.com` (`Senior_Technical_Recruiter`).
2. **Step 2.2**: Navigate to "Ficha Única de Candidato" $\to$ "Nuevo Registro".
3. **Step 2.3**: Enter DNI: `76128709` and press `Tab` or click "Validar DNI".
   - **Expected Outcome**: System resolves identity in <5ms from local cache (or APIsPERU), autocompleting:
     - Nombres: `DIEGO ALONSO`
     - Apellido Paterno: `RAMOS`
     - Apellido Materno: `QUISPE`
     - Fecha de Nacimiento: `1995-04-12`
     - Distrito: `Santiago de Surco`
     - Edad calculada dinámicamente: `31 años` (cero cálculo estático de 127 años).
4. **Step 2.4**: Enter mobile phone: `989322088` (without prefix).
   - **Expected Outcome**: Number automatically reformats to `+51989322088`.
   - A clickable green button appears: `[Iniciar WhatsApp Web]`, containing pre-filled protocol message: *"Hola DIEGO ALONSO, te saluda Carla Soto del equipo de Selección de TCS Perú..."*.
5. **Step 2.5**: If the candidate matches `historial_alumni_tcs`, an alert badge appears:
   - **Expected Outcome**: Purple badge `[Candidato Boomerang: Ex-colaborador TCS (Cuenta Entel, 2022-2024) - Rehire Eligible]`.
6. **Step 2.6**: Save the candidate.
   - **Expected Outcome**: Stored in `candidatos`. An audit event `Creacion` is appended to `bitacora_auditoria` with user `carla.soto@tcs.com`.

---

### Scenario 3: Human-in-the-Loop Phone Screening (7 Dimensions) (User Story 1)
**Objective**: Prove structured capture of the recruiter phone screening call with geographic commute alerts.

1. **Step 3.1**: In the candidate file, open the "Screening Telefónico" tab.
2. **Step 3.2**: Fill in the 7 mandatory dimensions:
   - Dim 1 (Disponibilidad): `2 semanas`
   - Dim 2 (Resumen Técnico): `Fuerte dominio en Java 17, Spring Boot 3, Kafka y arquitecturas de microservicios`
   - Dim 3 (Expectativa Salarial): `S/. 6,500 Bruto`
   - Dim 4 (Interés en Vacante): `Alto`
   - Dim 5 (Modalidad Aceptada): `Híbrido (2 días oficina)`
   - Dim 6 (Viabilidad de Traslado): Candidate lives in `Villa María del Triunfo`, client office is in `La Molina`.
     - **Expected Outcome**: System displays caution alert: `[⚠️ Alerta de Conmutación Geográfica: Distancia estimada >90 minutos entre residencia y sede cliente]`.
   - Dim 7 (Impresión General): `Excelente articulación técnica y buena disposición para turnos de guardia`.
3. **Step 3.3**: Select sovereign Human Verdict: `Avanza a Entrevista Técnica`.
4. **Step 3.4**: Click "Guardar Validación Humana".
   - **Expected Outcome**: Record saved in `screening_tecnico`. Immutable audit record created linking Carla Soto as the sole human evaluator.

---

### Scenario 4: CTC 1.56 Financial Simulator with Division-by-Zero Guard (User Story 4)
**Objective**: Prove exact 1.56 multiplier under D.L. 728, Net-to-Gross conversion, and zero `#DIV/0!` errors.

1. **Step 4.1**: In the candidate file, navigate to "Simulador Financiero CTC".
2. **Step 4.2 (Gross Salary Test)**:
   - Select: `Bruto`
   - Enter Monto: `5000.00`
   - Presupuesto Rol: `10000.00`
   - **Expected Outcome**:
     - Salario Bruto: `S/. 5,000.00`
     - CTC Solicitado ($5000 \times 1.56$): `S/. 7,800.00`
     - Variación Presupuestal: `-22.00%`
     - Semáforo: 🟢 `Dentro de Presupuesto`
3. **Step 4.3 (Net to Gross Conversion Test)**:
   - Select: `Neto`
   - Enter Monto: `5000.00`
   - **Expected Outcome**:
     - Salario Bruto Proyectado ($5000 / 0.79$): `S/. 6,329.11`
     - CTC Solicitado ($6329.11 \times 1.56$): `S/. 9,873.41`
     - Variación Presupuestal: `-1.27%`
     - Semáforo: 🟢 `Dentro de Presupuesto`
4. **Step 4.4 (Division-by-Zero Guard Test)**:
   - Clear or set Presupuesto Rol to `0.00` (or leave empty).
   - **Expected Outcome**:
     - No `#DIV/0!` error generated.
     - Variación display: `N/A - Pendiente de Presupuesto`
     - Semáforo: ⚪ `Pendiente de Presupuesto`
5. **Step 4.5 (Out of Band Warning Test)**:
   - Enter Monto Bruto: `9000.00` with Presupuesto `10000.00` (CTC Solicitado: `14,040.00`, Variación: `+40.40%`).
   - **Expected Outcome**: Semáforo turns 🔴 `Fuera de Banda Salarial`. Checkbox `Requiere Aprobación Especial` is triggered.

---

### Scenario 5: Mass Adecco Spreadsheet Ingestion & Traffic Light Validation (User Story 2)
**Objective**: Process heterogenous spreadsheets with alias headers and classify candidates into 🔴 / 🟡 / 🟢 and 🟣 Alumni.

1. **Step 5.1**: Navigate to "Validador de Proveedores (Adecco)".
2. **Step 5.2**: Upload a sample Adecco Excel spreadsheet (`adecco_batch_sample.xlsx`) containing 20 rows.
3. **Step 5.3**: Click "Procesar Planilla Masiva".
   - **Expected Outcome** in <2 seconds:
     - Executive summary cards:
       * Total Procesados: `20`
       * 🔴 Duplicados Activos / Exclusiones: `7` (shows reason and responsible recruiter)
       * 🟡 Reactivables (>180 días): `3`
       * 🟢 Perfiles Limpios / Inéditos: `8`
       * 🟣 Ex-Colaboradores TCS Detectados: `2`
4. **Step 5.4**: Review the classified table. Verify that alias headers (`Móvil`, `DNI / CE`, `Puesto`) were automatically mapped without requiring manual changes to the Excel file.
5. **Step 5.5**: Click "Importar Candidatos Limpios (8)".
   - **Expected Outcome**: All 8 green candidates are batch-inserted in an atomic database transaction. Audit log registers `Carga_Archivo` and individual `Creacion` entries.

---

### Scenario 6: On-Demand Adecco Exclusion Report under Ley 29733 (User Story 3 & 6)
**Objective**: Generate the strictly censored 5-column report ensuring 0.00% privacy leakage.

1. **Step 6.1**: Navigate to "Reporte de Cartera y Exclusiones Adecco".
2. **Step 6.2**: Select client filter: `BCP` (or leave as `Todas las Cuentas`).
3. **Step 6.3**: Click "Generar Reporte Oficial de Exclusiones".
   - **Expected Outcome**: Download button appears for `reporte_exclusiones_adecco_20260910.xlsx`.
4. **Step 6.4**: Open the downloaded Excel file and inspect headers and contents.
   - **Expected Outcome**:
     - File contains **EXACTLY 5 COLUMNS**:
       1. `DNI`
       2. `Nombres y Apellidos`
       3. `Perfil`
       4. `Vigencia de Exclusión`
       5. `Estado`
     - **Strict Privacy Compliance (Ley N° 29733)**: 0.00% presence of telephone numbers, email addresses, requested salaries, client billing rates, or interview notes.
5. **Step 6.5**: Access "Consola Central de Auditoría".
   - **Expected Outcome**: Audit log confirms an `Exportacion` event recorded with user `carla.soto@tcs.com`, timestamp, and count of exported rows.

---

## 4. Automated Test Commands

To execute the automated unit and contract verification test suite:

```powershell
# Run contract tests (30/30 tests covering Pydantic schemas, triggers and DDL)
python -m pytest tests/contract -v

# Run all unit tests once implemented
python -m pytest tests/unit -v

# Run financial math tests with division-by-zero coverage
python -m pytest tests/contract/test_ctc_contracts.py -v

# Run DDL and trigger tests with physical immutability validation
python -m pytest tests/contract/test_database_ddl.py -v
```
