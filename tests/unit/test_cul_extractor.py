"""Unit tests for CUL Extractor (Certificado Único Laboral MTPE)."""
from src.adapters.cv_parser.cul_extractor import CULExtractor


def test_cul_extractor_clean_background():
    extractor = CULExtractor()
    sample_text = """
    MINISTERIO DE TRABAJO Y PROMOCIÓN DEL EMPLEO
    CERTIFICADO ÚNICO LABORAL (CUL)
    N° 2026-99182 Fecha de emisión: 15/02/2026

    INFORMACIÓN DE ANTECEDENTES
    POLICÍA NACIONAL DEL PERÚ: NO REGISTRA ANTECEDENTES POLICIALES
    INSTITUTO NACIONAL PENITENCIARIO: NO REGISTRA ANTECEDENTES PENALES
    PODER JUDICIAL: NO REGISTRA ANTECEDENTES JUDICIALES

    TRAYECTORIA EDUCATIVA FORMAL
    SUNEDU: BACHILLER EN INGENIERIA DE SISTEMAS

    TRAYECTORIA LABORAL FORMAL (PLANILLA ELECTRÓNICA SUNAT)
    EMPRESA: BANCO DE CREDITO DEL PERU S.A.
    EMPRESA: TATA CONSULTANCY SERVICES S.A.C.
    """
    res = extractor.extract_from_text(sample_text)
    assert res["tiene_antecedentes_penales_policiales"] is False
    assert res["bgc_status"] == "Aprobado"
    assert "APROBADO" in res["bgc_dictamen"]
    assert any("BACHILLER EN INGENIERIA DE SISTEMAS" in g for g in res["grados_sunedu"])
    assert res["fecha_emision_cul"] == "2026-02-15"


def test_cul_extractor_with_background():
    extractor = CULExtractor()
    sample_text = """
    CERTIFICADO ÚNICO LABORAL
    POLICÍA NACIONAL DEL PERÚ: SÍ REGISTRA ANTECEDENTES POLICIALES
    """
    res = extractor.extract_from_text(sample_text)
    assert res["tiene_antecedentes_penales_policiales"] is True
    assert res["bgc_status"] == "Observado_No_Apto"
    assert "OBSERVADO" in res["bgc_dictamen"]
