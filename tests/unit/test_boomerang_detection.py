"""Unit tests for automatic Boomerang (Alumni TCS) detection."""
import pytest
from datetime import date
from src.services.alumni_service import AlumniService
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository


@pytest.fixture
def alumni_service(db_session):
    repo = AlumniRepository(db_session)
    return AlumniService(repo)


def test_boomerang_detection_exact_dni(alumni_service):
    # DNI 46753314 seeded as Carlos Garcia (Rehire_Eligible)
    res = alumni_service.detect_alumni(dni="46753314")
    assert res["is_alumni"] is True
    assert res["estatus_recontratacion"] == "Rehire_Eligible"
    assert res["bloquear_comision_agencia"] is True
    assert "CARLOS EDUARDO" in res["nombres_completos"]


def test_boomerang_detection_do_not_rehire(alumni_service):
    # DNI 10293847 seeded as Roberto Diaz (Do_Not_Rehire)
    res = alumni_service.detect_alumni(dni="10293847")
    assert res["is_alumni"] is True
    assert res["estatus_recontratacion"] == "Do_Not_Rehire"
    assert res["bloquear_comision_agencia"] is True
    assert "Falta Grave" in (res["motivo_desvinculacion"] or "")


def test_boomerang_detection_by_corporate_email(alumni_service):
    res = alumni_service.detect_alumni(email="carlos.garcia1@tcs.com")
    assert res["is_alumni"] is True
    assert res["alumni_id"] == "alm-001"


def test_boomerang_detection_fuzzy_name(alumni_service):
    # Inverted or slightly varied name: "Garcia Sanchez, Carlos E."
    res = alumni_service.detect_alumni(nombre_completo="Carlos Eduardo Garcia Sanchez")
    assert res["is_alumni"] is True
    assert res["estatus_recontratacion"] == "Rehire_Eligible"


def test_boomerang_detection_non_alumni(alumni_service):
    res = alumni_service.detect_alumni(dni="99999999", email="inedito@gmail.com", nombre_completo="Juan Perez Perez")
    assert res["is_alumni"] is False
    assert res["estatus_recontratacion"] is None
    assert res["bloquear_comision_agencia"] is False
