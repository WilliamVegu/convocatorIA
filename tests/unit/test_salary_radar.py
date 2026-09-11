"""Unit tests for Salary Radar & Tech Benchmarking service (Lima 2026)."""
from src.services.salary_radar_service import SalaryRadarService


def test_salary_radar_below_p25():
    svc = SalaryRadarService()
    radar = svc.evaluate_salary("Desarrollador Java", 3000.0, "Junior")
    assert radar.p25 == 3500.0
    assert radar.p50 == 4500.0
    assert radar.p75 == 5500.0
    assert "Por debajo de mercado" in radar.posicion_mercado


def test_salary_radar_median_p50():
    svc = SalaryRadarService()
    radar = svc.evaluate_salary("Data Engineer", 7500.0, "Semi-Senior")
    assert radar.p25 == 6000.0
    assert radar.p50 == 7500.0
    assert radar.p75 == 9500.0
    assert "P25 - P50" in radar.posicion_mercado or "P50 - P75" in radar.posicion_mercado


def test_salary_radar_above_p75():
    svc = SalaryRadarService()
    radar = svc.evaluate_salary("Cloud Architect", 30000.0, "Lead")
    assert radar.p75 == 25000.0
    assert "Sobre percentil 75" in radar.posicion_mercado


def test_salary_radar_seniority_normalization():
    svc = SalaryRadarService()
    r_lead = svc.evaluate_salary("DevOps Specialist", 15000.0, "Technical Lead / Architect")
    assert r_lead.seniority == "Lead"

    r_jr = svc.evaluate_salary("DevOps Specialist", 4000.0, "Jr Engineer")
    assert r_jr.seniority == "Junior"
