"""Salary Radar and Tech Benchmarking service for Lima (Perú) IT market."""
from __future__ import annotations

from typing import Dict, Any, Tuple
from src.domain.entities import SalaryRadar


# Market salary benchmarks in Soles (PEN) for Lima IT talent (2026 calibrated)
# Tuple format: (P25, P50, P75)
SALARY_BENCHMARKS: Dict[str, Dict[str, Tuple[float, float, float]]] = {
    "Desarrollador Java": {
        "Junior": (3500.0, 4500.0, 5500.0),
        "Semi-Senior": (5500.0, 7000.0, 8500.0),
        "Senior": (7500.0, 9500.0, 12000.0),
        "Lead": (11500.0, 14000.0, 17500.0),
    },
    "Data Engineer": {
        "Junior": (3800.0, 4800.0, 6000.0),
        "Semi-Senior": (6000.0, 7500.0, 9500.0),
        "Senior": (8500.0, 11000.0, 13500.0),
        "Lead": (12500.0, 15500.0, 19000.0),
    },
    "DevOps Specialist": {
        "Junior": (4000.0, 5000.0, 6200.0),
        "Semi-Senior": (6500.0, 8000.0, 10000.0),
        "Senior": (9000.0, 11500.0, 14000.0),
        "Lead": (13000.0, 16000.0, 20000.0),
    },
    "Full Stack Developer": {
        "Junior": (3200.0, 4200.0, 5200.0),
        "Semi-Senior": (5200.0, 6800.0, 8200.0),
        "Senior": (7000.0, 8800.0, 11000.0),
        "Lead": (10500.0, 13000.0, 16000.0),
    },
    "Cloud Architect": {
        "Junior": (5000.0, 6500.0, 8000.0),
        "Semi-Senior": (8000.0, 10000.0, 12500.0),
        "Senior": (12000.0, 15000.0, 18500.0),
        "Lead": (16000.0, 20000.0, 25000.0),
    },
    "QA Automation": {
        "Junior": (3000.0, 4000.0, 5000.0),
        "Semi-Senior": (4800.0, 6200.0, 7500.0),
        "Senior": (6500.0, 8000.0, 10000.0),
        "Lead": (9500.0, 11500.0, 14000.0),
    },
    "Scrum Master": {
        "Junior": (3500.0, 4500.0, 5800.0),
        "Semi-Senior": (5500.0, 7000.0, 8800.0),
        "Senior": (7500.0, 9500.0, 12000.0),
        "Lead": (11000.0, 13500.0, 16500.0),
    },
}


class SalaryRadarService:
    """Calculates market positioning and percentiles P25, P50, P75 for tech roles."""

    def evaluate_salary(
        self,
        perfil_puesto: str,
        salario_pretendido: float,
        seniority: str = "Senior",
    ) -> SalaryRadar:
        """Evaluate candidate salary ask against Lima market percentiles."""
        # Find matching base role
        base_role = "Desarrollador Java"
        for r_name in SALARY_BENCHMARKS.keys():
            if r_name.lower() in perfil_puesto.lower():
                base_role = r_name
                break

        # Normalize seniority
        sen_clean = "Senior"
        if "lead" in seniority.lower() or "architect" in seniority.lower():
            sen_clean = "Lead"
        elif "semi" in seniority.lower() or "ssr" in seniority.lower() or "intermedio" in seniority.lower():
            sen_clean = "Semi-Senior"
        elif "junior" in seniority.lower() or "jr" in seniority.lower() or "trainee" in seniority.lower():
            sen_clean = "Junior"

        role_table = SALARY_BENCHMARKS.get(base_role, SALARY_BENCHMARKS["Desarrollador Java"])
        p25, p50, p75 = role_table.get(sen_clean, role_table["Senior"])

        # Determine market positioning
        if salario_pretendido < p25:
            pos = "Por debajo de mercado (Bajo percentil 25 - Atractivo en costo)"
        elif salario_pretendido <= p50:
            pos = "Rango Competitivo Bajo (P25 - P50 - Óptimo presupuestal)"
        elif salario_pretendido <= p75:
            pos = "Rango Competitivo Alto (P50 - P75 - Mediana de mercado)"
        else:
            pos = "Sobre percentil 75 (Banda alta - Requiere justificación técnica)"

        return SalaryRadar(
            rol=f"{base_role} ({sen_clean})",
            seniority=sen_clean,
            p25=p25,
            p50=p50,
            p75=p75,
            salario_candidato=salario_pretendido,
            posicion_mercado=pos,
        )
