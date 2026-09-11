# Feature Specification: ATS Core MVP (Erradicación de Fricción Manual y Gestión Centralizada)

**Feature Branch**: `001-ats-core-mvp`  
**Created**: 2026-09-10  
**Status**: Draft  
**Input**: User description: "ats-core-mvp: Erradicar las 35 horas semanales de dolor operativo del equipo de Reclutamiento y Selección mediante la Ficha Única de Candidato con autollenado de DNI y normalización E.164, Validador masivo de planillas de Adecco con semáforo de duplicados, Generador a demanda de reporte de exclusión bajo Ley 29733, Simulador financiero CTC con Factor 1.56 blindado contra división por cero, y Alerta automática de ex-colaboradores TCS (Boomerang)." + Requerimiento mandatorio añadido en Gate de Revisión: "En todo esto debe haber un sistema de registro e inicio de sesión, y que al hacer cambios (subir archivos, cambiar datos, etc.), todos estos queden con el registro de quien lo realizó".

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ficha Única de Candidato con Autollenado por DNI, Normalización E.164, Parsing Estructurado de CVs y Registro de Validación Humana (Priority: P1)

Como reclutadora técnica o analista de selección de TCS,  
quiero registrar a un candidato nuevo ingresando únicamente su documento de identidad (DNI peruano de 8 dígitos) o adjuntando su archivo de CV, obteniendo la normalización automática de su teléfono móvil a formato canónico internacional (+51), un enlace directo de 1-clic a WhatsApp Web con mensaje protocolar, una alerta de viabilidad de transporte geográfico y la captura estructurada de las 7 dimensiones de la llamada de validación telefónica,  
para erradicar las 25 horas semanales dedicadas a transcribir datos fila por fila en el Excel operativo (`BD GENERAL FY27`), evitando errores de tipeo, cálculos absurdos de edad (como los 127 años de la plantilla anterior), duplicados en el pipeline y deserciones por incompatibilidad de traslado.

**Why this priority**: Es la base angular del sistema y el núcleo de mayor retorno operativo. Ataca de forma frontal el **Proceso 1 (Registro manual de candidatos)**, el cual consume 25 horas semanales del equipo (5 horas diarias acumuladas). Sin una ficha unificada y validada en el punto de entrada, cualquier dato downstream (búsquedas, reportes, comunicación y compliance) nace corrupto o fragmentado.

**Independent Test**: Puede ser probado de forma 100% autónoma registrando un candidato con solo ingresar un DNI de 8 dígitos y un teléfono móvil de 9 dígitos. El sistema autocompleta nombres y apellidos oficiales, calcula la edad real sin anomalías, almacena el teléfono en formato canónico internacional (`+519XXXXXXXX`), proporciona un botón activo de WhatsApp Web, permite subir un CV para extraer automáticamente competencias clave, compara el distrito de residencia contra la sede de trabajo emitiendo alertas de traslado, y registra los resultados de las 7 dimensiones de la llamada de validación sin depender de ninguna otra funcionalidad externa.

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
   **Given** que ya existe en la base corporativa un candidato registrado con DNI `46753314` o celular `+51987844071` o correo `b.ray.gch7@gmail.com`,  
   **When** una reclutadora intenta crear una nueva ficha utilizando dicho DNI, celular o correo electrónico,  
   **Then** el sistema interrumpe el registro, muestra una alerta no bloqueante indicando el duplicado, despliega el nombre del candidato, el reclutador responsable actual, la fecha del último contacto y un enlace directo para abrir la ficha histórica existente en lugar de crear un registro huérfano.

4. **Scenario 1.4 (Extracción estructurada inicial de CV adjunto):**  
   **Given** que la reclutadora carga un archivo de currículo en formato estándar (PDF o Word) al crear o editar una ficha,  
   **When** se completa la carga documental,  
   **Then** el sistema extrae de forma asistida y sin sesgos demográficos el resumen de competencias tecnológicas principales, años estimados de experiencia laboral, enlaces profesionales externos y nivel de idiomas, presentándolos en campos estructurados editables para confirmación humana antes de guardar.

5. **Scenario 1.5 (Captura de las 7 dimensiones de la llamada humana y alerta geográfica de traslado):**  
   **Given** que la reclutadora realiza la llamada telefónica de screening al candidato,  
   **When** ingresa a la sección de validación cualitativa en la ficha de postulación,  
   **Then** el sistema provee campos estructurados para registrar los 7 objetivos obligatorios: disponibilidad de inicio (Inmediata, 1 semana, 2 semanas, 1 mes), resumen técnico validado, expectativa salarial, interés en la vacante, aceptación de modalidad (híbrido/remoto), viabilidad de traslado geográfico con alerta de distancia (ej. alerta si reside en Villa María del Triunfo y la sede asignada es BCP La Molina), e impresión general, salvaguardando que la llamada y su veredicto sean ejecutados exclusivamente por una persona humana.

6. **Scenario 1.6 (Respuesta ante DNI no encontrado en el padrón oficial):**  
   **Given** que la reclutadora ingresa un número de 8 dígitos que no existe en los registros del padrón nacional de identidad,  
   **When** se ejecuta la validación de identidad,  
   **Then** el sistema notifica: "Documento no registrado en el padrón oficial de identidad. Verifique el número o complete los datos manualmente", habilitando la edición manual de nombres, apellidos y fecha de nacimiento, asignando a la ficha el distintivo "Pendiente de regularización de identidad".

---

### User Story 2 - Validador Masivo de Planillas Excel de Adecco con Semáforo Algorítmico y Detección Cruzada (Priority: P2)

Como reclutadora técnica responsable de la gestión de proveedores externos,  
quiero cargar en el sistema la planilla periódica remitida por Adecco con decenas de candidatos propuestos,  
para obtener en segundos un reporte comparativo con código de semáforo (🔴 Duplicado activo o exclusión permanente, 🟡 Reactivable >6 meses, 🟢 Limpio/Inédito), con detección cruzada de ex-colaboradores TCS y tolerancia a formatos heterogéneos,  
para saber exactamente cuáles perfiles ya fueron gestionados por TCS y cuáles son realmente inéditos, erradicando las 5 horas semanales de cotejo manual (Proceso 3) y evitando el pago indebido de comisiones por talento conocido.

**Why this priority**: Ataca directamente el **Proceso 3 (Cruce de candidatos con Adecco)** que consume 5 horas semanales. Hoy el equipo recibe planillas pesadas con candidatos que en un 90% ya fueron contactados, evaluados o descartados por TCS. Esta validación manual genera demoras operativas, roces con el proveedor y recontactos vergonzosos a profesionales que ya habían sido descartados.

**Independent Test**: Puede ser probado de forma independiente subiendo un archivo de planilla de prueba con 20 registros variados (5 idénticos a candidatos activos en TCS, 3 descartados hace más de 6 meses por pretensión salarial, 2 descartados por antecedentes/ética no recuperables, 2 ex-colaboradores TCS, y 8 totalmente nuevos). El sistema debe clasificar el 100% de las filas en las categorías del semáforo con su justificación correspondiente en menos de 5 segundos, alertar los casos de ex-colaboradores para evitar comisiones, y permitir descargar el listado depurado con un solo clic.

**Acceptance Scenarios**:

1. **Scenario 2.1 (Clasificación 🔴 Rojo - Duplicado Activo o Descarte Reciente):**  
   **Given** una fila de la planilla de Adecco con un candidato cuyo DNI, correo, teléfono normalizado o nombre con similitud fonética alta coincide con un registro de TCS en estado activo (`En proceso`, `En entrevista`) o descartado hace menos de 180 días naturales,  
   **When** el sistema ejecuta la validación algorítmica,  
   **Then** marca la fila con distintivo rojo (🔴), indica el motivo de la coincidencia ("En proceso activo en cuenta BCP" o "Descartado el 15/07/2026: No superó filtro técnico"), señala la reclutadora responsable y excluye el perfil de la lista limpia a procesar.

2. **Scenario 2.2 (Clasificación 🔴 Rojo - Descarte Histórico Permanente / No Recuperable):**  
   **Given** una fila de la planilla de Adecco con un candidato registrado en TCS cuya postulación fue cerrada hace más de 180 días (incluso años previos), pero cuyo motivo de descarte fue de carácter excluyente permanente (ej. "No apto en verificación personal BGC", "Falta a la ética", "Deuda castigada bancaria excluyente" o "Do Not Rehire"),  
   **When** el sistema evalúa el antecedente,  
   **Then** clasifica la fila indefectiblemente como roja (🔴 "Exclusión Permanente: No Elegible"), bloqueando cualquier categorización como reactivable amarillo sin importar el tiempo transcurrido.

