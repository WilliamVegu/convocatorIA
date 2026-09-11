"""Unit tests for dynamic candidate age calculation."""
from datetime import date
import pytest
from src.domain.entities import Candidato


def test_calculate_age_exact_birthday():
    cand = Candidato(
        id="c-1",
        tipo_documento="DNI",
        numero_documento="76128709",
        nombres="Diego",
        apellido_paterno="Ramos",
        nombres_completos_normalizado="DIEGO RAMOS",
        telefono_e164="+51989322088",
        email="diego@test.com",
        created_by_user_id="u-1",
        fecha_nacimiento=date(1995, 4, 12),
    )
    # On birthday in 2026: exactly 31
    assert cand.calcular_edad(referencia=date(2026, 4, 12)) == 31


def test_calculate_age_day_before_birthday():
    cand = Candidato(
        id="c-2",
        tipo_documento="DNI",
        numero_documento="76128709",
        nombres="Diego",
        apellido_paterno="Ramos",
        nombres_completos_normalizado="DIEGO RAMOS",
        telefono_e164="+51989322088",
        email="diego@test.com",
        created_by_user_id="u-1",
        fecha_nacimiento=date(1995, 4, 12),
    )
    # Day before birthday in 2026: still 30
    assert cand.calcular_edad(referencia=date(2026, 4, 11)) == 30


def test_calculate_age_day_after_birthday():
    cand = Candidato(
        id="c-3",
        tipo_documento="DNI",
        numero_documento="76128709",
        nombres="Diego",
        apellido_paterno="Ramos",
        nombres_completos_normalizado="DIEGO RAMOS",
        telefono_e164="+51989322088",
        email="diego@test.com",
        created_by_user_id="u-1",
        fecha_nacimiento=date(1995, 4, 12),
    )
    # Day after birthday in 2026: 31
    assert cand.calcular_edad(referencia=date(2026, 4, 13)) == 31


def test_calculate_age_leap_year():
    cand = Candidato(
        id="c-4",
        tipo_documento="DNI",
        numero_documento="88776655",
        nombres="Bisiesto",
        apellido_paterno="Perez",
        nombres_completos_normalizado="BISIESTO PEREZ",
        telefono_e164="+51999888777",
        email="bisiesto@test.com",
        created_by_user_id="u-1",
        fecha_nacimiento=date(2000, 2, 29),
    )
    # In non-leap year on Feb 28: still 25
    assert cand.calcular_edad(referencia=date(2026, 2, 28)) == 25
    # On March 1: turns 26
    assert cand.calcular_edad(referencia=date(2026, 3, 1)) == 26


def test_calculate_age_no_birthdate():
    cand = Candidato(
        id="c-5",
        tipo_documento="DNI",
        numero_documento="11223344",
        nombres="Sin",
        apellido_paterno="Fecha",
        nombres_completos_normalizado="SIN FECHA",
        telefono_e164="+51911223344",
        email="sinfecha@test.com",
        created_by_user_id="u-1",
        fecha_nacimiento=None,
    )
    assert cand.calcular_edad() is None
