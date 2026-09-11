"""Excel and CSV validator and semantic alias parser for Adecco payroll spreadsheets."""
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import openpyxl

from src.ports.adecco_port import AdeccoPort
from src.ports.contracts import ADECCO_COLUMN_ALIASES


def normalize_header(header: Any) -> str:
    if header is None:
        return ""
    h = str(header).strip().lower()
    # Remove accents
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", h)
    clean = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9_\s/]", "", clean).strip()


class ExcelAdeccoValidator(AdeccoPort):
    """Parses and normalizes external supplier spreadsheets with header alias resilience."""

    def parse_spreadsheet(
        self,
        file_content_or_path: bytes | str | Path,
        filename: str = "planilla_adecco.xlsx",
    ) -> Dict[str, Any]:
        """Read spreadsheet and map columns into canonical fields."""
        # Load into pandas DataFrame
        if isinstance(file_content_or_path, (str, Path)):
            p = Path(file_content_or_path)
            if p.suffix.lower() in [".csv", ".txt"]:
                df = pd.read_csv(p, dtype=str)
            else:
                df = pd.read_excel(p, dtype=str)
        else:
            b = file_content_or_path
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(io.BytesIO(b), dtype=str)
            else:
                df = pd.read_excel(io.BytesIO(b), dtype=str)

        # Drop entirely empty rows and columns
        df = df.dropna(how="all").dropna(axis=1, how="all")

        # Map headers
        column_map: Dict[str, str] = {}
        for col in df.columns:
            norm_col = normalize_header(col)
            # Find which canonical concept matches: 1. Try exact matches first
            matched_canonical = None
            for canonical, alias_list in ADECCO_COLUMN_ALIASES.items():
                if canonical in column_map.values():
                    continue
                for alias in alias_list:
                    norm_alias = normalize_header(alias)
                    if norm_alias == norm_col:
                        matched_canonical = canonical
                        break
                if matched_canonical:
                    break

            # 2. If no exact match, try substring match (only for aliases >= 3 chars or word boundaries)
            if not matched_canonical:
                for canonical, alias_list in ADECCO_COLUMN_ALIASES.items():
                    if canonical in column_map.values():
                        continue
                    for alias in alias_list:
                        norm_alias = normalize_header(alias)
                        if len(norm_alias) >= 3 and (norm_alias in norm_col or norm_col in norm_alias):
                            matched_canonical = canonical
                            break
                    if matched_canonical:
                        break

            if matched_canonical and matched_canonical not in column_map.values():
                column_map[col] = matched_canonical

        parsed_rows: List[Dict[str, Any]] = []
        for idx, row in df.iterrows():
            # Skip rows where all values are null or whitespace
            if row.isna().all():
                continue

            row_data: Dict[str, Any] = {
                "fila_original_index": int(idx) + 2,  # 1-based, account for header row
                "documento_raw": None,
                "nombres_raw": None,
                "telefono_raw": None,
                "perfil_raw": None,
                "email_raw": None,
                "salario_raw": None,
            }

            for original_col, canonical in column_map.items():
                val = row.get(original_col)
                if pd.notna(val):
                    val_str = str(val).strip()
                    # Remove trailing .0 from Excel integer conversions if any
                    if val_str.endswith(".0") and len(val_str) > 2:
                        val_str = val_str[:-2]
                    row_data[f"{canonical}_raw"] = val_str

            # Only append if at least document or name or phone exists
            if row_data["documento_raw"] or row_data["nombres_raw"] or row_data["telefono_raw"]:
                parsed_rows.append(row_data)

        return {
            "filename": filename,
            "total_rows_parsed": len(parsed_rows),
            "column_mapping": column_map,
            "rows": parsed_rows,
        }