3. **Scenario 2.3 (Clasificación 🟡 Amarillo - Candidato Reactivable > 6 meses con Cierre No Excluyente):**  
   **Given** una fila de la planilla de Adecco correspondiente a un candidato que postuló a TCS hace más de 180 días naturales y cuyo motivo de cierre fue subsanable o temporal (ej. "Expectativa salarial sobre presupuesto" o "Vacante cancelada por cliente"),  
   **When** el sistema evalúa el registro contra las reglas de reactivación temporal,  
   **Then** marca la fila con distintivo amarillo (🟡), detalla el antecedente histórico y ofrece la opción de reactivarlo asociándolo a la nueva vacante sin sobrescribir su historial anterior.

4. **Scenario 2.4 (Clasificación 🟢 Verde - Candidato Inédito y Limpio):**  
   **Given** una fila de la planilla de Adecco cuyos datos de identidad, teléfono, correo y coincidencia fonética no registran ninguna coincidencia en el histórico de TCS,  
   **When** concluye la evaluación del archivo,  
   **Then** marca la fila con distintivo verde (🟢), habilitando la importación masiva directa hacia la bandeja de entrada de candidatos nuevos listos para llamada de validación telefónica humana.

5. **Scenario 2.5 (Alerta de Ex-Colaborador TCS en Planilla Externa):**  
   **Given** una fila de la planilla de Adecco donde el candidato figura en la base histórica de ex-empleados de TCS,  
   **When** se procesa la validación del lote,  
   **Then** el sistema emite una insignia distintiva (🟣 "Ex-Colaborador TCS") alertando que el perfil pertenece al pool Alumni de la compañía, evitando que se reconozca comisión comercial de colocación a la agencia externa por un recurso propio y direccionando el caso a reclutamiento directo si es recontratable.

6. **Scenario 2.6 (Tolerancia a esquemas heterogéneos y encabezados con alias):**  
   **Given** que la planilla de Adecco presenta variaciones en los nombres de columnas (ej. `Móvil` o `Teléfono` en lugar de `Celular`; `Documento` en vez de `DNI / CE`), celdas combinadas o filas iniciales en blanco,  
   **When** se carga el archivo,  
   **Then** el sistema mapea semánticamente los encabezados contra el diccionario canónico, omite filas vacías y procesa los datos sin requerir que la reclutadora modifique manualmente el archivo Excel original.

---

### User Story 3 - Generador a Demanda de Reporte de Exclusión Anonimizado para Adecco según Ley 29733 (Priority: P3)

Como reclutadora técnica o líder de selección,  
quiero generar y descargar en cualquier momento con un solo clic un reporte de exclusión para Adecco,  
para entregar al proveedor la lista de profesionales que TCS ya tiene en proceso o en periodo de enfriamiento, garantizando el estricto cumplimiento de la Ley N° 29733 (Ley de Protección de Datos Personales de Perú) al anonimizar datos sensibles como pretensiones salariales, notas privadas y evaluaciones internas.

**Why this priority**: Ataca la causa raíz del problema con el proveedor externo. Adecco remite candidatos duplicados porque busca a ciegas. Si TCS le entrega periódicamente a demanda la lista de exclusión antes de que inicien sus búsquedas, se evita que busquen a los mismos candidatos, elevando el ratio de CV útil del 10% actual hacia más del 35% y eliminando el retrabajo de raíz.

**Independent Test**: Puede ser probado de forma independiente pulsando el botón "Generar Reporte de Exclusión Adecco" en la aplicación. El sistema compila los candidatos en estado activo y exclusión temporal, anonimiza los datos (mostrando DNI, primer apellido, inicial del nombre, fecha de vigencia de exclusión y perfil técnico; omitiendo remuneraciones, correo, celular y notas privadas), y descarga un archivo en formato estructurado estándar (.xlsx/.csv).

**Acceptance Scenarios**:

1. **Scenario 3.1 (Generación a demanda en 1-clic):**  
   **Given** que existen 450 candidatos en el sistema clasificados en estados que ameritan exclusión (en proceso de screening, entrevistas con clientes, ofertas en curso o descartados hace menos de 180 días),  
   **When** la reclutadora hace clic en "Descargar Reporte de Exclusión Adecco",  
   **Then** el sistema compila en menos de 2 segundos el archivo descargable actualizado al instante exacto, registrando en la auditoría del sistema la fecha, hora y usuario que efectuó la descarga.

2. **Scenario 3.2 (Anonimización estricta bajo Ley N° 29733):**  
   **Given** el listado de candidatos a incluir en el reporte para el proveedor externo,  
   **When** se construye la estructura del archivo de exportación,  
   **Then** el archivo contiene únicamente: Tipo y Número de Documento (DNI/CE), Primer Apellido e Inicial del Nombre, Código de Vacante/Perfil y Fecha hasta la cual aplica la exclusión; quedando estrictamente censurados y excluidos el número telefónico personal, correo electrónico, pretensión salarial, tarifas de facturación del cliente, notas cualitativas de descarte y cualquier atributo protegido.

3. **Scenario 3.3 (Filtro por cuenta o cliente específico):**  
   **Given** que el encargo a Adecco aplica únicamente a requerimientos de una cuenta cliente determinada (ej. BCP),  
   **When** la reclutadora selecciona la cuenta antes de descargar,  
   **Then** el sistema permite opcionalmente descargar la exclusión general consolidada o la exclusión segmentada por cuenta según la necesidad operativa del encargo.

4. **Scenario 3.4 (Exportación cuando no existen candidatos excluidos en el filtro):**  
   **Given** que para una cuenta cliente específica no existen candidatos en estado de exclusión activa,  
   **When** se solicita la descarga del reporte,  
   **Then** el sistema genera un archivo válido con los encabezados regulatorios y una fila informativa limpia indicando "Sin registros en periodo de exclusión activa para la cuenta seleccionada", evitando descargas vacías o fallos de archivo corrupto.

---

### User Story 4 - Simulador Financiero y Calculadora Dinámica de Costo Empresa CTC con Guardas Matemáticas y Manejo Neto/Bruto (Priority: P4)

Como reclutadora técnica durante la llamada telefónica o analista de selección al recibir una pretensión salarial,  
quiero ingresar la expectativa salarial mensual del postulante (en valor bruto o neto en Soles) y contrastarla instantáneamente contra el presupuesto autorizado de la vacante bajo el régimen laboral peruano D.L. 728 (Factor 1.56),  
para conocer la viabilidad económica en tiempo real, visualizar el semáforo presupuestal y erradicar por completo los errores matemáticos de división por cero (`#DIV/0!`) que corrompen las hojas de cálculo.

**Why this priority**: Resuelve la fragilidad financiera evidenciada en las columnas U, V, W y X del Excel `BD GENERAL FY27`. Los errores de `#DIV/0!` en el Excel paralizan las aprobaciones de finanzas, provocan ofertas inconsistentes y demandan tiempo de reproceso entre reclutamiento y control de gestión.

**Independent Test**: Puede ser probado de forma independiente ingresando una expectativa bruta de S/. 6,000 en una vacante con presupuesto CTC de S/. 12,410. El sistema calcula automáticamente el Costo Empresa de S/. 9,360 ($6000 \times 1.56$), reporta una variación de -24.58% (holgadamente dentro del presupuesto), y cuando se borra o se coloca en 0 el presupuesto del rol, la variación muestra un indicador neutral de "Sin presupuesto asignado" en lugar de fallar con `#DIV/0!`.

**Acceptance Scenarios**:

1. **Scenario 4.1 (Cálculo exacto del Costo Empresa mediante Factor legal 1.56):**  
   **Given** que un candidato comunica una pretensión salarial bruta de S/. 5,000 mensuales en moneda nacional (PEN),  
   **When** la reclutadora registra dicho valor en la ficha de postulación seleccionando la modalidad "Bruto",  
   **Then** el sistema aplica de inmediato el multiplicador laboral de 1.56 derivado de las cargas sociales del Régimen Privado D.L. 728 (Gratificaciones legales, Bonificación extraordinaria 9%, CTS, EsSalud 9%, Vacaciones, Seguro Vida Ley) y muestra el Costo Empresa (CTC Solicitado) exacto de S/. 7,800.00.

