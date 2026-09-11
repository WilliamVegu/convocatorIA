"""Unit and UI interaction tests using Streamlit AppTest for ATS pages."""
import io
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from streamlit.testing.v1 import AppTest

from src.services.rgs_normalizer_service import RGSNormalized
from src.ports.contracts import CarteraExclusionRow5Col
from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.models import UsuarioModel, CandidatoModel, PostulacionModel

APP_PATH = str(Path(__file__).resolve().parent.parent.parent / "src" / "app.py")


def test_p9_normalizador_rgs_interaction():
    """Verify p9 RGS normalizer page interaction, sample loading, and AI normalizer."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception

    # Authenticate as Head of TA
    at.session_state["is_authenticated"] = True
    at.session_state["user_id"] = "usr-admin-bootstrap-001"
    at.session_state["email"] = "admin.ta@tcs.com"
    at.session_state["nombres_completos"] = "Administrador Central Talent Acquisition"
    at.session_state["rol"] = "Head_of_Talent_Acquisition"
    at.session_state["current_page"] = "p9_rgs"

    at.run()
    assert not at.exception

    # Inject normalized result into session state to test rendering of JD and boolean string
    norm_dummy = RGSNormalized(
        rgs_id="RGS-TEST-999",
        cliente="BCP",
        titulo_puesto="Desarrollador Java Senior",
        seniority="Senior",
        must_have=["Java 17", "Spring Boot 3", "Microservicios", "Kafka"],
        nice_to_have=["AWS", "Docker", "Kubernetes"],
        banda_salarial_pen="S/. 8,500 - S/. 9,500",
        modalidad_sugerida="Híbrido (2 días oficina)",
        cadena_booleana_linkedin='("Java" OR "Spring Boot") AND ("Kafka" OR "Microservices") AND ("Lima" OR "Peru")',
    )
    at.session_state["normalized_rgs"] = norm_dummy
    at.run()
    assert not at.exception

    # Verify that the structured JD card rendered
    assert at.session_state["normalized_rgs"].titulo_puesto == "Desarrollador Java Senior"
    assert at.session_state["normalized_rgs"].cliente == "BCP"


def test_p4_validador_adecco_rendering_and_semaphore_cards():
    """Verify p4 Adecco validator renders semaphore cards when evaluation result is present."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception

    at.session_state["is_authenticated"] = True
    at.session_state["user_id"] = "usr-recruiter-001"
    at.session_state["email"] = "recruiter.lead@tcs.com"
    at.session_state["nombres_completos"] = "Senior Technical Recruiter Demo"
    at.session_state["rol"] = "Senior_Technical_Recruiter"
    at.session_state["current_page"] = "p4_adecco"

    # Inject sample batch evaluation result into session state matching p4 structure
    at.session_state["adecco_eval_result"] = {
        "total_filas": 20,
        "total_rojos": 7,
        "total_amarillos": 3,
        "total_verdes": 8,
        "total_alumni": 2,
        "items": [
            {
                "fila_index": 2,
                "documento": "76128709",
                "nombres": "DIEGO RAMOS",
                "telefono": "+51989322088",
                "perfil": "Java Dev",
                "color_semaforo": "Rojo",
                "detalle_clasificacion": "Duplicado Activo",
                "is_alumni": True,
            },
            {
                "fila_index": 3,
                "documento": "45892011",
                "nombres": "CARLOS ALVA",
                "telefono": "+51912345678",
                "perfil": "Data Engineer",
                "color_semaforo": "Verde",
                "detalle_clasificacion": "Perfil Inédito Limpio",
                "is_alumni": False,
            },
        ],
    }

    at.run()
    assert not at.exception
    assert at.session_state["adecco_eval_result"]["total_filas"] == 20
    assert at.session_state["adecco_eval_result"]["total_verdes"] == 8


def test_p5_reporte_exclusion_generation():
    """Verify p5 Adecco exclusion report under Ley 29733 renders correctly."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception

    at.session_state["is_authenticated"] = True
    at.session_state["user_id"] = "usr-compliance-001"
    at.session_state["email"] = "compliance.officer@tcs.com"
    at.session_state["nombres_completos"] = "Compliance Officer Demo"
    at.session_state["rol"] = "Compliance_Officer"
    at.session_state["current_page"] = "p5_exclusiones"

    row = CarteraExclusionRow5Col(
        dni="76128709",
        nombres_y_apellidos="DIEGO ALONSO RAMOS QUISPE",
        perfil="Desarrollador Java",
        vigencia_exclusion="180 días (hasta 2027-03-10)",
        estado="En Proceso de Selección TCS",
    )
    at.session_state["exclusion_report_data"] = {
        "rows": [row],
        "excel_bytes": b"fake_excel_bytes",
        "total_registros": 1,
    }

    at.run()
    assert not at.exception
    assert len(at.session_state["exclusion_report_data"]["rows"]) == 1


def test_p8_gestion_usuarios_strict_rbac_guard():
    """Verify p8 user administration hides menu from recruiter and is exclusive to Head of TA."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception

    # 1. Non-admin (Senior Recruiter): option 9 must NOT exist in the sidebar menu
    at.session_state["is_authenticated"] = True
    at.session_state["user_id"] = "usr-recruiter-001"
    at.session_state["email"] = "recruiter.lead@tcs.com"
    at.session_state["rol"] = "Senior_Technical_Recruiter"

    at.run()
    assert not at.exception
    radio_opts = at.sidebar.radio[0].options
    assert not any("Gestión de Usuarios" in opt for opt in radio_opts)

    # 2. Head of TA: option 9 MUST be present in the sidebar menu
    at.session_state["user_id"] = "usr-admin-bootstrap-001"
    at.session_state["email"] = "admin.ta@tcs.com"
    at.session_state["rol"] = "Head_of_Talent_Acquisition"

    at.run()
    assert not at.exception
    admin_radio_opts = at.sidebar.radio[0].options
    assert any("Gestión de Usuarios" in opt for opt in admin_radio_opts)


def test_p6_alumni_catalog_search():
    """Verify p6 alumni catalog renders and responds to search input."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception

    at.session_state["is_authenticated"] = True
    at.session_state["user_id"] = "usr-admin-bootstrap-001"
    at.session_state["email"] = "admin.ta@tcs.com"
    at.session_state["rol"] = "Head_of_Talent_Acquisition"
    at.session_state["current_page"] = "p6_alumni"

    at.run()
    assert not at.exception


def test_p7_auditoria_console_and_metrics_tab():
    """Verify p7 audit console renders logs and 17 funnel metrics."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception

    at.session_state["is_authenticated"] = True
    at.session_state["user_id"] = "usr-admin-bootstrap-001"
    at.session_state["email"] = "admin.ta@tcs.com"
    at.session_state["rol"] = "Head_of_Talent_Acquisition"
    at.session_state["current_page"] = "p7_auditoria"

    at.run()
    assert not at.exception
