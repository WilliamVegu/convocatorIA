"""Pure financial CTC calculation service with Factor 1.56 and mathematical zero-division guards."""
from __future__ import annotations

from typing import Optional, Dict, Any
from src.ports.ctc_port import CTCPort

SALARIO_MINIMO_VITAL_PEN = 1025.0
TOPE_SALARIAL_ESTANDAR_PEN = 35000.0
NET_TO_GROSS_RETENTION = 0.79


class CTCCalculatorService(CTCPort):
    """Calculates Costo Empresa (CTC) under Peruvian Labor Regime D.L. 728."""

    def calculate(
        self,
        tipo_expectativa: str,
        monto_declarado: float,
        ctc_presupuestado: Optional[float] = None,
        factor_ctc: float = 1.56,
    ) -> Dict[str, Any]:
        tipo = tipo_expectativa.strip().capitalize()
        if tipo not in {"Bruto", "Neto"}:
            raise ValueError(f"Tipo de expectativa inválido: '{tipo_expectativa}'. Debe ser 'Bruto' o 'Neto'.")

        if monto_declarado <= 0:
            raise ValueError(f"El monto declarado debe ser un valor positivo, se recibió {monto_declarado}.")

        # 1. Convert Net to Gross if applicable
        if tipo == "Neto":
            salario_bruto = round(monto_declarado / NET_TO_GROSS_RETENTION, 2)
        else:
            salario_bruto = round(float(monto_declarado), 2)

        # 2. Multiply by CTC factor
        ctc_solicitado = round(salario_bruto * factor_ctc, 2)

        # 3. Guards against zero division and null budget
        variacion_porcentual: Optional[float] = None
        semaforo_presupuestal: str = "Pendiente_Presupuesto"
        requiere_aprobacion: bool = False

        if ctc_presupuestado is not None and ctc_presupuestado > 0:
            variacion = ((ctc_solicitado - ctc_presupuestado) / ctc_presupuestado) * 100.0
            variacion_porcentual = round(variacion, 2 if abs(variacion) < 10 else 1)

            if variacion_porcentual <= 0.0:
                semaforo_presupuestal = "Dentro_Presupuesto"
                requiere_aprobacion = False
            elif variacion_porcentual <= 10.0:
                semaforo_presupuestal = "Requiere_Aprobacion"
                requiere_aprobacion = True
            else:
                semaforo_presupuestal = "Fuera_Banda"
                requiere_aprobacion = True

        # 4. Atypical salary warnings
        advertencia: Optional[str] = None
        if salario_bruto < SALARIO_MINIMO_VITAL_PEN:
            advertencia = f"Advertencia: El salario bruto mensual proyectado (S/. {salario_bruto:,.2f}) es inferior al Salario Mínimo Vital vigente (S/. {SALARIO_MINIMO_VITAL_PEN:,.2f})."
        elif salario_bruto > TOPE_SALARIAL_ESTANDAR_PEN:
            advertencia = f"Advertencia: El salario mensual proyectado (S/. {salario_bruto:,.2f}) supera el rango salarial estándar (> S/. {TOPE_SALARIAL_ESTANDAR_PEN:,.2f}). Requiere validación de banda ejecutiva."

        return {
            "tipo_expectativa": tipo,
            "monto_declarado": monto_declarado,
            "salario_bruto_mensual": salario_bruto,
            "factor_ctc": factor_ctc,
            "ctc_solicitado": ctc_solicitado,
            "ctc_presupuestado": ctc_presupuestado,
            "variacion_porcentual": variacion_porcentual,
            "semaforo_presupuestal": semaforo_presupuestal,
            "requiere_aprobacion": requiere_aprobacion,
            "advertencia_rango_atipico": advertencia,
        }
