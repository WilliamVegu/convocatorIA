# Feature Specification: ATS Core MVP (Erradicación de Fricción Manual y Gestión Centralizada)

**Feature Branch**: `001-ats-core-mvp`  
**Created**: 2026-09-10  
**Status**: Draft  
**Input**: User description: "ats-core-mvp: Erradicar las 35 horas semanales de dolor operativo del equipo de Reclutamiento y Selección mediante la Ficha Única de Candidato con autollenado de DNI y normalización E.164, Validador masivo de planillas de Adecco con semáforo de duplicados, Generador a demanda de reporte de exclusión bajo Ley 29733, Simulador financiero CTC con Factor 1.56 blindado contra división por cero, y Alerta automática de ex-colaboradores TCS (Boomerang)."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ficha Única de Candidato con Autollenado por DNI, Normalización E.164 y Parsing Estructurado de CVs (Priority: P1)

Como reclutadora técnica o analista de selección de TCS,  
quiero registrar a un candidato nuevo ingresando únicamente su documento de identidad (DNI peruano de 8 dígitos) o adjuntando su archivo de CV, obteniendo la normalización automática de su teléfono móvil a formato canónico internacional y un enlace directo a WhatsApp Web,  
para erradicar las 25 horas semanales dedicadas a transcribir datos fila por fila en el Excel operativo (`BD GENERAL FY27`), evitando errores de tipeo, cálculos absurdos de edad (como los 127 años de la plantilla anterior) y registros repetidos.

**Why this priority**: Es la base angular del sistema y el núcleo de mayor retorno operativo. Ataca de forma frontal el **Proceso 1 (Registro manual de candidatos)**, el cual consume 25 horas semanales del equipo (5 horas diarias acumuladas). Sin una ficha unificada y validada en el punto de entrada, cualquier dato downstream (búsquedas, reportes, comunicación y compliance) nace corrupto.

**Independent Test**: Puede ser probado de forma 100% autónoma registrando un candidato con solo ingresar un DNI de 8 dígitos y un teléfono móvil de 9 dígitos. El sistema autocompleta nombres y apellidos, calcula la edad real sin anomalías, almacena el teléfono en formato canónico internacional (`+519XXXXXXXX`), proporciona un botón activo de WhatsApp Web y permite subir un CV (PDF/Word) para extraer automáticamente competencias clave, persistiendo la ficha sin depender de ninguna otra funcionalidad.

**Acceptance Scenarios**:

1. **Scenario 1.1 (Autollenado exitoso por DNI):**  
   **Given** que la reclutadora se encuentra en el formulario de creación de ficha de candidato,  
   **When** ingresa un número de DNI peruano válido de 8 dígitos (ej. `76128709`) y presiona validar o cambia de campo,  
   **Then** el sistema consulta el servicio de validación de identidad nacional y autocompleta de inmediato los campos de nombres de pila, apellido paterno, apellido materno, fecha de nacimiento y distrito de residencia, calculando la edad cronológica exacta a la fecha actual y bloqueando la edición de campos de identidad oficial para evitar alteraciones accidentales.

2. **Scenario 1.2 (Normalización canónica de teléfono a E.164 y enlace a WhatsApp):**  
   **Given** que la reclutadora ingresa un teléfono de contacto en cualquiera de sus formatos habituales (ej. `989322088`, `51989322088`, `+51 989 322 088` o `989-322-088`),  
   **When** el sistema procesa el campo de contacto telefónico,  
   **Then** almacena el número bajo el estándar canónico estricto `+519XXXXXXXX`, verifica que no exista previamente en la base de datos y despliega en la interfaz un botón interactivo de 1-clic que abre WhatsApp Web dirigido al número con un mensaje protocolar preconfigurado de primer contacto de TCS.

3. **Scenario 1.3 (Detección reactiva inmediata de candidato duplicado en entrada):**  
   **Given** que ya existe en la base corporativa un candidato registrado con DNI `46753314` o celular `+51987844071`,  
   **When** una reclutadora intenta crear una nueva ficha utilizando dicho DNI, celular o correo electrónico,  
   **Then** el sistema interrumpe el registro, muestra una alerta no bloqueante indicando el duplicado, despliega el nombre del candidato, el reclutador responsable actual, la fecha del último contacto y un enlace directo para abrir la ficha histórica existente en lugar de crear un registro huérfano.

4. **Scenario 1.4 (Extracción estructurada inicial de CV adjunto):**  
   **Given** que la reclutadora carga un archivo de currículo en formato PDF o Word al crear o editar una ficha,  
   **When** se completa la carga documental,  
   **Then** el sistema extrae de forma asistida y sin sesgos demográficos el resumen de competencias tecnológicas principales, años estimados de experiencia laboral, enlaces profesionales externos y nivel de idiomas, presentándolos en campos estructurados editables para confirmación humana antes de guardar.

---

### User Story 2 - Validador Masivo de Planillas Excel de Adecco con Semáforo Algorítmico (Priority: P2)

