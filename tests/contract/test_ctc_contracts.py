import importlib
import pytest

contracts = importlib.import_module("specs.001-ats-core-mvp.contracts")


def test_ctc_factor_156_gross_within_budget():
    inp = contracts.CTCCalculationInput(
        tipo_expectativa=contracts.TipoExpectativaEnum.BRUTO,
        monto_declarado=5000.0,
        ctc_presupuestado=10000.0,
    )
    res = contracts.calculate_ctc(inp)
    assert res.salario_bruto_mensual == 5000.0
    assert res.ctc_solicitado == 7800.0  # 5000 * 1.56
    assert res.variacion_porcentual == -22.0  # (7800 - 10000)/10000 * 100
    assert res.semaforo_presupuestal == contracts.SemaforoFinancieroEnum.DENTRO_PRESUPUESTO
    assert res.requiere_aprobacion_especial is False
    assert res.advertencia_rango_atipico is None


def test_ctc_net_to_gross_conversion():
    inp = contracts.CTCCalculationInput(
        tipo_expectativa=contracts.TipoExpectativaEnum.NETO,
        monto_declarado=5000.0,
        ctc_presupuestado=10000.0,
    )
    res = contracts.calculate_ctc(inp)
    assert res.salario_bruto_mensual == 6329.11  # 5000 / 0.79
    assert res.ctc_solicitado == 9873.41  # 6329.11 * 1.56
    assert res.variacion_porcentual == -1.27  # (9873.41 - 10000)/10000 * 100
    assert res.semaforo_presupuestal == contracts.SemaforoFinancieroEnum.DENTRO_PRESUPUESTO
    assert res.requiere_aprobacion_especial is False


def test_ctc_division_by_zero_guard_with_zero_budget():
    inp = contracts.CTCCalculationInput(
        tipo_expectativa=contracts.TipoExpectativaEnum.BRUTO,
        monto_declarado=5000.0,
        ctc_presupuestado=0.0,
    )
    res = contracts.calculate_ctc(inp)
    assert res.ctc_solicitado == 7800.0
    assert res.variacion_porcentual is None
    assert res.semaforo_presupuestal == contracts.SemaforoFinancieroEnum.PENDIENTE_PRESUPUESTO
    assert res.requiere_aprobacion_especial is False


def test_ctc_division_by_zero_guard_with_negative_budget():
    inp = contracts.CTCCalculationInput(
        tipo_expectativa=contracts.TipoExpectativaEnum.BRUTO,
        monto_declarado=5000.0,
        ctc_presupuestado=-500.0,
    )
    res = contracts.calculate_ctc(inp)
    assert res.variacion_porcentual is None
    assert res.semaforo_presupuestal == contracts.SemaforoFinancieroEnum.PENDIENTE_PRESUPUESTO
    assert res.requiere_aprobacion_especial is False


def test_ctc_division_by_zero_guard_with_none_budget():
    inp = contracts.CTCCalculationInput(
        tipo_expectativa=contracts.TipoExpectativaEnum.BRUTO,
        monto_declarado=5000.0,
        ctc_presupuestado=None,
    )
    res = contracts.calculate_ctc(inp)
    assert res.variacion_porcentual is None
    assert res.semaforo_presupuestal == contracts.SemaforoFinancieroEnum.PENDIENTE_PRESUPUESTO


def test_ctc_out_of_band_traffic_light():
    # Desvío > 10%
    inp = contracts.CTCCalculationInput(
        tipo_expectativa=contracts.TipoExpectativaEnum.BRUTO,
        monto_declarado=9000.0,
        ctc_presupuestado=10000.0,
    )
    res = contracts.calculate_ctc(inp)
    assert res.ctc_solicitado == 14040.0
    assert res.variacion_porcentual == 40.4
    assert res.semaforo_presupuestal == contracts.SemaforoFinancieroEnum.FUERA_BANDA
    assert res.requiere_aprobacion_especial is True


def test_ctc_requires_approval_traffic_light():
    # Desvío entre 0% y 10%
    # If CTC solicitado is 10500, with budget 10000 -> +5.0%
    # gross = 10500 / 1.56 = 6730.77
    inp = contracts.CTCCalculationInput(
        tipo_expectativa=contracts.TipoExpectativaEnum.BRUTO,
        monto_declarado=6730.77,
        ctc_presupuestado=10000.0,
    )
    res = contracts.calculate_ctc(inp)
    assert res.ctc_solicitado == 10500.0
    assert res.variacion_porcentual == 5.0
    assert res.semaforo_presupuestal == contracts.SemaforoFinancieroEnum.REQUIERE_APROBACION
    assert res.requiere_aprobacion_especial is True


def test_ctc_atypical_salary_warnings():
    # Below SMV (1025)
    inp_low = contracts.CTCCalculationInput(
        tipo_expectativa=contracts.TipoExpectativaEnum.BRUTO,
        monto_declarado=800.0,
        ctc_presupuestado=2000.0,
    )
    res_low = contracts.calculate_ctc(inp_low)
    assert res_low.advertencia_rango_atipico is not None
    assert "inferior al Salario Mínimo Vital" in res_low.advertencia_rango_atipico

    # Above 35,000
    inp_high = contracts.CTCCalculationInput(
        tipo_expectativa=contracts.TipoExpectativaEnum.BRUTO,
        monto_declarado=40000.0,
        ctc_presupuestado=70000.0,
    )
    res_high = contracts.calculate_ctc(inp_high)
    assert res_high.advertencia_rango_atipico is not None
    assert "supera el rango salarial estándar" in res_high.advertencia_rango_atipico
