"""Unit tests for RGS Normalizer Service (Propuesta P11)."""
from unittest.mock import patch
from src.services.rgs_normalizer_service import RGSNormalizerService


@patch("src.services.rgs_normalizer_service.config.GEMINI_API_KEY", "")
def test_rgs_normalizer_heuristic_java_bcp():
    svc = RGSNormalizerService()
    raw_email = """
    Hola equipo TCS,
    Necesitamos con urgencia para BCP un Desarrollador Java Senior con 5+ años de experiencia.
    Excluyente: Java 17, Spring Boot, Microservicios y Kafka.
    Deseable: Docker, Kubernetes, AWS.
    Modalidad híbrida en La Molina. Presupuesto max: 12000 soles.
    """
    res = svc.normalize_raw_text(raw_email, cliente_sugerido="BCP")

    assert "Desarrollador Java" in res.titulo_puesto
    assert "Senior" in res.seniority
    assert res.cliente == "BCP"
    assert "Híbrido" in res.modalidad
    assert any("Java" in m for m in res.must_have)
    assert any("Spring Boot" in m for m in res.must_have)
    assert "Lima" in res.cadena_booleana
    assert "AND" in res.cadena_booleana


@patch("src.services.rgs_normalizer_service.config.GEMINI_API_KEY", "")
def test_rgs_normalizer_heuristic_data_engineer():
    svc = RGSNormalizerService()
    raw_msg = """
    Requerimiento Interbank: Data Engineer 100% remoto.
    Python, SQL, Spark. Sueldo 9000.
    """
    res = svc.normalize_raw_text(raw_msg, cliente_sugerido="Interbank")

    assert "Data Engineer" in res.titulo_puesto
    assert res.cliente == "Interbank"
    assert res.modalidad == "Remoto"
    assert any("Python" in m for m in res.must_have)