Como reclutadora técnica responsable de la gestión de proveedores externos,  
quiero cargar en el sistema la planilla Excel periódica remitida por Adecco con decenas de candidatos propuestos,  
para obtener en segundos un reporte comparativo con código de semáforo (🔴 Duplicado activo, 🟡 Reactivable >6 meses, 🟢 Limpio/Inédito) que me indique exactamente cuáles perfiles ya fueron gestionados por TCS y cuáles son realmente inéditos, erradicando las 5 horas semanales de cotejo manual (Proceso 3).

**Why this priority**: Ataca directamente el **Proceso 3 (Cruce de candidatos con Adecco)** que consume 5 horas semanales. Hoy el equipo recibe planillas pesadas con candidatos que en un 90% ya fueron contactados, evaluados o descartados por TCS. Esta validación manual genera demoras operativas, roces con el proveedor y recontactos vergonzosos a profesionales que ya habían sido descartados.

**Independent Test**: Puede ser probado de forma independiente subiendo un archivo Excel simulado con 15 registros de prueba (5 idénticos a candidatos activos en TCS, 3 descartados hace más de 6 meses por pretensión salarial, y 7 totalmente nuevos). El sistema debe clasificar el 100% de las filas en las categorías del semáforo con su justificación correspondiente en menos de 5 segundos, permitiendo descargar el listado depurado con un solo clic.

**Acceptance Scenarios**:

1. **Scenario 2.1 (Clasificación 🔴 Rojo - Duplicado Activo o Descarte Reciente):**  
   **Given** una fila de la planilla de Adecco con un candidato cuyo DNI, correo, teléfono normalizado o nombre con similitud fonética alta coincide con un registro de TCS en estado activo (`En proceso`, `En entrevista`) o descartado hace menos de 6 meses,  
   **When** el sistema ejecuta la validación algorítmica,  
   **Then** marca la fila con distintivo rojo (🔴), indica el motivo de la coincidencia ("En proceso activo en cuenta BCP" o "Descartado el 15/07/2026: No superó filtro técnico"), señala la reclutadora responsable y excluye el perfil de la lista limpia a procesar.

2. **Scenario 2.2 (Clasificación 🟡 Amarillo - Candidato Reactivable > 6 meses):**  
   **Given** una fila de la planilla de Adecco correspondiente a un candidato que postuló a TCS hace más de 6 meses y cuyo motivo de cierre fue no excluyente (ej. "Expectativa salarial sobre presupuesto" o "Vacante congelada por cliente"),  
   **When** el sistema evalúa el registro contra las reglas de reactivación temporal,  
   **Then** marca la fila con distintivo amarillo (🟡), detalla el antecedente histórico y ofrece la opción de reactivarlo asociándolo a la nueva vacante sin sobrescribir su historial anterior.

3. **Scenario 2.3 (Clasificación 🟢 Verde - Candidato Inédito y Limpio):**  
   **Given** una fila de la planilla de Adecco cuyos datos de identidad, teléfono, correo y coincidencia fonética no registran ninguna coincidencia en el histórico de TCS,  
   **When** concluye la evaluación del archivo,  
   **Then** marca la fila con distintivo verde (🟢), habilitando la importación masiva directa hacia la bandeja de entrada de candidatos nuevos listos para llamada de validación telefónica humana.

4. **Scenario 2.4 (Manejo de inconsistencias y formatos heterogéneos de Adecco):**  
   **Given** que la planilla de Adecco contiene celdas vacías en DNI, teléfonos con prefijos mezclados (`519...` y `9...`) o nombres en orden inverso,  
   **When** el sistema ingesta el archivo,  
   **Then** normaliza los teléfonos a estándar E.164, ejecuta cotejo por correo electrónico y similitud aproximada de nombres, y reporta en una bitácora visual las filas que requieren revisión manual por falta de identificador legal.

---

### User Story 3 - Generador a Demanda de Reporte de Exclusión Anonimizado para Adecco según Ley 29733 (Priority: P3)

Como reclutadora técnica o líder de selección,  
quiero generar y descargar en cualquier momento con un solo clic un reporte de exclusión para Adecco,  
para entregar al proveedor la lista de profesionales que TCS ya tiene en proceso o en periodo de enfriamiento, garantizando el estricto cumplimiento de la Ley N° 29733 (Ley de Protección de Datos Personales de Perú) al anonimizar datos sensibles como pretensiones salariales, notas privadas y evaluaciones internas.

**Why this priority**: Ataca la causa raíz del problema con el proveedor externo. Adecco remite candidatos duplicados porque busca a ciegas. Si TCS le entrega periódicamente a demanda la lista de exclusión antes de que inicien sus búsquedas, se evita que busquen a los mismos candidatos, elevando el ratio de CV útil del 10% actual hacia más del 30% y eliminando el retrabajo de raíz.

**Independent Test**: Puede ser probado de forma independiente pulsando el botón "Generar Reporte de Exclusión Adecco" en la aplicación. El sistema compila los candidatos en estado activo y exclusión temporal, anonimiza los datos (mostrando DNI, primer apellido, inicial del nombre, fecha de vigencia de exclusión y perfil técnico; omitiendo remuneraciones, correo, celular y notas privadas), y descarga un archivo en formato estructurado estándar (.xlsx/.csv).

