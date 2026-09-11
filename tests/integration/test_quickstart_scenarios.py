"""Validation tests for the 6 sequential quickstart scenarios from quickstart.md."""
import pytest
from datetime import date, datetime, timezone
import io
import openpyxl

from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.services.candidate_service import CandidateService
from src.services.screening_service import ScreeningService
from src.services.ctc_service import CTCService
from src.services.ctc_calculator_service import CTCCalculatorService
from src.services.adecco_service import AdeccoService
from src.services.deduplication_service import DeduplicationService
from src.services.alumni_service import AlumniService
from src.services.exclusion_report_service import ExclusionReportService
from src.adapters.identity.apisperu_adapter import APIsPeruDNIAdapter
from src.adapters.persistence.repositories.user_repository import UserRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.adapters.persistence.repositories.adecco_repository import AdeccoRepository
from src.domain.exceptions import InsufficientPermissionsError


def test_quickstart_scenarios_1_to_6(db_session, admin_user):
    # Prepare Repositories and Services
    user_repo = UserRepository(db_session)
    audit_repo = AuditRepository(db_session)
    cand_repo = CandidatoRepository(db_session)
    post_repo = PostulacionRepository(db_session)
    alumni_repo = AlumniRepository(db_session)
    adecco_repo = AdeccoRepository(db_session)

    audit_svc = AuditService(audit_repo)
    auth_svc = AuthService(user_repo, audit_svc)
    dni_adapter = APIsPeruDNIAdapter(cand_repo)
    cand_svc = CandidateService(cand_repo, dni_adapter, audit_svc, alumni_repo)
    scr_svc = ScreeningService(post_repo, cand_repo, audit_svc)
    ctc_svc = CTCService(post_repo, audit_svc)
    dedup_svc = DeduplicationService(cand_repo)
    alumni_svc = AlumniService(alumni_repo)
    adecco_svc = AdeccoService(cand_repo, post_repo, adecco_repo, dedup_svc, alumni_svc, audit_svc)
    exclusion_svc = ExclusionReportService(cand_repo, post_repo, adecco_repo, audit_svc)

    # -------------------------------------------------------------------------
    # Scenario 1: Authentication, RBAC and Default Least-Privilege Role (US6)
    # -------------------------------------------------------------------------
    # 1.1 - 1.3 Register Carla Soto
    reg = auth_svc.register_user(
        nombres_completos="Carla Soto Mendoza",
        email="carla.soto@tcs.com",
        password="Password123!",
    )
    assert reg["rol"] == "Compliance_Officer"
    assert reg["estado_cuenta"] == "Activa"

    # 1.4 Login
    login_carla = auth_svc.authenticate("carla.soto@tcs.com", "Password123!")
    assert login_carla["rol"] == "Compliance_Officer"

    # 1.6 - 1.7 Elevate role to Senior_Technical_Recruiter by Head of TA
    elevated = auth_svc.change_user_role(
        admin_user_id=admin_user.id,
        target_user_id=login_carla["id"],
        new_role="Senior_Technical_Recruiter",
        justification="Asignación a célula de selección de banca BCP",
        expected_version=login_carla["record_version"],
    )
    assert elevated["rol"] == "Senior_Technical_Recruiter"

    # -------------------------------------------------------------------------
    # Scenario 2: Candidate Registration, DNI Autofill & E.164 (US1 & US5)
    # -------------------------------------------------------------------------
    # 2.3 Lookup DNI 76128709
    dni_res = cand_svc.lookup_dni("76128709")
    assert dni_res["success"] is True
    assert dni_res["datos"]["nombres"] == "DIEGO ALONSO"

    cand_diego = cand_svc.create_candidate(
        actor_user_id=login_carla["id"],
        actor_email="carla.soto@tcs.com",
        actor_role="Senior_Technical_Recruiter",
        tipo_documento="DNI",
        numero_documento="76128709",
        nombres=dni_res["datos"]["nombres"],
        apellido_paterno=dni_res["datos"]["apellido_paterno"],
        apellido_materno=dni_res["datos"]["apellido_materno"],
        telefono_raw="989322088",
        email="diego.ramos.qs@gmail.com",
        fecha_nacimiento=dni_res["datos"]["fecha_nacimiento"],
        distrito_residencia="Villa María del Triunfo",
    )
    assert cand_diego.telefono_e164 == "+51989322088"
    age = cand_diego.calcular_edad(referencia=date(2026, 9, 10))
    assert age == 31  # Born 1995-04-12 -> 31 years (No 127 years bug)

    # -------------------------------------------------------------------------
    # Scenario 3: Human-in-the-Loop Phone Screening (7 Dimensions) (US1)
    # -------------------------------------------------------------------------
    post_diego = post_repo.create_postulacion(
        postulacion_id="post-diego-bcp",
        candidato_id=cand_diego.id,
        cliente_cuenta="BCP La Molina",
        rgs_vacante_id="RGS-JAVA-BCP-01",
        perfil_tecnico="Senior Java Developer",
        reclutador_asignado_id=login_carla["id"],
        fuente_origen="Adecco",
        trimestre_fiscal="FY27-Q1",
        created_by_user_id=login_carla["id"],
    )

    screening = scr_svc.record_screening_call(
        evaluador_user_id=login_carla["id"],
        evaluador_email="carla.soto@tcs.com",
        evaluador_role="Senior_Technical_Recruiter",
        postulacion_id=post_diego.id,
        dim1_disponibilidad="2_semanas",
        dim2_resumen_tecnico="Fuerte dominio en Java 17, Spring Boot 3, Kafka y arquitecturas de microservicios",
        dim3_expectativa_declarada=6500.0,
        dim4_interes_vacante="Alto",
        dim5_modalidad_aceptada="Híbrido",
        dim7_impresion_general="Excelente articulación técnica y buena disposición para turnos de guardia",
        dictamen_humano="Avanza_Entrevista_Tecnica",
    )
    # VMT to La Molina triggers critical distance alert
    assert screening.dim6_viabilidad_traslado == "Alerta_Distancia_Critica"
    assert "90" in (screening.dim6_alerta_distancia_nota or "")

    # -------------------------------------------------------------------------
    # Scenario 4: CTC 1.56 Financial Simulator with Division-by-Zero Guard (US4)
    # -------------------------------------------------------------------------
    calc_svc = CTCCalculatorService()
    # 4.2 Gross salary test
    res_gross = calc_svc.calculate("Bruto", 5000.0, 10000.0)
    assert res_gross["salario_bruto_mensual"] == 5000.0
    assert res_gross["ctc_solicitado"] == 7800.0
    assert res_gross["variacion_porcentual"] == -22.0
    assert res_gross["semaforo_presupuestal"] == "Dentro_Presupuesto"

    # 4.3 Net salary test
    res_net = calc_svc.calculate("Neto", 5000.0, 10000.0)
    assert res_net["salario_bruto_mensual"] == 6329.11
    assert res_net["ctc_solicitado"] == 9873.41
    assert res_net["variacion_porcentual"] == -1.27

    # 4.4 Division-by-zero guard test
    res_zero = calc_svc.calculate("Bruto", 5000.0, 0.0)
    assert res_zero["variacion_porcentual"] is None
    assert res_zero["semaforo_presupuestal"] == "Pendiente_Presupuesto"

    # 4.5 Out of band warning test
    res_high = calc_svc.calculate("Bruto", 9000.0, 10000.0)
    assert res_high["ctc_solicitado"] == 14040.0
    assert res_high["semaforo_presupuestal"] == "Fuera_Banda"
    assert res_high["requiere_aprobacion"] is True

    # -------------------------------------------------------------------------
    # Scenario 5: Mass Adecco Spreadsheet Ingestion (US2)
    # -------------------------------------------------------------------------
    spreadsheet_csv = """DNI / CE,Nombres y Apellidos,Móvil,Puesto,Correo
76128709,Diego Alonso Ramos,989322088,Java Dev,diego@test.com
46753314,Carlos Eduardo Garcia,999111222,Tech Lead,carlos@test.com
77889900,Roberto Carlos Sanchez,988776655,React Dev,roberto@test.com
"""
    eval_batch = adecco_svc.evaluate_spreadsheet(
        file_bytes=spreadsheet_csv.encode("utf-8"),
        filename="adecco_semana_demo.csv",
        actor_user_id=login_carla["id"],
        actor_email="carla.soto@tcs.com",
        actor_role="Senior_Technical_Recruiter",
    )
    assert eval_batch["total_filas"] == 3
    assert eval_batch["total_rojos"] >= 1  # Diego is active in process -> Red
    assert eval_batch["total_alumni"] >= 1  # Carlos Garcia is Alumni TCS -> Boomerang

    # Import clean candidate (Roberto Carlos)
    clean_items = [i for i in eval_batch["items"] if i["color_semaforo"] == "Verde"]
    assert len(clean_items) >= 1
    imported_cnt = adecco_svc.import_clean_candidates(
        lote_id=eval_batch["lote_id"],
        items_to_import=clean_items,
        actor_user_id=login_carla["id"],
        actor_email="carla.soto@tcs.com",
        actor_role="Senior_Technical_Recruiter",
        cliente_cuenta="BCP",
        rgs_vacante_id="RGS-BCP-FRONT",
        perfil_tecnico="Frontend Specialist",
    )
    assert imported_cnt >= 1

    # -------------------------------------------------------------------------
    # Scenario 6: On-Demand Adecco Exclusion Report under Ley 29733 (US3 & US6)
    # -------------------------------------------------------------------------
    rep = exclusion_svc.generate_exclusion_report(
        actor_user_id=login_carla["id"],
        actor_email="carla.soto@tcs.com",
        actor_role="Senior_Technical_Recruiter",
        cliente_cuenta="BCP La Molina",
    )
    assert rep["total_registros"] >= 1
    assert rep["excel_bytes"] is not None

    # Verify exactly 5 columns and censorship in generated excel
    wb = openpyxl.load_workbook(io.BytesIO(rep["excel_bytes"]))
    ws = wb.active
    headers = [c.value for c in ws[1]]
    assert headers == ["DNI", "Nombres y Apellidos", "Perfil", "Vigencia de Exclusión", "Estado"]

    # Check that Carla Soto's export action was audited
    export_logs = audit_svc.filter_logs(tipo_accion="Exportacion")
    assert len(export_logs) >= 1
    assert any(l.usuario_email == "carla.soto@tcs.com" for l in export_logs)
