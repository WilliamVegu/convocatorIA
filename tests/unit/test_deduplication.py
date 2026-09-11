"""Unit tests for multi-criteria deduplication service."""
import pytest
from src.services.deduplication_service import DeduplicationService


@pytest.fixture
def dedup_service(db_session):
    from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
    repo = CandidatoRepository(db_session)
    return DeduplicationService(repo)


def test_dedup_exact_dni_match(dedup_service, sample_candidate):
    match = dedup_service.check_duplicate(dni="76128709")
    assert match["is_duplicate"] is True
    assert match["matched_field"] == "DNI"
    assert match["existing_candidate_id"] == sample_candidate.id


def test_dedup_exact_phone_match(dedup_service, sample_candidate):
    match = dedup_service.check_duplicate(telefono="989322088")
    assert match["is_duplicate"] is True
    assert match["matched_field"] == "Telefono"


def test_dedup_exact_email_match(dedup_service, sample_candidate):
    match = dedup_service.check_duplicate(email="diego.ramos@test.com")
    assert match["is_duplicate"] is True
    assert match["matched_field"] == "Email"


def test_dedup_fuzzy_name_match(dedup_service, sample_candidate):
    # Inverted name order: "Ramos Quispe, Diego Alonso"
    match = dedup_service.check_duplicate(nombre_completo="Ramos Quispe Diego Alonso")
    assert match["is_duplicate"] is True
    assert match["matched_field"] == "Nombre_Fonetico"
    assert match["similarity_score"] >= 85.0


def test_dedup_clean_no_match(dedup_service, sample_candidate):
    match = dedup_service.check_duplicate(
        dni="88990011",
        telefono="911223344",
        email="nuevo.postulante@gmail.com",
        nombre_completo="Valeria Mendoza Silva",
    )
    assert match["is_duplicate"] is False
    assert match["matched_field"] is None
