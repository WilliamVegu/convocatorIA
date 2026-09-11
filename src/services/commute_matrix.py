"""Geographic commute distance matrix and travel alerts for Lima Metropolitan Area."""
from __future__ import annotations

from typing import Tuple, Optional

# Known critical commute pairs in Lima (>90 min one-way public transit)
CRITICAL_ZONES = {
    "CONO_SUR": {"VILLA MARIA DEL TRIUNFO", "VMT", "VILLA EL SALVADOR", "VES", "SAN JUAN DE MIRAFLORES", "SJM", "LURIN", "PACHACAMAC"},
    "CONO_NORTE": {"PUENTE PIEDRA", "CARABAYLLO", "COMAS", "ANCON", "SANTA ROSA", "VENTANILLA", "MI PERU", "LOS OLIVOS", "SAN MARTIN DE PORRES", "SMP", "INDEPENDENCIA"},
    "CONO_ESTE": {"SAN JUAN DE LURIGANCHO", "SJL", "CHACLACAYO", "CHOSICA", "LURIGANCHO", "CIENEGUILLA"},
}

NEAR_FINANCIAL_CENTERS = {
    "SAN ISIDRO", "MIRAFLORES", "SAN BORJA", "SANTIAGO DE SURCO", "SURCO",
    "SURQUILLO", "LINCE", "JESUS MARIA", "MAGDALENA DEL MAR", "PUEBLO LIBRE"
}


def normalize_district(name: str) -> str:
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", name.strip().upper())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def evaluate_commute(
    residence_district: Optional[str],
    client_or_workplace: str,
    modalidad: str = "Híbrido",
) -> Tuple[str, Optional[str]]:
    """
    Evaluate geographic travel feasibility.
    Returns: (dictamen_viabilidad, nota_alerta)
    dictamen_viabilidad: 'Viable_Cercano' | 'Viable_Con_Conmutacion' | 'Alerta_Distancia_Critica'
    """
    if modalidad == "Remoto":
        return ("Viable_Cercano", "Modalidad 100% Remota: no existe conmutación geográfica requerida.")

    if not residence_district:
        return ("Viable_Con_Conmutacion", "Distrito de residencia no especificado; conmutación no calculable.")

    dist_norm = normalize_district(residence_district)
    client_norm = normalize_district(client_or_workplace)

    # Specific client headquarters rules
    is_la_molina = any(k in client_norm for k in ["LA MOLINA", "BCP", "MELGAREJO"])
    is_san_isidro = any(k in client_norm for k in ["SAN ISIDRO", "TCS", "FALABELLA", "INTERBANK"])

    # High travel alert: Cono Sur or Cono Norte to La Molina
    if is_la_molina:
        if dist_norm in CRITICAL_ZONES["CONO_SUR"]:
            return (
                "Alerta_Distancia_Critica",
                f"Alerta Crítica: El candidato reside en {residence_district} y la sede de {client_or_workplace} se ubica en La Molina. Conmutación estimada >90-110 min por tramo.",
            )
        if dist_norm in CRITICAL_ZONES["CONO_NORTE"]:
            return (
                "Alerta_Distancia_Critica",
                f"Alerta Crítica: El candidato reside en {residence_district} y la sede de {client_or_workplace} se ubica en La Molina. Conmutación estimada >90-120 min por tramo.",
            )
        if dist_norm in CRITICAL_ZONES["CONO_ESTE"] and dist_norm not in {"SANTA ANITA", "ATE"}:
            return (
                "Viable_Con_Conmutacion",
                f"Conmutación Media-Alta: Residencia en {residence_district} hacia sede La Molina (~60-80 min).",
            )
        if dist_norm in {"LA MOLINA", "SANTIAGO DE SURCO", "SURCO", "SAN BORJA", "ATE", "SANTA ANITA"}:
            return ("Viable_Cercano", f"Excelente proximidad geográfica entre {residence_district} y sede cliente.")

    # High travel alert: Cono Norte extremo to San Isidro / Miraflores
    if is_san_isidro:
        if dist_norm in {"PUENTE PIEDRA", "CARABAYLLO", "ANCON", "VENTANILLA", "LURIN"}:
            return (
                "Alerta_Distancia_Critica",
                f"Alerta Crítica: Residencia en {residence_district} hacia San Isidro/Miraflores excede los 90 min de traslado habitual.",
            )
        if dist_norm in NEAR_FINANCIAL_CENTERS:
            return ("Viable_Cercano", f"Cercanía óptima (<30 min) entre {residence_district} y centro financiero.")

    # Default logic for generic districts
    if dist_norm in NEAR_FINANCIAL_CENTERS:
        return ("Viable_Cercano", "Proximidad geográfica favorable dentro del radio urbano central.")

    return (
        "Viable_Con_Conmutacion",
        f"Conmutación urbana estándar (~45-75 min) entre {residence_district} y sede laboral.",
    )
