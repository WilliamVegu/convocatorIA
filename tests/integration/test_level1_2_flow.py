"""Integration tests verifying complete flow of Nivel 1 and Nivel 2 innovation features."""
from unittest.mock import patch, MagicMock
from src.services.rgs_normalizer_service import RGSNormalizerService
from src.services.fit_gap_service import FitGapService
from src.services.cheat_sheet_service import CheatSheetService
from src.services.salary_radar_service import SalaryRadarService
from src.adapters.github.github_adapter import GitHubAdapter
from src.adapters.cv_parser.cul_extractor import CULExtractor
from src.adapters.reporting.one_pager_builder import OnePagerBuilder


@patch("src.services.rgs_normalizer_service.config.GEMINI_API_KEY", "")
@patch("src.services.fit_gap_service.config.GEMINI_API_KEY", "")
@patch("src.services.cheat_sheet_service.config.GEMINI_API_KEY", "")
def test_level1_and_level2_complete_recruiting_flow():
    # 1. Normalizar RGS desestructurado (Propuesta P11 - Nivel 2)
    raw_rgs = """
    Hola Reclutamiento TCS,
    Requerimiento URGENTE para BCP:
    Desarrollador Java Senior con 5+ años.
    Imprescindible: Java, Spring Boot, Microservicios, SQL.
    Deseable: Docker, AWS, Kafka.
    Modalidad Híbrida en San Isidro. Rango hasta S/. 9500.
    """
    normalizer = RGSNormalizerService()
    rgs_norm = normalizer.normalize_raw_text(raw_rgs, cliente_sugerido="BCP")

    assert "Desarrollador Java" in rgs_norm.titulo_puesto
    assert rgs_norm.cliente == "BCP"
    assert len(rgs_norm.must_have) >= 3
    assert "Lima" in rgs_norm.cadena_booleana

    # 2. Análisis Fit & Gap de Candidato (Propuesta N1 - Nivel 1)
    cand_cv_text = """
    Desarrollador Senior con 6 años de experiencia en Banca.
    Especialista en Java 17, Spring Boot, Microservicios, SQL, Kafka y Docker.
    Arquitecturas hexagonales y Clean Architecture.
    """
    fit_gap_svc = FitGapService()
    fit_result = fit_gap_svc.compare_cv_vs_rgs(
        cv_text=cand_cv_text,
        cv_skills=[{"nombre": "Java"}, {"nombre": "Spring Boot"}, {"nombre": "Kafka"}],
        perfil_puesto=rgs_norm.titulo_puesto,
        must_have=rgs_norm.must_have,
        nice_to_have=rgs_norm.nice_to_have,
    )
    assert fit_result.score_porcentaje >= 75.0
    assert len(fit_result.fortalezas) > 0

    # 3. Auditoría de Repositorio GitHub en Vivo (Propuesta P10 - Nivel 1)
    user_mock = MagicMock(status_code=200)
    user_mock.json.return_value = {"login": "javedev", "public_repos": 12, "followers": 15}
    repos_mock = MagicMock(status_code=200)
    repos_mock.json.return_value = [
        {"name": "bcp-microservices", "fork": False, "language": "Java", "stargazers_count": 8},
        {"name": "spring-boot-starter", "fork": False, "language": "Java", "stargazers_count": 14},
    ]

    with patch("requests.get") as mock_get:
        mock_get.side_effect = lambda url, **kwargs: repos_mock if "repos" in url else user_mock
        gh_adapter = GitHubAdapter()
        audit = gh_adapter.audit_user("https://github.com/javedev")

        assert audit.existe is True
        assert audit.repos_propios == 2
        assert "Java" in audit.lenguajes_principales

    # 4. Parsing Inteligente CUL MTPE (Propuesta P2 - Nivel 1)
    cul_text = """
    MINISTERIO DE TRABAJO Y PROMOCION DEL EMPLEO
    CERTIFICADO UNICO LABORAL
    POLICIA NACIONAL DEL PERU: NO REGISTRA ANTECEDENTES POLICIALES
    INSTITUTO NACIONAL PENITENCIARIO: NO REGISTRA ANTECEDENTES PENALES
    SUNEDU: BACHILLER EN INGENIERIA DE SOFTWARE
    """
    cul_extractor = CULExtractor()
    cul_result = cul_extractor.extract_from_text(cul_text)
    assert cul_result["tiene_antecedentes_penales_policiales"] is False
    assert cul_result["bgc_status"] == "Aprobado"

    # 5. Radar Salarial Tech y Benchmarking Local (Propuesta P22 - Nivel 1)
    radar_svc = SalaryRadarService()
    salary_radar = radar_svc.evaluate_salary(
        perfil_puesto="Desarrollador Java",
        salario_pretendido=9000.0,
        seniority="Senior",
    )
    assert salary_radar.p25 == 7500.0
    assert salary_radar.p50 == 9500.0
    assert "P25 - P50" in salary_radar.posicion_mercado or "P50 - P75" in salary_radar.posicion_mercado

    # 6. Cheat Sheet Técnico Asistido para Screening Telefónico (Propuesta P5 - Nivel 1)
    cs_svc = CheatSheetService()
    cheat_sheet = cs_svc.generate_cheat_sheet(
        postulacion_id="pos-integration-1",
        perfil_puesto="Desarrollador Java Senior",
        cv_text=cand_cv_text,
    )
    assert len(cheat_sheet.preguntas) >= 3
    assert cheat_sheet.preguntas[0].concepto_clave is not None

    # 7. Generador de Ficha One-Pager para Clientes (Propuesta N2 - Nivel 1)
    one_pager_html = OnePagerBuilder.build_html(
        candidato_nombre="Carlos Alva Sánchez",
        dni_masked="4589****",
        perfil_puesto="Desarrollador Java Senior",
        cliente="BCP",
        anios_experiencia=6.0,
        distrito="Santiago de Surco",
        modalidad="Híbrido",
        skills=["Java 17", "Spring Boot", "Microservicios", "Kafka", "Docker"],
        resumen_tecnico="Especialista Java Senior con sólida experiencia en arquitectura bancaria.",
        disponibilidad="2 semanas",
        expectativa_salarial=9000.0,
        bgc_status=cul_result["bgc_status"],
        evaluador_nombre="Senior Technical Recruiter",
        dictamen_humano="Avanza a Entrevista Técnica Cliente",
        alumni_tcs=False,
        fit_score=fit_result.score_porcentaje,
    )
    assert "<!DOCTYPE html>" in one_pager_html
    assert "Carlos Alva Sánchez" in one_pager_html
    assert "TATA CONSULTANCY SERVICES" in one_pager_html
    assert "BCP" in one_pager_html
