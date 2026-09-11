"""Unit and resilience tests covering edge cases, immutability, and security."""
import uuid
import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, IntegrityError

from src.adapters.persistence.models import (
    UsuarioModel,
    CandidatoModel,
    PostulacionModel,
    BitacoraAuditoriaModel,
    CacheDNIReniecModel,
)
from src.adapters.persistence.ddl import install_immutability_triggers
from src.adapters.persistence.repositories.user_repository import UserRepository
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.adapters.persistence.repositories.adecco_repository import AdeccoRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.security.password_hasher import (
    hash_password,
    verify_password,
    validate_password_complexity,
)
from src.adapters.cv_parser.langchain_extractor import LangChainCVExtractor
from src.adapters.identity.apisperu_adapter import APIsPeruDNIAdapter
from src.adapters.github.github_adapter import GitHubAdapter
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.services.candidate_service import CandidateService
from src.services.ctc_calculator_service import CTCCalculatorService
from src.services.deduplication_service import DeduplicationService
from src.services.commute_matrix import evaluate_commute
from src.services.cheat_sheet_service import CheatSheetService
from src.services.fit_gap_service import FitGapService
from src.services.rgs_normalizer_service import RGSNormalizerService
from src.services.adecco_service import AdeccoService
from src.services.alumni_service import AlumniService
from src.domain.exceptions import (
    OptimisticLockError,
    AuthenticationError,
    AccountLockedError,
    DuplicateEntityError,
    InsufficientPermissionsError,
    FinancialValidationError,
)


def test_audit_trigger_prevents_raw_update_and_delete(db_session, admin_user):
    """Verify that SQLite triggers block direct SQL UPDATE and DELETE on bitacora_auditoria."""
    install_immutability_triggers(db_session.connection())

    # 1. Insert audit row via ORM so all defaults and FKs are cleanly populated
    log = BitacoraAuditoriaModel(
        id=str(uuid.uuid4()),
        usuario_id=admin_user.id,
        usuario_email=admin_user.email,
        rol_en_momento=admin_user.rol,
        tipo_accion="Creacion",
        entidad_objeto="Candidato",
        registro_id="reg-imm-001",
        justificacion_operativa="Asiento inmutable de prueba",
    )
    db_session.add(log)
    db_session.flush()

    # 2. Attempt raw SQL UPDATE -> must fail with SQLite trigger error
    with pytest.raises((OperationalError, IntegrityError)) as exc_update:
        db_session.connection().execute(
            text("UPDATE bitacora_auditoria SET justificacion_operativa = 'MODIFICADO'")
        )
    assert "inmutable" in str(exc_update.value).lower() or "abort" in str(exc_update.value).lower()

    # 3. Attempt raw SQL DELETE -> must fail with SQLite trigger error
    with pytest.raises((OperationalError, IntegrityError)) as exc_delete:
        db_session.connection().execute(
            text("DELETE FROM bitacora_auditoria")
        )
    assert "eliminacion" in str(exc_delete.value).lower() or "inmutable" in str(exc_delete.value).lower()


def test_optimistic_concurrency_control_on_candidate_update(db_session, admin_user, sample_candidate):
    """Verify that updating a candidate with an outdated version raises OptimisticLockError."""
    cand_repo = CandidatoRepository(db_session)

    # Valid update increments version from 1 to 2
    updated = cand_repo.update(
        candidato_id=sample_candidate.id,
        expected_version=1,
        updated_by_user_id=admin_user.id,
        distrito_residencia="Miraflores",
    )
    assert updated.record_version == 2
    assert updated.distrito_residencia == "Miraflores"

    # Conflicting update with stale version 1 -> must fail
    with pytest.raises(OptimisticLockError):
        cand_repo.update(
            candidato_id=sample_candidate.id,
            expected_version=1,  # Stale! Current is 2
            updated_by_user_id=admin_user.id,
            distrito_residencia="San Isidro",
        )


def test_password_hasher_complexity_rules():
    """Verify password rules: min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char."""
    # Valid password
    valid_hash = hash_password("SecurePass123!")
    assert verify_password("SecurePass123!", valid_hash)
    assert not verify_password("WrongPassword123!", valid_hash)

    # Too short (<8 chars)
    with pytest.raises(ValueError, match="8"):
        validate_password_complexity("Pass1!")

    # No uppercase
    with pytest.raises(ValueError, match="may"):
        validate_password_complexity("password123!")

    # No lowercase
    with pytest.raises(ValueError, match="min"):
        validate_password_complexity("PASSWORD123!")

    # No digit
    with pytest.raises(ValueError, match="d.*gito"):
        validate_password_complexity("PasswordSpecial!")

    # No symbol
    with pytest.raises(ValueError, match="especial"):
        validate_password_complexity("Password1234")


