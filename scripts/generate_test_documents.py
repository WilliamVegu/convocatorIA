"""
Generador Maestro de Documentos de Prueba para ATS TCS Perú.
Crea un conjunto completo de documentos en la carpeta 'documentos_prueba/' para
verificar y validar de punta a punta todas las funcionalidades del sistema:
- CVs en formato PDF y DOCX (con habilidades técnicas, años de experiencia e idiomas)
- Certificados CUL MTPE oficiales simulados (aprobados y observados con antecedentes)
- Planillas de proveedores externos Adecco en formato Excel (.xlsx) y CSV (.csv)
- Reportes oficiales de cartera y exclusión de 5 columnas bajo Ley N° 29733
- Especificaciones de requerimientos de clientes (RGS a JD) para normalización con IA
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import date, datetime
import pandas as pd

# ReportLab imports for professional PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Python-docx for Word files
import docx
from docx.shared import Pt, Inches, RGBColor

# Register TrueType fonts if available
font_arial = "C:/Windows/Fonts/arial.ttf"
font_arial_bd = "C:/Windows/Fonts/arialbd.ttf"
font_arial_it = "C:/Windows/Fonts/ariali.ttf"
has_arial = os.path.exists(font_arial)

if has_arial:
    pdfmetrics.registerFont(TTFont("Arial", font_arial))
    if os.path.exists(font_arial_bd):
        pdfmetrics.registerFont(TTFont("Arial-Bold", font_arial_bd))
    else:
        pdfmetrics.registerFont(TTFont("Arial-Bold", font_arial))
    if os.path.exists(font_arial_it):
        pdfmetrics.registerFont(TTFont("Arial-Italic", font_arial_it))
    else:
        pdfmetrics.registerFont(TTFont("Arial-Italic", font_arial))
    FONT_NORMAL = "Arial"
    FONT_BOLD = "Arial-Bold"
    FONT_ITALIC = "Arial-Italic"
else:
    FONT_NORMAL = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"
    FONT_ITALIC = "Helvetica-Oblique"


BASE_DIR = Path(__file__).resolve().parent.parent / "documentos_prueba"
CVS_DIR = BASE_DIR / "cvs"
CULS_DIR = BASE_DIR / "certificados_cul_mtpe"
EXCELS_DIR = BASE_DIR / "planillas_adecco_excel"
REPORTES_DIR = BASE_DIR / "reportes_exclusion_ley29733"
RGS_DIR = BASE_DIR / "requerimientos_rgs"


def ensure_directories() -> None:
    """Crea los directorios destino si no existen."""
    for d in [BASE_DIR, CVS_DIR, CULS_DIR, EXCELS_DIR, REPORTES_DIR, RGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def build_cv_pdf(output_path: Path, cv_data: dict) -> None:
    """Genera un archivo PDF elegante y legible por motores de extracción de CVs."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    header_name = ParagraphStyle(
        "HeaderName",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
    )
    header_title = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=3,
    )
    header_contact = ParagraphStyle(
        "HeaderContact",
        parent=styles["Normal"],
        fontName=FONT_NORMAL,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8,
    )
    sec_title = ParagraphStyle(
        "SecTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_p = ParagraphStyle(
        "BodyP",
        parent=styles["Normal"],
        fontName=FONT_NORMAL,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )
    job_title = ParagraphStyle(
        "JobTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
    )
    job_sub = ParagraphStyle(
        "JobSub",
        parent=styles["Normal"],
        fontName=FONT_ITALIC,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=3,
    )

    story = []

    # Encabezado
    story.append(Paragraph(cv_data["nombre_completo"].upper(), header_name))
    story.append(Paragraph(f"{cv_data['titulo_profesional']} | DNI: {cv_data['dni']}", header_title))
    contact_line = (
        f"Ubicación: {cv_data.get('ubicacion', 'Lima, Perú')} | "
        f"Teléfono: {cv_data.get('telefono', '989322088')} | "
        f"Email: {cv_data.get('email', 'candidato@correo.com')} | "
        f"GitHub: {cv_data.get('github', 'github.com/perfil')}"
    )
    story.append(Paragraph(contact_line, header_contact))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3B82F6"), spaceAfter=8))

    # Resumen Profesional
    story.append(Paragraph("RESUMEN PROFESIONAL", sec_title))
    story.append(Paragraph(cv_data["resumen"], body_p))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    # Competencias Técnicas
    story.append(Paragraph("HABILIDADES TÉCNICAS Y HERRAMIENTAS", sec_title))
    skills_text = "<b>Tecnologías principales:</b> " + ", ".join(cv_data["habilidades"])
    story.append(Paragraph(skills_text, body_p))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    # Experiencia Laboral
    story.append(Paragraph("EXPERIENCIA LABORAL", sec_title))
    for exp in cv_data["experiencias"]:
        story.append(Paragraph(f"<b>{exp['puesto']}</b> — {exp['empresa']}", job_title))
        story.append(Paragraph(f"Periodo: {exp['periodo']} | Tecnologías: {', '.join(exp['tecnologias'])}", job_sub))
        story.append(Paragraph(exp["descripcion"], body_p))
        story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    # Formación y Certificaciones
    story.append(Paragraph("FORMACIÓN ACADÉMICA Y CERTIFICACIONES", sec_title))
    for edu in cv_data["educacion"]:
        story.append(Paragraph(f"• <b>{edu['titulo']}</b> — {edu['institucion']} ({edu['anio']})", body_p))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

    # Idiomas
    story.append(Paragraph("IDIOMAS", sec_title))
    idiomas_line = " | ".join([f"<b>{i['idioma']}:</b> {i['nivel']}" for i in cv_data["idiomas"]])
    story.append(Paragraph(idiomas_line, body_p))

    doc.build(story)


def build_cv_docx(output_path: Path, cv_data: dict) -> None:
    """Genera una versión en formato Microsoft Word (.docx)."""
    doc = docx.Document()

    # Margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.7)
        sec.bottom_margin = Inches(0.7)
        sec.left_margin = Inches(0.7)
        sec.right_margin = Inches(0.7)

    # Title
    p_name = doc.add_paragraph()
    r_name = p_name.add_run(cv_data["nombre_completo"].upper())
    r_name.font.name = "Arial"
    r_name.font.size = Pt(18)
    r_name.font.bold = True
    r_name.font.color.rgb = RGBColor(15, 23, 42)
    p_name.paragraph_format.space_after = Pt(2)

    # Subtitle
    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run(f"{cv_data['titulo_profesional']} | DNI: {cv_data['dni']}")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(11)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(37, 99, 235)
    p_sub.paragraph_format.space_after = Pt(4)

    # Contact
    p_ct = doc.add_paragraph()
    r_ct = p_ct.add_run(
        f"Ubicación: {cv_data.get('ubicacion', 'Lima, Perú')} | "
        f"Móvil: {cv_data.get('telefono', '989322088')} | "
        f"Email: {cv_data.get('email', 'candidato@correo.com')}"
    )
    r_ct.font.name = "Arial"
    r_ct.font.size = Pt(9)
    r_ct.font.color.rgb = RGBColor(100, 116, 139)
    p_ct.paragraph_format.space_after = Pt(12)

    def add_section_header(title: str):
        p = doc.add_paragraph()
        r = p.add_run(title)
        r.font.name = "Arial"
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(15, 23, 42)
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)

    # Summary
    add_section_header("RESUMEN PROFESIONAL")
    p_res = doc.add_paragraph(cv_data["resumen"])
    p_res.style.font.name = "Arial"
    p_res.style.font.size = Pt(9.5)

    # Skills
    add_section_header("HABILIDADES TÉCNICAS")
    p_sk = doc.add_paragraph(", ".join(cv_data["habilidades"]))
    p_sk.style.font.name = "Arial"
    p_sk.style.font.size = Pt(9.5)

    # Experience
    add_section_header("EXPERIENCIA LABORAL")
    for exp in cv_data["experiencias"]:
        p_exp_t = doc.add_paragraph()
        r1 = p_exp_t.add_run(f"{exp['puesto']} — {exp['empresa']}")
        r1.font.bold = True
        r1.font.size = Pt(10)
        p_exp_s = doc.add_paragraph()
        r2 = p_exp_s.add_run(f"Periodo: {exp['periodo']}")
        r2.font.italic = True
        r2.font.size = Pt(8.5)
        p_exp_d = doc.add_paragraph(exp["descripcion"])
        p_exp_d.style.font.size = Pt(9)

    # Education
    add_section_header("EDUCACIÓN Y CERTIFICACIONES")
    for edu in cv_data["educacion"]:
        p_ed = doc.add_paragraph(f"• {edu['titulo']} — {edu['institucion']} ({edu['anio']})")
        p_ed.style.font.size = Pt(9)

    # Languages
    add_section_header("IDIOMAS")
    idiomas_str = " | ".join([f"{i['idioma']}: {i['nivel']}" for i in cv_data["idiomas"]])
    p_id = doc.add_paragraph(idiomas_str)
    p_id.style.font.size = Pt(9)

    doc.save(str(output_path))


