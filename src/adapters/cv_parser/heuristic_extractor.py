"""Offline heuristic CV extractor using pypdf and technical dictionary matching."""
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Dict, Any, List
import pypdf

from src.ports.cv_parser_port import CVParserPort

# Dictionary of technical skills categorized
TECH_CATALOG = {
    "Python": "Backend",
    "Java": "Backend",
    "C#": "Backend",
    ".NET": "Backend",
    "Go": "Backend",
    "Node.js": "Backend",
    "FastAPI": "Backend",
    "Django": "Backend",
    "Spring Boot": "Backend",
    "PostgreSQL": "Database",
    "MySQL": "Database",
    "Oracle": "Database",
    "SQL Server": "Database",
    "MongoDB": "Database",
    "Redis": "Database",
    "React": "Frontend",
    "Angular": "Frontend",
    "Vue": "Frontend",
    "TypeScript": "Frontend",
    "JavaScript": "Frontend",
    "HTML/CSS": "Frontend",
    "AWS": "Cloud/DevOps",
    "Azure": "Cloud/DevOps",
    "GCP": "Cloud/DevOps",
    "Docker": "Cloud/DevOps",
    "Kubernetes": "Cloud/DevOps",
    "Terraform": "Cloud/DevOps",
    "Git": "Tools",
    "CI/CD": "Tools",
    "Linux": "Tools",
    "Kafka": "Messaging",
    "RabbitMQ": "Messaging",
}

LANGUAGE_PATTERNS = {
    "Inglés": [r"ingl[eé]s\s*(?:[:\-])?\s*(avanzado|intermedio|b[aá]sico|c2|c1|b2|b1|a2|a1|fluido|native)?", r"(?:advanced|intermediate|basic)\s+english"],
    "Portugués": [r"portugu[eé]s\s*(?:[:\-])?\s*(avanzado|intermedio|b[aá]sico|c2|c1|b2|b1|a2|a1|fluido)?", r"(?:advanced|intermediate|basic)\s+portuguese"],
    "Español": [r"español\s*(?:[:\-])?\s*(nativo|avanzado)?"],
}


class HeuristicCVExtractor(CVParserPort):
    """100% offline heuristic curriculum vitae parser."""

    def extract_from_pdf(self, file_content_or_path: bytes | str | Path) -> Dict[str, Any]:
        """Extract text from PDF using PyMuPDF (fitz) with fallback to pypdf, and parse."""
        text = ""
        # 1. Try PyMuPDF (fitz) first
        try:
            import pymupdf  # type: ignore
            if isinstance(file_content_or_path, (str, Path)):
                doc = pymupdf.open(str(file_content_or_path))
            else:
                doc = pymupdf.open(stream=file_content_or_path, filetype="pdf")
            for page in doc:
                t = page.get_text()
                if t:
                    text += t + "\n"
            doc.close()
        except Exception:
            text = ""

        # 2. Fallback to pypdf if PyMuPDF extracted nothing or failed
        if not text.strip():
            try:
                if isinstance(file_content_or_path, (str, Path)):
                    reader = pypdf.PdfReader(str(file_content_or_path))
                else:
                    reader = pypdf.PdfReader(io.BytesIO(file_content_or_path))

                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
            except Exception:
                pass

        return self.extract_from_text(text)

    def extract_from_text(self, text: str) -> Dict[str, Any]:
        """Parse raw text, extracting technical competencies and strictly omitting protected data."""
        # Clean text
        text_lower = text.lower()

        # 1. Identify technical skills
        found_skills: List[Dict[str, Any]] = []
        for skill, category in TECH_CATALOG.items():
            pattern = rf"\b{re.escape(skill.lower())}\b"
            if re.search(pattern, text_lower):
                found_skills.append({
                    "nombre": skill,
                    "categoria": category,
                    "anios_experiencia": None,
                })

        # 2. Estimate total years of experience
        years_found = []
        exp_matches = re.findall(r"(\d+)\s*(?:\+)?\s*(?:años|years|anios)\s*(?:de)?\s*(?:experiencia|exp)", text_lower)
        for m in exp_matches:
            try:
                y = float(m)
                if 0.5 <= y <= 40:
                    years_found.append(y)
            except Exception:
                pass

        if years_found:
            anios_experiencia = max(years_found)
        else:
            # Fallback estimation based on skill count
            anios_experiencia = min(10.0, max(1.0, len(found_skills) * 0.75))

        # Determine seniority
        if anios_experiencia >= 5.0:
            seniority = "Senior"
        elif anios_experiencia >= 2.5:
            seniority = "Semi-Senior"
        else:
            seniority = "Junior"

        # 3. Detect languages
        languages: List[Dict[str, str]] = []
        for lang, patterns in LANGUAGE_PATTERNS.items():
            for pat in patterns:
                m = re.search(pat, text_lower)
                if m:
                    level = "Intermedio"
                    if m.groups() and m.group(1):
                        lvl_text = m.group(1).lower()
                        if any(k in lvl_text for k in ["avanzado", "c2", "c1", "fluido", "advanced", "native", "nativo"]):
                            level = "Avanzado"
                        elif any(k in lvl_text for k in ["básico", "basico", "a1", "a2", "basic"]):
                            level = "Básico"
                    languages.append({"idioma": lang, "nivel": level})
                    break

        if not any(l["idioma"] == "Español" for l in languages):
            languages.append({"idioma": "Español", "nivel": "Nativo"})

        # Summary without protected attributes
        top_skills = [s["nombre"] for s in found_skills[:5]]
        resumen = f"Profesional {seniority} con experiencia en {', '.join(top_skills) if top_skills else 'Tecnologías de la Información'}."

        return {
            "resumen_profesional": resumen,
            "seniority_estimado": seniority,
            "anios_experiencia_total": round(anios_experiencia, 1),
            "modalidad_preferida": "Híbrido",
            "habilidades_tecnicas": found_skills,
            "idiomas": languages,
            "motor_extraccion_usado": "HEURISTICO_LOCAL_OFFLINE",
        }
