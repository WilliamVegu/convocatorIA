"""Domain Value Objects for ATS Core MVP."""
from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TelefonoE164:
    """Canonical E.164 phone number representation for Peruvian numbers (+519XXXXXXXX)."""

    value: str

    def __post_init__(self):
        cleaned = re.sub(r"[\s\-\(\)\.]", "", self.value)
        if not cleaned:
            raise ValueError("El número telefónico no puede estar vacío.")

        # Normalize Peruvian numbers
        if cleaned.startswith("+51"):
            digits = cleaned[3:]
        elif cleaned.startswith("51") and len(cleaned) == 11:
            digits = cleaned[2:]
        elif cleaned.startswith("0") and len(cleaned) == 10:
            digits = cleaned[1:]
        else:
            digits = cleaned

        if not (len(digits) == 9 and digits.startswith("9") and digits.isdigit()):
            raise ValueError(
                f"Formato telefónico inválido '{self.value}'. Debe ser un número móvil peruano canónico E.164 (+519XXXXXXXX)."
            )

        object.__setattr__(self, "value", f"+51{digits}")

    @property
    def raw_digits(self) -> str:
        """Returns digits without + (519XXXXXXXX)."""
        return self.value.replace("+", "")

    def generate_whatsapp_url(self, message: Optional[str] = None) -> str:
        """Generate interactive WhatsApp Web / API URL with protocol greeting."""
        default_msg = (
            "Estimado(a) candidato(a), le saluda el equipo de Selección de Talento de TCS Perú. "
            "Nos comunicamos respecto a su postulación profesional."
        )
        msg = message if message is not None else default_msg
        encoded = urllib.parse.quote(msg)
        return f"https://wa.me/{self.raw_digits}?text={encoded}"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DocumentoIdentidad:
    """Identity document with validation for DNI, CE, Pasaporte."""

    tipo: str  # 'DNI', 'CE', 'Pasaporte'
    numero: str

    def __post_init__(self):
        tipo_clean = self.tipo.strip().upper()
        if tipo_clean not in {"DNI", "CE", "PASAPORTE"}:
            raise ValueError(f"Tipo de documento inválido '{self.tipo}'. Debe ser DNI, CE o Pasaporte.")

        numero_clean = self.numero.strip()
        if tipo_clean == "DNI":
            if not (len(numero_clean) == 8 and numero_clean.isdigit()):
                raise ValueError(
                    f"El DNI debe contener exactamente 8 dígitos numéricos, se recibió '{self.numero}'."
                )
        elif tipo_clean in {"CE", "PASAPORTE"}:
            if not (3 <= len(numero_clean) <= 20 and numero_clean.isalnum()):
                raise ValueError(
                    f"El número de {tipo_clean} debe tener entre 3 y 20 caracteres alfanuméricos."
                )

        object.__setattr__(self, "tipo", tipo_clean if tipo_clean != "PASAPORTE" else "Pasaporte")
        object.__setattr__(self, "numero", numero_clean)

    def __str__(self) -> str:
        return f"{self.tipo}:{self.numero}"


@dataclass(frozen=True)
class EmailCorporativo:
    """Corporate email address restricted to domain @tcs.com."""

    value: str

    def __post_init__(self):
        cleaned = self.value.strip().lower()
        email_regex = r"^[\w\.-]+@([\w\.-]+\.)+[a-zA-Z]{2,4}$"
        if not re.match(email_regex, cleaned):
            raise ValueError(f"Correo electrónico con sintaxis inválida: '{self.value}'.")
        if not cleaned.endswith("@tcs.com"):
            raise ValueError(
                f"Acceso restringido: El correo '{self.value}' no pertenece al dominio institucional '@tcs.com'."
            )
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PorcentajeVariacion:
    """Percentage variation for CTC vs budget calculations."""

    value: Optional[float]

    def __post_init__(self):
        if self.value is not None:
            object.__setattr__(self, "value", round(float(self.value), 2))

    @property
    def semaforo(self) -> str:
        if self.value is None:
            return "Pendiente_Presupuesto"
        if self.value <= 0.0:
            return "Dentro_Presupuesto"
        if self.value <= 10.0:
            return "Requiere_Aprobacion"
        return "Fuera_Banda"

    def __str__(self) -> str:
        if self.value is None:
            return "N/A"
        sign = "+" if self.value > 0 else ""
        return f"{sign}{self.value:.2f}%"


@dataclass(frozen=True)
class MonedaPEN:
    """Monetary amount in Peruvian Soles (PEN)."""

    monto: float

    def __post_init__(self):
        if self.monto < 0:
            raise ValueError(f"El monto monetario no puede ser negativo: {self.monto}")
        object.__setattr__(self, "monto", round(float(self.monto), 2))

    def __str__(self) -> str:
        return f"S/. {self.monto:,.2f}"