2. **Scenario 4.2 (Tratamiento asistido de expectativa en Sueldo Neto a Bruto estimado):**  
   **Given** que durante la llamada el candidato declara su expectativa en dinero líquido de bolsillo (ej. "S/. 5,000 netos mensuales"),  
   **When** la reclutadora marca la opción "Neto" en el simulador,  
   **Then** el sistema aplica el factor de conversión tributaria y previsional representativo del régimen peruano (retención estimada de 5ta categoría y aportes AFP/ONP de ~21%) proyectando un salario bruto referencial de ~S/. 6,330.00 antes de computar el CTC de S/. 9,874.80 ($6,330 \times 1.56$), permitiendo a la reclutadora transparentar el costo real ante el candidato y finanzas.

3. **Scenario 4.3 (Cálculo protegido de variación presupuestal sin `#DIV/0!`):**  
   **Given** un registro donde el Costo Empresa presupuestado para el rol aún no ha sido cargado o es igual a cero (0.00),  
   **When** el sistema calcula el indicador de variación presupuestal,  
   **Then** activa una guarda matemática que previene la indeterminación, no emite ningún error visual ni matemático, y despliega en la interfaz la etiqueta informativa "Pendiente de Presupuesto", manteniendo la integridad de los datos.

4. **Scenario 4.4 (Semáforo de viabilidad financiera):**  
   **Given** una postulación donde el CTC Solicitado es contrastado contra un CTC Presupuestado válido de S/. 10,000,  
   **When** el valor solicitado es:  
   - Menor o igual al presupuesto (ej. S/. 8,500 $\to$ variación -15.00%): muestra semáforo verde ("Dentro de Presupuesto").  
   - Hasta 10% por encima del presupuesto (ej. S/. 10,800 $\to$ variación +8.00%): muestra semáforo ámbar ("Requiere Aprobación Especial").  
   - Más del 10% por encima del presupuesto (ej. S/. 13,000 $\to$ variación +30.00%): muestra semáforo rojo ("Fuera de Banda Salarial").  
   **Then** la reclutadora dispone de argumentos objetivos para negociar durante la llamada o tramitar excepciones con el Delivery Manager.

5. **Scenario 4.5 (Validación de límites y montos atípicos):**  
   **Given** que la reclutadora ingresa una expectativa salarial mensual menor al Sueldo Mínimo Vital (S/. 1,025) o superior a S/. 35,000 mensuales,  
   **When** se procesa el campo numérico,  
   **Then** el sistema solicita confirmación mediante un aviso preventivo ("¿El monto ingresado corresponde a un valor mensual o anual?"), evitando distorsiones por digitación de salarios anualizados.

---

### User Story 5 - Alerta Automática de Ex-Colaboradores TCS (Candidatos Boomerang) con Reconciliación Fonética Multicriterio (Priority: P5)

Como reclutadora técnica o coordinadora de selección,  
quiero que el sistema identifique de forma automática mediante DNI, correo electrónico histórico o cotejo fonético si el candidato postulante laboró previamente en TCS Perú o sedes asociadas,  
para visualizar de inmediato su antecedente corporativo, fecha de cese, cuenta en la que prestó servicios y condición de recontratabilidad (*Re-hire Eligibility*), acelerando el ciclo de contratación y mitigando riesgos de reincorporación no autorizada.

**Why this priority**: Resuelve la Columna AA del Excel (`Ha trabajado antes en TCS`), la cual hoy se llena de manera empírica si el candidato lo menciona voluntariamente. Detectar tempranamente a ex-colaboradores (*candidatos Boomerang*) permite aprovechar talento que ya conoce los estándares técnicos y la cultura de TCS, reduciendo los tiempos de inducción a cero, o bien alertar si la persona salió bajo condiciones que impiden su recontratación.

**Independent Test**: Puede ser probado de forma independiente registrando un candidato cuyo DNI, correo histórico o nombre completo coincida con la base de datos histórica de ex-colaboradores. El sistema debe emitir una insignia visual en la ficha destacando "Ex-Colaborador TCS (Boomerang)" y desplegando el historial corporativo previo (último proyecto, periodo laborado y estatus de recontratación según Recursos Humanos).

**Acceptance Scenarios**:

1. **Scenario 5.1 (Detección positiva de talento Boomerang elegible por DNI):**  
   **Given** que una reclutadora ingresa el DNI de un profesional que trabajó en TCS entre 2022 y 2024 y cuya salida fue voluntaria con evaluación favorable,  
   **When** se procesa la consulta de identidad,  
   **Then** el sistema muestra una alerta visual azul/verde destacada: "Candidato Boomerang: Ex-colaborador TCS (Cuenta Entel, 2022-2024). Condición: Recontratable", facilitando la priorización del perfil en la cola de llamadas.

2. **Scenario 5.2 (Alerta preventiva de candidato no recontratable):**  
   **Given** que el DNI o correo ingresado corresponde a un ex-empleado registrado con marca corporativa de no recontratación (*Do Not Rehire*),  
   **When** el sistema coteja el registro con el catálogo histórico,  
   **Then** emite una advertencia de compliance de alta prioridad para la reclutadora, sugiriendo validar el caso con la gerencia de Recursos Humanos antes de coordinar cualquier entrevista con el cliente.

3. **Scenario 5.3 (Detección por coincidencia fonética y nombres compuestos en ausencia de DNI):**  
   **Given** un ex-colaborador registrado en la base histórica antigua sin DNI registrado (ej. extrabajador registrado únicamente como "María del Carmen De la Cruz"),  
   **When** ingresa un candidato con nombre idéntico o fonéticamente equivalente,  
   **Then** el sistema emite una advertencia de coincidencia probable: "Posible Ex-Colaborador TCS (Coincidencia por nombre 92%): Verificar documento oficial con RRHH", evitando que perfiles antiguos pasen desapercibidos.

4. **Scenario 5.4 (Candidato nuevo sin antecedentes en la compañía):**  
   **Given** que ni el DNI ni el correo ni la fonética registran coincidencias en el historial laboral interno de TCS,  
   **When** se guarda la ficha,  
   **Then** el campo de antecedente TCS se establece automáticamente en "No registra antecedente interno" de forma limpia sin requerir intervención manual.

---

### User Story 6 - Autenticación, Control de Acceso Basado en Roles y Trazabilidad Integral con Registro Inmutable de Auditoría (Priority: P1)

Como reclutadora técnica, analista de selección, coordinador de cuenta o administrador del sistema,  
quiero registrarme, iniciar y cerrar sesión de manera segura con credenciales corporativas protegidas, acceder exclusivamente a las funciones y datos asignados a mi rol operativo, y contar con una bitácora inmutable de auditoría donde cada cambio de datos, subida de archivos, transición de estado, validación masiva o descarga de reporte quede estrictamente vinculado con mi identidad, marca de tiempo y detalle de la modificación,  
para deslindar inequívocamente las responsabilidades operativas sobre los candidatos y postulaciones, prevenir accesos o modificaciones anónimas en el pipeline de selección, y garantizar el estricto cumplimiento de las políticas de custodia de información y la Ley N° 29733.

**Why this priority**: Es el pilar fundacional e innegociable de seguridad, gobernanza y responsabilidad institucional. Sin autenticación individual y trazabilidad integral (audit trail), cualquier alteración en fichas de postulantes, subida de documentos, ingesta de planillas de Adecco o exportación de reportes queda anónima, impidiendo saber quién autorizó una oferta, quién modificó una expectativa salarial, quién cargó un CV o quién ejecutó un descarte, vulnerando los controles de auditoría interna de TCS y las normas de protección de datos personales.

**Independent Test**: Puede ser probado de forma independiente registrando una cuenta con correo institucional (`@tcs.com`) y credencial de acceso robusta, iniciando sesión para obtener acceso autorizado, navegando por el sistema bajo perfiles con diferentes roles (Reclutadora, Coordinador/Administrador, Observador), ejecutando mutaciones de prueba (editar un campo de candidato, subir un CV en PDF, cambiar el estado del embudo, cargar una planilla de prueba y generar el reporte de exclusión), verificando que la bitácora inmutable asiente de inmediato cada evento con el identificador del usuario actor, fecha/hora exacta con zona horaria, acción realizada y valores antes/después, e intentando realizar mutaciones con un rol no autorizado (Observador) o con una sesión cerrada/expirada comprobando el bloqueo preventivo y registro del intento.

**Acceptance Scenarios**:

1. **Scenario 6.1 (Registro e inicio de sesión de usuario corporativo con sesión protegida):**  
   **Given** un integrante del equipo de selección que cuenta con correo institucional de la compañía (`@tcs.com`),  
   **When** completa el formulario de registro ingresando sus nombres completos, correo corporativo y una credencial de acceso que satisfaga las políticas institucionales de robustez,  
   **Then** el sistema crea la cuenta de usuario de forma segura salvaguardando la confidencialidad de las credenciales sin exponerlas en texto claro, y al iniciar sesión emite una sesión autenticada activa con expiración automática por inactividad, desplegando la identidad del usuario en la interfaz del sistema.

