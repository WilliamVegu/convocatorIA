# Technical Research & Architecture Decisions: ATS Core MVP

**Feature**: `001-ats-core-mvp` | **Date**: 2026-09-10 | **Status**: Approved  
**Project**: ATS TCS Perú - Talent Acquisition Engine & Candidate Lifecycle Management  

---

## Executive Summary

Este documento consolida las decisiones de ingeniería, arquitectura técnica y componentes seleccionados para implementar la **Fase 3 (`speckit-plan`)** del `001-ats-core-mvp`. La meta técnica prioritaria es erradicar las 35 horas semanales de sobrecarga operativa manual (Proceso 1: 25h de registro manual; Proceso 2: 5h de actualización de estados; Proceso 3: 5h de cruce manual con Adecco) garantizando **supervisión humana innegociable (HITL)**, **cero web-scraping**, **fuente única de verdad relacional**, **deduplicación algorítmica** y **trazabilidad inmutable bajo RBAC y Ley N° 29733**.

---

## 1. Frontend & UI Layer

### Decision
Implementar la interfaz de usuario completa utilizando **Python Streamlit (v1.38+)** estilizada mediante inyección de **CSS corporativo avanzado de TCS** (`assets/tcs_theme.css`), consumiendo el logotipo oficial de alta resolución ubicado en `assets/tcs_logo.png`.

### Rationale
1. **Entorno corporativo de laboratorio restringido**: En los ambientes corporativos y de evaluación técnica de TCS, la instalación de dependencias Node.js, gestores de paquetes `npm`/`pnpm`, compiladores de frontend o contenedores Docker suele estar sujeta a políticas restrictivas de seguridad perimetral. Una pila 100% Python se ejecuta directamente en la estación de trabajo con `pip install` en un virtualenv local (`venv`), minimizando fricciones de despliegue a cero.
2. **Ciclo de renderizado reactivo y Ficha Única**: Streamlit permite orquestar flujos de entrada reactivos mediante componentes nativos (`st.form`, `st.data_editor`, `st.tabs`, `st.file_uploader`, `st.session_state`), ideales para los 28 atributos operativos de la Ficha Única de Candidato y la navegación entre módulos funcionales.
3. **Identidad Visual Corporativa TCS**: La paleta cromática oficial de Tata Consultancy Services se inyecta centralizadamente:
   - **TCS Deep Navy**: `#0A192F` / `#001E3C` (barras de navegación y encabezados ejecutivos).
   - **TCS Vibrant Blue**: `#0076CE` (botones principales de acción y call-to-actions).
   - **TCS Cyan Accent**: `#00B4D8` (indicadores de estado y enlaces activos).
   - **TCS Magenta Accent**: `#E91E63` / `#FF007F` (alertas críticas y distintivos especiales).
   - **Background Neutrals**: `#F8FAFC` (fondo de trabajo limpio) y `#FFFFFF` (tarjetas de datos).
   - **Semáforo Algorítmico**: `#2ECC71` (Verde Inédito / Dentro de Presupuesto), `#F1C40F` (Amarillo Reactivable / Aprobación Especial), `#E74C3C` (Rojo Duplicado / Fuera de Banda), `#9B59B6` (Púrpura Alumni TCS Boomerang).
4. **Seguridad y Control de Sesión**: La gestión de sesión se controla mediante `st.session_state` asociando el token de autenticación del usuario (`current_user_id`, `user_email`, `user_role`, `session_token`, `last_activity_time`), garantizando que ninguna vista operativa se renderice sin una sesión autenticada activa.

### Alternatives Considered
- **React 18 + FastAPI**: Proporciona desacoplamiento total, pero requiere infraestructura Node.js, mantenimiento de dos proyectos desacoplados (frontend + backend), configuración de CORS, empaquetado Vite y sobrecarga de desarrollo que excede las restricciones del entorno local corporativo.
- **Django Templates / Jinja2**: Ofrece robustez backend, pero la reactividad de la Ficha Única (autollenado dinámico de DNI al perder foco, normalización E.164 en vivo, cálculo instantáneo de variación presupuestal CTC) hubiera demandado código JavaScript espagueti (AJAX/Fetch) sin el beneficio de componentes preconstruidos.

---

## 2. Persistencia y Almacenamiento Relacional Agnóstico

