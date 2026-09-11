"""Service for transforming messy unstructured requirements (RGS) into standardized Job Descriptions."""
from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from src.ports.rgs_port import RGSPort
from src.domain.entities import RGSNormalizado
from src.config import config
from src.logger import logger


class RGSNormalizerService(RGSPort):
    """Normalizes raw emails or Teams messages into parameterized JDs with boolean search syntax."""

    def normalize_raw_text(self, raw_text: str, cliente_sugerido: str = "BCP") -> RGSNormalizado:
        """Parse raw text, extracting requirements, seniority, salary and boolean strings."""
        if config.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model="gemini-3.8-flash",
                    google_api_key=config.GEMINI_API_KEY,
                )
                return self._normalize_with_llm(llm, raw_text, cliente_sugerido)
            except Exception as e:
                logger.warning(f"Error normalizando RGS con LLM: {e}. Usando parser determinístico.")

        return self._normalize_heuristically(raw_text, cliente_sugerido)

    def _normalize_heuristically(self, raw_text: str, cliente_sugerido: str) -> RGSNormalizado:
        """Deterministic regex extraction of roles, stack, and boolean strings."""
        text_lower = raw_text.lower()

        # 1. Detect role title
        role = "Desarrollador de Software"
        for r in [
            "Desarrollador Java",
            "Data Engineer",
            "DevOps Specialist",
            "Full Stack Developer",
            "Cloud Architect",
            "QA Automation",
            "Scrum Master",
            "Frontend Developer",
            "Backend Developer",
        ]:
            if r.lower() in text_lower or (r.split()[0].lower() in text_lower and r.split()[-1].lower() in text_lower):
                role = r
                break

        # 2. Detect seniority
        seniority = "Senior"
        if "lead" in text_lower or "architect" in text_lower:
            seniority = "Lead / Architect"
        elif "junior" in text_lower or "jr" in text_lower:
            seniority = "Junior (1-2 años)"
        elif "semi" in text_lower or "ssr" in text_lower:
            seniority = "Semi-Senior (2-4 años)"
        else:
            exp_match = re.search(r"(\d+)\s*(?:\+)?\s*años", text_lower)
            if exp_match:
                y = int(exp_match.group(1))
                if y >= 5:
                    seniority = f"Senior ({y}+ años)"
                elif y >= 3:
                    seniority = f"Semi-Senior ({y}+ años)"
                else:
                    seniority = f"Junior ({y}+ años)"

        # 3. Detect client
        cliente = cliente_sugerido
        for c in ["BCP", "BBVA", "Interbank", "Entel", "Falabella", "Rimac", "Scotiabank"]:
            if c.lower() in text_lower:
                cliente = c
                break

        # 4. Detect salary
        salario_str = "A convenir / Según presupuesto"
        sal_match = re.search(r"(?:sueldo|salario|presupuesto|tarifa|max|monto)[:\s]*(?:s/\.?)?\s*(\d{1,2}[\.,]?\d{3})", text_lower)
        if sal_match:
            val = sal_match.group(1).replace(",", "").replace(".", "")
            salario_str = f"Hasta S/. {float(val):,.2f} Bruto"

        # 5. Extract Must-Have & Nice-to-Have
        tech_keywords = [
            "Java", "Spring Boot", "Python", "SQL", "Kafka", "Oracle", "PostgreSQL",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "React", "Node.js", "TypeScript",
            "Angular", "Terraform", "CI/CD", "Linux", "Microservicios", "Selenium"
        ]

        found_tech = []
        for t in tech_keywords:
            if re.search(rf"\b{re.escape(t.lower())}\b", text_lower):
                found_tech.append(t)

        must_have = found_tech[:4] if found_tech else ["Experiencia en desarrollo de software", "Bases de datos relacionales"]
        nice_to_have = found_tech[4:8] if len(found_tech) > 4 else ["Metodologías ágiles", "Cloud básico"]

        # 6. Build Boolean search string for LinkedIn Recruiter / Hiring Assistant
        bool_parts = []
        if must_have:
            # Group top 2 with OR if similar, otherwise AND
            bool_terms = [f'"{m}"' if " " in m else m for m in must_have[:3]]
            bool_parts.append(" AND ".join(bool_terms))
        bool_parts.append('(Lima OR Perú OR "Remote")')
        cadena_booleana = " AND ".join(bool_parts)

        # 7. Modality
        modalidad = "Híbrido"
        if "remoto" in text_lower or "100% remoto" in text_lower:
            modalidad = "Remoto"
        elif "presencial" in text_lower:
            modalidad = "Presencial"

        import uuid
        rgs_id = f"RGS-{cliente[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

        return RGSNormalizado(
            rgs_id=rgs_id,
            titulo_puesto=f"{role} {seniority}",
            cliente=cliente,
            seniority=seniority,
            banda_salarial_pen=salario_str,
            must_have=must_have,
            nice_to_have=nice_to_have,
            cadena_booleana_linkedin=cadena_booleana,
            modalidad_sugerida=modalidad,
        )

    def _normalize_with_llm(self, llm: Any, raw_text: str, cliente_sugerido: str) -> RGSNormalizado:
        """Query LLM to parse messy job request."""
        prompt = (
            "Eres un Senior Recruitment Operations Lead en TCS Perú.\n"
            f"Analiza el siguiente texto informal de solicitud de personal (cliente sugerido: {cliente_sugerido}).\n"
            "Estructura el requerimiento en un Job Description parametrizado y genera la cadena booleana para LinkedIn Recruiter.\n"
            "Devuelve ÚNICAMENTE un JSON con:\n"
            "{\n"
            '  "titulo_puesto": "Desarrollador Java Senior",\n'
            '  "cliente": "BCP",\n'
            '  "seniority": "Senior (5+ años)",\n'
            '  "banda_salarial_pen": "S/. 8,500.00 Bruto",\n'
            '  "must_have": ["Java 17", "Spring Boot", "Kafka"],\n'
            '  "nice_to_have": ["AWS", "Docker"],\n'
            '  "modalidad_sugerida": "Híbrido",\n'
            '  "cadena_booleana_linkedin": "(Java OR \\"Spring Boot\\") AND Kafka AND (Lima OR Perú)"\n'
            "}\n\n"
            f"Texto del Requerimiento:\n{raw_text[:3000]}"
        )
        try:
            resp = llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            import json
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", str(content), re.DOTALL)
            raw = match.group(1) if match else content
            data = json.loads(raw)
            import uuid
            rgs_id = f"RGS-{data.get('cliente', cliente_sugerido)[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
            return RGSNormalizado(
                rgs_id=rgs_id,
                titulo_puesto=data.get("titulo_puesto", "Perfil Técnico"),
                cliente=data.get("cliente", cliente_sugerido),
                seniority=data.get("seniority", "Senior"),
                banda_salarial_pen=data.get("banda_salarial_pen", "A convenir"),
                must_have=data.get("must_have", []),
                nice_to_have=data.get("nice_to_have", []),
                cadena_booleana_linkedin=data.get("cadena_booleana_linkedin", ""),
                modalidad_sugerida=data.get("modalidad_sugerida", "Híbrido"),
            )
        except Exception as e:
            logger.warning(f"Error parseando con LLM: {e}")
            return self._normalize_heuristically(raw_text, cliente_sugerido)