**Acceptance Scenarios**:

1. **Scenario 3.1 (Generación a demanda en 1-clic):**  
   **Given** que existen 450 candidatos en el sistema clasificados en estados que ameritan exclusión (en proceso de screening, entrevistas con clientes, ofertas en curso o descartados hace menos de 180 días),  
   **When** la reclutadora hace clic en "Descargar Reporte de Exclusión Adecco",  
   **Then** el sistema compila en menos de 2 segundos el archivo descargable actualizado al milisegundo exacto, registrando en la auditoría del sistema la fecha, hora y usuario que efectuó la descarga.

2. **Scenario 3.2 (Anonimización estricta bajo Ley N° 29733):**  
   **Given** el listado de candidatos a incluir en el reporte para el proveedor externo,  
   **When** se construye la estructura del archivo de exportación,  
   **Then** el archivo contiene únicamente: Tipo y Número de Documento (DNI/CE), Primer Apellido e Inicial del Nombre, Código de Vacante/Perfil y Fecha hasta la cual aplica la exclusión; quedando estrictamente censurados y excluidos el número telefónico personal, correo electrónico, pretensión salarial, tarifas de facturación del cliente, notas cualitativas de descarte y cualquier atributo protegido.

3. **Scenario 3.3 (Filtro por cuenta o cliente específico):**  
   **Given** que el encargo a Adecco aplica únicamente a requerimientos de una cuenta cliente determinada (ej. BCP),  
   **When** la reclutadora selecciona la cuenta antes de descargar,  
   **Then** el sistema permite opcionalmente descargar la exclusión general consolidada o la exclusión segmentada por cuenta según la necesidad operativa del encargo.

---

### User Story 4 - Simulador Financiero y Calculadora Dinámica de Costo Empresa CTC con Guardas Matemáticas (Priority: P4)

Como reclutadora técnica durante la llamada telefónica o analista de selección al recibir una pretensión salarial,  
quiero ingresar la expectativa salarial mensual bruta o neta del postulante y contrastarla instantáneamente contra el presupuesto autorizado de la vacante bajo el régimen laboral peruano D.L. 728 (Factor 1.56),  
para conocer la viabilidad económica en tiempo real, visualizar el porcentaje de variación presupuestal y erradicar por completo los errores matemáticos de división por cero (`#DIV/0!`) que corrompen las hojas de cálculo.

**Why this priority**: Resuelve la fragilidad financiera evidenciada en las columnas U, V, W y X del Excel `BD GENERAL FY27`. Los errores de `#DIV/0!` en el Excel paralizan las aprobaciones de finanzas, provocan ofertas inconsistentes y demandan tiempo de reproceso entre reclutamiento y control de gestión.

**Independent Test**: Puede ser probado de forma independiente ingresando una expectativa de S/. 6,000 en una vacante con presupuesto CTC de S/. 12,410. El sistema calcula automáticamente el Costo Empresa de S/. 9,360 ($6000 \times 1.56$), reporta una variación de -24.58% (holgadamente dentro del presupuesto), y cuando se borra o se coloca en 0 el presupuesto del rol, la variación muestra un indicador neutral de "Sin presupuesto asignado" en lugar de fallar con `#DIV/0!`.

**Acceptance Scenarios**:

1. **Scenario 4.1 (Cálculo exacto del Costo Empresa mediante Factor legal 1.56):**  
   **Given** que un candidato comunica una pretensión salarial bruta de S/. 5,000 mensuales en moneda nacional (PEN),  
   **When** la reclutadora registra dicho valor en la ficha de postulación,  
   **Then** el sistema aplica de inmediato el multiplicador laboral de 1.56 derivado de las cargas sociales del Régimen Privado D.L. 728 (Gratificaciones legales, CTS, EsSalud, Vacaciones, Seguro Vida Ley) y muestra el Costo Empresa (CTC Solicitado) exacto de S/. 7,800.00.

2. **Scenario 4.2 (Cálculo protegido de variación presupuestal sin `#DIV/0!`):**  
   **Given** un registro donde el Costo Empresa presupuestado para el rol aún no ha sido cargado o es igual a cero (0.00),  
   **When** el sistema calcula el indicador de variación presupuestal,  
   **Then** activa una guarda matemática que previene la indeterminación, no emite ningún error visual ni matemático, y despliega en la interfaz la etiqueta informativa "Pendiente de Presupuesto", manteniendo la integridad de los datos.

3. **Scenario 4.3 (Semáforo de viabilidad financiera):**  
   **Given** una postulación donde el CTC Solicitado es contrastado contra un CTC Presupuestado válido de S/. 10,000,  
   **When** el valor solicitado es:  
   - Menor o igual al presupuesto (ej. S/. 8,500 $\to$ variación -15.00%): muestra semáforo verde ("Dentro de Presupuesto").  
   - Hasta 10% por encima del presupuesto (ej. S/. 10,800 $\to$ variación +8.00%): muestra semáforo ámbar ("Requiere Aprobación Especial").  
   - Más del 10% por encima del presupuesto (ej. S/. 13,000 $\to$ variación +30.00%): muestra semáforo rojo ("Fuera de Banda Salarial").  
   **Then** la reclutadora dispone de argumentos objetivos para negociar durante la llamada o tramitar excepciones con el Delivery Manager.