### Decision
Utilizar **SQLAlchemy 2.0 (Core & ORM Declarative v2)** bajo el **Patrón Repositorio Agnóstico (Repository Pattern & Unit of Work)**. El almacenamiento por defecto para el entorno local y de laboratorio es **SQLite local (`ats_demo.db`)** con `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL` (Write-Ahead Logging) y `PRAGMA busy_timeout = 5000`. La conmutación hacia **PostgreSQL 15+** en producción corporativa se realiza de forma transparente sin alterar una sola línea de código de dominio, modificando únicamente la variable de entorno `DATABASE_URL` en el archivo `.env`.

### Rationale
1. **Erradicación del Excel Operativo (`BD GENERAL FY27`)**: La Constitución (Principio III) exige una fuente única relacional. SQLAlchemy 2.0 define el esquema con tipos fuertemente tipados (`Mapped[...]`), llaves foráneas mandatorias, restricciones de unicidad e índices compuestos.
2. **Agnosticismo del Motor**: Tanto SQLite como PostgreSQL soportan los tipos estándar definidos (`String`, `Integer`, `Float`, `DateTime`, `Text`, `Boolean`, `JSON`). Las expresiones JSON se manejan a través del dialecto agnóstico `sqlalchemy.types.JSON`, asegurando compatibilidad total al registrar diferenciales antes/después en la bitácora de auditoría.
3. **Cero Dependencias de Infraestructura en Local**: Los evaluadores y reclutadores pueden clonar el repositorio y ejecutar el ATS de inmediato sobre SQLite local sin necesidad de instalar, configurar o autenticar un servicio externo de PostgreSQL. En despliegues productivos de TCS, se conecta a PostgreSQL mediante `postgresql+psycopg2://user:pass@host:5432/ats_tcs`.
4. **Control de Concurrencia Optimista**: Se implementa un campo `record_version: Mapped[int]` con incremento atómico en cada actualización (`UPDATE ... WHERE id = :id AND record_version = :old_version`). Si las versiones no coinciden, se lanza una excepción `OptimisticLockError`, previniendo sobreescrituras ciegas entre reclutadores.

### Alternatives Considered
- **Raw SQL con `sqlite3`**: Código frágil, carente de tipado estático, con riesgo de inyección SQL y sin portabilidad a PostgreSQL sin reescribir consultas.
- **Tortoise-ORM o Peewee**: Carecen de la madurez, ecosistema de migraciones (Alembic) y soporte empresarial de SQLAlchemy 2.0.

---

## 3. Identidad Nacional DNI y Resiliencia Offline

### Decision
Integración con la API REST de **APIsPERU** (`https://dniruc.apisperu.com/api/v1/dni/{dni}`) utilizando un token configurable vía `.env` (`APISPERU_TOKEN`). La integración se desacopla mediante un puerto abstracto (`DNIProviderPort`) con una implementación primaria que consulta en **primer orden la caché local SQLite** (`cache_dni_reniec`), en **segundo orden el servicio HTTP de APIsPERU**, y ante desconexión o fallo, se degrada a **captura manual asistida** marcando la ficha como `"Pendiente de regularización de identidad"` y encolándola para sincronización asíncrona.

### Rationale
1. **Resolución Instantánea y Ahorro de Cuotas**: El 90% de las consultas de candidatos recurrentes o del pool se resuelven en <5ms desde la tabla local de caché (`dni`, `nombres`, `apellido_paterno`, `apellido_materno`, `fecha_nacimiento`, `ubigeo`, `distrito`, `cached_at`). Esto evita consumir peticiones externas y permite trabajar 100% desconectado de internet para identidades ya cacheadas.
2. **Resiliencia Operativa y Degradación Elegante**: Si la red corporativa bloquea el endpoint, si el servicio experimenta timeout (>3s) o si la cuota gratuita mensual se agota, el sistema no bloquea al reclutador; abre de inmediato los campos para digitación humana asistida y genera una tarea encolada de regularización.
3. **Cálculo Dinámico de Edad**: La fecha de nacimiento devuelta (o ingresada manualmente) se utiliza para computar la edad exacta:
   $$\text{edad} = \text{año\_actual} - \text{año\_nacimiento} - (1 \text{ si } (\text{mes, día})_{\text{actual}} < (\text{mes, día})_{\text{nacimiento}} \text{ else } 0)$$
   Esto erradica de forma permanente la anomalía detectada en el Excel legacy donde los candidatos figuraban con 127 años de edad.