def test_auth_lockout_and_admin_unlock(db_session, admin_user):
    """Verify 5 failed login attempts trigger account lock, and admin can unlock."""
    user_repo = UserRepository(db_session)
    audit_repo = AuditRepository(db_session)
    audit_svc = AuditService(audit_repo)
    auth_svc = AuthService(user_repo, audit_svc)

    # Register target user
    user = auth_svc.register_user(
        nombres_completos="Roberto Lockout Test",
        email="roberto.lockout@tcs.com",
        password="Password123!",
    )
    user_id = user["id"]

    # Fail 4 times with wrong password -> still active
    for _ in range(4):
        with pytest.raises(AuthenticationError):
            auth_svc.authenticate("roberto.lockout@tcs.com", "WrongPass123!")
    
    u_state = user_repo.get_by_id(user_id)
    assert u_state.intentos_fallidos == 4
    assert u_state.estado_cuenta == "Activa"

    # 5th failure -> triggers lock
    with pytest.raises(AccountLockedError):
        auth_svc.authenticate("roberto.lockout@tcs.com", "WrongPass123!")

    u_state = user_repo.get_by_id(user_id)
    assert u_state.estado_cuenta == "Bloqueada_Por_Intentos"
    assert u_state.bloqueado_hasta is not None

    # Attempt with correct password while locked -> still blocked
    with pytest.raises(AccountLockedError):
        auth_svc.authenticate("roberto.lockout@tcs.com", "Password123!")

    # Admin unlocks account
    unlocked = auth_svc.unlock_user_account(
        admin_user_id=admin_user.id,
        target_user_id=user_id,
        justification="Desbloqueo tras validación de identidad por TI",
    )
    assert unlocked["estado_cuenta"] == "Activa"
    refreshed_user = user_repo.get_by_id(user_id)
    assert refreshed_user.intentos_fallidos == 0

    # Now login succeeds
    login_succ = auth_svc.authenticate("roberto.lockout@tcs.com", "Password123!")
    assert login_succ["email"] == "roberto.lockout@tcs.com"


def test_apisperu_dni_offline_fallback_and_regularization_queue(db_session, admin_user):
    """Verify that when APIsPERU fails, candidate is flagged for regularization and synced later."""
    cand_repo = CandidatoRepository(db_session)
    audit_repo = AuditRepository(db_session)
    alumni_repo = AlumniRepository(db_session)
    audit_svc = AuditService(audit_repo)

    # DNI adapter mock that fails network connection
    mock_dni_port = MagicMock()
    mock_dni_port.resolve_dni.return_value = {
        "success": False,
        "fuente_origen": "APISPERU_OFFLINE_FALLBACK",
        "mensaje": "Servicio de RENIEC no disponible temporalmente.",
        "estado_identidad": "Pendiente_Regularizacion",
        "regularizacion_pendiente": True,
        "datos": {},
    }

    cand_svc = CandidateService(
        candidato_repository=cand_repo,
        dni_port=mock_dni_port,
        audit_service=audit_svc,
        alumni_repository=alumni_repo,
    )

    # Create candidate under offline conditions
    cand = cand_svc.create_candidate(
        actor_user_id=admin_user.id,
        actor_email=admin_user.email,
        actor_role=admin_user.rol,
        tipo_documento="DNI",
        numero_documento="48192031",
        nombres="JUAN CARLOS",
        apellido_paterno="PEREZ",
        apellido_materno="LOPEZ",
        telefono_raw="998877665",
        email="juan.carlos.offline@gmail.com",
        estado_identidad="Pendiente_Regularizacion",
        regularizacion_pendiente=True,
    )
    assert cand.regularizacion_pendiente is True
    assert cand.estado_identidad == "Pendiente_Regularizacion"

    # Verify candidate appears in pending regularizations
    pending_list = cand_repo.list_pending_regularizations()
    assert any(c.id == cand.id for c in pending_list)

    # Simulate network restored: DNI port now resolves successfully
    mock_dni_port.resolve_dni.return_value = {
        "success": True,
        "fuente_origen": "APISPERU_LIVE_RENIEC",
        "datos": {
            "nombres": "JUAN CARLOS",
            "apellido_paterno": "PEREZ",
            "apellido_materno": "LOPEZ",
            "fecha_nacimiento": date(1992, 8, 15),
            "ubigeo": "150136",
            "distrito": "San Miguel",
        },
    }

    # Process offline regularization queue
    regularized_count = cand_svc.process_pending_regularizations(
        actor_user_id=admin_user.id,
        actor_email=admin_user.email,
        actor_role=admin_user.rol,
    )
    assert regularized_count >= 1

    # Verify candidate identity is now officially validated
    cand_updated = cand_repo.get_by_id(cand.id)
    assert cand_updated.regularizacion_pendiente is False
    assert cand_updated.estado_identidad == "Validado_Oficialmente"
    assert cand_updated.distrito_residencia == "San Miguel"
    assert cand_updated.fecha_nacimiento == date(1992, 8, 15)


