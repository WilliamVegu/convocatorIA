"""Fit & Gap Analysis service comparing candidate CV against vacancy requirements."""
from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from src.ports.fit_gap_port import FitGapPort
from src.domain.entities import FitGapResult
from src.config import config
from src.logger import logger


# Common tech profile standard requirements mapping
STANDARD_ROLE_REQUIREMENTS = {
    "Desarrollador Java Senior": {
        "must_have": ["Java", "Spring Boot", "Microservicios", "SQL"],
        "nice_to_have": ["Kafka", "Docker", "Kubernetes", "AWS"],
    },
    "Data Engineer": {
        "must_have": ["Python", "SQL", "ETL", "Spark"],
        "nice_to_have": ["Airflow", "GCP", "AWS", "Databricks"],
    },
    "DevOps Specialist": {
        "must_have": ["Docker", "Kubernetes", "CI/CD", "Linux"],
        "nice_to_have": ["Terraform", "AWS", "Azure", "Ansible"],
    },
    "Full Stack Developer": {
        "must_have": ["JavaScript", "React", "Node.js", "SQL"],
        "nice_to_have": ["TypeScript", "Next.js", "Docker", "MongoDB"],
    },
    "Cloud Architect": {
        "must_have": ["AWS", "Arquitectura Cloud", "Seguridad Cloud", "Kubernetes"],
        "nice_to_have": ["Terraform", "FinOps", "GCP", "Azure"],
    },
    "QA Automation": {
        "must_have": ["Selenium", "Java", "Pruebas Automatizadas", "Git"],
        "nice_to_have": ["Cypress", "Appium", "Postman", "Jenkins"],
    },
    "Scrum Master": {
        "must_have": ["Scrum", "Agile", "Jira", "Facilitación"],
        "nice_to_have": ["Kanban", "SAFe", "Certificación PSM", "Confluence"],
    },
}


class FitGapService(FitGapPort):
    """Service evaluating technical compatibility, strengths, and critical gaps."""

    def compare_cv_vs_rgs(
        self,
        cv_text: str,
        cv_skills: List[Dict[str, Any]],
        perfil_puesto: str,
        must_have: Optional[List[str]] = None,
        nice_to_have: Optional[List[str]] = None,
    ) -> FitGapResult:
        """Evaluate technical match (0-100%) and produce explainable strengths and gaps."""
        # 1. Resolve requirements for the role
        defaults = STANDARD_ROLE_REQUIREMENTS.get(
            perfil_puesto,
            {
                "must_have": ["Experiencia técnica afín", "Bases de datos", "Git"],
                "nice_to_have": ["Metodologías ágiles", "Cloud"],
            },
        )
        req_must = must_have if must_have is not None else defaults["must_have"]
        req_nice = nice_to_have if nice_to_have is not None else defaults["nice_to_have"]

        # 2. Try LLM if API Key is configured
        if config.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model="gemini-3.8-flash",
                    google_api_key=config.GEMINI_API_KEY,
                )
                return self._compare_with_llm(llm, cv_text, perfil_puesto, req_must, req_nice)
            except Exception as e:
                logger.warning(f"Error evaluando FitGap con Gemini: {e}. Usando motor heurístico.")

        # 3. Fallback: Deterministic Heuristic Semantic Matching
        return self._compare_heuristically(cv_text, cv_skills, perfil_puesto, req_must, req_nice)

    def _compare_heuristically(
        self,
        cv_text: str,
        cv_skills: List[Dict[str, Any]],
        perfil_puesto: str,
        must_have: List[str],
        nice_to_have: List[str],
    ) -> FitGapResult:
        """Deterministic keyword & taxonomy scoring."""
        text_lower = cv_text.lower()
        skills_set = set()
        for s in cv_skills:
            if isinstance(s, dict) and s.get("nombre"):
                skills_set.add(s["nombre"].lower())
            elif isinstance(s, str):
                skills_set.add(s.lower())

        fortalezas: List[str] = []
        gaps: List[str] = []

        # Check Must-Have (70% total weight)
        must_matched = 0
        for m in must_have:
            m_clean = m.strip().lower()
            if m_clean in text_lower or any(m_clean in s for s in skills_set):
                must_matched += 1
                fortalezas.append(f"Cumple con requisito excluyente: '{m}'")
            else:
                gaps.append(f"No evidencia experiencia comprobable en '{m}'")

        # Check Nice-to-Have (30% total weight)
        nice_matched = 0
        for n in nice_to_have:
            n_clean = n.strip().lower()
            if n_clean in text_lower or any(n_clean in s for s in skills_set):
                nice_matched += 1
                fortalezas.append(f"Deseable complementario: '{n}'")
            else:
                gaps.append(f"Oportunidad de capacitación en '{n}'")

        must_pct = (must_matched / len(must_have)) if must_have else 1.0
        nice_pct = (nice_matched / len(nice_to_have)) if nice_to_have else 1.0

        score = round((must_pct * 70.0) + (nice_pct * 30.0), 1)
        score = max(5.0, min(100.0, score))

        if score >= 80.0:
            rec = "Perfil Altamente Recomendado para Screening Telefónico."
        elif score >= 60.0:
            rec = "Perfil Calificado con observaciones; validar vacíos en llamada."
        else:
            rec = "Descalce Técnico Relevante. Descartar o evaluar para otra vacante."

        return FitGapResult(
            score_porcentaje=score,
            fortalezas=fortalezas[:5],
            gaps_criticos=gaps[:5],
            recomendacion=rec,
        )

    def _compare_with_llm(
        self,
        llm: Any,
        cv_text: str,
        perfil_puesto: str,
        must_have: List[str],
        nice_to_have: List[str],
    ) -> FitGapResult:
        """Deep comparison using LLM structured output."""
        prompt = (
            f"Eres un arquitecto de selección técnica en TCS Perú para el puesto '{perfil_puesto}'.\n"
            f"Requisitos Must-Have: {', '.join(must_have)}\n"
            f"Requisitos Nice-to-Have: {', '.join(nice_to_have)}\n\n"
            "Compara el siguiente CV contra estos requisitos. "
            "IMPORTANTE (Principio V): No consideres atributos protegidos (edad, género, foto, domicilio).\n"
            "Devuelve ÚNICAMENTE un JSON estructurado con:\n"
            "{\n"
            '  "score_porcentaje": 85.0,\n'
            '  "fortalezas": ["Cumple con 4 años en Spring Boot", "Experiencia en microservicios bancarios"],\n'
            '  "gaps_criticos": ["No menciona Kafka", "Sin certificaciones cloud"],\n'
            '  "recomendacion": "Recomendado para entrevista"\n'
            "}\n\n"
            f"Texto del CV:\n{cv_text[:3500]}"
        )
        try:
            resp = llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            import json
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", str(content), re.DOTALL)
            raw_json = match.group(1) if match else content
            data = json.loads(raw_json)
            return FitGapResult(
                score_porcentaje=float(data.get("score_porcentaje", 75.0)),
                fortalezas=data.get("fortalezas", []),
                gaps_criticos=data.get("gaps_criticos", []),
                recomendacion=data.get("recomendacion", "Validar en screening"),
            )
        except Exception as e:
            logger.warning(f"Fallo en structured output LLM: {e}")
            return self._compare_heuristically(cv_text, [], perfil_puesto, must_have, nice_to_have)
