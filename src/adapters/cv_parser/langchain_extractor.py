"""LangChain multi-provider CV extractor with fallback to local heuristic engine."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, Any, Optional
import pypdf

from src.ports.cv_parser_port import CVParserPort
from src.adapters.cv_parser.heuristic_extractor import HeuristicCVExtractor
from src.config import config
from src.logger import logger


class LangChainCVExtractor(CVParserPort):
    """Multi-provider LLM extractor with Google Gemini, xAI Grok and offline fallback."""

    def __init__(self, fallback_extractor: Optional[CVParserPort] = None):
        self.fallback = fallback_extractor or HeuristicCVExtractor()

    def extract_from_pdf(self, file_content_or_path: bytes | str | Path) -> Dict[str, Any]:
        # Extract text first
        text = ""
        try:
            if isinstance(file_content_or_path, (str, Path)):
                reader = pypdf.PdfReader(str(file_content_or_path))
            else:
                reader = pypdf.PdfReader(io.BytesIO(file_content_or_path))

            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        except Exception as e:
            logger.warning(f"Error extrayendo texto del PDF con pypdf: {e}")

        if not text.strip():
            return self.fallback.extract_from_pdf(file_content_or_path)

        # Check API keys
        if config.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model="gemini-3.8-flash",
                    google_api_key=config.GEMINI_API_KEY,
                )
                logger.info("LangChain Gemini extractor invoked with gemini-3.8-flash.")
                return self._parse_with_llm(llm, text, "Google Gemini 3.8 Flash (IA)")
            except Exception as e:
                logger.warning(f"Fallo en LangChain Gemini, intentando Grok o Fallback: {e}")

        if config.GROK_API_KEY:
            try:
                from langchain_xai import ChatXAI
                llm = ChatXAI(
                    model="grok-2",
                    xai_api_key=config.GROK_API_KEY,
                    temperature=0.0,
                )
                logger.info("LangChain Grok extractor invoked.")
                return self._parse_with_llm(llm, text, "xAI Grok (IA)")
            except Exception as e:
                logger.warning(f"Fallo en LangChain Grok: {e}")

        # Fallback to local heuristic extractor
        logger.info("Usando extractor heurístico local 100% offline.")
        return self.fallback.extract_from_pdf(file_content_or_path)

    def _parse_with_llm(self, llm: Any, text: str, provider_tag: str) -> Dict[str, Any]:
        """Query LLM with strict privacy prompt preventing protected demographic attributes."""
        prompt = (
            "Eres un asistente de selección de personal técnico de TCS Perú. "
            "Extrae las competencias técnicas, años de experiencia total estimada y niveles de idiomas del siguiente CV. "
            "IMPORTANTE: Cumpliendo el Principio Constitucional V y la Ley N° 29733, está ESTRICTAMENTE PROHIBIDO "
            "extraer datos protegidos: no extraigas edad, fecha de nacimiento, género, estado civil, dirección domiciliaria ni foto. "
            "Retorna ÚNICAMENTE un JSON estructurado (sin texto introductorio ni explicaciones) con las siguientes claves:\n"
            "{\n"
            '  "resumen_profesional": "Breve resumen técnico del candidato",\n'
            '  "seniority_estimado": "Junior" | "Semi-Senior" | "Senior",\n'
            '  "anios_experiencia_total": 4.5,\n'
            '  "modalidad_preferida": "Híbrido",\n'
            '  "habilidades_tecnicas": [{"nombre": "Python", "categoria": "Backend"}],\n'
            '  "idiomas": [{"idioma": "Inglés", "nivel": "Intermedio"}]\n'
            "}\n\n"
            f"Texto del CV:\n{text[:4000]}"
        )
        try:
            response = llm.invoke(prompt)
            raw_content = response.content if hasattr(response, "content") else str(response)

            # Handle content when returned as list of dicts (e.g. [{'type': 'text', 'text': '...'}])
            if isinstance(raw_content, list):
                text_parts = []
                for part in raw_content:
                    if isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                    elif isinstance(part, str):
                        text_parts.append(part)
                content_str = "\n".join(text_parts)
            else:
                content_str = str(raw_content)

            import json, re
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content_str, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                # Try finding first { and last }
                start_idx = content_str.find("{")
                end_idx = content_str.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    parsed = json.loads(content_str[start_idx : end_idx + 1])
                else:
                    parsed = json.loads(content_str)

            parsed["motor_extraccion_usado"] = provider_tag
            return parsed
        except Exception as e:
            logger.warning(f"Error estructurando salida LLM: {e}; delegando a fallback heurístico.")
            return self.fallback.extract_from_text(text)
