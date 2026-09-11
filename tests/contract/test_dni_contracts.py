import importlib
import pytest
from datetime import date

contracts = importlib.import_module("specs.001-ats-core-mvp.contracts")


def test_dni_request_valid():
    req = contracts.DNIRequest(dni="76128709")
    assert req.dni == "76128709"


def test_dni_request_invalid_length():
    with pytest.raises(ValueError, match="exactamente 8 dígitos numéricos"):
        contracts.DNIRequest(dni="1234567")


def test_dni_request_non_numeric():
    with pytest.raises(ValueError, match="exactamente 8 dígitos numéricos"):
        contracts.DNIRequest(dni="7612870A")


def test_dni_response_data_with_and_without_maternal_surname():
    # Case with maternal surname
    data1 = contracts.DNIResponseData(
        dni="76128709",
        nombres="DIEGO ALONSO",
        apellido_paterno="RAMOS",
        apellido_materno="QUISPE",
        fecha_nacimiento=date(1995, 4, 12),
        distrito="Santiago de Surco",
    )
    assert data1.nombres_completos == "DIEGO ALONSO RAMOS QUISPE"

    # Case without maternal surname (None passed, e.g. from SQL NULL or foreigner)
    data2 = contracts.DNIResponseData(
        dni="46753314",
        nombres="CARLOS",
        apellido_paterno="GARCIA",
        apellido_materno=None,
    )
    assert data2.apellido_materno == ""
    assert data2.nombres_completos == "CARLOS GARCIA"


def test_dni_cache_entry_normalization():
    entry = contracts.DNICacheEntry(
        dni="76128709",
        nombres="DIEGO ALONSO",
        apellido_paterno="RAMOS",
        apellido_materno=None,
    )
    assert entry.apellido_materno == ""
    assert entry.cached_at is not None
    assert entry.cached_at.tzinfo is not None  # Timezone aware UTC


def test_dni_validation_result():
    res = contracts.DNIValidationResult(
        success=True,
        fuente_origen="CACHE_LOCAL",
        datos=contracts.DNIResponseData(
            dni="76128709",
            nombres="DIEGO ALONSO",
            apellido_paterno="RAMOS",
        ),
    )
    assert res.success is True
    assert res.estado_identidad == contracts.EstadoIdentidadEnum.VALIDADO_OFICIALMENTE
    assert res.timestamp_consulta.tzinfo is not None