2. **Scenario 6.2 (Control de acceso basado en roles - Reclutadora, Administrador/Coordinador, Observador):**  
   **Given** tres usuarios con diferentes perfiles operativos: Reclutadora (operación ordinaria del embudo), Administrador/Coordinador (gestión de usuarios, autorizaciones presupuestales y auditoría global) y Observador (modo consulta y analítica),  
   **When** el usuario con rol de Observador intenta editar una ficha, subir un currículo o alterar el estado de una postulación,  
   **Then** el sistema bloquea de inmediato la operación de escritura, despliega un aviso formal de permiso denegado ("Acceso denegado: su rol solo posee permisos de consulta"), preserva los datos existentes intactos y registra en la bitácora de seguridad el intento de mutación no autorizada.

3. **Scenario 6.3 (Trazabilidad obligatoria y atómica en mutaciones de Ficha de Candidato y Postulación):**  
   **Given** una reclutadora autenticada con usuario `carla.soto@tcs.com` que visualiza la postulación activa de un candidato,  
   **When** modifica la expectativa salarial de S/. 4,500 a S/. 5,200 o transiciona el estado del embudo de `Screening telefónico` a `Pendiente entrevistas`,  
   **Then** el sistema persiste la modificación y de forma atómica e indisociable genera un registro en la bitácora de auditoría vinculando el identificador del candidato/postulación, el usuario ejecutor, la marca de tiempo exacta con zona horaria, el campo modificado, el valor previo y el valor nuevo, desplegando este evento de inmediato en la línea de tiempo histórica de la ficha.

4. **Scenario 6.4 (Trazabilidad estricta en subida de documentos y carga masiva de planillas de Adecco):**  
   **Given** un usuario autenticado que adjunta un archivo de currículo (CV en PDF o Word) a una ficha o carga una planilla masiva de Adecco con 50 postulantes,  
   **When** culmina con éxito la transferencia y procesamiento del archivo,  
   **Then** el sistema asocia de forma permanente el documento o lote al usuario autenticado, registrando en la bitácora de auditoría el identificador del operador, fecha y hora precisa, nombre original del archivo, tamaño en bytes, identificador de integridad del documento y resultado de la operación, prohibiendo cualquier ingesta documental anónima.

5. **Scenario 6.5 (Trazabilidad de exportaciones regulatorias bajo Ley 29733 y simulaciones financieras):**  
   **Given** un usuario autenticado que solicita la generación y descarga del Reporte de Exclusión para Adecco o formaliza el cálculo de simulación CTC para una oferta,  
   **When** se produce la exportación o el guardado del análisis financiero,  
   **Then** el sistema consigna en la bitácora de auditoría el identificador del usuario solicitante, tipo de acción, parámetros o filtros aplicados, cantidad de registros exportados y estampa temporal exacta, garantizando la rendición de cuentas para fines regulatorios y de control interno.

6. **Scenario 6.6 (Cierre de sesión seguro e invalidación inmediata de sesión activa):**  
   **Given** una reclutadora con una sesión autenticada activa en el sistema,  
   **When** presiona la opción "Cerrar Sesión",  
   **Then** el sistema invalida de inmediato la sesión activa, revoca los identificadores de autorización y redirige a la pantalla de inicio de sesión, impidiendo que cualquier intento de navegación hacia atrás en el historial del navegador permita acceder a información o realizar acciones sin autenticarse nuevamente.

---

### Edge Cases

1. **Documento de Identidad Extranjero o No Estandarizado (Carné de Extranjería / Pasaporte):**  
   ¿Qué ocurre cuando el candidato no cuenta con DNI peruano de 8 dígitos sino con Carné de Extranjería (CE) de 9 o 12 dígitos, o Pasaporte?  
   *Comportamiento del sistema*: El sistema admite tipos de documento alternativos (`CE`, `Pasaporte`). Cuando el tipo es distinto de DNI peruano, inhabilita el autollenado automático por el servicio nacional de identidad, solicita el ingreso manual validado de los nombres y apellidos, y exige obligatoriamente la fecha de nacimiento para garantizar el cálculo dinámico de edad sin provocar el fallo de 127 años.

2. **Falla o Indisponibilidad Temporal del Servicio de Identidad Nacional:**  
   ¿Qué sucede si el servicio externo de consulta de DNI no responde o excede el tiempo límite de espera (timeout > 3 segundos)?  
   *Comportamiento del sistema*: El sistema se degrada elegantemente (*graceful degradation*). Despliega una advertencia sutil ("Servicio de identidad temporalmente inaccesible; proceda con llenado manual"), permite a la reclutadora tipear los nombres y apellidos manualmente, y deja una marca de "Pendiente de verificación de identidad" para revalidación asíncrona posterior con un solo clic.

3. **Agotamiento de Cuota o Rate Limit del Servicio de Identidad Nacional (HTTP 429 / Cuota Mensual):**  
   ¿Qué sucede si el plan contratado con el proveedor de identidad nacional agota sus consultas del mes o supera el límite de transacciones por segundo?  
   *Comportamiento del sistema*: El sistema captura el estado, notifica al administrador del sistema mediante alerta interna ("Límite de consultas de identidad alcanzado"), conmuta de forma automática y transparente a modo de ingreso manual asistido para las reclutadoras, y no interrumpe el flujo de registro de candidatos.

4. **DNI de 8 Dígitos Inexistente o Cancelado en Padrón Nacional:**  
   ¿Qué sucede cuando se ingresa un DNI con formato numérico de 8 dígitos pero que no corresponde a ningún ciudadano registrado o figura como cancelado por defunción?  
   *Comportamiento del sistema*: El sistema informa el motivo exacto devuelto por el servicio oficial ("DNI no hallado en padrón nacional" o "Documento no vigente"), bloquea la continuidad automática y exige a la reclutadora confirmar el número con el candidato antes de proceder con registro manual observado.

5. **Disparidad, Permutaciones y Nombres Compuestos Peruanos en Deduplicación:**  
   ¿Cómo responde el sistema cuando un candidato figura en LinkedIn como "Alonso Huanca", en la planilla de Adecco como "Huanca, Alonso", y en el documento de identidad como "Alonso Jesús Huanca Mamani", o cuando existen partículas compuestas ("De la Cruz", "Del Carpio")?  
   *Comportamiento del sistema*: El algoritmo de reconciliación fonética realiza tokenización de cadenas, remueve partículas y artículos ("de", "la", "del", "los", "san"), identifica posibles inversiones de orden (apellidos primero vs nombres primero) y aplica cotejo de similitud aproximada con umbral mínimo de 85%. Si el DNI no está disponible pero la similitud fonética es alta y el teléfono o correo coinciden, se clasifica como duplicado directo; si solo coincide el nombre fonético, se presenta a la reclutadora como "Coincidencia probable (85%)" para resolución humana con 1 clic.

6. **Formatos Telefónicos Internacionales no Peruanos o Números Incompletos:**  
   ¿Qué sucede cuando se ingresa un número móvil de otro país (ej. Colombia `+57`, Argentina `+54`) o un número incompleto (8 dígitos en vez de 9)?  
   *Comportamiento del sistema*: Si el número cuenta con prefijo de otro país válido, se normaliza al formato canónico E.164 respectivo. Si el número tiene menos de 9 dígitos y no cuenta con código de país identificable, el sistema rechaza la entrada indicando: "Número telefónico inválido. Para números peruanos ingrese los 9 dígitos móviles".

7. **Planilla de Adecco con Encabezados Modificados, Columnas Desordenadas o Celdas Vacías:**  
   ¿Cómo responde el validador de Adecco si el proveedor alteró el nombre de las columnas (ej. puso `Celular` en vez de `Teléfono`), insertó filas vacías al inicio o pegó celdas combinadas?  
   *Comportamiento del sistema*: El módulo de ingesta implementa un diccionario semántico de alias tolerante a variaciones de encabezado comunes (`Celular`, `Teléfono`, `Móvil`, `Contacto`; `DNI`, `Documento`, `DNI/CE`), omite filas enteramente en blanco sin abortar el proceso y, si falta una columna crítica para la deduplicación (DNI o Correo), detiene la importación señalando exactamente la deficiencia encontrada con instrucciones claras de corrección.

