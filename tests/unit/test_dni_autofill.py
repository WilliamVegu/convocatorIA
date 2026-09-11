"""Test verifying DNI validation auto-fills candidate personal fields."""
import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent.parent / "src" / "app.py")


def test_dni_autofill_in_ficha_candidato():
    """Verify that clicking Validar DNI with an existing cached DNI auto-populates personal fields."""
    at = AppTest.from_file(APP_PATH)
    at.run()

    # Authenticate as Senior Recruiter
    at.session_state["is_authenticated"] = True
    at.session_state["user_id"] = "usr-recruiter-001"
    at.session_state["email"] = "recruiter.lead@tcs.com"
    at.session_state["nombres_completos"] = "Senior Technical Recruiter Demo"
    at.session_state["rol"] = "Senior_Technical_Recruiter"
    at.session_state["current_page"] = "p1_ficha"
    at.run()
    assert not at.exception

    # Locate DNI input field and type cached DNI 76128709 (Diego Alonso Ramos Quispe)
    dni_input = None
    for ti in at.text_input:
        if "Ej. 76128709" in (ti.placeholder or "") or "DNI" in (ti.label or ""):
            dni_input = ti
            break

    assert dni_input is not None, "DNI input field not found"
    dni_input.input("76128709").run()

    # Click "Validar DNI" button
    val_btn = None
    for b in at.button:
        if "Validar DNI" in (b.label or ""):
            val_btn = b
            break

    assert val_btn is not None, "Validar DNI button not found"
    val_btn.click().run()

    assert not at.exception
    # Check that Nombres, Apellido Paterno, Apellido Materno have been auto-filled
    ti_map = {ti.label: ti.value for ti in at.text_input}
    assert ti_map.get("Nombres") == "DIEGO ALONSO", f"Expected 'DIEGO ALONSO', got '{ti_map.get('Nombres')}'"
    assert ti_map.get("Apellido Paterno") == "RAMOS", f"Expected 'RAMOS', got '{ti_map.get('Apellido Paterno')}'"
    assert ti_map.get("Apellido Materno") == "QUISPE", f"Expected 'QUISPE', got '{ti_map.get('Apellido Materno')}'"
    assert ti_map.get("Distrito de Residencia (Lima)") == "Santiago de Surco"
    assert ti_map.get("Ubigeo") == "150140"


def test_dni_autofill_with_live_apisperu_dni():
    """Verify that validating a DNI fetched via APIsPERU auto-populates names."""
    at = AppTest.from_file(APP_PATH)
    at.run()

    at.session_state["is_authenticated"] = True
    at.session_state["user_id"] = "usr-recruiter-001"
    at.session_state["email"] = "recruiter.lead@tcs.com"
    at.session_state["nombres_completos"] = "Senior Technical Recruiter Demo"
    at.session_state["rol"] = "Senior_Technical_Recruiter"
    at.session_state["current_page"] = "p1_ficha"
    at.run()
    assert not at.exception

    # Find DNI input and enter 73861082 (user's DNI)
    for ti in at.text_input:
        if "Ej. 76128709" in (ti.placeholder or "") or "DNI" in (ti.label or ""):
            ti.input("73861082").run()
            break

    # Click Validar DNI
    for b in at.button:
        if "Validar DNI" in (b.label or ""):
            b.click().run()
            break

    assert not at.exception
    ti_map = {ti.label: ti.value for ti in at.text_input}
    assert ti_map.get("Nombres") == "WILLIAM FACUNDO CELSO"
    assert ti_map.get("Apellido Paterno") == "VEGA"
    assert ti_map.get("Apellido Materno") == "GUTIERREZ"


def test_dni_not_found_handling():
    """Verify that a non-existent DNI returns error message without crashing."""
    from src.adapters.persistence.database import SessionLocal
    from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
    from src.adapters.identity.apisperu_adapter import APIsPeruDNIAdapter

    with SessionLocal() as db:
        repo = CandidatoRepository(db)
        adapter = APIsPeruDNIAdapter(repo)
        res = adapter.resolve_dni("00000000")
        assert res["success"] is False
        assert res["regularizacion_pendiente"] is True
        assert res["estado_identidad"] == "Pendiente_Regularizacion"


def test_ruc_resolution_apisperu():
    """Verify RUC resolution returns company data from SUNAT via APIsPERU."""
    from src.adapters.persistence.database import SessionLocal
    from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
    from src.adapters.identity.apisperu_adapter import APIsPeruDNIAdapter

    with SessionLocal() as db:
        repo = CandidatoRepository(db)
        adapter = APIsPeruDNIAdapter(repo)
        res = adapter.resolve_ruc("20100070970")
        assert res["success"] is True
        assert "SUPERMERCADOS PERUANOS" in res["datos"]["razon_social"]
        assert res["datos"]["estado"] == "ACTIVO"
        assert res["datos"]["condicion"] == "HABIDO"


