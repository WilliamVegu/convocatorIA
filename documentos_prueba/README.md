# 📁 Carpeta de Documentos de Prueba - ATS TCS Perú

Esta carpeta contiene un repositorio completo de documentos y archivos de prueba calibrados para validar todas las funcionalidades del Sistema de Reclutamiento y Selección con Inteligencia Artificial (ATS TCS Perú).

---

## 📂 Estructura de Subcarpetas

```
documentos_prueba/
│
├── cvs/                               # Curriculums Vitae en PDF y Word
│   ├── CV_01_Diego_Ramos_Java_Senior_BCP.pdf (.docx)
│   ├── CV_02_Carlos_Garcia_DevOps_Lead_AlumniTCS.pdf (.docx)
│   ├── CV_03_Ana_Lucia_Quispe_Data_Engineer_Entel.pdf (.docx)
│   ├── CV_04_Valeria_Flores_FullStack_React_Node.pdf
│   ├── CV_05_Jorge_Chavez_Cloud_Architect.pdf
│   ├── CV_06_Sebastian_Lopez_Junior_Mobile_Flutter.pdf
│   ├── CV_07_Lucia_Benitez_Security_Engineer.pdf
│   ├── CV_08_Brenda_Gutierrez_Java_Inedita.pdf
│   ├── CV_09_Miguel_Torres_QA_Automation.pdf
│   └── CV_10_Patricia_Vargas_Scrum_Master.pdf
│
├── certificados_cul_mtpe/              # Certificados Únicos Laborales (CUL - MTPE)
│   ├── CUL_01_Aprobado_Diego_Ramos_Limpio.pdf
│   ├── CUL_02_Observado_Roberto_Montes_Antecedentes.pdf
│   └── CUL_03_Aprobado_Carlos_Garcia_AlumniTCS.pdf
│
├── planillas_adecco_excel/            # Planillas de Proveedores (Adecco) en Excel y CSV
│   ├── Planilla_Adecco_01_Semanal_Calibrada_20_Candidatos.xlsx
│   ├── Planilla_Adecco_02_Cabeceras_Alternativas_Alias.xlsx
│   ├── Planilla_Adecco_03_Casos_Borde_y_Formatos_Sucios.xlsx
│   ├── Planilla_Adecco_04_Lote_Grande_50_Candidatos.xlsx
│   └── Planilla_Adecco_05_Sourcing_Proveedor.csv
│
├── reportes_exclusion_ley29733/       # Reportes oficiales bajo Ley N° 29733
│   └── Reporte_Exclusion_Ley29733_5Columnas_Modelo.xlsx
│
├── requerimientos_rgs/                # Solicitudes de vacantes de clientes (RGS a JD)
│   ├── RGS_01_BCP_Java_Backend_Senior.txt
│   ├── RGS_02_Entel_Data_Engineer_Remoto.txt
│   ├── RGS_03_Falabella_DevOps_Cloud_Hibrido.txt
│   └── RGS_04_Interbank_QA_Automation_Lead.txt
│
├── README.md                          # Este archivo descriptivo
└── GUIA_DE_PRUEBAS.md                 # Matriz paso a paso con pantallas y resultados esperados
```

---

## 🎯 Resumen de Casos de Prueba Clave

| Archivo | Pantalla de Prueba | Objetivo / Resultado Esperado |
|---|---|---|
| `CV_01_Diego_Ramos...pdf` | **P1: Ficha Candidato** | Autocompletado de DNI 76128709, extracción de Java/Spring/Kafka, Fit & Gap 90%+ con vacante BCP Java. |
| `CV_02_Carlos_Garcia...pdf` | **P1** y **P6: Alumni TCS** | Detección inmediata de candidato **Boomerang / Alumni TCS** (alerta de ahorro sin comisión externa). |
| `CUL_01_Aprobado...pdf` | **P1: Ficha Candidato** | BGC Aprobado (PNP, INPE y PJ limpios), extracción de grado SUNEDU y empresas formales SUNAT. |
| `CUL_02_Observado...pdf` | **P1: Ficha Candidato** | BGC Observado No Apto (alerta roja por registro de antecedentes policiales). |
| `Planilla_Adecco_01...xlsx` | **P4: Validador Adecco** | Semáforo completo: 7 Rojos (duplicados), 3 Amarillos (reactivables), 8 Verdes (limpios), 2 Púrpuras (alumni). |
| `Planilla_Adecco_02...xlsx` | **P4: Validador Adecco** | Resiliencia de cabeceras con alias no estándar (`Documento de Identidad`, `Postulante`, `Celular`). |
| `Planilla_Adecco_03...xlsx` | **P4: Validador Adecco** | Tolerancia a espacios en blanco, números `.0` de Excel, números internacionales y filas vacías. |
| `RGS_01_BCP...txt` | **P9: Normalizador RGS** | Ingesta de texto desestructurado de correo y generación de Job Description y sintaxis booleana. |

Consulte **`GUIA_DE_PRUEBAS.md`** para la guía paso a paso con capturas, botones y verificaciones.
