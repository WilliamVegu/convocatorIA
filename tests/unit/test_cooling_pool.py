"""Unit tests for Cooling Pool Candidate Reactivation service."""
import uuid
from datetime import datetime, timezone, timedelta
from src.services.cooling_pool_service import CoolingPoolService
from src.adapters.persistence.models import CandidatoModel, PostulacionModel


def test_cooling_pool_service_reactivation(db_session):
    cand_id = f"cand-{uuid.uuid4().hex[:8]}"
    post_id = f"post-{uuid.uuid4().hex[:8]}"
    created_past = datetime.now(timezone.utc) - timedelta(days=120)

    c = CandidatoModel(
        id=cand_id,
        tipo_documento="DNI",
        numero_documento="77665544",
        nombres="Candidato Enfriado",
        apellido_paterno="Test",
        apellido_materno="",
        nombres_completos_normalizado="CANDIDATO ENFRIADO TEST",
        email="enfriado@test.com",
        telefono_e164="+51999888777",
        cv_resumen_tecnico="Desarrollador Java con Spring Boot",
        created_by_user_id="usr-admin-bootstrap-001",
    )
    db_session.add(c)

    p = PostulacionModel(
        id=post_id,
        candidato_id=cand_id,
        cliente_cuenta="BCP",
        rgs_vacante_id="RGS-BCP-001",
        perfil_tecnico="Desarrollador Java Senior",
        reclutador_asignado_id="usr-admin-bootstrap-001",
        fuente_origen="Bolsa_Web",
        trimestre_fiscal="2026-Q1",
        estado_embudo="Descartado_Economico",
        motivo_cierre_tipo="Temporal_No_Excluyente",
        observaciones="Pretensión: 7500 soles",
        created_by_user_id="usr-admin-bootstrap-001",
        created_at=created_past,
    )
    db_session.add(p)
    db_session.commit()

    class MockSessionFactory:
        def __call__(self):
            return db_session

    svc = CoolingPoolService(MockSessionFactory())
    reactivables = svc.find_reactivable_candidates(
        perfil_tecnico="Desarrollador Java",
        presupuesto_max_bruto=8500.0,
        dias_minimos_enfriamiento=90,
    )

    assert len(reactivables) >= 1
    item = next(r for r in reactivables if r["candidato_id"] == cand_id)
    assert item["nombres_completos"] == "Candidato Enfriado Test"
    assert "BCP" in item["cliente_anterior"]
    assert item["salario_registrado"] == 7500.0