---

### User Story 5 - Alerta Automática de Ex-Colaboradores TCS (Candidatos Boomerang) (Priority: P5)

Como reclutadora técnica o coordinadora de selección,  
quiero que el sistema identifique de forma automática mediante el DNI si el candidato postulante laboró previamente en TCS Perú o sedes asociadas,  
para visualizar de inmediato su antecedente corporativo, fecha de cese, cuenta en la que prestó servicios y condición de recontratabilidad (*Re-hire Eligibility*), acelerando el ciclo de contratación y mitigando riesgos de reincorporación no autorizada.

**Why this priority**: Resuelve la Columna AA del Excel (`Ha trabajado antes en TCS`), la cual hoy se llena de manera empírica si el candidato lo menciona voluntariamente. Detectar tempranamente a ex-colaboradores (*candidatos Boomerang*) permite aprovechar talento que ya conoce los estándares técnicos y la cultura de TCS, reduciendo los tiempos de inducción a cero, o bien alertar si la persona salió bajo condiciones que impiden su recontratación.

**Independent Test**: Puede ser probado de forma independiente registrando un DNI que coincida con la base de datos histórica de ex-colaboradores. El sistema debe emitir una insignia visual en la ficha del candidato destacando "Ex-Colaborador TCS (Boomerang)" y desplegando el historial corporativo previo (último proyecto, periodo laborado y estatus de recontratación según recursos humanos).

**Acceptance Scenarios**:

1. **Scenario 5.1 (Detección positiva de talento Boomerang elegible):**  
   **Given** que una reclutadora ingresa el DNI de un profesional que trabajó en TCS entre 2022 y 2024 y cuya salida fue por renuncia voluntaria con evaluación favorable,  
   **When** se procesa la consulta de identidad,  
   **Then** el sistema muestra una alerta visual azul/verde destacada: "Candidato Boomerang: Ex-colaborador TCS (Cuenta Entel, 2022-2024). Condición: Recontratable", facilitando la priorización del perfil en la cola de llamadas.

2. **Scenario 5.2 (Alerta preventiva de candidato no recontratable):**  
   **Given** que el DNI ingresado corresponde a un ex-empleado registrado con marca corporativa de no recontratación (*Do Not Rehire*),  
   **When** el sistema coteja el registro con el catálogo histórico,  
   **Then** emite una advertencia de compliance de alta prioridad para la reclutadora, sugiriendo validar el caso con la gerencia de Recursos Humanos antes de coordinar cualquier entrevista con el cliente.

3. **Scenario 5.3 (Candidato nuevo sin antecedentes en la compañía):**  
   **Given** que el DNI no registra ninguna coincidencia en el historial laboral interno de TCS,  
   **When** se guarda la ficha,  
   **Then** el campo de antecedente TCS se establece automáticamente en "No registra antecedente interno" de forma limpia sin requerir intervención manual.

---

### Edge Cases

1. **Documento de Identidad Extranjero o No Estandarizado (Carné de Extranjería / Pasaporte):**  
   ¿Qué ocurre cuando el candidato no cuenta con DNI peruano de 8 dígitos sino con Carné de Extranjería (CE) de 9 o 12 dígitos, o Pasaporte?  
   *Comportamiento del sistema*: El sistema debe admitir tipos de documento alternativos (`CE`, `Pasaporte`). Cuando el tipo es distinto de DNI peruano, inhabilita el autollenado automático por el servicio nacional de identidad, solicita el ingreso manual validado de los nombres y apellidos, y exige obligatoriamente la fecha de nacimiento para garantizar el cálculo dinámico de edad sin provocar el fallo de 127 años.

2. **Falla o Indisponibilidad Temporal del Servicio de Identidad Nacional:**  
   ¿Qué sucede si el servicio externo de consulta de DNI no responde o excede el tiempo límite de espera (timeout > 3 segundos)?  
   *Comportamiento del sistema*: El sistema debe degradarse elegantemente (*graceful degradation*). Despliega una advertencia sutil ("Servicio de identidad temporalmente inaccesible; proceda con llenado manual"), permite a la reclutadora tipear los nombres y apellidos manualmente, y deja una marca de "Pendiente de verificación de identidad" para revalidación asíncrona posterior con un solo clic.

3. **Formatos Telefónicos Internacionales no Peruanos o Números Incompletos:**  
   ¿Qué sucede cuando se ingresa un número móvil de otro país (ej. Colombia `+57`, Argentina `+54`) o un número incompleto (8 dígitos en vez de 9)?  
   *Comportamiento del sistema*: Si el número cuenta con prefijo de otro país válido, se normaliza al formato canónico E.164 respectivo. Si el número tiene menos de 9 dígitos y no cuenta con código de país identificable, el sistema rechaza la entrada indicando: "Número telefónico inválido. Para números peruanos ingrese los 9 dígitos móviles".