### Alternatives Considered
- **Scraping directo al portal web de RENIEC/Sunat**: Violación flagrante del Principio II de la Constitución (Cero Web-Scraping). Además, los portales estatales incorporan Cloudflare, reCAPTCHA v3 y cambios de DOM continuos.
- **Reniec Convenio IDP Oficial**: Requiere meses de tramitación institucional y líneas dedicadas VPN/IPsec, inviable para un MVP operativo de Reclutamiento y Selección.

---

## 4. Extracción de CVs y CUL: LangChain Multimodelo + Fallback Heurístico Local

### Decision
Diseñar un motor de extracción documental desacoplado (`CVParserPort`) que orquesta **LangChain** con soporte dual configurable mediante variables de entorno:
1. **Google Gemini**: Utilizando `langchain-google-genai` (`ChatGoogleGenerativeAI`, modelos `gemini-2.5-flash` o `gemini-1.5-flash`) cuando `GEMINI_API_KEY` está presente.
2. **xAI Grok**: Utilizando `langchain-xai` (`ChatXAI`, modelo `grok-2` o `grok-beta`) cuando `GROK_API_KEY` está presente.
3. **Structured Outputs**: Empleando el método `.with_structured_output(CVExtractionResult)` basado en esquemas Pydantic v2 para garantizar tipos de datos estandarizados (habilidades técnicas, años de experiencia, trayectoria de roles, nivel de inglés, certificaciones, y antecedentes formales extraídos de CUL - Certificado Único Laboral).
4. **Fallback Heurístico Local 100% Offline**: En ausencia de API keys o ante caída de red, el sistema activa un extractor heurístico local basado en `pypdf` y expresiones regulares / diccionarios de taxonomía de habilidades tecnológicas (Java, Python, Spring Boot, React, AWS, SQL, etc.), asegurando continuidad operativa ininterrumpida.

### Rationale
1. **Human-in-the-Loop y Cero Sesgo Demográfico**: El prompt del sistema y el esquema estructurado censuran explícitamente atributos protegidos (edad, género, estado civil, dirección domiciliaria, fotografía, afiliaciones políticas o religiosas). La extracción presenta los datos al reclutador en campos editables de la Ficha Única para validación y ratificación humana soberana antes de persistir.
2. **Soporte de CUL (Certificado Único Laboral)**: El documento oficial emitido por el Ministerio de Trabajo del Perú (MTPE) contiene información de antecedentes policiales, judiciales, penales y trayectoria laboral formal. El parser extrae las fechas de inicio/cese y razones sociales declaradas para cotejarlas contra antecedentes corporativos.
3. **Compatibilidad con Roadmap IA (`IAfinanciero`)**: La arquitectura desacoplada permite que futuras fases incorporen RAG híbrido (búsqueda semántica sobre repositorios vectoriales FAISS/Chroma combinada con filtros relacionales SQL) y flujos multi-agente en grafos de estado con **LangGraph** (como en el patrón de `IAfinanciero`), sin requerir refactorizaciones del núcleo de dominio.

### Alternatives Considered
- **OpenAI GPT-4o exclusivo**: Introduce dependencia única de un proveedor sujeto a límites de cuota y costos por token en entornos masivos de CVs. La estrategia multi-proveedor (Gemini + Grok + Heurístico) otorga redundancia absoluta.
- **Bibliotecas OCR pesadas (Tesseract / EasyOCR)**: Requieren binarios del sistema operativo (`tesseract.exe`), paquetes C++ adicionales y aumentan la latencia en 5-10 segundos por página. Para el 98% de los CVs en formato digital vectorial, `pypdf` extrae el texto puro en milisegundos.

---

## 5. Deduplicación Algorítmica y Reconciliación Fonética