8. **Simulación Financiera con Presupuesto Cero, Negativo o Vacío:**  
   ¿Cómo se comporta la calculadora de variación presupuestal si el reclutador ingresa una pretensión salarial pero el presupuesto del rol está en blanco, en cero (`0.00`) o con valor negativo por error?  
   *Comportamiento del sistema*: El cálculo del porcentaje de variación está protegido por una guarda condicional estricta. Si el presupuesto es menor o igual a cero o nulo, la celda de variación porcentual se muestra como valor descriptivo no aplicable ("N/A - Sin Presupuesto Asignado"), imposibilitando matemáticamente la generación del error `#DIV/0!`.

9. **CVs Ilegibles, Protegidos con Contraseña o Escaneados sin Texto Seleccionable:**  
   ¿Qué ocurre cuando la reclutadora sube un CV en PDF que es una imagen escaneada borrosa o tiene clave de apertura?  
   *Comportamiento del sistema*: El sistema detecta el error de lectura, informa a la reclutadora que el documento no posee texto procesable y habilita la edición manual de la ficha, almacenando el archivo adjunto para consulta visual humana sin interrumpir el flujo.

10. **Candidato con Múltiples Postulaciones Simultáneas a Diferentes Cuentas:**  
    ¿Cómo maneja el sistema a un candidato que ya está en proceso para BCP pero calza perfecto para una vacante de Banco Falabella o Entel?  
    *Comportamiento del sistema*: La arquitectura desacopla la ficha de identidad (`Candidato`) de sus participaciones en procesos (`Postulacion`). El candidato conserva una única ficha maestra y puede tener múltiples postulaciones asociadas, emitiendo una alerta al reclutador si se detecta que ya tiene un proceso activo en curso para evitar duplicidad de entrevistas y definir ownership entre reclutadores.

11. **Exportación de Exclusión para Adecco sin Registros Elegibles:**  
    ¿Qué sucede si se solicita la descarga del reporte de exclusión y no existen candidatos en estado de exclusión activa para los filtros aplicados?  
    *Comportamiento del sistema*: El sistema genera el archivo con la cabecera estándar y un aviso informativo indicando que no hay registros excluidos para los parámetros seleccionados, impidiendo descargas fallidas o archivos corruptos.

12. **Descartes Históricos Irreversibles frente al Paso del Tiempo en Validador de Proveedor:**  
    ¿Puede un candidato descartado hace más de 6 meses por motivos éticos, antecedentes penales o fraude ser considerado reactivable amarillo en planillas de Adecco?  
    *Comportamiento del sistema*: Las reglas de reactivación temporal aplican única y exclusivamente a motivos no excluyentes (salario, vacante cerrada, falta momentánea de seniority). Los descartes clasificados como irreversibles o de compliance nunca expiran y se categorizan invariablemente como 🔴 Rojo en cualquier cotejo posterior.

13. **Intentos Reiterados de Autenticación Fallida y Bloqueo Preventivo de Cuenta:**  
    ¿Qué ocurre si un usuario o agente externo ingresa credenciales erróneas de forma reiterada (ej. 5 intentos fallidos consecutivos)?  
    *Comportamiento del sistema*: El sistema incrementa el contador de intentos fallidos, responde con un mensaje neutral que no revele la existencia previa del correo ("Credenciales no válidas"), bloquea preventivamente el acceso a la cuenta durante 15 minutos al superar los 5 intentos y genera un evento de auditoría de seguridad detallando el identificador ingresado y la marca de tiempo.

14. **Expiración de Sesión por Inactividad durante Edición de Ficha o Carga de Datos:**  
    ¿Qué sucede si una reclutadora deja una ficha de candidato o formulario de llamada abierto sin interactuar durante un lapso prolongado (ej. 30 minutos) y luego presiona "Guardar"?  
    *Comportamiento del sistema*: El sistema detecta la sesión expirada, retiene localmente en el navegador los datos modificados para proteger el trabajo de la reclutadora, despliega una ventana modal de reautenticación solicitando credenciales, y tras una validación exitosa, aplica la mutación registrando en la bitácora de auditoría al usuario autenticado sin pérdida de información.

15. **Solicitud de Mutación sin Autenticación Activa o con Permisos Insuficientes:**  
    ¿Qué sucede si se envía una solicitud de modificación de datos, subida de documentos o exportación sin una sesión autenticada válida o desde una cuenta con permisos restringidos (ej. rol Observador intentando editar un candidato)?  
    *Comportamiento del sistema*: El sistema intercepta y deniega categóricamente la solicitud, bloquea la ejecución de cualquier cambio en la base de datos, emite una notificación de "Acceso Denegado" y registra en la bitácora de seguridad el evento con el usuario, rol, recurso objetivo y estampa temporal.

16. **Garantía de Inmutabilidad y Bloqueo de Alteración Retroactiva en la Bitácora de Auditoría:**  
    ¿Puede un usuario con privilegios de Administrador o Coordinador editar, sobrescribir o eliminar registros de la bitácora de auditoría para encubrir un error o modificación indebida?  
    *Comportamiento del sistema*: La bitácora de auditoría es estrictamente inmutable y opera bajo arquitectura de solo adición (*append-only*). La aplicación no provee interfaces ni mecanismos funcionales para modificar o purgar asientos históricos. Cualquier consulta a la bitácora es de solo lectura y cualquier intento de mutación directa es rechazado por las políticas de integridad de datos del sistema.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Identidad Nacional, Normalización de Contacto y Ficha Única (Proceso 1)
- **FR-001**: El sistema DEBE proveer un formulario unificado de registro de candidato ("Ficha Única") accesible vía interfaz web que consolide los 28 atributos operativos del proceso eliminando las 11 pestañas del Excel manual.
- **FR-002**: Al ingresar un número de DNI peruano de 8 dígitos, el sistema DEBE consultar en tiempo real el servicio de validación de identidad nacional y autocompletar de forma obligatoria: nombres de pila, apellido paterno, apellido materno, fecha de nacimiento y distrito de residencia.
- **FR-003**: En caso de que el DNI no exista en el padrón, el servicio externo no responda o la cuota del proveedor se agote, el sistema DEBE degradarse elegantemente a modo de digitación manual asistida con marca visible de "Pendiente de regularización de identidad".
- **FR-004**: El sistema DEBE calcular la edad cronológica del candidato de manera dinámica a partir de la fecha de nacimiento (`Fecha actual - Fecha de nacimiento`), asignando valor no aplicable si la fecha de nacimiento no está disponible, prohibiendo terminantemente cualquier valor estático o el cálculo erróneo de 127 años.
- **FR-005**: El sistema DEBE normalizar todo número telefónico registrado al estándar canónico internacional E.164 (`+519XXXXXXXX` para móviles peruanos), eliminando prefijos redundantemente digitados (`51`, `+51`), espacios, guiones y paréntesis.
- **FR-006**: El sistema DEBE incorporar en la ficha del candidato un control interactivo de un solo clic que abra la interfaz de WhatsApp Web con el número normalizado en estándar E.164 del postulante y un mensaje predefinido de primer contacto corporativo de TCS.
- **FR-007**: El sistema DEBE validar la unicidad estricta del candidato en el momento de la digitación, ejecutando verificación inmediata por número de documento (DNI/CE), número telefónico normalizado y correo electrónico.
- **FR-008**: Si se detecta una coincidencia por documento, teléfono o correo, el sistema DEBE bloquear la creación de un nuevo registro huérfano y redirigir a la reclutadora hacia la ficha existente con su historial consolidado.
- **FR-009**: El sistema DEBE admitir la carga de documentos de currículo en formatos estándar (PDF y Word/DOCX), asociándolos a la ficha del candidato.
- **FR-010**: Al cargarse un currículo, el sistema DEBE extraer de manera estructurada y asistida las herramientas tecnológicas, años de experiencia, roles previos e idiomas, poniéndolos a disposición de la reclutadora para su validación sin alterar la autoridad humana sobre el dato.
- **FR-011**: El sistema DEBE registrar de forma estructurada los resultados de las 7 dimensiones de la llamada de validación telefónica humana (disponibilidad, resumen técnico, pretensión salarial, interés, modalidad, viabilidad de traslado e impresión general), incluyendo una alerta geográfica automática que compare el distrito de residencia del postulante con la sede física de trabajo de la cuenta cliente para prevenir deserciones por transporte.

