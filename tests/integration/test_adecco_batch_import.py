"""Integration tests for Adecco mass ingestion, alias tolerance, and atomic batch rollback."""
import io
import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta

from src.services.adecco_service import AdeccoService
from src.services.deduplication_service import DeduplicationService
from src.services.alumni_service import AlumniService
from src.services.audit_service import AuditService
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.adecco_repository import AdeccoRepository
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository


@pytest.fixture
def adecco_service(db_session):
    cand_repo = CandidatoRepository(db_session)
    post_repo = PostulacionRepository(db_session)
    adecco_repo = AdeccoRepository(db_session)
    alumni_repo = AlumniRepository(db_session)
    audit_repo = AuditRepository(db_session)

    dedup = DeduplicationService(cand_repo)
    alumni = AlumniService(alumni_repo)
    audit = AuditService(audit_repo)

    return AdeccoService(
        candidato_repo=cand_repo,
        postulacion_repo=post_repo,
        adecco_repo=adecco_repo,
        dedup_service=dedup,
        alumni_service=alumni,
        audit_service=audit,
    )


def test_adecco_alias_tolerance_and_traffic_light(adecco_service, sample_candidate, recruiter_user):
    # Create an in-memory CSV with alias headers: 'DNI / CE', 'Móvil', 'Puesto'
    # 1. Row matching sample_candidate (76128709) -> Red
    # 2. Row matching alumni (46753314) -> Boomerang + Green (not in candidates yet)
    # 3. Completely new candidate (88771122) -> Green
    csv_data = """DNI / CE,Nombres y Apellidos,Móvil,Puesto,Correo
76128709,Diego Alonso Ramos Quispe,989322088,Backend Developer,diego@test.com
46753314,Carlos Eduardo Garcia,955443322,Tech Lead,carlos@test.com
88771122,Valeria Maria Soto,911335577,QA Engineer,valeria@test.com
"""
    file_bytes = csv_data.encode("utf-8")

    res = adecco_service.evaluate_spreadsheet(
        file_bytes=file_bytes,
        filename="adecco_test.csv",
        actor_user_id=recruiter_user.id,
        actor_email=recruiter_user.email,
        actor_role=recruiter_user.rol,
    )

    assert res["total_filas"] == 3
    assert res["total_rojos"] >= 1  # 76128709 is duplicate
    assert res["total_alumni"] >= 1  # 46753314 is alumni
    assert res["total_verdes"] >= 1  # 88771122 is clean

    items = res["items"]
    # First item is red
    assert items[0]["color_semaforo"] == "Rojo"
    assert items[0]["categoria"] == "Rojo_Duplicado_Activo"

    # Second item has Boomerang alert
    assert items[1]["is_alumni"] is True
    assert items[1]["bloquear_comision"] is True

    # Third item is green
    assert items[2]["color_semaforo"] == "Verde"
    assert items[2]["categoria"] == "Verde_Limpio"


def test_adecco_atomic_batch_import(adecco_service, recruiter_user):
    clean_items = [
        {
            "documento": "55443322",
            "nombres": "Marcos Diaz Lopez",
            "telefono": "988112233",
            "email": "marcos.diaz@gmail.com",
            "perfil": "Java Specialist",
            "is_alumni": False,
        },
        {
            "documento": "66554433",
            "nombres": "Elena Gomez Morales",
            "telefono": "977223344",
            "email": "elena.gomez@gmail.com",
            "perfil": "React Developer",
            "is_alumni": False,
        },
    ]

    imported = adecco_service.import_clean_candidates(
        lote_id="lot-test-001",
        items_to_import=clean_items,
        actor_user_id=recruiter_user.id,
        actor_email=recruiter_user.email,
        actor_role=recruiter_user.rol,
        cliente_cuenta="BCP",
        rgs_vacante_id="RGS-BCP-001",
        perfil_tecnico="Software Engineer",
    )

    assert imported == 2
    # Verify candidate exists
    cand = adecco_service.candidato_repo.get_by_dni("55443322")
    assert cand is not None
    assert cand.nombres == "Marcos"
    assert cand.apellido_paterno == "Diaz"


def test_adecco_atomic_rollback_on_failure(adecco_service, recruiter_user, sample_candidate):
    # Attempting to import an item that causes an unhandled conflict
    failing_items = [
        {
            "documento": "99001122",
            "nombres": "Good Candidate",
            "telefono": "944556677",
            "email": "good@test.com",
        },
        {
            # Causes duplicate phone with sample_candidate
            "documento": "99001133",
            "nombres": "Conflict Candidate",
            "telefono": sample_candidate.telefono_e164,
            "email": "conflict@test.com",
        },
    ]

    with pytest.raises(RuntimeError, match="rollback ejecutado"):
        adecco_service.import_clean_candidates(
            lote_id="lot-rollback-test",
            items_to_import=failing_items,
            actor_user_id=recruiter_user.id,
            actor_email=recruiter_user.email,
            actor_role=recruiter_user.rol,
            cliente_cuenta="BCP",
            rgs_vacante_id="RGS-002",
            perfil_tecnico="Dev",
        )

    # First candidate must NOT be persisted due to atomic rollback
    cand1 = adecco_service.candidato_repo.get_by_dni("99001122")
    assert cand1 is None