### Decision
Implementar un servicio de deduplicación multicriterio (`DeduplicationService`) basado en tres capas de evaluación:
1. **Cotejo Primario Exacto**: Coincidencia unívoca por Número de Documento (DNI/CE/Pasaporte), Correo Electrónico normalizado (`lower().strip()`) y Teléfono Móvil en estándar canónico internacional E.164 (`+519XXXXXXXX`).
2. **Normalización Fonética y Remoción de Partículas**: Tokenización de nombres peruanos removiendo preposiciones y partículas comunes ("de", "la", "del", "los", "las", "san", "santa"). Manejo de permutaciones (Apellidos primero vs. Nombres primero).
3. **Cotejo Fonético y de Similitud Aproximada**: Algoritmo **Double Metaphone** combinado con **Token Sort Ratio / Levenshtein Distance** (mediante `difflib` o `rapidfuzz`):
   - Coincidencia $\ge 90\%$: Clasificación como *Duplicado Alta Probabilidad*.
   - Coincidencia $80\% - 89\%$: Alerta no bloqueante *Coincidencia Probable* para arbitraje humano en 1-clic.
   - Coincidencia $< 80\%$: Considerado candidato inédito.

### Rationale
En el contexto de selección en Perú, es habitual encontrar candidatos registrados como "Alonso Jesús Huanca Mamani" en DNI, "Huanca, Alonso" en la planilla de Adecco y "Alonso Huanca" en LinkedIn. Un cotejo por texto exacto fracasaría en el 40% de los casos. La combinación de Double Metaphone con Token Sort Ratio resuelve las inversiones de nombres y apellidos manteniendo la consulta en <15ms.

---

## 6. Normalización E.164 y Deep Link a WhatsApp Web

### Decision
Crear una utilidad de normalización telefónica basada en reglas estrictas para el ecosistema móvil peruano e internacional:
1. Limpieza de caracteres no numéricos (espacios, guiones, paréntesis, puntos).
2. Si el número inicia con `+51` o `51` y tiene 11 dígitos, se valida que el noveno dígito anterior inicie en `9`.
3. Si el número tiene 9 dígitos e inicia con `9`, se prefija canónicamente con `+51`.
4. Si el número pertenece a otro país (código de país reconocido internacionalmente, e.g. `+57`, `+54`), se preserva su formato E.164.
5. Si no cumple las reglas de longitud o formato, se rechaza con error de validación descriptivo.

Para el enlace interactivo:
Generar una URL segura para WhatsApp Web:
`https://web.whatsapp.com/send?phone=519XXXXXXXX&text={url_encoded_protocol_message}`
Donde `{url_encoded_protocol_message}` es la plantilla de saludo institucional de TCS:  
*"Hola [Nombres], te saluda [Recruiter] del equipo de Selección de Tata Consultancy Services (TCS Perú). Te contactamos respecto a tu postulación para la vacante de [Perfil]. ¿Tendrías 5 minutos para conversar?"*

---

## 7. Ingesta Masiva de Adecco y Generador de Cartera y Exclusiones (Ley 29733)

### Decision
1. **Validador de Planillas de Adecco**:
   - Motor de ingesta basado en `pandas` / `openpyxl`.
   - **Diccionario de Mapeo Semántico de Encabezados (Alias Mapping)**: Permite que columnas como `Móvil`, `Celular`, `Telefono`, `Teléfono`, `WhatsApp` se normalicen automáticamente al atributo canónico `telefono_raw`. Lo propio para `DNI`, `Documento`, `Doc`, `DNI / CE` $\to$ `documento_raw`.
   - **Semáforo de Clasificación**:
     * 🔴 **Rojo (Duplicado Activo / Exclusión Permanente)**: En proceso activo, descartado $<180$ días, o descarte histórico no subsanable (BGC fallido, fraude, falta a la ética, *Do Not Rehire*).
     * 🟡 **Amarillo (Reactivable)**: Descartado $>180$ días por motivos subsanables (expectativa salarial, vacante congelada).
     * 🟢 **Verde (Limpio / Inédito)**: Sin antecedentes en la base.
     * 🟣 **Insignia Boomerang (Alumni TCS)**: Detección cruzada con el repositorio histórico de ex-empleados TCS para bloquear comisiones de intermediación.
   - **Atomicidad Transaccional**: La confirmación de importación de candidatos verdes se ejecuta en una única transacción de base de datos; ante cualquier falla de conexión o interrupción, se realiza un rollback integral sin dejar registros parciales.

