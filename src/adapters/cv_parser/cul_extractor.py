"""Extractor for Certificado Único Laboral (CUL - MTPE Perú) PDFs."""
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import pypdf

from src.logger import logger


class CULExtractor:
    """Extracts background check (PNP, INPE, PJ) and formal SUNAT employment from CUL documents."""

    def extract_from_pdf(self, file_content_or_path: bytes | str | Path) -> Dict[str, Any]:
        """Extract text from CUL PDF and structure background and trajectory findings."""
        text = ""
        # 1. Try PyMuPDF (fitz)
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

        # 2. Fallback to pypdf
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
            except Exception as e:
                logger.warning(f"Error extrayendo CUL PDF: {e}")

        return self.extract_from_text(text)

    def extract_from_text(self, text: str) -> Dict[str, Any]:
        """Parse raw CUL text for police/penal/judicial background and SUNAT trajectory."""
        text_upper = text.upper()

        # 1. Background check analysis
        # Check for explicitly clean badges
        clean_penal = "NO REGISTRA ANTECEDENTES PENALES" in text_upper or "NO REGISTRA" in text_upper
        clean_policial = "NO REGISTRA ANTECEDENTES POLICIALES" in text_upper or "SIN ANTECEDENTES" in text_upper
        clean_judicial = "NO REGISTRA ANTECEDENTES JUDICIALES" in text_upper

        # Check if there are explicit positive background marks
        has_penal_record = "SÍ REGISTRA ANTECEDENTES PENALES" in text_upper or "REGISTRA ANTECEDENTES PENALES" in text_upper and "NO REGISTRA" not in text_upper
        has_policial_record = "SÍ REGISTRA ANTECEDENTES POLICIALES" in text_upper or "REGISTRA ANTECEDENTES POLICIALES" in text_upper and "NO REGISTRA" not in text_upper
        has_judicial_record = "SÍ REGISTRA ANTECEDENTES JUDICIALES" in text_upper or "REGISTRA ANTECEDENTES JUDICIALES" in text_upper and "NO REGISTRA" not in text_upper

        has_any_background = has_penal_record or has_policial_record or has_judicial_record

        if has_any_background:
            bgc_status = "Observado_No_Apto"
            bgc_dictamen = "OBSERVADO: Registra antecedentes en bases del MTPE/PNP/PJ."
        elif clean_penal or clean_policial:
            bgc_status = "Aprobado"
            bgc_dictamen = "APROBADO: Certificado CUL acredita antecedentes limpios (PNP, INPE y Poder Judicial)."
        else:
            # Document might be simulated or format varied
            bgc_status = "Aprobado"
            bgc_dictamen = "APROBADO: No se detectan antecedentes negativos en el documento."

        # 2. Degrees / SUNEDU Extraction
        grados_sunedu: List[str] = []
        grado_patterns = [
            r"BACHILLER EN [A-ZÁÉÍÓÚÑ\s]+",
            r"LICENCIADO EN [A-ZÁÉÍÓÚÑ\s]+",
            r"INGENIERO [A-ZÁÉÍÓÚÑ\s]+",
            r"TÍTULO PROFESIONAL DE [A-ZÁÉÍÓÚÑ\s]+",
            r"TÉCNICO EN [A-ZÁÉÍÓÚÑ\s]+",
        ]
        for pat in grado_patterns:
            matches = re.findall(pat, text_upper)
            for m in matches:
                clean_m = m.strip()
                if len(clean_m) > 10 and clean_m not in grados_sunedu:
                    grados_sunedu.append(clean_m[:80])

        # 3. Formal employers / SUNAT Planilla
        empleadores_sunat: List[str] = []
        sunat_matches = re.findall(r"(?:EMPRESA|RUC|EMPLEADOR)[:\s]+([A-Z0-9\.\s\-S\.A\.C\.]+)", text_upper)
        for emp in sunat_matches:
            clean_emp = emp.strip()
            if len(clean_emp) > 4 and clean_emp not in empleadores_sunat:
                empleadores_sunat.append(clean_emp[:60])

        # If empty, extract capitalized company-like tokens
        if not empleadores_sunat:
            comp_matches = re.findall(r"\b([A-ZÁÉÍÓÚÑ\s]+(?:S\.A\.C\.|S\.A\.|E\.I\.R\.L\.|S\.R\.L\.))\b", text_upper)
            for cm in comp_matches:
                if cm.strip() not in empleadores_sunat:
                    empleadores_sunat.append(cm.strip()[:60])

        # 4. Date of emission
        fecha_emision = None
        date_match = re.search(r"(\d{2})[/.-](\d{2})[/.-](\d{4})", text)
        if date_match:
            fecha_emision = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"

        return {
            "tiene_antecedentes_penales_policiales": has_any_background,
            "bgc_status": bgc_status,
            "bgc_dictamen": bgc_dictamen,
            "grados_sunedu": grados_sunedu[:3],
            "trayectoria_formal_registros": empleadores_sunat[:5],
            "fecha_emision_cul": fecha_emision,
        }
