"""Unit tests for Fit & Gap Analysis service."""
from unittest.mock import patch
from src.services.fit_gap_service import FitGapService


@patch("src.services.fit_gap_service.config.GEMINI_API_KEY", "")
def test_fit_gap_deterministic_perfect_match():
    svc = FitGapService()
    cv_text = "Ingeniero de Software con amplia experiencia en Java 17, Spring Boot, Microservicios, SQL y Kafka, Docker, Kubernetes y AWS."
    cv_skills = [{"nombre": "Java"}, {"nombre": "Spring Boot"}, {"nombre": "SQL"}, {"nombre": "AWS"}]

    res = svc.compare_cv_vs_rgs(
        cv_text=cv_text,
        cv_skills=cv_skills,
        perfil_puesto="Desarrollador Java Senior",
    )

    assert res.score_porcentaje >= 80.0
    assert len(res.fortalezas) > 0
    assert "Altamente Recomendado" in res.recomendacion


@patch("src.services.fit_gap_service.config.GEMINI_API_KEY", "")
def test_fit_gap_deterministic_low_match():
    svc = FitGapService()
    cv_text = "Diseñador gráfico y community manager con manejo de Photoshop, Illustrator y Canva."
    cv_skills = [{"nombre": "Photoshop"}, {"nombre": "Illustrator"}]

    res = svc.compare_cv_vs_rgs(
        cv_text=cv_text,
        cv_skills=cv_skills,
        perfil_puesto="Desarrollador Java Senior",
    )

    assert res.score_porcentaje < 50.0
    assert len(res.gaps_criticos) > 0
    assert "Descalce Técnico" in res.recomendacion


@patch("src.services.fit_gap_service.config.GEMINI_API_KEY", "")
def test_fit_gap_custom_requirements():
    svc = FitGapService()
    cv_text = "Especialista en Python y FastAPI con PostgreSQL."
    cv_skills = [{"nombre": "Python"}, {"nombre": "PostgreSQL"}]

    res = svc.compare_cv_vs_rgs(
        cv_text=cv_text,
        cv_skills=cv_skills,
        perfil_puesto="Backend Developer",
        must_have=["Python", "FastAPI"],
        nice_to_have=["PostgreSQL", "Redis"],
    )

    # 100% must have (70 pts) + 50% nice to have (15 pts) = 85 pts
    assert res.score_porcentaje == 85.0
    assert any("Python" in f for f in res.fortalezas)
    assert any("Redis" in g for g in res.gaps_criticos)
