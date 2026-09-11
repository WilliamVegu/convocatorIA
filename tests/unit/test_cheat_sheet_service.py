"""Unit tests for Technical Screening Cheat Sheet service."""
from unittest.mock import patch
from src.services.cheat_sheet_service import CheatSheetService


@patch("src.services.cheat_sheet_service.config.GEMINI_API_KEY", "")
def test_cheat_sheet_service_known_role():
    svc = CheatSheetService()
    sheet = svc.generate_cheat_sheet(
        postulacion_id="pos-test-123",
        perfil_puesto="Desarrollador Java Senior",
        cv_text="Java 17, Spring Boot, Microservicios, Kafka",
    )

    assert sheet.postulacion_id == "pos-test-123"
    assert sheet.perfil == "Desarrollador Java Senior"
    assert len(sheet.preguntas) >= 3
    first_q = sheet.preguntas[0]
    assert first_q.pregunta is not None
    assert first_q.concepto_clave is not None
    assert first_q.respuesta_esperada is not None
    assert first_q.criterio_evaluacion is not None


def test_cheat_sheet_service_generic_role_fallback():
    svc = CheatSheetService()
    sheet = svc.generate_cheat_sheet(
        postulacion_id="pos-gen-456",
        perfil_puesto="Especialista en Cobol Mainframe",
    )

    assert sheet.postulacion_id == "pos-gen-456"
    assert len(sheet.preguntas) == 3
    assert any("Especialista en Cobol Mainframe" in q.pregunta for q in sheet.preguntas)