4. **Planilla de Adecco con Encabezados Modificados o Filas en Blanco:**  
   ¿Cómo responde el validador de Adecco si el proveedor alteró el nombre de las columnas (ej. puso `Celular` en vez de `Teléfono`), insertó filas vacías al inicio o pegó celdas combinadas?  
   *Comportamiento del sistema*: El módulo de ingesta debe implementar mapeo semántico tolerante a variaciones de encabezado comunes, omitir filas enteramente en blanco sin abortar el proceso y, si falta una columna crítica para la deduplicación (DNI o Correo), detener la importación señalando exactamente la deficiencia encontrada con instrucciones claras de corrección.

5. **Simulación Financiera con Presupuesto Cero, Negativo o Vacío:**  
   ¿Cómo se comporta la calculadora de variación presupuestal si el reclutador ingresa una pretensión salarial pero el presupuesto del rol está en blanco, en cero (`0.00`) o con valor negativo por error?  
   *Comportamiento del sistema*: El cálculo del porcentaje de variación debe estar protegido por una guarda condicional estricta. Si el presupuesto es menor o igual a cero o nulo, la celda de variación porcentual se muestra como valor vacío/no aplicable ("N/A - Sin Presupuesto Asignado"), imposibilitando que se genere el error `#DIV/0!`.

6. **CVs Ilegibles, Protegidos con Contraseña o Escaneados sin Texto Seleccionable:**  
   ¿Qué ocurre cuando la reclutadora sube un CV en PDF que es una imagen escaneada borrosa o tiene clave de apertura?  
   *Comportamiento del sistema*: El sistema detecta el error de lectura, informa a la reclutadora que el documento no posee texto procesable y habilita la edición manual de la ficha, almacenando el archivo adjunto para consulta visual humana sin interrumpir el flujo.

7. **Candidato con Múltiples Postulaciones Simultáneas a Diferentes Cuentas:**  
   ¿Cómo maneja el sistema a un candidato que ya está en proceso para BCP pero calza perfecto para una vacante de Banco Falabella o Entel?  
   *Comportamiento del sistema*: La arquitectura desacopla la ficha de identidad (`Candidato`) de sus participaciones en procesos (`Postulacion`). El candidato conserva una única ficha maestra y puede tener múltiples postulaciones asociadas, emitiendo una alerta al reclutador si se detecta que ya tiene un proceso activo en curso para evitar duplicidad de entrevistas y definir ownership entre reclutadores.

8. **Exportación de Exclusión para Adecco sin Registros Elegibles:**  
   ¿Qué sucede si se solicita la descarga del reporte de exclusión y no existen candidatos en estado de exclusión activa para los filtros aplicados?  
   *Comportamiento del sistema*: El sistema genera el archivo con la cabecera estándar y un aviso informativo indicando que no hay registros excluidos para los parámetros seleccionados, impidiendo descargas fallidas o archivos corruptos.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Identidad Nacional, Normalización de Contacto y Ficha Única (Proceso 1)
- **FR-001**: El sistema DEBE proveer un formulario unificado de registro de candidato ("Ficha Única") accesible vía interfaz web que consolide los 28 atributos operativos del proceso.
- **FR-002**: Al ingresar un número de DNI peruano de 8 dígitos, el sistema DEBE consultar en tiempo real el servicio de identidad y autocompletar obligatoriamente: nombres de pila, apellido paterno, apellido materno, fecha de nacimiento y distrito de residencia.
- **FR-003**: El sistema DEBE calcular la edad cronológica del candidato de manera dinámica a partir de la fecha de nacimiento (`Fecha actual - Fecha de nacimiento`), asignando valor nulo o no aplicable si la fecha de nacimiento no está disponible, prohibiendo terminantemente cualquier valor estático o el cálculo erróneo de 127 años.
- **FR-004**: El sistema DEBE normalizar todo número telefónico registrado al estándar canónico internacional E.164 (`+519XXXXXXXX` para móviles peruanos), eliminando prefijos redundantemente digitados (`51`, `+51`), espacios, guiones y paréntesis.
- **FR-005**: El sistema DEBE incorporar en la ficha del candidato un control interactivo de un solo clic que abra la interfaz de WhatsApp Web con el número normalizado en estándar E.164 del postulante y un mensaje predefinido de primer contacto.
- **FR-006**: El sistema DEBE validar la unicidad estricta del candidato en el momento de la digitación, ejecutando verificación inmediata por número de documento (DNI/CE), número telefónico normalizado y correo electrónico.
- **FR-007**: Si se detecta una coincidencia por documento, teléfono o correo, el sistema DEBE bloquear la creación de un nuevo registro huérfano y redirigir a la reclutadora hacia la ficha existente con su historial consolidado.
- **FR-008**: El sistema DEBE admitir la carga de documentos de currículo en formatos estándar (PDF y Word/DOCX), asociándolos a la ficha del candidato.
- **FR-009**: Al cargarse un currículo, el sistema DEBE extraer de manera estructurada y asistida las herramientas tecnológicas, años de experiencia, roles previos e idiomas, poniéndolos a disposición de la reclutadora para su validación sin alterar la autoridad humana sobre el dato.

