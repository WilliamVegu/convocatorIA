"""Unit tests for offline heuristic CV extractor."""
import pytest
from src.adapters.cv_parser.heuristic_extractor import HeuristicCVExtractor


def test_heuristic_extractor_detects_skills():
    text = """
    EXPERIENCIA PROFESIONAL
    Senior Software Engineer con 6 años de experiencia en desarrollo Backend.
    Habilidades: Python, PostgreSQL, Docker, AWS, FastAPI, Git, Redis.
    Educación: Ingeniero de Sistemas - UNI (2019).
    Idiomas: Inglés avanzado, Portugués básico.
    """
    extractor = HeuristicCVExtractor()
    result = extractor.extract_from_text(text)

    skills = [s["nombre"] for s in result["habilidades_tecnicas"]]
    assert "Python" in skills
    assert "PostgreSQL" in skills
    assert "Docker" in skills
    assert "AWS" in skills
    assert result["anios_experiencia_total"] >= 5.0

    idiomas = {i["idioma"]: i["nivel"] for i in result["idiomas"]}
    assert "Inglés" in idiomas
    assert idiomas["Inglés"] in {"Avanzado", "Intermedio", "Básico"}


def test_heuristic_extractor_censors_protected_attributes():
    text = """
    Datos Personales:
    Edad: 29 años, Género: Femenino, Estado Civil: Soltera.
    Dirección: Calle Los Álamos 123 Dpto 402, Urb. Las Flores.
    Teléfono: 989322088.
    Experiencia: Desarrollador Java Backend (3 años). Habilidades: Spring Boot, Oracle, Kafka.
    """
    extractor = HeuristicCVExtractor()
    result = extractor.extract_from_text(text)

    # Protected attributes must NOT be returned in extraction result
    assert "edad" not in result
    assert "genero" not in result
    assert "estado_civil" not in result
    assert "direccion_exacta" not in result
    assert "foto" not in result
    # Technical skills extracted
    skills = [s["nombre"] for s in result["habilidades_tecnicas"]]
    assert "Java" in skills
