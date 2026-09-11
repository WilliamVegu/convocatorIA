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
                    model="gemini-2.5-flash",
                    google_api_key=config.GEMINI_API_KEY,
                    temperature=0.0,
                )
                logger.info("LangChain Gemini extractor invoked.")
                # We can perform structured extraction or fallback
                return self._parse_with_llm(llm, text, "GEMINI_LANGCHAIN")
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
                return self._parse_with_llm(llm, text, "GROK_LANGCHAIN")
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
            "Retorna un JSON estructurado con: resumen_profesional, seniority_estimado (Junior, Semi-Senior, Senior), "
            "anios_experiencia_total (número float), modalidad_preferida (Remoto, Presencial, Híbrido), "
            "habilidades_tecnicas (lista de objetos con nombre, categoria), idiomas (lista de objetos con idioma, nivel).\n\n"
            f"Texto del CV:\n{text[:4000]}"
        )
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            # Parse json or fallback
            import json, re
            json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                parsed = json.loads(content)
            parsed["motor_extraccion_usado"] = provider_tag
            return parsed
        except Exception as e:
            logger.warning(f"Error estructurando salida LLM: {e}; delegando a fallback heurístico.")
            return self.fallback.extract_from_text(text)