2. **Generador a Demanda de Reporte de Cartera y Exclusiones**:
   - Generación instantánea en 1-clic de archivos descargables `.xlsx` o `.csv`.
   - **Estructura fija y uniforme de 5 columnas oficiales**:
     1. `DNI`
     2. `Nombres y Apellidos`
     3. `Perfil`
     4. `Vigencia de Exclusión` (e.g., `"Hasta 15/12/2026"` o `"Permanente"`)
     5. `Estado` (e.g., `"En Proceso Activo"`, `"Cartera Excluida"`, `"Exclusión Institucional"`)
   - **Censura Estricta bajo Ley N° 29733**: Se prohíbe la inclusión de teléfonos, correos personales, remuneraciones pretendidas, tarifas de facturación del cliente, notas cualitativas de entrevista o motivos confidenciales de descarte.
   - **Registro de Auditoría**: Cada descarga registra usuario solicitante, fecha/hora exacta, cliente filtrado (o consolidado) y cantidad total de filas exportadas.

---

## 8. Simulador Financiero CTC con Factor Legal 1.56 y Guardas Matemáticas

### Decision
Implementar el servicio financiero de compensación laboral modelando los sobrecostos del **Régimen General Privado Peruano (D.L. 728)**:
- **Sobrecostos de Ley (56%)**:
  * Gratificaciones Legales (Julio y Diciembre): $\frac{2}{12} = 16.67\%$
  * Bonificación Extraordinaria sobre Gratificación (Ley 29351 - EsSalud 9%): $16.67\% \times 9\% = 1.50\%$
  * Compensación por Tiempo de Servicios (CTS - Mayo y Noviembre): $\frac{1 + 1/6}{12} \approx 9.72\%$
  * Aporte a la Seguridad Social (EsSalud): $9.00\%$
  * Descanso Vacacional Remunerado (30 días): $\frac{1}{12} = 8.33\%$
  * Seguro Vida Ley (D.U. 044-2019) y provisiones operativas: $\approx 0.78\%$
  * **Factor Total CTC**: $\mathbf{1.56}$

- **Fórmulas de Cálculo**:
  * **Bruto Solicitado**: Si se ingresa en bruto: $\text{Salario Bruto}$.
  * **Conversión Neto a Bruto**: Si el candidato declara su pretensión en neto líquido:
    $$\text{Salario Bruto Proyectado} = \frac{\text{Sueldo Neto}}{1 - \text{Tasa Retención Estimada (21\%)}} = \frac{\text{Sueldo Neto}}{0.79}$$
  * **Costo Empresa (CTC Solicitado)**:
    $$\text{CTC Solicitado} = \text{Salario Bruto} \times 1.56$$
  * **Variación Presupuestal Protegida contra División por Cero**:
    $$\text{Variacion} = \begin{cases} \text{None ("Pendiente de Presupuesto")}, & \text{si } \text{CTC Presupuestado} \le 0 \\ \frac{\text{CTC Solicitado} - \text{CTC Presupuestado}}{\text{CTC Presupuestado}} \times 100, & \text{si } \text{CTC Presupuestado} > 0 \end{cases}$$
  * **Semáforo Financiero**:
    - $\text{Variación} \le 0\%$: 🟢 *Dentro de Presupuesto*.
    - $0\% < \text{Variación} \le 10\%$: 🟡 *Requiere Aprobación Especial*.
    - $\text{Variación} > 10\%$: 🔴 *Fuera de Banda Salarial*.

---

## 9. Seguridad, Autenticación, RBAC y Bitácora de Auditoría Inmutable

### Decision
1. **Autenticación y Criptografía**:
   - Hashing de contraseñas mediante **bcrypt** con salt criptográfico aleatorio (`passlib[bcrypt]` o `bcrypt`).
   - Restricción de registro a correos corporativos oficiales con dominio `@tcs.com`.
   - Política de contraseñas: mínimo 8 caracteres, al menos 1 mayúscula, 1 minúscula, 1 número y 1 caracter especial.
   - Bloqueo preventivo de cuenta tras 5 intentos fallidos consecutivos durante 15 minutos (con capacidad de desbloqueo anticipado por un Head of Talent Acquisition).