#### Validador Masivo de Planillas de Adecco (Proceso 3)
- **FR-010**: El sistema DEBE permitir la carga por lotes de archivos de planilla electrónica (.xlsx / .csv) remitidos por el proveedor externo Adecco.
- **FR-011**: El sistema DEBE procesar cada registro de la planilla en menos de 100 milisegundos por fila, contrastándolo contra la totalidad de la base histórica de candidatos de TCS.
- **FR-012**: El sistema DEBE clasificar algorítmicamente cada fila de la planilla en uno de tres estados visuales excluyentes:
  - 🔴 **Rojo (Duplicado Activo / Descarte Reciente):** Candidato con proceso en curso o descartado hace menos de 180 días naturales.
  - 🟡 **Amarillo (Reactivable):** Candidato registrado en el sistema con más de 180 días naturales sin proceso activo y con motivo de cierre no excluyente.
  - 🟢 **Verde (Limpio / Inédito):** Candidato que no registra ninguna coincidencia de identidad ni telefónica ni coincidencia fonética significativa en el histórico.
- **FR-013**: La evaluación de duplicados en planillas DEBE aplicar cotejo exacto por documento de identidad, correo y teléfono normalizado E.164, complementado con cotejo fonético aproximado sobre nombres y apellidos para capturar variaciones tipográficas u omisiones de tildes.
- **FR-014**: El sistema DEBE generar un resumen ejecutivo del lote cargado indicando: Total de perfiles procesados, porcentaje de duplicidad, cantidad de reactivables y cantidad de perfiles limpios.
- **FR-015**: El sistema DEBE permitir la descarga de la lista depurada (*shortlist limpio*) en formato estándar y posibilitar la importación en lote de los candidatos verdes hacia la bandeja de entrada de candidatos nuevos.

#### Generador de Reporte de Exclusión a Demanda bajo Ley 29733 (Proceso 3 y Gobernanza de Proveedores)
- **FR-016**: El sistema DEBE incluir un generador a demanda del Reporte de Exclusión para Adecco, ejecutable con un solo clic en cualquier instante sin restricción de día u horario.
- **FR-017**: El Reporte de Exclusión DEBE contener únicamente los siguientes campos por registro: Tipo de Documento, Número de Documento (DNI/CE), Primer Apellido, Inicial del Nombre, Identificador de Vacante o Perfil y Fecha de Vigencia de la Exclusión.
- **FR-018**: En cumplimiento estricto de la Ley N° 29733 (Protección de Datos Personales), el sistema DEBE omitir de forma absoluta del reporte de exclusión cualquier dato de pretensión salarial, tarifas presupuestales, teléfonos personales, correos, notas privadas de evaluación y motivos sensibles de descarte.
- **FR-019**: El sistema DEBE registrar en una bitácora de auditoría inmutable cada generación de reporte de exclusión, detallando usuario que lo solicitó, marca de tiempo y cantidad de registros exportados.

#### Módulo de Compensación y Simulador CTC con Factor 1.56 (Gobernanza Financiera)
- **FR-020**: El sistema DEBE calcular automáticamente el Costo Empresa (CTC Solicitado) multiplicando la remuneración mensual bruta pretendida por el factor laboral estándar de 1.56, fundamentado en los sobrecostos del Régimen Laboral Privado D.L. 728 de Perú.
- **FR-021**: El sistema DEBE contrastar el CTC Solicitado contra el presupuesto autorizado para el rol (`CTC Presupuestado`) calculando el porcentaje de variación presupuestal mediante la fórmula: `(CTC Solicitado - CTC Presupuestado) / CTC Presupuestado * 100`.
- **FR-022**: El sistema DEBE incorporar una guarda lógica contra división por cero que impida la generación del error `#DIV/0!`: si el CTC Presupuestado es nulo, cero o negativo, el cálculo no debe ejecutarse, asignando un estado descriptivo ("Sin Presupuesto Asignado") y manteniendo la estabilidad numérica.
- **FR-023**: El sistema DEBE proveer un semáforo visual financiero que alerte a la reclutadora durante la llamada telefónica si la pretensión del candidato se encuentra dentro del presupuesto (verde), con desvío moderado de hasta 10% (ámbar) o desvío crítico superior al 10% (rojo).

#### Detección de Candidatos Boomerang (Ex-Colaboradores TCS)
- **FR-024**: El sistema DEBE contrastar de forma automática todo DNI ingresado contra el repositorio corporativo histórico de ex-colaboradores de TCS Perú.
- **FR-025**: Al existir coincidencia, el sistema DEBE emitir una alerta visual prioritaria en la ficha del candidato indicando su condición de "Ex-Colaborador TCS (Boomerang)", especificando el periodo de servicio previo, la cuenta o proyecto en el que laboró y su condición de recontratabilidad.
- **FR-026**: Si el registro histórico señala al ex-colaborador como no elegible para reingreso, el sistema DEBE emitir una advertencia de compliance para que la reclutadora detenga el avance del proceso antes de comprometer entrevistas con el cliente.

