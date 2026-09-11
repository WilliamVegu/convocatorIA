"""Unit tests for CTC financial calculator with Factor 1.56 and zero-division guards."""
import pytest
from src.services.ctc_calculator_service import CTCCalculatorService


@pytest.fixture
def ctc_service():
    return CTCCalculatorService()


def test_gross_salary_exact_multiplication(ctc_service):
    # Gross S/. 5,000 with budget S/. 10,000 -> CTC = 7,800 (-22.0%)
    res = ctc_service.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=5000.0,
        ctc_presupuestado=10000.0,
    )
    assert res["salario_bruto_mensual"] == 5000.0
    assert res["ctc_solicitado"] == 7800.0
    assert res["variacion_porcentual"] == -22.0
    assert res["semaforo_presupuestal"] == "Dentro_Presupuesto"
    assert res["requiere_aprobacion"] is False
    assert res["advertencia_rango_atipico"] is None


def test_net_salary_to_gross_conversion(ctc_service):
    # Net S/. 5,000 -> Gross S/. 6,329.11 -> CTC S/. 9,873.41
    res = ctc_service.calculate(
        tipo_expectativa="Neto",
        monto_declarado=5000.0,
        ctc_presupuestado=10000.0,
    )
    assert res["salario_bruto_mensual"] == 6329.11
    assert res["ctc_solicitado"] == 9873.41
    assert res["variacion_porcentual"] == -1.27
    assert res["semaforo_presupuestal"] == "Dentro_Presupuesto"
    assert res["requiere_aprobacion"] is False


def test_zero_division_guard_budget_zero(ctc_service):
    res = ctc_service.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=5000.0,
        ctc_presupuestado=0.0,
    )
    assert res["ctc_solicitado"] == 7800.0
    assert res["variacion_porcentual"] is None
    assert res["semaforo_presupuestal"] == "Pendiente_Presupuesto"
    assert res["requiere_aprobacion"] is False


def test_zero_division_guard_budget_negative(ctc_service):
    res = ctc_service.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=5000.0,
        ctc_presupuestado=-1000.0,
    )
    assert res["variacion_porcentual"] is None
    assert res["semaforo_presupuestal"] == "Pendiente_Presupuesto"


def test_zero_division_guard_budget_none(ctc_service):
    res = ctc_service.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=5000.0,
        ctc_presupuestado=None,
    )
    assert res["variacion_porcentual"] is None
    assert res["semaforo_presupuestal"] == "Pendiente_Presupuesto"


def test_requires_approval_range_0_to_10_percent(ctc_service):
    # Budget 10,000, Requested CTC 10,500 (+5.0%) -> gross = 10500/1.56 = 6730.77
    res = ctc_service.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=6730.77,
        ctc_presupuestado=10000.0,
    )
    assert res["ctc_solicitado"] == 10500.0
    assert res["variacion_porcentual"] == 5.0
    assert res["semaforo_presupuestal"] == "Requiere_Aprobacion"
    assert res["requiere_aprobacion"] is True


def test_out_of_band_greater_than_10_percent(ctc_service):
    # Budget 10,000, Gross 9,000 -> CTC 14,040 (+40.4%)
    res = ctc_service.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=9000.0,
        ctc_presupuestado=10000.0,
    )
    assert res["ctc_solicitado"] == 14040.0
    assert res["variacion_porcentual"] == 40.4
    assert res["semaforo_presupuestal"] == "Fuera_Banda"
    assert res["requiere_aprobacion"] is True


def test_smv_low_salary_warning(ctc_service):
    res = ctc_service.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=800.0,
        ctc_presupuestado=2000.0,
    )
    assert res["advertencia_rango_atipico"] is not None
    assert "inferior al Salario Mínimo Vital" in res["advertencia_rango_atipico"]


def test_high_salary_warning(ctc_service):
    res = ctc_service.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=40000.0,
        ctc_presupuestado=70000.0,
    )
    assert res["advertencia_rango_atipico"] is not None
    assert "supera el rango salarial estándar" in res["advertencia_rango_atipico"]