def build_cul_pdf(output_path: Path, cul_data: dict) -> None:
    """Genera un Certificado Único Laboral oficial (MTPE Perú) simulado en PDF."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=45,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()
    style_ministry = ParagraphStyle(
        "MinistryHeader",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        alignment=1,  # Center
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=2,
    )
    style_cert_title = ParagraphStyle(
        "CertTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=18,
        alignment=1,  # Center
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=4,
    )
    style_law = ParagraphStyle(
        "LawRef",
        parent=styles["Normal"],
        fontName=FONT_NORMAL,
        fontSize=8.5,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=14,
    )
    style_box_header = ParagraphStyle(
        "BoxHeader",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4,
    )
    style_data = ParagraphStyle(
        "DataField",
        parent=styles["Normal"],
        fontName=FONT_NORMAL,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=3,
    )
    style_badge_ok = ParagraphStyle(
        "BadgeOK",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#166534"),
        spaceAfter=2,
    )
    style_badge_bad = ParagraphStyle(
        "BadgeBad",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#991B1B"),
        spaceAfter=2,
    )

    story = []

    # Cabecera Institucional
    story.append(Paragraph("REPÚBLICA DEL PERÚ", style_ministry))
    story.append(Paragraph("MINISTERIO DE TRABAJO Y PROMOCIÓN DEL EMPLEO", style_ministry))
    story.append(Spacer(1, 6))
    story.append(Paragraph("CERTIFICADO ÚNICO LABORAL (CUL)", style_cert_title))
    story.append(Paragraph("Emitido bajo el amparo de la Ley N° 31131 y el D.S. N° 014-2020-TR", style_law))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1E3A8A"), spaceAfter=12))

    # Identificación del Ciudadano
    story.append(Paragraph("1. DATOS DE IDENTIDAD DEL CIUDADANO", style_box_header))
    story.append(Paragraph(f"<b>Nombres y Apellidos:</b> {cul_data['nombres_completos']}", style_data))
    story.append(Paragraph(f"<b>Documento de Identidad:</b> DNI {cul_data['dni']}", style_data))
    story.append(Paragraph(f"<b>Fecha de Emisión:</b> {cul_data['fecha_emision']}", style_data))
    story.append(Paragraph(f"<b>Código de Verificación Digital:</b> CUL-{cul_data['dni']}-2026-X9", style_data))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=10))

    # Antecedentes Oficiales (PNP, INPE, Poder Judicial)
    story.append(Paragraph("2. ANTECEDENTES PENALES, POLICIALES Y JUDICIALES", style_box_header))
    if cul_data.get("tiene_antecedentes", False):
        story.append(Paragraph("POLICIALES: SÍ REGISTRA ANTECEDENTES POLICIALES A NIVEL NACIONAL.", style_badge_bad))
        story.append(Paragraph("PENALES: NO REGISTRA ANTECEDENTES PENALES EN EL REGISTRO NACIONAL.", style_data))
        story.append(Paragraph("JUDICIALES: NO REGISTRA ANTECEDENTES JUDICIALES EN EL PODER JUDICIAL.", style_data))
    else:
        story.append(Paragraph("POLICIALES: NO REGISTRA ANTECEDENTES POLICIALES A NIVEL NACIONAL.", style_badge_ok))
        story.append(Paragraph("PENALES: NO REGISTRA ANTECEDENTES PENALES EN EL REGISTRO NACIONAL.", style_badge_ok))
        story.append(Paragraph("JUDICIALES: NO REGISTRA ANTECEDENTES JUDICIALES EN EL PODER JUDICIAL.", style_badge_ok))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=10))

    # Grados SUNEDU
    story.append(Paragraph("3. GRADOS ACADÉMICOS REGISTRADOS ANTE SUNEDU", style_box_header))
    for g in cul_data["grados_sunedu"]:
        story.append(Paragraph(f"• {g}", style_data))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=10))

    # Trayectoria Laboral Formal SUNAT
    story.append(Paragraph("4. TRAYECTORIA LABORAL FORMAL (PLANILLA ELECTRÓNICA - SUNAT / MTPE)", style_box_header))
    for t in cul_data["trayectoria_formal"]:
        story.append(Paragraph(f"• {t}", style_data))

    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "<i>Documento emitido con firma digital de acuerdo a la Ley N° 27269 sobre Firmas y Certificados Digitales. "
            "Su validez puede ser verificada en el portal oficial del MTPE: https://www.empleosperu.gob.pe/CertificadoUnicoLaboral</i>",
            style_law,
        )
    )

    doc.build(story)


# -------------------------------------------------------------------------------------------------
# GENERACIÓN DE DOCUMENTOS CONCRETOS
# -------------------------------------------------------------------------------------------------

CV_CANDIDATES = [
    {
        "id": "01",
        "filename": "CV_01_Diego_Ramos_Java_Senior_BCP",
        "dni": "76128709",
        "nombre_completo": "Diego Alonso Ramos Quispe",
        "titulo_profesional": "Desarrollador Java Senior & Arquitectura Microservicios",
        "ubicacion": "Santiago de Surco, Lima, Perú",
        "telefono": "989322088",
        "email": "diego.ramos@gmail.com",
        "github": "github.com/diegoramos-dev",
        "resumen": (
            "Ingeniero de Sistemas con 8 años de experiencia en desarrollo backend con Java 17, "
            "Spring Boot 3, Microservicios, PostgreSQL, Docker y AWS. Especializado en arquitecturas "
            "distribuidas de alta concurrencia y mensajería con Kafka para el sector banca y finanzas. "
            "Idiomas: Español nativo, Inglés avanzado."
        ),
        "habilidades": [
            "Java", "Spring Boot", "FastAPI", "Microservicios", "Kafka",
            "PostgreSQL", "Oracle", "Docker", "Kubernetes", "AWS", "Git", "CI/CD"
        ],
        "experiencias": [
            {
                "puesto": "Lead Backend Engineer",
                "empresa": "Banco de Crédito del Perú (BCP)",
                "periodo": "2021 - Actualidad (3 años)",
                "tecnologias": ["Java 17", "Spring Boot 3", "Kafka", "PostgreSQL", "AWS"],
                "descripcion": (
                    "Liderazgo técnico del motor de transferencias inmediatas interbancarias. "
                    "Diseño de microservicios resilientes soportando 12,000 transacciones por minuto con 99.99% uptime."
                ),
            },
            {
                "puesto": "Senior Java Developer",
                "empresa": "Tata Consultancy Services (TCS Perú)",
                "periodo": "2018 - 2021 (3 años)",
                "tecnologias": ["Java 11", "Spring Cloud", "Oracle", "Docker", "RabbitMQ"],
                "descripcion": (
                    "Desarrollo e integración de APIs bancarias para clientes en Lima y Santiago de Chile. "
                    "Optimización de consultas SQL complejas reduciendo latencia en un 40%."
                ),
            },
            {
                "puesto": "Backend Software Engineer",
                "empresa": "Interbank",
                "periodo": "2016 - 2018 (2 años)",
                "tecnologias": ["Java 8", "Spring MVC", "MySQL", "Git"],
                "descripcion": "Mantenimiento y evolución de plataformas transaccionales de banca retail.",
            },
        ],
        "educacion": [
            {"titulo": "Bachiller en Ingeniería de Sistemas", "institucion": "Universidad Nacional Mayor de San Marcos (UNMSM)", "anio": 2016},
            {"titulo": "AWS Certified Solutions Architect – Associate", "institucion": "Amazon Web Services", "anio": 2023},
        ],
        "idiomas": [
            {"idioma": "Español", "nivel": "Nativo"},
            {"idioma": "Inglés", "nivel": "Avanzado"},
        ],
        "generate_docx": True,
    },
    {
        "id": "02",
        "filename": "CV_02_Carlos_Garcia_DevOps_Lead_AlumniTCS",
        "dni": "46753314",
        "nombre_completo": "Carlos Eduardo García Sánchez",
        "titulo_profesional": "DevOps Specialist & Cloud Infrastructure Lead (Ex-TCS Alumni)",
        "ubicacion": "San Borja, Lima, Perú",
        "telefono": "999001122",
        "email": "carlos.garcia@adecco-post.pe",
        "github": "github.com/carlosgarcia-devops",
        "resumen": (
            "Especialista en Infraestructura Cloud y DevOps con 9 años de experiencia en diseño e implementación "
            "de plataformas cloud-native. Amplio dominio de Kubernetes, Terraform, Docker, AWS, Azure, Linux, "
            "Python y pipelines de CI/CD. Ex-colaborador de TCS Perú (Alumni Boomerang rehire eligible). "
            "Idiomas: Español nativo, Inglés avanzado, Portugués intermedio."
        ),
        "habilidades": [
            "Kubernetes", "Docker", "Terraform", "AWS", "Azure", "Linux",
            "CI/CD", "Git", "Python", "Prometheus", "Grafana", "Bash"
        ],
        "experiencias": [
            {
                "puesto": "Lead DevOps Engineer",
                "empresa": "Tata Consultancy Services (TCS Perú)",
                "periodo": "2021 - 2024 (3 años)",
                "tecnologias": ["Kubernetes", "Terraform", "AWS", "GitLab CI", "Linux"],
                "descripcion": (
                    "Líder del equipo de automatización para la cuenta BCP Home Banking. "
                    "Estandarización de despliegues GitOps reduciendo tiempo de release de 4 horas a 15 minutos."
                ),
            },
            {
                "puesto": "Cloud & DevOps Specialist",
                "empresa": "BBVA Continental",
                "periodo": "2018 - 2021 (3 años)",
                "tecnologias": ["AWS", "Docker", "Jenkins", "Python", "Terraform"],
                "descripcion": "Implementación de arquitectura multi-cuenta en AWS y hardening de clusters EKS.",
            },
            {
                "puesto": "Linux Infrastructure Administrator",
                "empresa": "Telefónica del Perú",
                "periodo": "2015 - 2018 (3 años)",
                "tecnologias": ["Linux", "Bash", "Ansible", "MySQL", "Nagios"],
                "descripcion": "Administración de más de 300 servidores productivos Red Hat Enterprise Linux.",
            },
        ],
        "educacion": [
            {"titulo": "Ingeniero Informático", "institucion": "Pontificia Universidad Católica del Perú (PUCP)", "anio": 2015},
            {"titulo": "Certified Kubernetes Administrator (CKA)", "institucion": "Linux Foundation / CNCF", "anio": 2022},
        ],
        "idiomas": [
            {"idioma": "Español", "nivel": "Nativo"},
            {"idioma": "Inglés", "nivel": "Avanzado"},
            {"idioma": "Portugués", "nivel": "Intermedio"},
        ],
        "generate_docx": True,
    },
    {
        "id": "03",
        "filename": "CV_03_Ana_Lucia_Quispe_Data_Engineer_Entel",
        "dni": "72345678",
        "nombre_completo": "Ana Lucía Quispe Mendoza",
        "titulo_profesional": "Data Engineer Senior & Big Data Architect",
        "ubicacion": "Los Olivos, Lima, Perú",
        "telefono": "987112233",
        "email": "ana.quispe@gmail.com",
        "github": "github.com/analucia-data",
        "resumen": (
            "Ingeniera de Datos con 5 años de experiencia diseñando arquitecturas lakehouse y pipelines de "
            "procesamiento batch y streaming. Sólida experiencia en Python, Apache Spark, Airflow, GCP, "
            "BigQuery, PostgreSQL, AWS Glue y Docker. Especializada en optimización de consultas SQL masivas. "
            "Idiomas: Español nativo, Inglés avanzado."
        ),
        "habilidades": [
            "Python", "Apache Spark", "Airflow", "PostgreSQL", "GCP",
            "BigQuery", "AWS", "Docker", "Git", "SQL Server", "Linux"
        ],
        "experiencias": [
            {
                "puesto": "Senior Data Engineer",
                "empresa": "Falabella Digital",
                "periodo": "2022 - Actualidad (2.5 años)",
                "tecnologias": ["Python", "Apache Spark", "Airflow", "GCP", "BigQuery"],
                "descripcion": (
                    "Construcción del data pipeline central procesando más de 50 millones de eventos diarios "
                    "de e-commerce para alimentar modelos predictivos de recomendación y analítica de ventas."
                ),
            },
            {
                "puesto": "Data Engineer",
                "empresa": "Entel Perú",
                "periodo": "2019 - 2022 (2.5 años)",
                "tecnologias": ["Python", "Airflow", "PostgreSQL", "AWS Glue", "Docker"],
                "descripcion": "Automatización de procesos ETL para reportería regulatoria y cálculo de churn de abonados.",
            },
        ],
        "educacion": [
            {"titulo": "Bachiller en Ciencias de la Computación", "institucion": "Universidad Nacional de Ingeniería (UNI)", "anio": 2019},
            {"titulo": "Google Cloud Certified Professional Data Engineer", "institucion": "Google Cloud", "anio": 2023},
        ],
        "idiomas": [
            {"idioma": "Español", "nivel": "Nativo"},
            {"idioma": "Inglés", "nivel": "Avanzado"},
        ],
        "generate_docx": True,
    },
    {
        "id": "04",
        "filename": "CV_04_Valeria_Flores_FullStack_React_Node",
        "dni": "71984512",
        "nombre_completo": "Valeria Beatriz Flores Rodríguez",
        "titulo_profesional": "Full Stack Developer Semi-Senior (React & Node.js)",
        "ubicacion": "San Isidro, Lima, Perú",
        "telefono": "976543210",
        "email": "valeria.flores@gmail.com",
        "github": "github.com/valeria-dev",
        "resumen": (
            "Desarrolladora Full Stack con 4 años de experiencia creando aplicaciones web modernas y "
            "escalables. Experta en React, TypeScript, Node.js, Python, PostgreSQL, Docker, HTML/CSS y Git. "
            "Enfocada en rendimiento de frontend, clean code y pruebas unitarias. "
            "Idiomas: Español nativo, Inglés intermedio."
        ),
        "habilidades": [
            "React", "TypeScript", "JavaScript", "Node.js", "Python",
            "HTML/CSS", "PostgreSQL", "Docker", "Git", "CI/CD"
        ],
        "experiencias": [
            {
                "puesto": "Full Stack Developer",
                "empresa": "Interbank Digital Lab",
                "periodo": "2021 - Actualidad (3 años)",
                "tecnologias": ["React", "TypeScript", "Node.js", "PostgreSQL", "Docker"],
                "descripcion": "Desarrollo del portal de onboarding digital para apertura de cuentas corrientes corporativas.",
            },
            {
                "puesto": "Frontend Web Developer",
                "empresa": "Culqi Perú",
                "periodo": "2020 - 2021 (1 año)",
                "tecnologias": ["React", "JavaScript", "HTML/CSS", "Git"],
                "descripcion": "Maquetación responsive y consumo de APIs para la pasarela de pagos web.",
            },
        ],
        "educacion": [
            {"titulo": "Licenciada en Ingeniería de Software", "institucion": "Universidad Peruana de Ciencias Aplicadas (UPC)", "anio": 2020},
        ],
        "idiomas": [
            {"idioma": "Español", "nivel": "Nativo"},
            {"idioma": "Inglés", "nivel": "Intermedio"},
        ],
        "generate_docx": False,
    },
    {
        "id": "05",
        "filename": "CV_05_Jorge_Chavez_Cloud_Architect",
        "dni": "45892134",
        "nombre_completo": "Jorge Luis Chávez Pinto",
        "titulo_profesional": "Principal Cloud Solutions Architect",
        "ubicacion": "La Molina, Lima, Perú",
        "telefono": "987654321",
        "email": "jorge.chavez@gmail.com",
        "github": "github.com/jorgechavez-arch",
        "resumen": (
            "Arquitecto de Soluciones Cloud con 10 años de experiencia liderando transformación digital "
            "en banca y telecomunicaciones. Dominio experto de AWS, Azure, Kubernetes, Microservicios, Kafka, "
            "Java, Docker y Terraform. Especialista en seguridad cloud y optimización de costos FinOps. "
            "Idiomas: Español nativo, Inglés avanzado."
        ),
        "habilidades": [
            "AWS", "Azure", "Kubernetes", "Microservicios", "Kafka",
            "Java", "Terraform", "Docker", "Linux", "Git"
        ],
        "experiencias": [
            {
                "puesto": "Lead Cloud Architect",
                "empresa": "BBVA Perú",
                "periodo": "2020 - Actualidad (4 años)",
                "tecnologias": ["AWS", "Azure", "Kubernetes", "Kafka", "Terraform"],
                "descripcion": "Definición de lineamientos de arquitectura cloud y modernización de plataformas core.",
            },
            {
                "puesto": "Senior Solutions Architect",
                "empresa": "IBM del Perú",
                "periodo": "2015 - 2020 (5 años)",
                "tecnologias": ["Java", "Microservicios", "Docker", "Linux"],
                "descripcion": "Consultoría de arquitectura para entidades financieras de primer nivel en Perú y Colombia.",
            },
            {
                "puesto": "Software Architect",
                "empresa": "Rimac Seguros",
                "periodo": "2014 - 2015 (1 año)",
                "tecnologias": ["Java", "Oracle", "Spring"],
                "descripcion": "Arquitectura de aplicaciones para cotización de pólizas en línea.",
            },
        ],
        "educacion": [
            {"titulo": "Ingeniero de Sistemas", "institucion": "Universidad de Lima", "anio": 2014},
            {"titulo": "AWS Certified Solutions Architect – Professional", "institucion": "AWS", "anio": 2022},
        ],
        "idiomas": [
            {"idioma": "Español", "nivel": "Nativo"},
            {"idioma": "Inglés", "nivel": "Avanzado"},
        ],
        "generate_docx": False,
    },
    {
        "id": "06",
        "filename": "CV_06_Sebastian_Lopez_Junior_Mobile_Flutter",
        "dni": "74890123",
        "nombre_completo": "Sebastián Andrés López Herrera",
        "titulo_profesional": "Mobile Developer Junior (Flutter & Dart)",
        "ubicacion": "Pueblo Libre, Lima, Perú",
        "telefono": "921098765",
        "email": "sebastian.lopez@gmail.com",
        "github": "github.com/sebaslopez-dev",
        "resumen": (
            "Desarrollador Móvil con 1 año de experiencia profesional creando aplicaciones nativas e híbridas "
            "con Flutter, Dart, Android, iOS, Firebase, Git y consumo de REST APIs. Graduado con honores y "
            "apasionado por las buenas prácticas de UI/UX móvil. "
            "Idiomas: Español nativo, Inglés básico."
        ),
        "habilidades": [
            "Flutter", "Dart", "Android", "iOS", "Firebase",
            "Git", "HTML/CSS"
        ],
        "experiencias": [
            {
                "puesto": "Junior Flutter Developer",
                "empresa": "Applaudo Studios Perú",
                "periodo": "2023 - Actualidad (1 año)",
                "tecnologias": ["Flutter", "Dart", "Firebase", "REST APIs"],
                "descripcion": "Implementación de pantallas de catálogo y carrito de compras para app móvil retail.",
            },
        ],
        "educacion": [
            {"titulo": "Bachiller en Ingeniería de Sistemas e Informática", "institucion": "Universidad Tecnológica del Perú (UTP)", "anio": 2023},
        ],
        "idiomas": [
            {"idioma": "Español", "nivel": "Nativo"},
            {"idioma": "Inglés", "nivel": "Básico"},
        ],
        "generate_docx": False,
    },
    {
        "id": "07",
        "filename": "CV_07_Lucia_Benitez_Security_Engineer",
        "dni": "43981276",
        "nombre_completo": "Lucía Esperanza Benítez Navarro",
        "titulo_profesional": "Senior Cybersecurity & DevSecOps Engineer",
        "ubicacion": "Lince, Lima, Perú",
        "telefono": "910987654",
        "email": "lucia.benitez@gmail.com",
        "github": "github.com/luciabenitez-sec",
        "resumen": (
            "Ingeniera de Seguridad con 6 años de experiencia en seguridad ofensiva y defensiva para el sector "
            "financiero. Experiencia comprobada en Ethical Hacking, OWASP, SIEM, Python, Cloud Security en AWS, "
            "Docker y Linux. Implementación de escaneo de vulnerabilidades en pipelines CI/CD. "
            "Idiomas: Español nativo, Inglés intermedio."
        ),
        "habilidades": [
            "Ethical Hacking", "OWASP", "SIEM", "Python", "Cloud Security",
            "Linux", "Docker", "CI/CD", "AWS", "Git"
        ],
        "experiencias": [
            {
                "puesto": "Senior Security Analyst",
                "empresa": "Banco BBVA Perú",
                "periodo": "2020 - Actualidad (4 años)",
                "tecnologias": ["SIEM", "OWASP", "Python", "AWS", "Linux"],
                "descripcion": "Monitoreo del SOC nivel 3, análisis forense digital y pruebas periódicas de penetración.",
            },
            {
                "puesto": "Information Security Specialist",
                "empresa": "Claro Perú",
                "periodo": "2018 - 2020 (2 años)",
                "tecnologias": ["Ethical Hacking", "Linux", "Docker", "Python"],
                "descripcion": "Hardening de infraestructura y remediación de vulnerabilidades web y móviles.",
            },
        ],
        "educacion": [
            {"titulo": "Ingeniera de Telecomunicaciones", "institucion": "Universidad Nacional de Ingeniería (UNI)", "anio": 2018},
            {"titulo": "Certified Information Systems Security Professional (CISSP)", "institucion": "(ISC)²", "anio": 2022},
        ],
        "idiomas": [
            {"idioma": "Español", "nivel": "Nativo"},
            {"idioma": "Inglés", "nivel": "Intermedio"},
        ],
        "generate_docx": False,
    },
    {
        "id": "08",
        "filename": "CV_08_Brenda_Gutierrez_Java_Inedita",
        "dni": "80112233",
        "nombre_completo": "Brenda Sofía Gutiérrez Paredes",
        "titulo_profesional": "Desarrollador Java Mid-Level (Candidato Limpio / Inédito)",
        "ubicacion": "Surquillo, Lima, Perú",
        "telefono": "911223344",
        "email": "brenda.gutierrez@adecco-post.pe",
        "github": "github.com/brendagutierrez-dev",
        "resumen": (
            "Desarrolladora Java con 3 años de experiencia construyendo APIs REST y microservicios con "
            "Spring Boot, MySQL, Docker, Linux y Git. Candidata limpia sin antecedentes en cartera previa, "
            "calibrada para importación masiva directa en lote de Adecco. "
            "Idiomas: Español nativo, Inglés intermedio."
        ),
        "habilidades": [
            "Java", "Spring Boot", "MySQL", "Docker", "Git", "Linux", "PostgreSQL"
        ],
        "experiencias": [
            {
                "puesto": "Java Developer",
                "empresa": "Everis / NTT Data Perú",
                "periodo": "2021 - Actualidad (3 años)",
                "tecnologias": ["Java", "Spring Boot", "MySQL", "Docker", "Git"],
                "descripcion": "Desarrollo de módulos de facturación electrónica y pasarelas de pago.",
            },
        ],
        "educacion": [
            {"titulo": "Bachiller en Ingeniería de Sistemas", "institucion": "Universidad San Ignacio de Loyola (USIL)", "anio": 2021},
        ],
        "idiomas": [
            {"idioma": "Español", "nivel": "Nativo"},
            {"idioma": "Inglés", "nivel": "Intermedio"},
        ],
        "generate_docx": False,
    },
    {
        "id": "09",
        "filename": "CV_09_Miguel_Torres_QA_Automation",
        "dni": "70812390",
        "nombre_completo": "Miguel Ángel Torres Huamán",
        "titulo_profesional": "QA Automation Lead Specialist",
        "ubicacion": "Surquillo, Lima, Perú",
        "telefono": "965432109",
        "email": "miguel.torres@gmail.com",
        "github": "github.com/migueltorres-qa",
        "resumen": (
            "Ingeniero de Calidad de Software con 5 años de experiencia diseñando frameworks de automatización "
            "de pruebas end-to-end con Selenium, Cypress, Python, Java, CI/CD, Postman y Git. Especializado en "
            "pruebas de regresión automatizadas en entornos ágiles. "
            "Idiomas: Español nativo, Inglés intermedio."
        ),
        "habilidades": [
            "Selenium", "Cypress", "Python", "Java", "CI/CD",
            "Postman", "Git", "Docker", "Linux"
        ],
        "experiencias": [
            {
                "puesto": "Senior QA Automation Engineer",
                "empresa": "Entel Perú",
                "periodo": "2021 - Actualidad (3 años)",
                "tecnologias": ["Cypress", "Selenium", "Python", "CI/CD", "Postman"],
                "descripcion": "Liderazgo del framework de pruebas automatizadas para la app móvil y web transaccional.",
            },
            {
                "puesto": "QA Analyst",
                "empresa": "Belcorp",
                "periodo": "2019 - 2021 (2 años)",
                "tecnologias": ["Selenium", "Java", "Postman", "Git"],
                "descripcion": "Automatización de flujos críticos de facturación y despacho para 14 países.",
            },
        ],
        "educacion": [
            {"titulo": "Bachiller en Ingeniería Informática", "institucion": "Universidad Ricardo Palma (URP)", "anio": 2019},
        ],
        "idiomas": [
            {"idioma": "Español", "nivel": "Nativo"},
            {"idioma": "Inglés", "nivel": "Intermedio"},
        ],
        "generate_docx": False,
    },
    {
        "id": "10",
        "filename": "CV_10_Patricia_Vargas_Scrum_Master",
        "dni": "47589623",
        "nombre_completo": "Patricia Elena Vargas Delgado",
        "titulo_profesional": "Agile Coach & Senior Scrum Master",
        "ubicacion": "Miraflores, Lima, Perú",
        "telefono": "954321098",
        "email": "patricia.vargas@gmail.com",
        "github": "github.com/patriciavargas-agile",
        "resumen": (
            "Líder Ágil y Scrum Master con 7 años de experiencia transformando equipos de desarrollo de software "
            "de alto desempeño en banca y retail. Dominio experto de Agile, Scrum, Jira, Kanban, Facilitación "
            "y Gestión de Proyectos tecnológicos. "
            "Idiomas: Español nativo, Inglés avanzado."
        ),
        "habilidades": [
            "Agile", "Scrum", "Jira", "Kanban", "Facilitación",
            "Gestión de Proyectos", "Git"
        ],
        "experiencias": [
            {
                "puesto": "Senior Scrum Master",
                "empresa": "Falabella Digital",
                "periodo": "2020 - Actualidad (4 años)",
                "tecnologias": ["Scrum", "Jira", "Kanban", "Agile"],
                "descripcion": "Facilitación de 3 squads multidisciplinarios de producto digital aumentando velocity en 35%.",
            },
            {
                "puesto": "Scrum Master",
                "empresa": "Banco Ripley",
                "periodo": "2017 - 2020 (3 años)",
                "tecnologias": ["Agile", "Jira", "Scrum"],
                "descripcion": "Acompañamiento a equipos de desarrollo en adopción de Scrum y ceremonias ágiles.",
            },
        ],
        "educacion": [
            {"titulo": "Licenciada en Administración de Empresas y TI", "institucion": "Universidad del Pacífico (UP)", "anio": 2017},
            {"titulo": "Professional Scrum Master II (PSM II)", "institucion": "Scrum.org", "anio": 2021},
        ],
        "idiomas": [
            {"idioma": "Español", "nivel": "Nativo"},
            {"idioma": "Inglés", "nivel": "Avanzado"},
        ],
        "generate_docx": False,
    },
]


CUL_CASES = [
    {
        "filename": "CUL_01_Aprobado_Diego_Ramos_Limpio.pdf",
        "dni": "76128709",
        "nombres_completos": "DIEGO ALONSO RAMOS QUISPE",
        "fecha_emision": "15/01/2026",
        "tiene_antecedentes": False,
        "grados_sunedu": [
            "BACHILLER EN INGENIERIA DE SISTEMAS, UNIVERSIDAD NACIONAL MAYOR DE SAN MARCOS.",
        ],
        "trayectoria_formal": [
            "EMPRESA: BANCO DE CREDITO DEL PERU S.A., PERIODO 2021-ACTUALIDAD.",
            "EMPRESA: TCS SOLUTION CENTER S.A.C., PERIODO 2018-2021.",
            "EMPLEADOR: INTERBANK S.A., PERIODO 2016-2018.",
        ],
    },
    {
        "filename": "CUL_02_Observado_Roberto_Montes_Antecedentes.pdf",
        "dni": "41998877",
        "nombres_completos": "ROBERTO CARLOS MONTES VILCA",
        "fecha_emision": "20/02/2026",
        "tiene_antecedentes": True,
        "grados_sunedu": [
            "TECNICO EN COMPUTACION E INFORMATICA, INSTITUTO SUPERIOR CIBERTEC.",
        ],
        "trayectoria_formal": [
            "EMPRESA: SERVICIOS GENERALES LIMA S.A.C., PERIODO 2020-2022.",
        ],
    },
    {
        "filename": "CUL_03_Aprobado_Carlos_Garcia_AlumniTCS.pdf",
        "dni": "46753314",
        "nombres_completos": "CARLOS EDUARDO GARCIA SANCHEZ",
        "fecha_emision": "10/02/2026",
        "tiene_antecedentes": False,
        "grados_sunedu": [
            "INGENIERO INFORMATICO, PONTIFICIA UNIVERSIDAD CATOLICA DEL PERU.",
        ],
        "trayectoria_formal": [
            "EMPLEADOR: TCS SOLUTION CENTER S.A.C., PERIODO 2021-2024.",
            "EMPRESA: BBVA CONTINENTAL S.A., PERIODO 2018-2021.",
            "EMPLEADOR: TELEFONICA DEL PERU S.A.A., PERIODO 2015-2018.",
        ],
    },
]


def generate_all_cvs() -> None:
    """Genera todos los CVs en formato PDF y DOCX."""
    print("-> Generando CVs en PDF y DOCX...")
    for cv in CV_CANDIDATES:
        pdf_path = CVS_DIR / f"{cv['filename']}.pdf"
        build_cv_pdf(pdf_path, cv)
        print(f"   [OK] {pdf_path.name}")
        if cv.get("generate_docx", False):
            docx_path = CVS_DIR / f"{cv['filename']}.docx"
            build_cv_docx(docx_path, cv)
            print(f"   [OK] {docx_path.name}")


def generate_all_culs() -> None:
    """Genera certificados CUL MTPE oficiales simulados."""
    print("-> Generando Certificados CUL (MTPE Perú) en PDF...")
    for cul in CUL_CASES:
        out_path = CULS_DIR / cul["filename"]
        build_cul_pdf(out_path, cul)
        print(f"   [OK] {out_path.name}")


def generate_all_excels() -> None:
    """Genera planillas de prueba de Adecco con distintos escenarios."""
    print("-> Generando Planillas de Adecco en Excel y CSV...")

    # 1. Planilla Semanal Calibrada (20 filas, balance exacto de los 4 colores)
    data_p1 = [
        # 7 Rojos Duplicados Activos (presentes en BD activa)
        {"DNI / CE": "76128709", "Nombres y Apellidos": "Diego Alonso Ramos Quispe", "Móvil": "989322088", "Puesto": "Desarrollador Java Senior", "Correo": "diego.ramos@gmail.com", "Sueldo Bruto": 9000},
        {"DNI / CE": "45892134", "Nombres y Apellidos": "Jorge Luis Chavez Pinto", "Móvil": "987654321", "Puesto": "Cloud Architect", "Correo": "jorge.chavez@gmail.com", "Sueldo Bruto": 12000},
        {"DNI / CE": "71984512", "Nombres y Apellidos": "Valeria Beatriz Flores Rodriguez", "Móvil": "976543210", "Puesto": "Full Stack Developer", "Correo": "valeria.flores@gmail.com", "Sueldo Bruto": 7000},
        {"DNI / CE": "70812390", "Nombres y Apellidos": "Miguel Angel Torres Huaman", "Móvil": "965432109", "Puesto": "QA Automation", "Correo": "miguel.torres@gmail.com", "Sueldo Bruto": 6800},
        {"DNI / CE": "47589623", "Nombres y Apellidos": "Patricia Elena Vargas Delgado", "Móvil": "954321098", "Puesto": "Scrum Master", "Correo": "patricia.vargas@gmail.com", "Sueldo Bruto": 8500},
        {"DNI / CE": "73412589", "Nombres y Apellidos": "Renzo Paolo Castillo Morales", "Móvil": "943210987", "Puesto": "Backend Python Developer", "Correo": "renzo.castillo@gmail.com", "Sueldo Bruto": 6500},
        {"DNI / CE": "48912345", "Nombres y Apellidos": "Monica Beatriz Rojas Soto", "Móvil": "932109876", "Puesto": "Frontend Angular Specialist", "Correo": "monica.rojas@gmail.com", "Sueldo Bruto": 6200},
        # 3 Amarillos Reactivables (>180 días de cierre previo por sueldo o vacante cancelada)
        {"DNI / CE": "74890123", "Nombres y Apellidos": "Sebastian Andres Lopez Herrera", "Móvil": "921098765", "Puesto": "Mobile Developer Flutter", "Correo": "sebastian.lopez@gmail.com", "Sueldo Bruto": 4500},
        {"DNI / CE": "43981276", "Nombres y Apellidos": "Lucia Esperanza Benitez Navarro", "Móvil": "910987654", "Puesto": "Security Engineer", "Correo": "lucia.benitez@gmail.com", "Sueldo Bruto": 9500},
        {"DNI / CE": "75619283", "Nombres y Apellidos": "Gonzalo Martin Palacios Vega", "Móvil": "909876543", "Puesto": "Data Analyst", "Correo": "gonzalo.palacios@gmail.com", "Sueldo Bruto": 5000},
        # 8 Verdes Limpios / Inéditos (listos para importación directa en 1 clic)
        {"DNI / CE": "80112233", "Nombres y Apellidos": "Brenda Sofia Gutierrez Paredes", "Móvil": "911223344", "Puesto": "Desarrollador Java", "Correo": "brenda.gutierrez@adecco-post.pe", "Sueldo Bruto": 5800},
        {"DNI / CE": "80223344", "Nombres y Apellidos": "Victor Manuel Romero Diaz", "Móvil": "922334455", "Puesto": "Data Engineer", "Correo": "victor.romero@adecco-post.pe", "Sueldo Bruto": 7200},
        {"DNI / CE": "80334455", "Nombres y Apellidos": "Camila Andrea Morales Rios", "Móvil": "933445566", "Puesto": "DevOps Specialist", "Correo": "camila.morales@adecco-post.pe", "Sueldo Bruto": 8000},
        {"DNI / CE": "80445566", "Nombres y Apellidos": "Andres Felipe Salazar Castro", "Móvil": "944556677", "Puesto": "Cloud Architect", "Correo": "andres.salazar@adecco-post.pe", "Sueldo Bruto": 11500},
        {"DNI / CE": "80556677", "Nombres y Apellidos": "Daniela Alejandra Ponce Vega", "Móvil": "955667788", "Puesto": "Full Stack Developer", "Correo": "daniela.ponce@adecco-post.pe", "Sueldo Bruto": 6800},
        {"DNI / CE": "80667788", "Nombres y Apellidos": "Mateo Nicolas Cardenas Ruiz", "Móvil": "966778899", "Puesto": "QA Automation", "Correo": "mateo.cardenas@adecco-post.pe", "Sueldo Bruto": 6500},
        {"DNI / CE": "80778899", "Nombres y Apellidos": "Lucia Fernanda Tapia Cruz", "Móvil": "977889900", "Puesto": "Scrum Master", "Correo": "lucia.tapia@adecco-post.pe", "Sueldo Bruto": 8200},
        {"DNI / CE": "80889900", "Nombres y Apellidos": "Gabriel Alejandro Vidal Ortiz", "Móvil": "988990011", "Puesto": "Backend Python Developer", "Correo": "gabriel.vidal@adecco-post.pe", "Sueldo Bruto": 6900},
        # 2 Púrpuras Alumni TCS (Boomerang ex-colaborador)
        {"DNI / CE": "46753314", "Nombres y Apellidos": "Carlos Eduardo Garcia Sanchez", "Móvil": "999001122", "Puesto": "Tech Lead Java", "Correo": "carlos.garcia@adecco-post.pe", "Sueldo Bruto": 10500},
        {"DNI / CE": "41239876", "Nombres y Apellidos": "Raul Fernando Munoz Arias", "Móvil": "911002233", "Puesto": "Senior Cloud Engineer", "Correo": "raul.munoz@adecco-post.pe", "Sueldo Bruto": 9800},
    ]
    p1_path = EXCELS_DIR / "Planilla_Adecco_01_Semanal_Calibrada_20_Candidatos.xlsx"
    pd.DataFrame(data_p1).to_excel(p1_path, index=False)
    print(f"   [OK] {p1_path.name}")

    # 2. Planilla con Cabeceras Alternativas (Prueba de resiliencia semántica de alias)
    data_p2 = [
        {"Documento de Identidad": "76128709", "Postulante": "Diego Alonso Ramos Quispe", "Celular": "989322088", "Cargo Solicitado": "Desarrollador Java Senior", "Email Personal": "diego.ramos@gmail.com", "Expectativa Salarial": "9000"},
        {"Documento de Identidad": "46753314", "Postulante": "Carlos Eduardo Garcia Sanchez", "Celular": "999001122", "Cargo Solicitado": "DevOps Specialist", "Email Personal": "carlos.garcia@adecco-post.pe", "Expectativa Salarial": "10500"},
        {"Documento de Identidad": "80112233", "Postulante": "Brenda Sofia Gutierrez Paredes", "Celular": "911223344", "Cargo Solicitado": "Desarrollador Java", "Email Personal": "brenda.gutierrez@adecco-post.pe", "Expectativa Salarial": "5800"},
        {"Documento de Identidad": "74890123", "Postulante": "Sebastian Andres Lopez Herrera", "Celular": "921098765", "Cargo Solicitado": "Mobile Developer Flutter", "Email Personal": "sebastian.lopez@gmail.com", "Expectativa Salarial": "4500"},
        {"Documento de Identidad": "80223344", "Postulante": "Victor Manuel Romero Diaz", "Celular": "922334455", "Cargo Solicitado": "Data Engineer", "Email Personal": "victor.romero@adecco-post.pe", "Expectativa Salarial": "7200"},
    ]
    p2_path = EXCELS_DIR / "Planilla_Adecco_02_Cabeceras_Alternativas_Alias.xlsx"
    pd.DataFrame(data_p2).to_excel(p2_path, index=False)
    print(f"   [OK] {p2_path.name}")

    # 3. Planilla con Casos Borde y Formatos "Sucios"
    data_p3 = [
        {"DNI": "  76128709  ", "Candidato": "DIEGO RAMOS (CON ESPACIOS)", "Telefono": "+51 989 322 088", "Puesto": "Desarrollador Java Senior", "Correo": "  DIEGO.RAMOS@GMAIL.COM  "},
        {"DNI": "46753314.0", "Candidato": "Carlos Garcia Sanchez", "Telefono": "999-001-122", "Puesto": "DevOps Specialist", "Correo": "carlos.garcia@tcs.com"},
        {"DNI": "80112233", "Candidato": "Brenda Gutierrez", "Telefono": "(51) 911223344", "Puesto": "Desarrollador Java", "Correo": ""},  # Sin correo
        {"DNI": None, "Candidato": None, "Telefono": None, "Puesto": None, "Correo": None},  # Fila vacía
        {"DNI": "80445566", "Candidato": "Andres Felipe Salazar Castro", "Telefono": "944556677", "Puesto": "Cloud Architect", "Correo": "andres.salazar@adecco-post.pe"},
        {"DNI": "74890123", "Candidato": "Sebastian Lopez", "Telefono": "921098765", "Puesto": "Mobile Developer", "Correo": "sebastian.lopez@gmail.com"},
    ]
    p3_path = EXCELS_DIR / "Planilla_Adecco_03_Casos_Borde_y_Formatos_Sucios.xlsx"
    pd.DataFrame(data_p3).to_excel(p3_path, index=False)
    print(f"   [OK] {p3_path.name}")

    # 4. Planilla Lote Grande (50 candidatos)
    nombres_pool = [
        "Alejandro", "Sofia", "Mateo", "Valentina", "Leonardo", "Camila", "Matias", "Isabella",
        "Nicolas", "Luciana", "Santiago", "Valeria", "Samuel", "Mariana", "Lucas", "Gabriela",
        "Benjamin", "Daniela", "Daniel", "Catalina", "Joaquin", "Victoria", "Alonso", "Martina",
        "Diego", "Paula", "Felipe", "Andrea", "Rodrigo", "Natalia", "Ignacio", "Elena",
        "Sebastian", "Renata", "Esteban", "Clara", "Emilio", "Sara", "Gabriel", "Juana",
        "Tomas", "Alicia", "Alvaro", "Florencia", "Bruno", "Constanza", "Maximiliano", "Laura",
        "Adrian", "Miranda"
    ]
    apellidos_pool = [
        "Alvarez", "Benitez", "Castillo", "Duran", "Espinoza", "Flores", "Garcia", "Herrera",
        "Ibanez", "Juarez", "Lozano", "Morales", "Navarro", "Ortega", "Perez", "Quispe",
        "Ramos", "Sanchez", "Torres", "Ugarte", "Vargas", "Yanez", "Zapata", "Aliaga",
        "Bustamante", "Cornejo", "Diaz", "Enciso", "Fuentes", "Guzman", "Hidalgo", "Jauregui",
        "Lara", "Medina", "Noriega", "Ochoa", "Paredes", "Quintana", "Ramirez", "Salazar",
        "Tapia", "Urbina", "Villanueva", "Zambrano", "Acosta", "Becerra", "Carrasco", "Delgado",
        "Escalante", "Farfan"
    ]
    roles_pool = [
        "Desarrollador Java Senior", "Data Engineer", "DevOps Specialist", "Full Stack Developer",
        "Cloud Architect", "QA Automation", "Scrum Master", "Frontend Angular Specialist"
    ]
    data_p4 = []
    for i in range(50):
        dni_num = 81000000 + i
        # Intercalar duplicados conocidos cada ciertas filas
        if i == 5:
            dni_str = "76128709"  # Diego Ramos (Rojo)
            nom = "Diego Alonso Ramos Quispe"
        elif i == 12:
            dni_str = "46753314"  # Carlos Garcia (Alumni)
            nom = "Carlos Eduardo Garcia Sanchez"
        elif i == 20:
            dni_str = "74890123"  # Sebastian Lopez (Amarillo)
            nom = "Sebastian Andres Lopez Herrera"
        else:
            dni_str = str(dni_num)
            nom = f"{nombres_pool[i]} {apellidos_pool[i]} {apellidos_pool[(i + 7) % len(apellidos_pool)]}"

        data_p4.append({
            "DNI / CE": dni_str,
            "Nombres y Apellidos": nom,
            "Móvil": f"9{random_phone_suffix(i)}",
            "Puesto": roles_pool[i % len(roles_pool)],
            "Correo": f"candidato.{i+1}@proveedor-talento.pe",
            "Pretensión Salarial": 5500 + (i % 8) * 700,
        })
    p4_path = EXCELS_DIR / "Planilla_Adecco_04_Lote_Grande_50_Candidatos.xlsx"
    pd.DataFrame(data_p4).to_excel(p4_path, index=False)
    print(f"   [OK] {p4_path.name}")

    # 5. Planilla en formato CSV (15 candidatos)
    data_p5 = data_p1[:15]
    p5_path = EXCELS_DIR / "Planilla_Adecco_05_Sourcing_Proveedor.csv"
    pd.DataFrame(data_p5).to_csv(p5_path, index=False, encoding="utf-8-sig")
    print(f"   [OK] {p5_path.name}")


def random_phone_suffix(i: int) -> str:
    """Genera 8 dígitos para un teléfono móvil peruano."""
    base = 80000000 + (i * 1371) % 9999999
    return str(base)[:8]


def generate_all_reports() -> None:
    """Genera el reporte oficial de 5 columnas para Adecco bajo Ley 29733."""
    print("-> Generando Reporte de Exclusión de 5 Columnas (Ley 29733)...")
    rep_data = [
        {
            "DNI": "76128709",
            "Nombres y Apellidos": "Diego Alonso Ramos Quispe",
            "Perfil": "Desarrollador Java Senior",
            "Vigencia Exclusión": "Hasta 15/12/2026",
            "Estado": "En Proceso Activo",
        },
        {
            "DNI": "45892134",
            "Nombres y Apellidos": "Jorge Luis Chavez Pinto",
            "Perfil": "Cloud Architect",
            "Vigencia Exclusión": "Hasta 30/11/2026",
            "Estado": "En Proceso Activo",
        },
        {
            "DNI": "71984512",
            "Nombres y Apellidos": "Valeria Beatriz Flores Rodriguez",
            "Perfil": "Full Stack Developer",
            "Vigencia Exclusión": "Hasta 10/01/2027",
            "Estado": "En Proceso Activo",
        },
        {
            "DNI": "70812390",
            "Nombres y Apellidos": "Miguel Angel Torres Huaman",
            "Perfil": "QA Automation",
            "Vigencia Exclusión": "Hasta 28/02/2027",
            "Estado": "En Proceso Activo",
        },
        {
            "DNI": "47589623",
            "Nombres y Apellidos": "Patricia Elena Vargas Delgado",
            "Perfil": "Scrum Master",
            "Vigencia Exclusión": "Hasta 15/03/2027",
            "Estado": "Cartera Excluida",
        },
        {
            "DNI": "42345678",
            "Nombres y Apellidos": "Manuel Alberto Paredes Meza",
            "Perfil": "Database Administrator",
            "Vigencia Exclusión": "Permanente",
            "Estado": "Exclusión Institucional",
        },
        {
            "DNI": "46753314",
            "Nombres y Apellidos": "Carlos Eduardo Garcia Sanchez",
            "Perfil": "Tech Lead Java",
            "Vigencia Exclusión": "Permanente",
            "Estado": "Alumni TCS Perú (Patrimonio Interno)",
        },
    ]
    rep_path = REPORTES_DIR / "Reporte_Exclusion_Ley29733_5Columnas_Modelo.xlsx"
    pd.DataFrame(rep_data).to_excel(rep_path, index=False)
    print(f"   [OK] {rep_path.name}")


def generate_all_rgs() -> None:
    """Genera ejemplos de mensajes de solicitudes de requerimiento de clientes."""
    print("-> Generando Requerimientos RGS en texto plano...")

    rgs_samples = {
        "RGS_01_BCP_Java_Backend_Senior.txt": (
            "De: delivery.manager@tcs.com\n"
            "Para: recruiting.lead@tcs.com\n"
            "Asunto: URGENTE: 2 Posiciones Backend Java Senior - Cuenta BCP\n\n"
            "Hola equipo,\n\n"
            "El líder de arquitectura de BCP necesita con urgencia cubrir 2 posiciones "
            "de desarrollador backend senior para el proyecto de transferencias inmediatas.\n\n"
            "Requisitos indispensables (Must have):\n"
            "- Al menos 5 años con Java 17 o superior y Spring Boot 3.\n"
            "- Experiencia sólida en Microservicios y mensajería distribuida con Kafka.\n"
            "- Manejo avanzado de base de datos Oracle o PostgreSQL.\n\n"
            "Requisitos deseables (Nice to have):\n"
            "- Nube AWS y contenedores con Docker y Kubernetes.\n"
            "- Pruebas unitarias con JUnit y Mockito.\n\n"
            "Condiciones del puesto:\n"
            "- Presupuesto máximo autorizado: S/. 9,500 bruto mensual en planilla TCS.\n"
            "- Modalidad de trabajo: Híbrida (2 días presenciales en sede La Molina, Lima).\n"
            "- Cliente: BCP.\n\n"
            "Por favor priorizar sourcing inmediato.\n"
            "Saludos,\n"
            "Delivery Manager TCS Perú"
        ),
        "RGS_02_Entel_Data_Engineer_Remoto.txt": (
            "De: dm.entel@tcs.com\n"
            "Para: sourcing.team@tcs.com\n"
            "Asunto: Requerimiento Data Engineer 100% Remoto - Entel Perú\n\n"
            "Buen día equipo,\n\n"
            "Para la cuenta Entel requerimos incorporar un Data Engineer con 3 a 4 años "
            "de experiencia sólida en arquitecturas analíticas.\n\n"
            "Requisitos obligatorios:\n"
            "- Python avanzado y SQL para procesamiento de grandes volúmenes.\n"
            "- Apache Spark (PySpark) y orquestación con Apache Airflow.\n"
            "- Construcción y optimización de pipelines ETL y ELT.\n\n"
            "Deseables:\n"
            "- Experiencia en Google Cloud Platform (GCP), especialmente BigQuery.\n"
            "- Databricks y AWS Glue.\n\n"
            "Presupuesto y condiciones:\n"
            "- Tarifa salarial: Hasta S/. 8,000 bruto mensual.\n"
            "- Modalidad: 100% Remoto a nivel nacional (Perú).\n"
            "- Cliente: Entel.\n"
        ),
        "RGS_03_Falabella_DevOps_Cloud_Hibrido.txt": (
            "De: falabella.techlead@tcs.com\n"
            "Para: talent.acquisition@tcs.com\n"
            "Asunto: Vacante DevOps Specialist - Falabella Digital\n\n"
            "Hola Reclutamiento,\n\n"
            "Necesitamos con urgencia un DevOps Specialist para la célula de Checkout de Falabella Digital.\n\n"
            "Requisitos excluyentes:\n"
            "- Mínimo 4 años administrando clusters productivos de Kubernetes (EKS / GKE).\n"
            "- Automatización de infraestructura con Terraform y Docker.\n"
            "- Construcción de pipelines CI/CD con GitLab CI o GitHub Actions.\n"
            "- Sólidos fundamentos de Linux y redes cloud.\n\n"
            "Requisitos valorados:\n"
            "- Nube AWS, monitoreo con Prometheus y Grafana.\n"
            "- Conocimientos de Python o Go para scripting.\n\n"
            "Presupuesto: Hasta S/. 11,000 según seniority evaluado.\n"
            "Modalidad: Híbrido en San Isidro (1 día por semana).\n"
            "Cliente: Falabella."
        ),
        "RGS_04_Interbank_QA_Automation_Lead.txt": (
            "De: interbank.operations@tcs.com\n"
            "Para: recruiters@tcs.com\n"
            "Asunto: Búsqueda QA Automation Specialist - Interbank Digital Lab\n\n"
            "Estimado equipo de selección,\n\n"
            "Buscamos un especialista en automatización de pruebas de software para Interbank.\n\n"
            "Competencias indispensables:\n"
            "- 4 a 5 años en testing automatizado web y móvil.\n"
            "- Dominio avanzado de Cypress, Selenium WebDriver y Postman.\n"
            "- Lenguajes de scripting: Python o Java.\n"
            "- Integración de suites de pruebas en pipelines de CI/CD.\n\n"
            "Condiciones:\n"
            "- Salario ofrecido: S/. 7,500 bruto mensual.\n"
            "- Modalidad: Híbrido (sede Interbank San Isidro).\n"
            "- Cliente: Interbank."
        ),
    }

    for fname, content in rgs_samples.items():
        out_f = RGS_DIR / fname
        out_f.write_text(content, encoding="utf-8")
        print(f"   [OK] {out_f.name}")


def generate_documentation() -> None:
    """Genera README.md y GUIA_DE_PRUEBAS.md en la carpeta raíz de pruebas."""
    print("-> Generando Documentación y Guías de Uso...")

    readme_content = """# 📁 Carpeta de Documentos de Prueba - ATS TCS Perú

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
"""
    (BASE_DIR / "README.md").write_text(readme_content, encoding="utf-8")

    guia_content = """# 🚀 Guía Paso a Paso de Pruebas de Usuario (ATS TCS Perú)

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
"""
    (BASE_DIR / "GUIA_DE_PRUEBAS.md").write_text(guia_content, encoding="utf-8")
    print("   [OK] README.md y GUIA_DE_PRUEBAS.md creados con éxito.")


def main():
    print("=================================================================")
    print("  GENERANDO LOTE COMPLETO DE DOCUMENTOS DE PRUEBA (ATS TCS PERÚ) ")
    print("=================================================================")
    ensure_directories()
    generate_all_cvs()
    generate_all_culs()
    generate_all_excels()
    generate_all_reports()
    generate_all_rgs()
    generate_documentation()
    print("=================================================================")
    print(f"  FINALIZADO: Todos los archivos generados en:\n  {BASE_DIR}")
    print("=================================================================")


if __name__ == "__main__":
    main()