#### Principios Constitucionales de Gobernanza y Human-in-the-Loop
- **FR-027**: El sistema DEBE garantizar que ninguna funcionalidad de asistencia o inteligencia artificial descarte automáticamente a un candidato, modifique unilateralmente su estado o tome decisiones de contratación; toda transición de estado y descarte DEBE ser ejecutada y ratificada por una persona humana (reclutadora o líder de selección).
- **FR-028**: La llamada telefónica de validación técnica y screening (con sus 7 dimensiones de evaluación: disponibilidad, validación técnica, pretensión salarial, interés, modalidad, factibilidad de traslado e impresión general) DEBE ser realizada íntegramente por un ser humano, limitándose el sistema a brindar fichas y resúmenes de soporte.
- **FR-029**: En estricto apego al principio constitucional anti-scraping, el sistema DEBE operar exclusivamente sobre datos propios almacenados internamente y archivos formalmente importados/exportados, sin ejecutar ningún mecanismo de automatización sobre la web de LinkedIn Recruiter.
- **FR-030**: Los modelos de análisis y extracción estructurada NO DEBEN considerar en ningún momento atributos protegidos (edad, género, estado civil, dirección domiciliaria exacta o fotografía) para calificar perfiles, garantizando una evaluación técnica objetiva y auditable.

---

### Key Entities *(mandatory)*

- **Candidato (Ficha de Identidad Centralizada):**  
  Representa a la persona física individual como entidad única en la organización. Sus atributos funcionales clave comprenden: Tipo y Número de Documento de Identidad (DNI/CE/Pasaporte, único), Nombres de Pila, Apellido Paterno, Apellido Materno, Teléfono Móvil Canónico (estándar E.164, único), Correo Electrónico Principal (único), Fecha de Nacimiento, Edad Calculada Dinámicamente, Ubigeo / Distrito de Residencia, Condición de Ex-Colaborador TCS (Boomerang), y Fecha de Creación/Actualización. Posee una relación 1:N con las Postulaciones a procesos.

- **Postulación a Proceso (Ciclo de Vida en Embudo):**  
  Modela la participación formal de un candidato en una vacante o requerimiento específico. Sus atributos funcionales comprenden: Identificador de Postulación, Referencia al Candidato, Cuenta o Cliente Corporativo (ej. BCP, Entel, Banco Falabella), Identificador de Requerimiento (RGS/Vacante), Perfil Técnico Solicitado, Reclutadora Responsable Asignada, Fuente de Reclutamiento de Origen (Adecco, Offshore, BYB, LinkedIn), Trimestre Fiscal Corporativo (Q1, Q2, Q3, Q4), Estado Operativo del Embudo (`Nuevo`, `En proceso`, `Screening telefónico`, `Pendiente entrevistas`, `Pendiente envío cliente`, `Oferta aceptada`, `No apto`, `Desistió`), Disponibilidad de Incorporación, Observaciones Cualitativas y Trazabilidad Cronológica.

- **Evaluación Financiera y CTC (Compensación Laboral):**  
  Entidad vinculada a la postulación que gobierna el análisis de viabilidad económica. Sus atributos comprenden: Expectativa Salarial Bruta Mensual (PEN), Factor Legal CTC Aplicado (1.56), Costo Empresa Solicitado (Calculado), Techo Presupuestal CTC del Rol, Variación Presupuestal Porcentual (Calculada con guarda contra división por cero), y Estado del Semáforo Presupuestal (En Banda, Observado, Fuera de Banda).

- **Verificación de Compliance y Antecedentes:**  
  Entidad asociada a la postulación para el control de riesgos y filtros institucionales. Atributos: Estado de Verificación Personal BGC (`Pendiente`, `En proceso`, `Aprobado`, `Observado`), Consulta de Centrales de Riesgo Crediticio (Equifax/Infocorp: Sí/No registra deuda castigada excluyente), Fecha de Consulta y Notas de Cumplimiento Legal.

- **Historial Alumni TCS (Repositorio de Ex-Colaboradores):**  
  Entidad corporativa de referencia para la detección de candidatos Boomerang. Atributos: Número de Documento (DNI/CE), Nombres Completos, Último Periodo Laborado (Fecha Inicio - Fecha Fin), Última Cuenta/Proyecto Asignado, Motivo de Desvinculación, y Estatus de Recontratabilidad (`Rehire Eligible`, `Do Not Rehire`, `Requiere Aprobación RH`).

- **Lote de Planilla de Proveedor (Ingesta Adecco):**  
  Entidad que registra cada sesión de carga masiva de candidatos remitidos por agencias externas. Atributos: Identificador del Lote, Nombre del Proveedor, Fecha y Hora de Carga, Reclutadora que Ingesta, Nombre del Archivo Original, Total de Filas Leídas, Cantidad de Duplicados Rojos, Cantidad de Reactivables Amarillos y Cantidad de Perfiles Limpios Verdes.

