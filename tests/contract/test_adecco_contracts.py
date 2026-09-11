import importlib
import pytest

contracts = importlib.import_module("specs.001-ats-core-mvp.contracts")


def test_adecco_column_aliases_coverage():
    aliases = contracts.ADECCO_COLUMN_ALIASES
    assert "documento" in aliases
    assert "telefono" in aliases
    assert "nombres" in aliases
    assert "perfil" in aliases
    assert "celular" in aliases["telefono"]
    assert "movil" in aliases["telefono"]
    assert "dni" in aliases["documento"]


def test_cartera_exclusion_row_5_columns_structure():
    row = contracts.CarteraExclusionRow5Col(
        dni="76128709",
        nombres_y_apellidos="Diego Alonso Ramos Quispe",
        perfil="Senior Java Backend Developer",
        vigencia_exclusion="Hasta 15/12/2026",
        estado="En Proceso Activo",
    )
    dumped = row.model_dump()
    assert len(dumped) == 5
    assert set(dumped.keys()) == {
        "dni",
        "nombres_y_apellidos",
        "perfil",
        "vigencia_exclusion",
        "estado",
    }
    # Check strict compliance: no phone, email or salary
    assert "telefono" not in dumped
    assert "email" not in dumped
    assert "sueldo" not in dumped


def test_adecco_batch_summary_metrics():
    summary = contracts.AdeccoBatchSummary(
        lote_id="lot-001",
        nombre_archivo="planilla_adecco_set2026.xlsx",
        total_filas_leidas=20,
        total_rojos_duplicados=7,
        total_amarillos_reactivables=3,
        total_verdes_limpios=8,
        total_alumni_detectados=2,
        items=[],
        tiempo_procesamiento_ms=1420.5,
        procesado_por_user_id="usr-recruiter-01",
    )
    assert summary.total_filas_leidas == 20
    assert summary.timestamp.tzinfo is not None
