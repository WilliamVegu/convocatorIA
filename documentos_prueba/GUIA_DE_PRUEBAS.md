# 🚀 Guía Paso a Paso de Pruebas de Usuario (ATS TCS Perú)

Siga este flujo interactivo para probar todas las capacidades del sistema con los documentos generados.

---

## Caso 1: Ingesta de CV, Validación DNI y Análisis Fit & Gap (Pantalla P1)

1. Inicie sesión en la aplicación con cualquier usuario (ej. `admin@tcs.com` o reclutador).
2. Diríjase al menú lateral: **"📋 Ficha Única de Candidato"**.
3. **Paso 1 - DNI:**
   - Ingrese el DNI: `76128709` y presione **"🔎 Validar DNI"**.
   - Verifique que se autocompletan los nombres (*Diego Alonso Ramos Quispe*), la fecha de nacimiento dinámica y el ubigeo.
4. **Paso 2 - WhatsApp y GitHub:**
   - Ingrese el número móvil: `989322088`.
   - Observe la normalización instantánea a E.164 (`+51989322088`) y el botón verde **"💬 Iniciar WhatsApp Web"**.
   - Ingrese en GitHub: `torvalds` y presione **"🔎 Auditar GitHub"** para ver los repositorios activos.
5. **Paso 3 - Adjuntar CV:**
   - Arrastre el archivo `documentos_prueba/cvs/CV_01_Diego_Ramos_Java_Senior_BCP.pdf`.
   - Presione **"📄 Extraer Datos CV (IA / Heurística)"**.
   - Observe cómo se detectan automáticamente las habilidades (*Java, Spring Boot, Microservicios, Kafka, Docker, AWS*) y los 8 años de experiencia.
6. **Paso 4 - Adjuntar CUL:**
   - Arrastre el archivo `documentos_prueba/certificados_cul_mtpe/CUL_01_Aprobado_Diego_Ramos_Limpio.pdf`.
   - Presione **"🏛️ Extraer Antecedentes y SUNAT (CUL)"**.
   - Observe la confirmación verde: *BGC Aprobado (PNP, INPE y Poder Judicial limpios)* y los grados SUNEDU.
7. **Paso 5 - Fit & Gap Automático:**
   - En *Cliente* seleccione **BCP** y en *Perfil* **Desarrollador Java Senior**.
   - Desplace hacia abajo: verá la tarjeta de **Compatibilidad Técnica (Fit & Gap)** con un score sobresaliente (~90%+), radar de habilidades cubiertas y brechas identificadas.

---

## Caso 2: Detección de Candidato Boomerang / Alumni TCS (Pantallas P1 y P6)

1. En la misma pantalla **"📋 Ficha Única de Candidato"**:
   - Ingrese el DNI: `46753314` (Carlos Eduardo García Sánchez).
   - Observe la **alerta púrpura instantánea**:
     > 🟣 **CANDIDATO BOOMERANG DETECTADO (Ex-colaborador TCS Perú)**
     > Cuenta: BCP Home Banking | Estatus: `Rehire_Eligible`
     > *Alerta de Ahorro: Este candidato es patrimonio TCS. No procede pago de comisión a agencia externa.*
2. Puede adjuntar su CV `documentos_prueba/cvs/CV_02_Carlos_Garcia_DevOps_Lead_AlumniTCS.pdf` y su CUL `documentos_prueba/certificados_cul_mtpe/CUL_03_Aprobado_Carlos_Garcia_AlumniTCS.pdf`.
3. Vaya a la página **"🟣 Directorio Alumni TCS" (P6)**:
   - Verifique el historial de proyectos previos, evaluaciones y su condición de recontratación aprobada.

---

## Caso 3: CUL con Antecedentes Negativos / BGC Observado (Pantalla P1)