#### Validador Masivo de Planillas de Adecco y Detección Cruzada (Proceso 3)
- **FR-012**: El sistema DEBE permitir la carga por lotes de archivos de planilla electrónica (.xlsx / .csv) remitidos por el proveedor externo Adecco.
- **FR-013**: El módulo de ingesta DEBE aplicar tolerancia semántica a variaciones de encabezados de columnas (alias como `Celular` / `Móvil` / `Teléfono`, `DNI` / `Documento` / `DNI/CE`) y omitir filas en blanco sin abortar la operación.
- **FR-014**: El sistema DEBE procesar cada registro de la planilla en menos de 100 milisegundos por fila, contrastándolo contra la totalidad de la base histórica de candidatos y ex-colaboradores de TCS.
- **FR-015**: El sistema DEBE clasificar algorítmicamente cada fila de la planilla en uno de tres estados visuales excluyentes:
  - 🔴 **Rojo (Duplicado Activo / Exclusión Permanente):** Candidato con proceso en curso, descartado hace menos de 180 días naturales, o con descarte histórico permanente no subsanable (BGC fallido, falta ética, Do Not Rehire).
  - 🟡 **Amarillo (Reactivable):** Candidato registrado en el sistema con más de 180 días naturales sin proceso activo y cuyo motivo de cierre fue temporal o no excluyente (salario o cupo).
  - 🟢 **Verde (Limpio / Inédito):** Candidato que no registra ninguna coincidencia de identidad ni telefónica ni coincidencia fonética significativa en el histórico.
- **FR-016**: La evaluación de duplicados en planillas DEBE aplicar cotejo exacto por documento de identidad, correo y teléfono normalizado E.164, complementado con cotejo fonético aproximado sobre nombres y apellidos que contemple inversión de nombres/apellidos y remoción de partículas ("de", "la", "del").
- **FR-017**: Si un candidato de la planilla de Adecco figura en el registro histórico de ex-colaboradores de TCS, el sistema DEBE emitir una insignia visual destacada (🟣 "Ex-Colaborador TCS") para impedir el pago de comisión comercial externa y orientar el perfil a reincorporación directa si es elegible.
- **FR-018**: El sistema DEBE generar un resumen ejecutivo del lote cargado indicando: total de perfiles procesados, porcentaje de duplicidad, cantidad de reactivables, cantidad de perfiles limpios y total de ex-colaboradores detectados.
- **FR-019**: El sistema DEBE permitir la descarga de la lista depurada (*shortlist limpio*) en formato estándar y posibilitar la importación en lote de los candidatos verdes hacia la bandeja de entrada de candidatos nuevos.

#### Generador de Reporte de Exclusión a Demanda bajo Ley 29733 (Proceso 3 y Gobernanza de Proveedores)
- **FR-020**: El sistema DEBE incluir un generador a demanda del Reporte de Exclusión para Adecco, ejecutable con un solo clic en cualquier instante sin restricción de día u horario.
- **FR-021**: El Reporte de Exclusión DEBE contener únicamente los siguientes campos por registro: Tipo de Documento, Número de Documento (DNI/CE), Primer Apellido, Inicial del Nombre, Identificador de Vacante o Perfil y Fecha de Vigencia de la Exclusión.
- **FR-022**: En cumplimiento estricto de la Ley N° 29733 (Protección de Datos Personales), el sistema DEBE omitir de forma absoluta del reporte de exclusión cualquier dato de pretensión salarial, tarifas presupuestales, teléfonos personales, correos, notas privadas de evaluación y motivos sensibles de descarte.
- **FR-023**: El sistema DEBE registrar en una bitácora de auditoría inmutable cada generación de reporte de exclusión, detallando usuario que lo solicitó, marca de tiempo y cantidad de registros exportados.

#### Módulo de Compensación y Simulador CTC con Factor 1.56 (Gobernanza Financiera)
- **FR-024**: El sistema DEBE calcular automáticamente el Costo Empresa (CTC Solicitado) multiplicando la remuneración mensual bruta pretendida por el factor laboral estándar de 1.56, fundamentado en los sobrecostos del Régimen Laboral Privado D.L. 728 de Perú (Gratificaciones, CTS, EsSalud, Vacaciones, Seguro Vida Ley).
- **FR-025**: El sistema DEBE admitir la entrada de expectativa salarial en modalidad Neta o Bruta; si se ingresa en valor Neto, DEBE proyectar el salario bruto referencial aplicando las deducciones fiscales y previsionales peruanas estimadas (~21%) antes de computar el Costo Empresa con el factor 1.56.
- **FR-026**: El sistema DEBE contrastar el CTC Solicitado contra el presupuesto autorizado para el rol (`CTC Presupuestado`) calculando el porcentaje de variación presupuestal mediante la fórmula: `(CTC Solicitado - CTC Presupuestado) / CTC Presupuestado * 100`.
- **FR-027**: El sistema DEBE incorporar una guarda lógica contra división por cero que impida la generación del error `#DIV/0!`: si el CTC Presupuestado es nulo, cero o negativo, el cálculo no debe ejecutarse, asignando un estado descriptivo ("Pendiente de Presupuesto") y manteniendo la estabilidad numérica.
- **FR-028**: El sistema DEBE proveer un semáforo visual financiero que alerte a la reclutadora durante la llamada telefónica si la pretensión del candidato se encuentra dentro del presupuesto (verde), con desvío moderado de hasta 10% (ámbar) o desvío crítico superior al 10% (rojo).
- **FR-029**: El sistema DEBE emitir advertencias de verificación si se ingresan montos salariales fuera de rangos operativos razonables (inferiores al salario mínimo vital o superiores a S/. 35,000 mensuales).

#### Detección de Candidatos Boomerang (Ex-Colaboradores TCS)
- **FR-030**: El sistema DEBE contrastar de forma automática todo candidato ingresado contra el repositorio corporativo histórico de ex-colaboradores de TCS Perú mediante cotejo primario por documento de identidad (DNI/CE) y secundario por correo electrónico y similitud fonética de nombres.
- **FR-031**: Al existir coincidencia, el sistema DEBE emitir una alerta visual prioritaria en la ficha del candidato indicando su condición de "Ex-Colaborador TCS (Boomerang)", especificando el periodo de servicio previo, la cuenta o proyecto en el que laboró y su condición de recontratabilidad (*Rehire Eligible* / *Do Not Rehire*).
- **FR-032**: Si el registro histórico señala al ex-colaborador como no elegible para reingreso (*Do Not Rehire*), el sistema DEBE emitir una advertencia de compliance para que la reclutadora detenga el avance del proceso antes de comprometer entrevistas con el cliente.

#### Principios Constitucionales de Gobernanza y Human-in-the-Loop
- **FR-033**: El sistema DEBE garantizar que ninguna funcionalidad de asistencia o inteligencia artificial descarte automáticamente a un candidato, modifique unilateralmente su estado o tome decisiones de contratación; toda transición de estado y descarte DEBE ser ejecutada y ratificada por una persona humana (reclutadora o líder de selección).
- **FR-034**: La llamada telefónica de validación técnica y screening (con sus 7 dimensiones de evaluación) DEBE ser realizada íntegramente por un ser humano, limitándose el sistema a brindar fichas, alertas de conmutación y resúmenes de soporte.
- **FR-035**: En estricto apego al principio constitucional anti-scraping, el sistema DEBE operar exclusivamente sobre datos propios almacenados internamente y archivos formalmente importados/exportados, sin ejecutar ningún mecanismo de automatización sobre la web de LinkedIn Recruiter.
- **FR-036**: Los modelos de análisis y extracción estructurada NO DEBEN considerar en ningún momento atributos protegidos (edad, género, estado civil, dirección domiciliaria exacta o fotografía) para calificar perfiles, garantizando una evaluación técnica objetiva y auditable.

#### Autenticación, Control de Acceso y Trazabilidad Integral (Seguridad y Gobernanza)
- **FR-037**: El sistema DEBE proveer un mecanismo seguro de registro de cuentas para usuarios corporativos, requiriendo nombres y apellidos completos, correo electrónico institucional (`@tcs.com`) y credencial de acceso que satisfaga políticas de longitud y robustez.
- **FR-038**: El sistema DEBE autenticar las credenciales de los usuarios protegiendo su confidencialidad sin exponerlas en texto claro, y gestionar sesiones autenticadas con expiración automática tras un lapso de inactividad configurable.
- **FR-039**: El sistema DEBE implementar un modelo de Control de Acceso Basado en Roles (RBAC) con al menos tres niveles de permisos operativos:
  - *Reclutadora*: Creación y modificación de fichas de candidatos, edición del embudo de postulaciones asignadas, registro del screening telefónico, carga de currículos, validación de planillas de Adecco y generación del reporte de exclusión.
  - *Coordinador / Administrador*: Todos los privilegios operativos de Reclutadora más administración de cuentas de usuario, asignación de roles, autorización de variaciones presupuestales salariales fuera de banda y consulta de la bitácora global de auditoría.
  - *Observador*: Acceso exclusivamente en modo de solo lectura a fichas, postulaciones, tableros de control y reportes consolidados, con prohibición estricta de crear registros, mutar datos o cargar archivos.
