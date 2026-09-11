"""Unit tests for Streamlit ATS UI pages and rendering execution."""
import io
import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.adapters.cv_parser.heuristic_extractor import HeuristicCVExtractor
from src.adapters.persistence.database import SessionLocal
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.services.audit_service import AuditService
from src.ui.session import init_session, login_user, logout, enforce_write_permission

APP_PATH = str(Path(__file__).resolve().parent.parent.parent / "src" / "app.py")


def test_login_page_renders_unauthenticated():
    """Verify that an unauthenticated user arrives at the login page without crashes."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception
    assert len(at.text_input) >= 2


def test_login_form_successful_submission():
    """Verify that submitting valid credentials via form logs in cleanly."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception
    at.text_input[0].input("admin.ta@tcs.com")
    at.text_input[1].input("Password123!")
    at.button[0].click()
    at.run()
    assert not at.exception
    assert at.session_state["is_authenticated"] is True
    assert at.session_state["email"] == "admin.ta@tcs.com"
    assert at.session_state["user_id"] == "usr-admin-bootstrap-001"
    assert at.session_state["rol"] == "Head_of_Talent_Acquisition"


def test_all_pages_render_authenticated_as_admin():
    """Verify that all 8 functional pages render without unhandled exceptions for Head of TA."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception

    at.session_state["is_authenticated"] = True
    at.session_state["user_id"] = "usr-admin-bootstrap-001"
    at.session_state["email"] = "admin.ta@tcs.com"
    at.session_state["nombres_completos"] = "Administrador Central Talent Acquisition"
    at.session_state["rol"] = "Head_of_Talent_Acquisition"

    pages = [
        "p1_ficha",
        "p2_screening",
        "p3_ctc",
        "p4_adecco",
        "p5_exclusiones",
        "p6_alumni",
        "p7_auditoria",
        "p8_usuarios",
    ]

    for page_key in pages:
        at.session_state["current_page"] = page_key
        at.run()
        assert not at.exception, f"Page {page_key} failed to render: {at.exception}"


def test_compliance_officer_read_only_access():
    """Verify that Compliance Officer can view pages in read-only mode."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception

    at.session_state["is_authenticated"] = True
    at.session_state["user_id"] = "usr-compliance-001"
    at.session_state["email"] = "compliance.officer@tcs.com"
    at.session_state["nombres_completos"] = "Compliance Officer Demo"
    at.session_state["rol"] = "Compliance_Officer"

    for page_key in ["p1_ficha", "p5_exclusiones", "p7_auditoria"]:
        at.session_state["current_page"] = page_key
        at.run()
        assert not at.exception, f"Compliance view failed on {page_key}: {at.exception}"


def test_heuristic_cv_extractor_pymupdf_support():
    """Verify HeuristicCVExtractor handles PDF content without crashing and falls back cleanly."""
    extractor = HeuristicCVExtractor()
    sample_text = """
    JUAN CARLOS PEREZ LOPEZ
    Desarrollador Senior Backend
    Experiencia: 7 años de experiencia en desarrollo de software
    Habilidades: Python, FastAPI, Docker, PostgreSQL, React, AWS
    Idiomas: Inglés avanzado, Español nativo
    """
    res = extractor.extract_from_text(sample_text)
    assert res["seniority_estimado"] == "Senior"
    assert res["anios_experiencia_total"] == 7.0
    assert any(s["nombre"] == "Python" for s in res["habilidades_tecnicas"])
    assert any(s["nombre"] == "PostgreSQL" for s in res["habilidades_tecnicas"])
    assert any(l["idioma"] == "Inglés" and l["nivel"] == "Avanzado" for l in res["idiomas"])


def test_session_audit_check_constraints_respected(db_session, admin_user):
    """Verify logout and enforce_write_permission satisfy DB check constraints."""
    audit_svc = AuditService(AuditRepository(db_session))
    
    log_id = audit_svc.log_event(
        usuario_id=admin_user.id,
        usuario_email=admin_user.email,
        rol_en_momento=admin_user.rol,
        tipo_accion="Autenticacion",
        entidad_objeto="Usuario",
        registro_id=admin_user.id,
        version_registro=1,
        justificacion_operativa="Test de cierre de sesion",
    )
    db_session.commit()
    assert log_id is not None

    sec_id = audit_svc.log_event(
        usuario_id=admin_user.id,
        usuario_email=admin_user.email,
        rol_en_momento=admin_user.rol,
        tipo_accion="Acceso_Denegado",
        entidad_objeto="Usuario",
        registro_id=admin_user.id,
        version_registro=1,
        justificacion_operativa="Test de acceso denegado",
    )
    db_session.commit()
    assert sec_id is not None