def test_ctc_calculator_mathematical_edge_cases():
    """Verify CTC calculation handles zero, negative, and extreme values gracefully."""
    calc = CTCCalculatorService()

    # Budget is zero -> must NOT raise ZeroDivisionError
    res_zero_budget = calc.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=6000.0,
        ctc_presupuestado=0.0,
    )
    assert res_zero_budget["variacion_porcentual"] is None
    assert res_zero_budget["semaforo_presupuestal"] == "Pendiente_Presupuesto"
    assert res_zero_budget["ctc_solicitado"] == 6000.0 * 1.56

    # Budget is None
    res_none_budget = calc.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=6000.0,
        ctc_presupuestado=None,
    )
    assert res_none_budget["variacion_porcentual"] is None
    assert res_none_budget["semaforo_presupuestal"] == "Pendiente_Presupuesto"

    # Within budget
    res_within = calc.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=5000.0,
        ctc_presupuestado=10000.0,
    )
    assert res_within["semaforo_presupuestal"] == "Dentro_Presupuesto"
    assert res_within["requiere_aprobacion"] is False
    assert res_within["variacion_porcentual"] < 0

    # Out of band (CTC > 15% above budget)
    res_out = calc.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=9000.0,
        ctc_presupuestado=10000.0,
    )
    # CTC = 9000 * 1.56 = 14040. Var = (14040 - 10000) / 10000 = +40.4%
    assert res_out["semaforo_presupuestal"] == "Fuera_Banda"
    assert res_out["requiere_aprobacion"] is True

    # Net to Gross calculation
    res_neto = calc.calculate(
        tipo_expectativa="Neto",
        monto_declarado=5000.0,
        ctc_presupuestado=12000.0,
    )
    # Bruto = 5000 / 0.79 = 6329.11, CTC = 6329.11 * 1.56 = 9873.42
    assert abs(res_neto["salario_bruto_mensual"] - 6329.11) < 0.1
    assert abs(res_neto["ctc_solicitado"] - 9873.42) < 0.2

    # Negative declared salary -> ValueError
    with pytest.raises(ValueError, match="positivo"):
        calc.calculate(tipo_expectativa="Bruto", monto_declarado=-100.0)


def test_deduplication_fuzzy_and_phonetic_boundaries(db_session, admin_user):
    """Verify deduplication detects exact and phonetic duplicates under edge conditions."""
    cand_repo = CandidatoRepository(db_session)
    dedup_svc = DeduplicationService(cand_repo)

    # Persist base candidate
    cand_base = CandidatoModel(
        id="cand-dedup-base",
        tipo_documento="DNI",
        numero_documento="71234567",
        nombres="CRISTHIAN DANIEL",
        apellido_paterno="UCEDA",
        apellido_materno="RENTERIA",
        nombres_completos_normalizado="CRISTHIAN DANIEL UCEDA RENTERIA",
        telefono_e164="+51999111222",
        email="cristhian.uceda@gmail.com",
        created_by_user_id=admin_user.id,
    )
    db_session.add(cand_base)
    db_session.commit()

    # Exact DNI match -> Score 100
    m_dni = dedup_svc.check_duplicate(dni="71234567")
    assert m_dni["is_duplicate"] is True
    assert m_dni["matched_field"] == "DNI"

    # Exact Email match -> Score 100
    m_email = dedup_svc.check_duplicate(email="cristhian.uceda@gmail.com")
    assert m_email["is_duplicate"] is True
    assert m_email["matched_field"] == "Email"

    # Exact Phone match -> Score 100
    m_phone = dedup_svc.check_duplicate(telefono="+51999111222")
    assert m_phone["is_duplicate"] is True
    assert m_phone["matched_field"] == "Telefono"

    # Fuzzy name match with typo: "Christian Daniel Uceda Renteria"
    m_fuzzy = dedup_svc.check_duplicate(nombre_completo="Christian Daniel Uceda Renteria")
    assert m_fuzzy["is_duplicate"] is True
    assert m_fuzzy["similarity_score"] >= 85.0

    # Completely different name -> No duplicate
    m_diff = dedup_svc.check_duplicate(nombre_completo="Mariana Alexandra Flores Gutierrez")
    assert m_diff["is_duplicate"] is False