- **FR-040**: El sistema DEBE incorporar una función explícita de cierre de sesión seguro que invalide de inmediato la sesión activa en el sistema e impida la reutilización de identificadores de sesión previos.
- **FR-041**: El sistema DEBE asociar de manera obligatoria, automática e indisociable al usuario autenticado en sesión con cada una de las siguientes operaciones del pipeline:
  - Creación y edición de campos en la Ficha Única de Candidato (datos personales, de contacto y residencia).
  - Creación y cambios de estado en el ciclo de vida de la Postulación (desde ingreso hasta cierre o contratación).
  - Registro y modificación de la expectativa salarial, cálculo CTC y autorizaciones presupuestales.
  - Carga, reemplazo o actualización de archivos de currículo (CV) y documentos anexos.
  - Ingesta y validación masiva de planillas de candidatos remitidas por Adecco.
  - Generación y descarga a demanda de Reportes de Exclusión bajo Ley N° 29733.
  - Registro estructurado de las 7 dimensiones y dictamen cualitativo de la llamada humana de screening telefónico.
- **FR-042**: El sistema DEBE persistir cada evento de mutación o acción relevante en una bitácora inmutable de auditoría (*append-only*), registrando obligatoriamente: identificador único del evento, identificador y correo del usuario ejecutor, rol del usuario al momento de la acción, marca de tiempo precisa con zona horaria, tipo de entidad afectada (Candidato, Postulación, Documento, Planilla, Reporte, Usuario), identificador del registro afectado, tipo de operación (Creación, Modificación, Carga de Archivo, Exportación, Transición de Estado, Autenticación, Acceso Denegado), y en modificaciones de datos, el detalle comparativo de los valores previos y nuevos valores resultantes.
- **FR-043**: La bitácora de auditoría DEBE ser estrictamente inmutable; el sistema DEBE prohibir y rechazar funcionalmente cualquier modificación retroactiva, alteración o eliminación de eventos de auditoría registrados, garantizando que el historial sea íntegro, perdurable y no repudiable.
- **FR-044**: El sistema DEBE presentar en la interfaz de la Ficha Única del Candidato y de la Postulación una vista cronológica accesible que despliegue el historial completo de cambios, indicando el usuario responsable, la fecha/hora y el detalle del cambio realizado.
- **FR-045**: El sistema DEBE registrar en la bitácora de seguridad los eventos de control de acceso, tales como inicios de sesión exitosos, intentos fallidos de autenticación, bloqueos temporales por reiteración de fallos e intentos de ejecución de operaciones no autorizadas por rol.

---

### Key Entities *(mandatory)*

- **Candidato (Ficha de Identidad Centralizada):**  
  Representa a la persona física individual como entidad única en la organización. Sus atributos funcionales clave comprenden: Tipo y Número de Documento de Identidad (DNI/CE/Pasaporte, único), Nombres de Pila, Apellido Paterno, Apellido Materno, Nombres Completos Normalizados (sin partículas), Teléfono Móvil Canónico (estándar E.164, único), Correo Electrónico Principal (único), Fecha de Nacimiento, Edad Calculada Dinámicamente, Ubigeo / Distrito de Residencia, Condición de Ex-Colaborador TCS (Boomerang), Estado de Validación de Identidad (`Validado Oficialmente`, `Pendiente de Regularización`), y Marcas de Auditoría Cronológica. Posee una relación 1:N con las Postulaciones a procesos.

- **Postulación a Proceso (Ciclo de Vida en Embudo):**  
  Modela la participación formal de un candidato en una vacante o requerimiento específico. Sus atributos funcionales comprenden: Identificador de Postulación, Referencia al Candidato, Cuenta o Cliente Corporativo (ej. BCP, Entel, Banco Falabella), Identificador de Requerimiento (RGS/Vacante), Perfil Técnico Solicitado, Reclutadora Responsable Asignada, Fuente de Reclutamiento de Origen (Adecco, Offshore, BYB, LinkedIn), Trimestre Fiscal Corporativo (Q1, Q2, Q3, Q4), Estado Operativo del Embudo (`Nuevo`, `En proceso`, `Screening telefónico`, `Pendiente entrevistas`, `Pendiente envío cliente`, `Oferta aceptada`, `No apto`, `Desistió`), Motivo Detallado de Cierre/Descarte (con clasificación entre `Excluyente Permanente` o `Temporal No Excluyente`), Disponibilidad de Incorporación, Observaciones Cualitativas y Trazabilidad Cronológica.

- **Screening Telefónico y Validación Cualitativa (Registro Humano):**  
  Entidad vinculada a la postulación que captura los resultados objetivos y cualitativos de la llamada telefónica humana. Atributos: Identificador de Screening, Referencia a la Postulación, Reclutadora Evaluadora, Fecha y Hora de la Llamada, Disponibilidad de Incorporación (`Inmediata`, `1 semana`, `2 semanas`, `1 mes`), Modalidad Aceptada (`Híbrido`, `Remoto`, `Presencial`), Viabilidad de Traslado Geográfico (Distrito Residencia vs Sede Cliente con indicador de conmutación), Resumen Técnico Validado, Notas Cualitativas de la Entrevista, y Dictamen Humano de Avance (`Avanza a Entrevista Técnica`, `No Apto`, `Enfriar/Recontactar`).

- **Evaluación Financiera y CTC (Compensación Laboral):**  
  Entidad vinculada a la postulación que gobierna el análisis de viabilidad económica. Sus atributos comprenden: Tipo de Expectativa Declarada (`Bruta`, `Neta`), Monto Declarado (PEN), Salario Bruto Mensual Resultante, Factor Legal CTC Aplicado (1.56 bajo D.L. 728), Costo Empresa Solicitado (Calculado), Techo Presupuestal CTC del Rol, Variación Presupuestal Porcentual (Calculada con guarda contra división por cero), y Estado del Semáforo Presupuestal (`Dentro de Presupuesto`, `Requiere Aprobación Especial`, `Fuera de Banda Salarial`, `Pendiente de Presupuesto`).

- **Verificación de Compliance y Antecedentes:**  
  Entidad asociada a la postulación para el control de riesgos y filtros institucionales. Atributos: Estado de Verificación Personal BGC (`Pendiente`, `En proceso`, `Aprobado`, `Observado / No Apto`), Consulta de Centrales de Riesgo Crediticio (Equifax/Infocorp: Sí/No registra deuda castigada excluyente para banca), Fecha de Consulta y Notas de Cumplimiento Legal.

- **Historial Alumni TCS (Repositorio de Ex-Colaboradores):**  
  Entidad corporativa de referencia para la detección de candidatos Boomerang. Atributos: Tipo y Número de Documento (DNI/CE), Nombres Completos Oficiales, Correo Electrónico Corporativo/Personal Histórico, Último Periodo Laborado (Fecha Inicio - Fecha Fin), Última Cuenta/Proyecto Asignado, Motivo de Desvinculación, y Estatus de Recontratabilidad (`Rehire Eligible`, `Do Not Rehire`, `Requiere Aprobación RRHH`).

- **Lote de Planilla de Proveedor (Ingesta Adecco):**  
  Entidad que registra cada sesión de carga masiva de candidatos remitidos por agencias externas. Atributos: Identificador del Lote, Nombre del Proveedor, Fecha y Hora de Carga, Reclutadora que Ingesta, Nombre del Archivo Original, Total de Filas Leídas, Cantidad de Duplicados Rojos, Cantidad de Reactivables Amarillos, Cantidad de Perfiles Limpios Verdes y Cantidad de Ex-Colaboradores TCS Detectados.

- **Reporte de Exclusión de Proveedor (Exportación a Demanda):**  
  Entidad que audita las descargas de listas de exclusión para proveedores bajo la Ley N° 29733. Atributos: Identificador de Reporte, Destinatario (Adecco), Fecha y Hora de Generación, Usuario Solicitante, Cuenta/Cliente Filtrado (o consolidado general), Cantidad de Candidatos Excluidos, y Periodo de Vigencia de la Exclusión.

