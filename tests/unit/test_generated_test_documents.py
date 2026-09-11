"""Unit tests verifying the integrity and compatibility of generated test documents."""
from pathlib import Path
import pytest
import pandas as pd

from src.adapters.cv_parser.heuristic_extractor import HeuristicCVExtractor
from src.adapters.cv_parser.cul_extractor import CULExtractor
from src.adapters.adecco.excel_validator import ExcelAdeccoValidator
from src.services.rgs_normalizer_service import RGSNormalizerService


BASE_DIR = Path("documentos_prueba")
CVS_DIR = BASE_DIR / "cvs"
CULS_DIR = BASE_DIR / "certificados_cul_mtpe"
EXCELS_DIR = BASE_DIR / "planillas_adecco_excel"
REPORTES_DIR = BASE_DIR / "reportes_exclusion_ley29733"
RGS_DIR = BASE_DIR / "requerimientos_rgs"


def test_directories_and_core_files_exist():
    assert BASE_DIR.exists()
    assert (BASE_DIR / "README.md").exists()
    assert (BASE_DIR / "GUIA_DE_PRUEBAS.md").exists()
    assert CVS_DIR.exists()
    assert CULS_DIR.exists()
    assert EXCELS_DIR.exists()
    assert REPORTES_DIR.exists()
    assert RGS_DIR.exists()


def test_cv_pdf_extraction_diego_ramos():
    cv_path = CVS_DIR / "CV_01_Diego_Ramos_Java_Senior_BCP.pdf"
    assert cv_path.exists()
    assert cv_path.stat().st_size > 1000

    extractor = HeuristicCVExtractor()
    res = extractor.extract_from_pdf(cv_path)

    assert res["seniority_estimado"] == "Senior"
    assert res["anios_experiencia_total"] >= 5.0
    skill_names = [s["nombre"] for s in res["habilidades_tecnicas"]]
    assert "Java" in skill_names
    assert "Spring Boot" in skill_names
    assert "PostgreSQL" in skill_names or "Kafka" in skill_names


def test_cv_pdf_extraction_carlos_garcia():
    cv_path = CVS_DIR / "CV_02_Carlos_Garcia_DevOps_Lead_AlumniTCS.pdf"
    assert cv_path.exists()

    extractor = HeuristicCVExtractor()
    res = extractor.extract_from_pdf(cv_path)

    assert res["seniority_estimado"] == "Senior"
    skill_names = [s["nombre"] for s in res["habilidades_tecnicas"]]
    assert "Kubernetes" in skill_names
    assert "Docker" in skill_names
    assert "Terraform" in skill_names


def test_cv_docx_files_exist():
    docx_files = list(CVS_DIR.glob("*.docx"))
    assert len(docx_files) >= 3
    for f in docx_files:
        assert f.stat().st_size > 500


def test_cul_aprobado_clean():
    cul_path = CULS_DIR / "CUL_01_Aprobado_Diego_Ramos_Limpio.pdf"
    assert cul_path.exists()

    extractor = CULExtractor()
    res = extractor.extract_from_pdf(cul_path)

    assert res["tiene_antecedentes_penales_policiales"] is False
    assert res["bgc_status"] == "Aprobado"
    assert "APROBADO" in res["bgc_dictamen"]
    assert len(res["grados_sunedu"]) >= 1
    assert len(res["trayectoria_formal_registros"]) >= 1


def test_cul_observado_background():
    cul_path = CULS_DIR / "CUL_02_Observado_Roberto_Montes_Antecedentes.pdf"
    assert cul_path.exists()

    extractor = CULExtractor()
    res = extractor.extract_from_pdf(cul_path)

    assert res["tiene_antecedentes_penales_policiales"] is True
    assert res["bgc_status"] == "Observado_No_Apto"
    assert "OBSERVADO" in res["bgc_dictamen"]


def test_adecco_excel_parser_calibrada():
    excel_path = EXCELS_DIR / "Planilla_Adecco_01_Semanal_Calibrada_20_Candidatos.xlsx"
    assert excel_path.exists()

    validator = ExcelAdeccoValidator()
    res = validator.parse_spreadsheet(excel_path)

    assert res["total_rows_parsed"] == 20
    assert "documento" in res["column_mapping"].values()
    assert "nombres" in res["column_mapping"].values()
    assert "telefono" in res["column_mapping"].values()
    assert "perfil" in res["column_mapping"].values()


def test_adecco_excel_parser_alias():
    excel_path = EXCELS_DIR / "Planilla_Adecco_02_Cabeceras_Alternativas_Alias.xlsx"
    assert excel_path.exists()

    validator = ExcelAdeccoValidator()
    res = validator.parse_spreadsheet(excel_path)

    assert res["total_rows_parsed"] == 5
    assert "documento" in res["column_mapping"].values()
    assert "nombres" in res["column_mapping"].values()
    assert "telefono" in res["column_mapping"].values()


def test_adecco_csv_parser():
    csv_path = EXCELS_DIR / "Planilla_Adecco_05_Sourcing_Proveedor.csv"
    assert csv_path.exists()

    validator = ExcelAdeccoValidator()
    res = validator.parse_spreadsheet(csv_path)

    assert res["total_rows_parsed"] == 15
    assert "documento" in res["column_mapping"].values()


def test_reporte_exclusion_ley29733_columns():
    rep_path = REPORTES_DIR / "Reporte_Exclusion_Ley29733_5Columnas_Modelo.xlsx"
    assert rep_path.exists()

    df = pd.read_excel(rep_path)
    assert len(df.columns) == 5
    expected_cols = ["DNI", "Nombres y Apellidos", "Perfil", "Vigencia Exclusión", "Estado"]
    assert list(df.columns) == expected_cols

    # Verify zero private contact data
    for col in df.columns:
        col_lower = col.lower()
        assert "telefono" not in col_lower
        assert "celular" not in col_lower
        assert "correo" not in col_lower
        assert "email" not in col_lower
        assert "sueldo" not in col_lower


def test_rgs_normalizer_with_sample():
    rgs_file = RGS_DIR / "RGS_01_BCP_Java_Backend_Senior.txt"
    assert rgs_file.exists()

    text = rgs_file.read_text(encoding="utf-8")
    normalizer = RGSNormalizerService()
    res = normalizer.normalize_raw_text(text, cliente_sugerido="BCP")

    assert "Java" in res.titulo_puesto
    assert res.seniority in ["Senior", "Lead / Architect"]
    assert "BCP" in res.cliente
    assert len(res.must_have) >= 1
    assert any("java" in s.lower() for s in res.must_have)