2. **Roles y Permisos Corporativos (RBAC)**:
   - `Head_of_Talent_Acquisition`: Administrador total. Gestión de usuarios, elevación de roles, aprobaciones salariales excepcionales, consulta global de auditoría y desbloqueo de cuentas.
   - `Senior_Technical_Recruiter`: Operador principal. Registro y edición de candidatos, embudo de postulaciones, screening telefónico, carga de CVs, validador de Adecco y reporte de exclusiones.
   - `Account_Recruitment_Coordinator`: Coordinador de cuentas. Gestión de vacantes por cliente, reasignación de postulaciones, consulta de métricas de avance.
   - `Compliance_Officer`: Rol por defecto para cuentas recién registradas (Principio de Mínimo Privilegio). Modo estricto de solo lectura, consulta de consola de auditoría y reportes de cumplimiento. Cualquier intento de mutación de datos se bloquea y audita.

3. **Bitácora de Auditoría Inmutable (Append-Only)**:
   - Tabla `bitacora_auditoria` que registra cada evento con: `id`, `timestamp` (UTC con timezone), `usuario_id`, `usuario_email`, `rol_en_momento`, `tipo_accion`, `entidad_objeto`, `registro_id`, `version_registro`, `valores_previos_json`, `valores_nuevos_json`, `justificacion_operativa`, `nombre_archivo_adjunto`, `hash_integridad_sha256`.
   - Prohibición arquitectónica y funcional de operaciones `UPDATE` o `DELETE` sobre la tabla de auditoría.

---

## 10. Hoja de Ruta de Integración con el Patrón `IAfinanciero`

### Decision
Para garantizar que el ATS Core MVP sea modularmente ampliable hacia capacidades avanzadas en fases subsiguientes, la estructura del proyecto reserva la capa de servicios desacoplados para admitir la integración del patrón **`IAfinanciero`**:
1. **RAG Híbrido**: Repositorio vectorial (`ports/vector_store_port.py`) que combina búsqueda densa de embeddings semánticos sobre CVs y perfiles con filtrado relacional estricto en SQLite/PostgreSQL.
2. **Grafos de LangGraph**: Orquestación de flujos multi-agente con estados tipados (`StateGraph`) para pre-evaluaciones comparativas automáticas de candidatos contra JDs (Job Descriptions).
3. **Mantenimiento del Principio I (HITL)**: Aunque se agreguen nodos evaluadores de IA, el grafo culmina indefectiblemente en un nodo de confirmación humana antes de aplicar cualquier acción en el pipeline.

---

## Tabla Resumen de Decisiones Técnicas

| Dominio Técnico | Solución Seleccionada | Justificación Principal | Alternativa Descartada |
|-----------------|-----------------------|--------------------------|------------------------|
| **Frontend** | Streamlit + TCS Custom CSS | Cero Node.js, 100% Python, rápido, corporativo | React + FastAPI (sobrecarga de setup en lab) |
| **Persistencia** | SQLAlchemy 2.0 (SQLite WAL / Postgres) | Agnosticismo, tipado estático, conmutación transparente | Raw SQL / Django ORM (demasiado acoplado) |
| **Identidad DNI** | APIsPERU + Caché Local SQLite + Cola | Autollenado <5ms, resiliencia offline, ahorro cuotas | Scraping RENIEC (Viola Principio II) |
| **Extracción CV** | LangChain (Gemini/Grok) + Fallback Heurístico | Multi-proveedor, Pydantic outputs, funciona offline | GPT-4o exclusivo / Tesseract OCR |
| **Deduplicación** | Double Metaphone + Token Sort Ratio | Manejo de inversiones de nombres y partículas | Regex simple / Exact string match |
| **Normalización Tel** | Reglas Canónicas E.164 (`+519XXXXXXXX`) | Estándar internacional, enlace 1-clic a WhatsApp Web | Almacenar cadenas crudas con guiones/espacios |
| **Cruce Adecco** | Pandas con alias semánticos + Semáforo | Mapea encabezados variables, semáforo instantáneo | Cotejo manual en Excel (5h perdidas) |
| **Reporte Exclusión** | Exportador de 5 columnas fijas a demanda | Cumple Ley 29733, censura salarios y teléfonos | Enviar base general sin censura (ilegal) |
| **Finanzas CTC** | Factor 1.56 (D.L. 728) con guarda `#DIV/0!` | Precisión laboral peruana, estabilidad matemática | Fórmulas manuales en Excel que fallan en `#DIV/0!` |
| **Seguridad & RBAC** | Bcrypt + 4 Roles + Bitácora Append-Only | Seguridad corporativa, auditoría inmutable no repudiable | Autenticación básica sin auditoría de cambios |