1. En **"📋 Ficha Única de Candidato"**:
   - En la sección de CUL, adjunte el archivo `documentos_prueba/certificados_cul_mtpe/CUL_02_Observado_Roberto_Montes_Antecedentes.pdf`.
   - Presione **"🏛️ Extraer Antecedentes y SUNAT (CUL)"**.
   - Verifique que el sistema muestra un **banner de advertencia en rojo**:
     > ⚠️ *CUL MTPE: OBSERVADO: Registra antecedentes en bases del MTPE/PNP/PJ.*

---

## Caso 4: Validador Masivo de Planillas de Proveedores (Pantalla P4)

1. Diríjase a **"📊 Validador Masivo Adecco" (P4)**.
2. **Prueba Semáforo Completo:**
   - Arrastre `documentos_prueba/planillas_adecco_excel/Planilla_Adecco_01_Semanal_Calibrada_20_Candidatos.xlsx`.
   - Presione el botón **"⚡ Procesar Planilla Masiva"**.
   - Verifique el semáforo métrico:
     - 🔴 **7 Duplicados / Excluidos**
     - 🟡 **3 Reactivables (>180d)**
     - 🟢 **8 Inéditos / Limpios**
     - 🟣 **2 Alumni TCS Detectados**
   - Presione el botón de **Importación Atómica** para ingresar los 8 candidatos limpios a la base de datos en una sola transacción.
3. **Prueba de Resiliencia de Cabeceras (Alias):**
   - Arrastre `documentos_prueba/planillas_adecco_excel/Planilla_Adecco_02_Cabeceras_Alternativas_Alias.xlsx`.
   - Procese la planilla y observe cómo reconoce columnas nombradas como `Documento de Identidad`, `Postulante`, `Celular`.
4. **Prueba de Formatos Sucios:**
   - Arrastre `documentos_prueba/planillas_adecco_excel/Planilla_Adecco_03_Casos_Borde_y_Formatos_Sucios.xlsx`.
   - Procese y verifique que omite filas en blanco, limpia prefijos internacionales y remueve sufijos `.0`.
5. **Prueba de Archivo CSV:**
   - Arrastre `documentos_prueba/planillas_adecco_excel/Planilla_Adecco_05_Sourcing_Proveedor.csv`.
   - Verifique que procesa los registros delimitados por comas sin errores.

---

## Caso 5: Normalizador de Requerimientos de Cliente RGS a JD (Pantalla P9)

1. Diríjase a **"📝 Normalizador de Requerimientos (RGS)" (P9)**.
2. Abra cualquiera de los archivos de `documentos_prueba/requerimientos_rgs/`:
   - Por ejemplo: `RGS_01_BCP_Java_Backend_Senior.txt`.
3. Copie todo el texto del archivo y péguelo en el área de texto *"Texto sin estructurar del Requerimiento"*.
4. Seleccione cliente **BCP** y presione **"🚀 Normalizar con IA"**.
5. Observe la respuesta estructurada generada:
   - Título homologado del puesto.
   - Nivel de Seniority detectado (Senior).
   - Presupuesto máximo (S/. 9,500) y modalidad (Híbrido).
   - Requisitos técnicos indispensables y deseables clasificados.
   - **Sintaxis Booleana de Búsqueda** lista para copiar a LinkedIn Recruiter.

---

## Caso 6: Reporte Oficial de Cartera de Exclusiones Ley 29733 (Pantalla P5)

1. Diríjase a **"🛡️ Reporte de Cartera y Exclusiones" (P5)**.
2. Genere el reporte oficial para entrega a Adecco en formato Excel.
3. Compare el resultado con `documentos_prueba/reportes_exclusion_ley29733/Reporte_Exclusion_Ley29733_5Columnas_Modelo.xlsx`:
   - Verifique que contiene **exactamente 5 columnas** (`DNI`, `Nombres y Apellidos`, `Perfil`, `Vigencia Exclusión`, `Estado`).
   - Verifique la ausencia total de datos de contacto (cero números telefónicos, correos electrónicos o remuneraciones), cumpliendo al 100% el Principio de Proporcionalidad de la Ley N° 29733.