- **Reporte de Exclusión de Proveedor (Exportación a Demanda):**  
  Entidad que audita las descargas de listas de exclusión para proveedores. Atributos: Identificador de Reporte, Destinatario (Adecco), Fecha y Hora de Generación, Usuario Solicitante, Cantidad de Candidatos Excluidos, y Periodo de Vigencia de la Exclusión.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Erradicación del Proceso 1 - Registro Manual):**  
  Reducir el tiempo promedio de registro y creación de ficha de un candidato de 6-8 minutos (en el ecosistema manual de Excel) a menos de 45 segundos utilizando el autollenado por DNI y la extracción estructurada de CV, recuperando el 100% de las **25 horas semanales** de esfuerzo invertidas en transcripción manual.
- **SC-002 (Erradicación del Proceso 3 - Cruce con Adecco):**  
  Reducir el tiempo de validación de una planilla semanal de Adecco de 50 filas de 60 minutos a menos de 5 segundos con el validador algorítmico de semáforo, recuperando el 100% de las **5 horas semanales** dedicadas al cruce manual de postulantes.
- **SC-003 (Recuperación del Proceso 2 - Actualización de Estados):**  
  Permitir la actualización de estados de postulación y registro de notas en un solo clic sincronizado en tiempo real para todo el equipo, eliminando la apertura asíncrona permanente de libros de Excel locales y recuperando las **5 horas semanales** de mantenimiento de históricos.
- **SC-004 (Cero Errores Numéricos y de Normalización):**  
  Lograr una tasa de 0.00% de ocurrencias del error de división por cero (`#DIV/0!`), 0.00% de errores en cálculo de edad (cero candidatos con 127 años), y un 100% de cumplimiento en la normalización de números celulares bajo el estándar canónico internacional E.164 (`+519XXXXXXXX`).
- **SC-005 (Protección Legal y Anonimización Estricta Ley 29733):**  
  Garantizar un 100% de cumplimiento normativo en los reportes de exclusión generados para proveedores externos, con 0.00% de filtración de remuneraciones, tarifas de facturación, notas privadas de evaluación o atributos demográficos protegidos.
- **SC-006 (Incremento de Efectividad del Proveedor Externo):**  
  Elevar el ratio de perfiles útiles remitidos por Adecco del 10% actual (donde 9 de cada 10 son repetidos o inadecuados) a al menos 35% en los primeros 60 días de entrega regular del reporte de exclusión a demanda.
- **SC-007 (Detección de Talento Boomerang en Tiempo Real):**  
  Identificar al 100% de los ex-colaboradores de TCS postulantes en el instante exacto de ingresar su DNI, reduciendo el tiempo de verificación de antecedentes internos de 3 días a menos de 1 segundo.

---

## Assumptions

- **A-001 (Disponibilidad de Servicio de Identidad):** Se asume que el servicio nacional de consulta de identidad (Reniec / APIs de identidad peruanas autorizadas) mantiene una disponibilidad operativa de al menos 99% en días hábiles; en caso de caída temporal, el sistema contempla fallback a digitación manual con marca de verificación pendiente.
- **A-002 (Estandarización de Documentos Nacionales):** Se asume que la gran mayoría (>90%) de las búsquedas de talento local en Perú involucran profesionales con DNI peruano de 8 dígitos, mientras que profesionales extranjeros con Carné de Extranjería o Pasaporte son soportados mediante validación manual estructurada.
- **A-003 (Factor de Cargas Sociales 1.56):** Se asume que el factor multiplicador 1.56 representa con fidelidad la estructura de costos laborales del Régimen General Privado (D.L. 728) acordada entre la gerencia de Reclutamiento y el área financiera de TCS Perú para fines de evaluación preliminar en selección.
- **A-004 (Autoridad y Juicio Humano Innegociable):** Se asume que la reclutadora humana siempre tiene la facultad de revisar, editar, confirmar o rectificar cualquier sugerencia, extracción o advertencia generada por el sistema antes de guardar o derivar un perfil.
- **A-005 (Operación Desacoplada de LinkedIn):** Se asume que no existe dependencia ni integración directa no oficial con LinkedIn Recruiter; el sourcing continúa ejecutándose en dicha plataforma según sus términos comerciales y los datos ingresan al sistema mediante exportaciones autorizadas (XLSX, CSV) o carga individual de CVs.
- **A-006 (Hardware y Conectividad del Usuario):** Se asume que las reclutadoras y analistas operan desde estaciones de trabajo corporativas de TCS con acceso a navegadores web modernos y conectividad a la red corporativa para interactuar con WhatsApp Web.
- **A-007 (Acuerdo Operativo con Adecco):** Se asume que el proveedor externo Adecco aceptará recibir y utilizar el reporte de exclusión a demanda como filtro previo mandatario antes de iniciar sus jornadas de búsqueda y remitir sus planillas semanales.
