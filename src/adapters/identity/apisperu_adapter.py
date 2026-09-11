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

    def _build_url(self, endpoint: str, identifier: str) -> str:
        """Construct canonical endpoint URL supporting various base URL formats."""
        base = self.base_url.rstrip("/")
        if base.endswith("/dni"):
            base = base[:-4]
        elif base.endswith("/ruc"):
            base = base[:-4]

        if not base.endswith("/api/v1"):
            if base.endswith("/api"):
                base = f"{base}/v1"
            elif not base.endswith("/v1"):
                base = f"{base}/api/v1"

        return f"{base}/{endpoint}/{identifier}"

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
                    "codigo_verificacion": "",
                    "codigo_verificacion_letra": "",
                },
            }

        # 2. Second order: APIsPERU endpoint
        if self.token:
            try:
                url = self._build_url("dni", cleaned_dni)
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                }
                params = {"token": self.token}
                resp = requests.get(url, headers=headers, params=params, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    # Check for ErrorResponse: {"success": false, "message": "..."}
                    if data.get("success") is False:
                        msg = data.get("message", "DNI no encontrado en RENIEC.")
                        logger.warning(f"APIsPERU DNI {cleaned_dni}: {msg}")
                        return {
                            "success": False,
                            "fuente_origen": "APISPERU_ERROR",
                            "mensaje": msg,
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
                                "codigo_verificacion": "",
                                "codigo_verificacion_letra": "",
                            },
                        }

                    nombres = (data.get("nombres") or data.get("nombre") or "").strip()
                    paterno = (data.get("apellidoPaterno") or data.get("apellido_paterno") or "").strip()
                    materno = (data.get("apellidoMaterno") or data.get("apellido_materno") or "").strip()

                    if not nombres and not paterno:
                        msg = data.get("message", "No se obtuvieron nombres válidos para el DNI.")
                        logger.warning(f"APIsPERU DNI {cleaned_dni}: {msg}")
                        return {
                            "success": False,
                            "fuente_origen": "APISPERU_NOT_FOUND",
                            "mensaje": msg,
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
                                "codigo_verificacion": "",
                                "codigo_verificacion_letra": "",
                            },
                        }

                    fecha_nac_str = data.get("fechaNacimiento") or data.get("fecha_nacimiento")
                    fecha_nac = None
                    if fecha_nac_str:
                        try:
                            fecha_nac = date.fromisoformat(str(fecha_nac_str))
                        except Exception:
                            pass

                    ubigeo = data.get("ubigeo")
                    distrito = data.get("distrito")
                    direccion = data.get("direccion")
                    cod_verifica = str(data.get("codVerifica") or data.get("cod_verifica") or "")
                    cod_verifica_letra = str(data.get("codVerificaLetra") or "")

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
                            "codigo_verificacion": cod_verifica,
                            "codigo_verificacion_letra": cod_verifica_letra,
                        },
                    }
                else:
                    logger.warning(f"APIsPERU HTTP {resp.status_code} para DNI {cleaned_dni}: {resp.text}")
            except Exception as e:
                logger.warning(f"Error consultando APIsPERU para DNI {cleaned_dni}: {e}")

        # 3. Fallback: Offline manual capture with pending regularization
        logger.warning(f"DNI {cleaned_dni} no disponible en cache ni API; degradando a Pendiente_Regularizacion.")
        return {
            "success": False,
            "fuente_origen": "CAPTURA_MANUAL_OFFLINE",
            "mensaje": "DNI no disponible en caché ni en APIsPERU. Ingrese los datos manualmente.",
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
                "codigo_verificacion": "",
                "codigo_verificacion_letra": "",
            },
        }

    def resolve_ruc(self, ruc: str) -> Dict[str, Any]:
        """Resolve company / taxpayer details via APIsPERU RUC endpoint (SUNAT)."""
        cleaned_ruc = ruc.strip()
        if not (len(cleaned_ruc) == 11 and cleaned_ruc.isdigit()):
            raise ValueError(f"RUC inválido '{ruc}'. Debe contener exactamente 11 dígitos numéricos.")

        if not self.token:
            return {
                "success": False,
                "mensaje": "Token de APIsPERU no configurado.",
                "fuente_origen": "ERROR_CONFIG",
                "datos": {},
            }

        try:
            url = self._build_url("ruc", cleaned_ruc)
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            params = {"token": self.token}
            resp = requests.get(url, headers=headers, params=params, timeout=5.0)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") is False:
                    msg = data.get("message", "RUC no encontrado en SUNAT.")
                    logger.warning(f"APIsPERU RUC {cleaned_ruc}: {msg}")
                    return {
                        "success": False,
                        "fuente_origen": "APISPERU_ERROR",
                        "mensaje": msg,
                        "datos": {},
                    }

                razon_social = (data.get("razonSocial") or data.get("razon_social") or "").strip()
                if not razon_social:
                    return {
                        "success": False,
                        "fuente_origen": "APISPERU_NOT_FOUND",
                        "mensaje": "RUC no encontrado en SUNAT.",
                        "datos": {},
                    }

                return {
                    "success": True,
                    "fuente_origen": "APISPERU_LIVE_SUNAT",
                    "datos": {
                        "ruc": cleaned_ruc,
                        "razon_social": razon_social,
                        "nombre_comercial": data.get("nombreComercial") or "",
                        "estado": data.get("estado") or "ACTIVO",
                        "condicion": data.get("condicion") or "HABIDO",
                        "direccion": data.get("direccion") or "",
                        "departamento": data.get("departamento") or "",
                        "provincia": data.get("provincia") or "",
                        "distrito": data.get("distrito") or "",
                        "ubigeo": data.get("ubigeo") or "",
                        "telefonos": data.get("telefonos") or [],
                        "capital": data.get("capital") or "",
                    },
                }
            else:
                logger.warning(f"APIsPERU RUC HTTP {resp.status_code}: {resp.text}")
                return {
                    "success": False,
                    "fuente_origen": "APISPERU_HTTP_ERROR",
                    "mensaje": f"Error del servidor APIsPERU (HTTP {resp.status_code}).",
                    "datos": {},
                }
        except Exception as e:
            logger.warning(f"Error consultando APIsPERU RUC {cleaned_ruc}: {e}")
            return {
                "success": False,
                "fuente_origen": "APISPERU_EXCEPTION",
                "mensaje": f"Fallo de conexión con APIsPERU: {e}",
                "datos": {},
            }