def test_github_adapter_error_and_edge_handling():
    """Verify GitHub adapter handles HTTP 404, rate limits and malformed URLs."""
    adapter = GitHubAdapter()

    # Malformed URL
    bad_res = adapter.audit_user("")
    assert bad_res.actividad_verificada is False

    # Mock 404 Not Found
    with patch("requests.get") as mock_get:
        mock_404 = MagicMock(status_code=404)
        mock_get.return_value = mock_404
        res_404 = adapter.audit_user("https://github.com/non_existent_dev_404_tcs")
        assert res_404.existe is False
        assert "no encontrado" in res_404.resumen_actividad.lower()

    # Mock Rate Limit 403
    with patch("requests.get") as mock_get:
        mock_403 = MagicMock(status_code=403)
        mock_get.return_value = mock_403
        res_403 = adapter.audit_user("https://github.com/ratelimited_user")
        assert res_403.existe is False


def test_commute_matrix_boundary_evaluations():
    """Verify commute matrix categorizes distances and handles unknown districts."""
    # Near residence
    dictamen_near, nota_near = evaluate_commute(
        residence_district="San Isidro",
        client_or_workplace="Miraflores",
    )
    assert dictamen_near in ["Viable_Cercano", "Viable_Con_Conmutacion"]

    # Critical distance (>90 min)
    dictamen_crit, nota_crit = evaluate_commute(
        residence_district="Villa María del Triunfo",
        client_or_workplace="La Molina",
    )
    assert dictamen_crit == "Alerta_Distancia_Critica"
    assert "Alerta Crítica" in nota_crit or "Alerta" in nota_crit

    # Unknown or empty district -> fallback
    dictamen_unknown, _ = evaluate_commute(
        residence_district="Distrito Desconocido",
        client_or_workplace="La Molina",
    )
    assert dictamen_unknown in ["Viable_Con_Conmutacion", "Alerta_Distancia_Critica", "Viable_Cercano"]


@patch("src.services.fit_gap_service.config.GEMINI_API_KEY", "")
def test_fit_gap_service_score_permutations():
    """Verify Fit & Gap service generates expected scores across coverage levels."""
    svc = FitGapService()

    # 100% Match
    res_full = svc.compare_cv_vs_rgs(
        cv_text="Experto en Java, Spring Boot, Microservicios, Docker, AWS y Kafka con 7 años de experiencia.",
        cv_skills=[{"nombre": "Java"}, {"nombre": "Spring Boot"}, {"nombre": "Microservicios"}, {"nombre": "Docker"}],
        perfil_puesto="Desarrollador Java Senior",
        must_have=["Java", "Spring Boot", "Microservicios"],
        nice_to_have=["Docker", "AWS", "Kafka"],
    )
    assert res_full.score_porcentaje >= 75.0

    # 0% Match
    res_zero = svc.compare_cv_vs_rgs(
        cv_text="Especialista en Marketing Digital, SEO, SEM y Redes Sociales.",
        cv_skills=[{"nombre": "SEO"}, {"nombre": "Marketing"}],
        perfil_puesto="Desarrollador Java Senior",
        must_have=["Java", "Spring Boot", "Kafka"],
        nice_to_have=["Docker", "Kubernetes"],
    )
    assert res_zero.score_porcentaje < 40.0
    assert len(res_zero.gaps_criticos) > 0


def test_langchain_cv_extractor_multi_provider_fallbacks():
    """Verify LangChain extractor attempts Gemini/Grok and cleanly falls back to heuristic."""
    # Test with no API keys -> uses heuristic fallback directly
    with patch("src.adapters.cv_parser.langchain_extractor.config.GEMINI_API_KEY", ""):
        with patch("src.adapters.cv_parser.langchain_extractor.config.GROK_API_KEY", ""):
            extractor = LangChainCVExtractor()
            sample_pdf_text = b"%PDF-1.4 sample content"
            with patch.object(extractor.fallback, "extract_from_pdf", return_value={"seniority_estimado": "Junior"}):
                res = extractor.extract_from_pdf(sample_pdf_text)
                assert res["seniority_estimado"] == "Junior"
