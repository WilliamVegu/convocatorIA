"""
Contratos de Interfaz y Esquemas Pydantic: Simulador Financiero y Costo Empresa CTC (Factor 1.56)
Módulo: specs/001-ats-core-mvp/contracts/ctc_contracts.py
Feature: 001-ats-core-mvp
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TipoExpectativaEnum(str, Enum):
    BRUTO = "Bruto"
    NETO = "Neto"


class SemaforoFinancieroEnum(str, Enum):
    DENTRO_PRESUPUESTO = "Dentro_Presupuesto"
    REQUIERE_APROBACION = "Requiere_Aprobacion"
    FUERA_BANDA = "Fuera_Banda"
    PENDIENTE_PRESUPUESTO = "Pendiente_Presupuesto"


FACTOR_CTC_LEGAL_728: float = 1.56
TASA_RETENCION_ESTIMADA_NETO: float = 0.21  # 5ta categoría + AFP/ONP promedio en Perú (~21%)
FACTOR_CONVERSION_NETO_BRUTO: float = 1.0 - TASA_RETENCION_ESTIMADA_NETO  # 0.79
SALARIO_MINIMO_VITAL_PEN: float = 1025.0
SALARIO_MAXIMO_ALERTA_PEN: float = 35000.0


class CTCCalculationInput(BaseModel):
    """Parámetros de entrada para la simulación económica de una pretensión salarial."""
    model_config = ConfigDict(str_strip_whitespace=True)

    tipo_expectativa: TipoExpectativaEnum = Field(
        default=TipoExpectativaEnum.BRUTO,
        description="Modalidad de la expectativa: 'Bruto' o 'Neto'"
    )
    monto_declarado: float = Field(
        ...,
        gt=0.0,
        description="Monto mensual en Soles (PEN) comunicado por el candidato",
        examples=[5000.0, 7500.0]
    )
    ctc_presupuestado: Optional[float] = Field(
        default=None,
        description="Costo Empresa máximo autorizado por finanzas para la vacante en PEN. Puede ser None, 0 o negativo.",
        examples=[10000.0, 12410.0]
    )

    @field_validator("monto_declarado")
    @classmethod
    def validate_positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El monto de expectativa salarial debe ser estrictamente mayor a 0.")
        return round(v, 2)


class CTCCalculationResult(BaseModel):
    """
    Resultado detallado de la simulación de Costo Empresa con guardas matemáticas blindadas.
    Garantiza 0.00% de errores de división por cero (#DIV/0!).
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    tipo_expectativa: TipoExpectativaEnum
    monto_declarado: float
    salario_bruto_mensual: float = Field(..., description="Sueldo bruto mensual en PEN")
    factor_ctc: float = Field(default=FACTOR_CTC_LEGAL_728, description="Factor laboral multiplicador 1.56")
    ctc_solicitado: float = Field(..., description="Costo Empresa Total mensual en PEN (bruto * 1.56)")
    ctc_presupuestado: Optional[float] = Field(default=None, description="Presupuesto de referencia")
    variacion_porcentual: Optional[float] = Field(
        default=None,
        description="Porcentaje de desvío presupuestal ((solicitado - presupuestado)/presupuestado * 100). Nulo si no hay presupuesto."
    )
    semaforo_presupuestal: SemaforoFinancieroEnum = Field(
        ...,
        description="Estado semafórico: Verde (<=0%), Ámbar (>0% y <=10%), Rojo (>10%), Gris (Sin Presupuesto)"
    )
    requiere_aprobacion_especial: bool = Field(
        default=False,
        description="Verdadero si el CTC solicitado excede el presupuesto autorizado"
    )
    advertencia_rango_atipico: Optional[str] = Field(
        default=None,
        description="Aviso preventivo si el salario es menor al SMV (S/. 1,025) o mayor a S/. 35,000"
    )


class CTCApprovalRequest(BaseModel):
    """Solicitud formal de aprobación salarial fuera de banda autorizada por Head of Talent Acquisition."""
    model_config = ConfigDict(str_strip_whitespace=True)

    postulacion_id: str
    evaluacion_ctc_id: str
    aprobado_por_user_id: str
    justificacion_operativa: str = Field(
        ...,
        min_length=15,
        description="Justificación técnica/comercial obligatoria de la excepción"
    )


def calculate_ctc(input_data: CTCCalculationInput) -> CTCCalculationResult:
    """
    Función de cálculo financiero puro conforme a la legislación laboral peruana (D.L. 728).
    Implementa:
    1. Conversión de Neto a Bruto (tasa de retención ~21%, divisor 0.79).
    2. Multiplicador de Costo Empresa Factor 1.56.
    3. Guarda matemática contra división por cero (#DIV/0!) para presupuestos nulos, <= 0.
    4. Semáforo financiero de 4 estados.
    5. Detección de rangos atípicos (<SMV S/. 1,025 o >S/. 35,000).
    """
    # 1. Proyección de salario bruto mensual
    if input_data.tipo_expectativa == TipoExpectativaEnum.NETO:
        salario_bruto = round(input_data.monto_declarado / FACTOR_CONVERSION_NETO_BRUTO, 2)
    else:
        salario_bruto = round(input_data.monto_declarado, 2)

    # 2. Costo Empresa solicitado (Factor 1.56)
    ctc_solicitado = round(salario_bruto * FACTOR_CTC_LEGAL_728, 2)

    # 3. Guarda contra división por cero y semáforo presupuestal
    presupuesto = input_data.ctc_presupuestado
    if presupuesto is None or presupuesto <= 0.0:
        variacion_porcentual = None
        semaforo = SemaforoFinancieroEnum.PENDIENTE_PRESUPUESTO
        requiere_aprobacion = False
    else:
        variacion_porcentual = round(((ctc_solicitado - presupuesto) / presupuesto) * 100.0, 2)
        if variacion_porcentual <= 0.0:
            semaforo = SemaforoFinancieroEnum.DENTRO_PRESUPUESTO
            requiere_aprobacion = False
        elif variacion_porcentual <= 10.0:
            semaforo = SemaforoFinancieroEnum.REQUIERE_APROBACION
            requiere_aprobacion = True
        else:
            semaforo = SemaforoFinancieroEnum.FUERA_BANDA
            requiere_aprobacion = True

    # 4. Advertencia de rango atípico
    advertencia = None
    if salario_bruto < SALARIO_MINIMO_VITAL_PEN:
        advertencia = f"Salario bruto proyectado (S/. {salario_bruto:,.2f}) es inferior al Salario Mínimo Vital vigente (S/. {SALARIO_MINIMO_VITAL_PEN:,.2f})."
    elif salario_bruto > SALARIO_MAXIMO_ALERTA_PEN:
        advertencia = f"Salario bruto proyectado (S/. {salario_bruto:,.2f}) supera el rango salarial estándar corporativo (S/. {SALARIO_MAXIMO_ALERTA_PEN:,.2f})."

    return CTCCalculationResult(
        tipo_expectativa=input_data.tipo_expectativa,
        monto_declarado=input_data.monto_declarado,
        salario_bruto_mensual=salario_bruto,
        factor_ctc=FACTOR_CTC_LEGAL_728,
        ctc_solicitado=ctc_solicitado,
        ctc_presupuestado=presupuesto,
        variacion_porcentual=variacion_porcentual,
        semaforo_presupuestal=semaforo,
        requiere_aprobacion_especial=requiere_aprobacion,
        advertencia_rango_atipico=advertencia,
    )


class CTCServicePort(ABC):
    """Puerto para el servicio de simulación y cálculo financiero de compensaciones."""

    @abstractmethod
    def calculate(self, input_data: CTCCalculationInput) -> CTCCalculationResult:
        """Ejecuta el cálculo protegido de Costo Empresa con factor 1.56 y guardas contra #DIV/0!."""
        pass
