"""Adapter for Peruvian DNI resolution via local cache and APIsPERU."""
from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime, date, timezone
import requests

from src.ports.dni_port import DNIPort
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.config import config
from src.logger import logger


class APIsPeruDNIAdapter(DNIPort):
    """Adapter implementing identity resolution with offline-first local cache."""

    def __init__(self, candidato_repo: CandidatoRepository):
        self.repo = candidato_repo
        self.base_url = config.APISPERU_BASE_URL.rstrip("/")
        self.token = config.APISPERU_TOKEN

    def resolve_dni(self, dni: str) -> Dict[str, Any]:
        cleaned_dni = dni.strip()
        if not (len(cleaned_dni) == 8 and cleaned_dni.isdigit()):
            raise ValueError(f"DNI inválido '{dni}'. Debe contener exactamente 8 dígitos numéricos.")

        # 1. First order: Local cache (<5ms)
        cached = self.repo.get_cached_dni(cleaned_dni)
        if cached:
            logger.info(f"DNI {cleaned_dni} resuelto desde cache local.")
            return {
                "success": True,
                "fuente_origen": "CACHE_LOCAL",
                "estado_identidad": "Validado_Oficialmente",
                "regularizacion_pendiente": False,
                "datos": {
                    "dni": cached.dni,
                    "nombres": cached.nombres,
                    "apellido_paterno": cached.apellido_paterno,
                    "apellido_materno": cached.apellido_materno or "",
                    "nombres_completos": f"{cached.nombres} {cached.apellido_paterno} {cached.apellido_materno or ''}".strip(),
                    "fecha_nacimiento": cached.fecha_nacimiento,
                    "ubigeo": cached.ubigeo,
                    "distrito": cached.distrito,
                    "direccion": cached.direccion,
                },
            }

        # 2. Second order: APIsPERU endpoint
        if self.token:
            try:
                url = f"{self.base_url}/{cleaned_dni}"
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                }
                resp = requests.get(url, headers=headers, timeout=4.0)
                if resp.status_code == 200:
                    data = resp.json()
                    nombres = data.get("nombres", "").strip()
                    paterno = data.get("apellidoPaterno", "").strip()
                    materno = data.get("apellidoMaterno", "").strip()
                    fecha_nac_str = data.get("fechaNacimiento")
                    fecha_nac = None
                    if fecha_nac_str:
                        try:
                            fecha_nac = date.fromisoformat(fecha_nac_str)
                        except Exception:
                            pass

                    ubigeo = data.get("ubigeo")
                    distrito = data.get("distrito")
                    direccion = data.get("direccion")

                    # Persist to local cache
                    self.repo.set_cached_dni(
                        dni=cleaned_dni,
                        nombres=nombres,
                        apellido_paterno=paterno,
                        apellido_materno=materno,
                        fecha_nacimiento=fecha_nac,
                        ubigeo=ubigeo,
                        distrito=distrito,
                        direccion=direccion,
                    )

                    logger.info(f"DNI {cleaned_dni} validado oficialmente via APIsPERU y almacenado en cache.")
                    return {
                        "success": True,
                        "fuente_origen": "APISPERU_LIVE",
                        "estado_identidad": "Validado_Oficialmente",
                        "regularizacion_pendiente": False,
                        "datos": {
                            "dni": cleaned_dni,
                            "nombres": nombres,
                            "apellido_paterno": paterno,
                            "apellido_materno": materno,
                            "nombres_completos": f"{nombres} {paterno} {materno}".strip(),
                            "fecha_nacimiento": fecha_nac,
                            "ubigeo": ubigeo,
                            "distrito": distrito,
                            "direccion": direccion,
                        },
                    }
            except Exception as e:
                logger.warning(f"Error consultando APIsPERU para DNI {cleaned_dni}: {e}")

        # 3. Fallback: Offline manual capture with pending regularization
        logger.warning(f"DNI {cleaned_dni} no disponible en cache ni API; degradando a Pendiente_Regularizacion.")
        return {
            "success": False,
            "fuente_origen": "CAPTURA_MANUAL_OFFLINE",
            "estado_identidad": "Pendiente_Regularizacion",
            "regularizacion_pendiente": True,
            "datos": {
                "dni": cleaned_dni,
                "nombres": "",
                "apellido_paterno": "",
                "apellido_materno": "",
                "nombres_completos": "",
                "fecha_nacimiento": None,
                "ubigeo": None,
                "distrito": None,
                "direccion": None,
            },
        }