- **Usuario (Operador del Sistema y Cuenta Corporativa):**  
  Representa a la persona física individual autorizada para operar el sistema en sus distintas capacidades. Sus atributos funcionales comprenden: Identificador de Usuario, Nombres y Apellidos Completos, Correo Electrónico Corporativo Oficial (único, dominio institucional `@tcs.com`), Rol Asignado (`Reclutadora`, `Coordinador_Admin`, `Observador`), Estado de la Cuenta (`Activa`, `Suspendida`, `Bloqueada por Intentos Fallidos`), Credencial de Acceso Confidencial, Contador de Intentos Fallidos de Autenticación, Fecha y Hora del Último Acceso Exitoso, y Marcas Temporales de Creación y Modificación. Posee una relación 1:N con las Postulaciones asignadas y con los Registros de Auditoría generados por sus acciones.

- **Registro de Auditoría / Bitácora de Cambios (Trazabilidad Inmutable):**  
  Modela el asiento cronológico e inmutable de toda acción, mutación de datos, subida de documentos, exportación regulatoria o evento de seguridad ejecutado en el sistema. Atributos funcionales: Identificador Único de Evento, Referencia al Usuario Actor (Identificador y Correo Institucional), Rol Operativo del Usuario al momento de la operación, Marca de Tiempo Precisa (fecha, hora exacta y zona horaria), Tipo de Acción Realizada (`Creación`, `Modificación`, `Carga_Archivo`, `Exportación`, `Transición_Estado`, `Autenticación`, `Acceso_Denegado`), Entidad Objeto Afectada (`Candidato`, `Postulación`, `Screening`, `Planilla_Adecco`, `Reporte_Exclusión`, `Usuario`), Identificador del Registro Objeto Afectado, Detalle Estructurado de la Mutación (nombre del campo modificado, valor previo y nuevo valor resultante), y Metadatos de Integridad Documental (nombre original del archivo, tipo de documento, tamaño en bytes e identificador de almacenamiento para archivos adjuntos).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Erradicación del Proceso 1 - Registro Manual):**  
  Reducir el tiempo promedio de registro y creación de ficha de un candidato de 6-8 minutos (en el ecosistema manual de Excel) a menos de 45 segundos utilizando el autollenado por DNI, la normalización canónica E.164 y la extracción estructurada de CV, recuperando el 100% de las **25 horas semanales** de esfuerzo invertidas en transcripción manual.
- **SC-002 (Erradicación del Proceso 3 - Cruce con Adecco):**  
  Reducir el tiempo de validación de una planilla semanal de Adecco de 50 filas de 60 minutos a menos de 5 segundos con el validador algorítmico de semáforo y detección de ex-colaboradores, recuperando el 100% de las **5 horas semanales** dedicadas al cruce manual de postulantes.
- **SC-003 (Recuperación del Proceso 2 - Actualización de Estados e Histórico):**  
  Permitir la actualización de estados de postulación, notas cualitativas de la llamada y feedback en un solo clic sincronizado en tiempo real para todo el equipo, eliminando la apertura asíncrona permanente de libros de Excel locales y recuperando las **5 horas semanales** de mantenimiento de históricos.
- **SC-004 (Cero Errores Numéricos, de Formato y de División por Cero):**  
  Lograr una tasa de 0.00% de ocurrencias del error de división por cero (`#DIV/0!`), 0.00% de errores en cálculo de edad (cero candidatos con 127 años), y un 100% de cumplimiento en la normalización de números celulares bajo el estándar canónico internacional E.164 (`+519XXXXXXXX`).
- **SC-005 (Protección Legal y Anonimización Estricta Ley 29733):**  
  Garantizar un 100% de cumplimiento normativo en los reportes de exclusión generados para proveedores externos, con 0.00% de filtración de remuneraciones, tarifas de facturación, teléfonos personales, correos, notas privadas de evaluación o atributos demográficos protegidos.
- **SC-006 (Incremento de Efectividad del Proveedor Externo Adecco):**  
  Elevar el ratio de perfiles útiles remitidos por Adecco del 10% actual (donde 9 de cada 10 son repetidos o inadecuados) a al menos 35% en los primeros 60 días de entrega regular del reporte de exclusión a demanda.
- **SC-007 (Detección de Talento Boomerang y Ahorro de Comisiones en Tiempo Real):**  
  Identificar al 100% de los ex-colaboradores de TCS postulantes (tanto por ficha individual como por planilla masiva) en menos de 1 segundo desde su ingreso, reduciendo el tiempo de verificación de antecedentes internos de 3 días a menos de 1 segundo y previniendo el pago innecesario de comisiones comerciales por perfiles Alumni.
- **SC-008 (Trazabilidad y Responsabilidad Operativa al 100%):**  
  Garantizar que el 100% de las mutaciones de datos, cambios de estado en el embudo, subida de CVs, ingesta de planillas masivas y exportaciones de reportes de exclusión queden vinculadas a un usuario autenticado con marca de tiempo precisa en la bitácora inmutable, con 0.00% de operaciones anónimas permitidas o huérfanas de autoría.
- **SC-009 (Seguridad de Acceso y Control de Roles):**  
  Lograr una tasa de 100% de efectividad en el bloqueo de accesos no autorizados a funciones restringidas (ej. edición o carga denegada para rol Observador) y una tasa de 0.00% de exposición de credenciales en texto claro o de sesiones activas sin invalidar tras el cierre de sesión.

---

## Assumptions

- **A-001 (Disponibilidad y Fallback de Servicio de Identidad):** Se asume que el servicio nacional de consulta de identidad mantiene una disponibilidad operativa regular en días hábiles; ante caídas temporales, demoras de red (>3s) o agotamiento de cuotas mensuales, el sistema asume la continuidad mediante fallback a digitación manual con marca de verificación pendiente sin bloquear el flujo de trabajo.
- **A-002 (Estandarización de Documentos Nacionales y Soporte Extranjero):** Se asume que más del 90% de las búsquedas de talento local en Perú involucran profesionales con DNI peruano de 8 dígitos, mientras que profesionales extranjeros con Carné de Extranjería o Pasaporte son soportados mediante validación manual estructurada sin autollenado.
- **A-003 (Factor de Cargas Sociales 1.56 bajo D.L. 728):** Se asume que el factor multiplicador 1.56 representa con fidelidad técnica la estructura de costos laborales del Régimen General Privado (D.L. 728: Gratificaciones 16.67%, Bonificación Extraordinaria 1.50%, CTS 9.72%, EsSalud 9.00%, Vacaciones 8.33%, Seguro Vida Ley y contingencias) acordada entre Selección y Finanzas de TCS Perú.
- **A-004 (Autoridad y Juicio Humano Innegociable):** Se asume que la reclutadora humana siempre tiene la facultad soberana de revisar, editar, confirmar o rectificar cualquier sugerencia, extracción o advertencia generada por el sistema antes de guardar o derivar un perfil a una cuenta cliente.
- **A-005 (Operación Desacoplada de LinkedIn Recruiter):** Se asume que no existe dependencia ni integración directa no oficial con LinkedIn Recruiter; el sourcing continúa ejecutándose en dicha plataforma según sus términos comerciales y los datos ingresan al sistema mediante exportaciones autorizadas (XLSX, CSV) o carga individual de CVs.
- **A-006 (Hardware, Conectividad y Entorno del Usuario):** Se asume que las reclutadoras y analistas operan desde estaciones de trabajo corporativas de TCS con navegadores web modernos y conectividad a la red interna para interactuar con WhatsApp Web y los servicios de selección.
- **A-007 (Acuerdo Operativo con Adecco):** Se asume que el proveedor externo Adecco aceptará recibir y utilizar el reporte de exclusión a demanda como filtro previo mandatario antes de iniciar sus jornadas de búsqueda y remitir sus planillas semanales.
- **A-008 (Reconciliación Fonética y Permutación de Nombres):** Se asume que la disparidad en el orden de nombres y apellidos en perfiles peruanos se resuelve mediante tokenización, eliminación de partículas y cotejo de similitud aproximada con confirmación humana en casos limítrofes (80-89% de similitud).
- **A-009 (Integridad de la Base Histórica Alumni):** Se asume que Recursos Humanos suministrará un volcado maestro inicial de ex-colaboradores TCS con DNI, nombres y condición de recontratabilidad para alimentar el motor de detección de candidatos Boomerang.
- **A-010 (Gestión de Identidades y Cuentas Corporativas):** Se asume que todos los colaboradores autorizados del equipo de Selección (reclutadoras, coordinadores y observadores) cuentan con un correo corporativo oficial institucional de TCS (`@tcs.com`) y que el sistema gestiona la autenticación, roles operativos y sesiones activas de manera autónoma garantizando la trazabilidad integral de sus operaciones.
