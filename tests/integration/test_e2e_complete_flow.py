"""End-to-end integration test validating the complete ATS TCS Peru recruitment system from start to finish."""
import pytest
from datetime import date, datetime, timezone
import io
import openpyxl
from pathlib import Path
from unittest.mock import patch
import uuid

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
from src.services.rgs_normalizer_service import RGSNormalizerService
from src.services.cooling_pool_service import CoolingPoolService
from src.services.fit_gap_service import FitGapService
from src.services.cheat_sheet_service import CheatSheetService
from src.services.salary_radar_service import SalaryRadarService
from src.services.commute_matrix import evaluate_commute
from src.adapters.reporting.one_pager_builder import OnePagerBuilder
from src.adapters.identity.apisperu_adapter import APIsPeruDNIAdapter
from src.adapters.persistence.repositories.user_repository import UserRepository
from src.adapters.persistence.repositories.audit_repository import AuditRepository
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.alumni_repository import AlumniRepository
from src.adapters.persistence.repositories.adecco_repository import AdeccoRepository
from src.adapters.persistence.models import BitacoraAuditoriaModel, HistorialAlumniModel


@patch("src.services.rgs_normalizer_service.config.GEMINI_API_KEY", "")
@patch("src.services.fit_gap_service.config.GEMINI_API_KEY", "")
@patch("src.services.cheat_sheet_service.config.GEMINI_API_KEY", "")
def test_complete_end_to_end_talent_acquisition_pipeline(db_session, admin_user):
    """Execute complete 9-stage end-to-end flow with rigorous verification across all layers."""
    # -------------------------------------------------------------------------
    # Setup Repositories & Services
    # -------------------------------------------------------------------------
    user_repo = UserRepository(db_session)
    audit_repo = AuditRepository(db_session)
    cand_repo = CandidatoRepository(db_session)
    post_repo = PostulacionRepository(db_session)
    alumni_repo = AlumniRepository(db_session)
    adecco_repo = AdeccoRepository(db_session)

    audit_svc = AuditService(audit_repo)
    auth_svc = AuthService(user_repo, audit_svc)
    dni_adapter = APIsPeruDNIAdapter(cand_repo)
    alumni_svc = AlumniService(alumni_repo)
    dedup_svc = DeduplicationService(cand_repo)
    cand_svc = CandidateService(cand_repo, dni_adapter, audit_svc, alumni_repo)
    scr_svc = ScreeningService(post_repo, cand_repo, audit_svc)
    ctc_svc = CTCService(post_repo, audit_svc)
    ctc_calc = CTCCalculatorService()
    adecco_svc = AdeccoService(cand_repo, post_repo, adecco_repo, dedup_svc, alumni_svc, audit_svc)
    exclusion_svc = ExclusionReportService(cand_repo, post_repo, adecco_repo, audit_svc)
    rgs_normalizer = RGSNormalizerService()
    fit_gap_svc = FitGapService()
    cheat_sheet_svc = CheatSheetService()
    salary_radar_svc = SalaryRadarService()

    # Pre-seed an alumni record for boomerang testing
    alumni_record = HistorialAlumniModel(
        id="alumni-e2e-001",
        tipo_documento="DNI",
        numero_documento="76128709",
        nombres_completos="DIEGO ALONSO RAMOS QUISPE",
        nombres_normalizado="DIEGO ALONSO RAMOS QUISPE",
        email_corporativo_historico="diego.ramos@tcs.com",
        fecha_ingreso=date(2022, 3, 1),
        fecha_cese=date(2024, 4, 30),
        ultima_cuenta_proyecto="Cuenta Entel",
        motivo_desvinculacion="Mejor oferta salarial",
        estatus_recontratacion="Rehire_Eligible",
    )
    db_session.add(alumni_record)
    db_session.commit()

    # =========================================================================
    # STAGE 0: Authentication, RBAC & Role Elevation
    # =========================================================================
    # 0.1 Register recruiter
    recruiter_reg = auth_svc.register_user(
        nombres_completos="Carmen Rueda Vargas",
        email="carmen.rueda@tcs.com",
        password="Password123!",
    )
    assert recruiter_reg["rol"] == "Compliance_Officer"  # Least-privilege default
    assert recruiter_reg["estado_cuenta"] == "Activa"

    # 0.2 Head of TA elevates recruiter
    recruiter_promoted = auth_svc.change_user_role(
        admin_user_id=admin_user.id,
        target_user_id=recruiter_reg["id"],
        new_role="Senior_Technical_Recruiter",
        justification="Asignación como Lead Recruiter para célula de Banca BCP",
        expected_version=1,
    )
    assert recruiter_promoted["rol"] == "Senior_Technical_Recruiter"

    # 0.3 Authenticate as elevated recruiter
    auth_carmen = auth_svc.authenticate("carmen.rueda@tcs.com", "Password123!")
    carmen_id = auth_carmen["id"]

    # =========================================================================
    # STAGE 1: Unstructured RGS Requirement to Structured JD & Boolean Query
    # =========================================================================
    raw_rgs_text = """
    Hola equipo de reclutamiento TCS,
    Requerimiento URGENTE para cuenta BCP:
    Se solicitan 2 Desarrolladores Java Backend Senior con mínimo 5 años de experiencia.
    Indispensable: Java 17, Spring Boot 3, Microservicios, Kafka y SQL (Oracle o PostgreSQL).
    Deseable: Docker, Kubernetes, AWS.
    Presupuesto máximo de la posición: S/. 9,500 bruto mensual.
    Modalidad híbrida con 2 días en sede La Molina.
    """
    rgs_norm = rgs_normalizer.normalize_raw_text(raw_rgs_text, cliente_sugerido="BCP")
    assert rgs_norm.cliente == "BCP"
    assert "Java" in rgs_norm.titulo_puesto
    assert len(rgs_norm.must_have) >= 3
    assert len(rgs_norm.cadena_booleana_linkedin) > 20

    # Cooling pool search for existing candidates
    cooling_svc = CoolingPoolService(lambda: db_session)
    cooling_matches = cooling_svc.find_reactivable_candidates(
        perfil_tecnico="Desarrollador Java",
        presupuesto_max_bruto=9500.0,
        dias_minimos_enfriamiento=30,
    )
    assert isinstance(cooling_matches, list)

    # =========================================================================
    # STAGE 2: Candidate Intake, DNI Autofill, Age & E.164 Normalization
    # =========================================================================
    # 2.1 DNI Lookup
    dni_info = cand_svc.lookup_dni("76128709")
    assert dni_info["success"] is True
    assert dni_info["datos"]["nombres"] == "DIEGO ALONSO"

    # 2.2 Create Candidate profile
    cand = cand_svc.create_candidate(
        actor_user_id=carmen_id,
        actor_email="carmen.rueda@tcs.com",
        actor_role="Senior_Technical_Recruiter",
        tipo_documento="DNI",
        numero_documento="76128709",
        nombres=dni_info["datos"]["nombres"],
        apellido_paterno=dni_info["datos"]["apellido_paterno"],
        apellido_materno=dni_info["datos"]["apellido_materno"],
        telefono_raw="989322088",
        email="diego.alonso.ramos@gmail.com",
        fecha_nacimiento=date(1995, 4, 12),
        distrito_residencia="Villa María del Triunfo",
    )
    # Check E.164 normalization & dynamic age
    assert cand.telefono_e164 == "+51989322088"
    assert cand.calcular_edad(referencia=date(2026, 9, 10)) == 31  # No 127 years bug

    # Check Boomerang alumni detection
    assert cand.is_tcs_alumni is True
    assert cand.alumni_id == "alumni-e2e-001"

    # 2.3 Create Postulación for BCP vacancy
    postulacion_id = f"pos-e2e-{uuid.uuid4().hex[:8]}"
    postulacion = post_repo.create_postulacion(
        postulacion_id=postulacion_id,
        candidato_id=cand.id,
        cliente_cuenta="BCP",
        rgs_vacante_id=rgs_norm.rgs_id,
        perfil_tecnico=rgs_norm.titulo_puesto,
        reclutador_asignado_id=carmen_id,
        fuente_origen="LinkedIn_Oficial",
        trimestre_fiscal="FY27-Q2",
        created_by_user_id=carmen_id,
    )
    assert postulacion.id is not None
    assert postulacion.estado_embudo == "Nuevo"

    # 2.4 Fit & Gap Analysis
    fit_res = fit_gap_svc.compare_cv_vs_rgs(
        cv_text="Desarrollador Java Senior con 6 años de experiencia en Java 17, Spring Boot 3, Microservicios, Kafka, SQL, Oracle, PostgreSQL, Docker, Kubernetes y AWS.",
        cv_skills=[
            {"nombre": "Java"},
            {"nombre": "Spring Boot"},
            {"nombre": "Microservicios"},
            {"nombre": "Kafka"},
            {"nombre": "SQL"},
            {"nombre": "Oracle"},
            {"nombre": "PostgreSQL"},
            {"nombre": "Docker"},
            {"nombre": "Kubernetes"},
            {"nombre": "AWS"},
        ],
        perfil_puesto=rgs_norm.titulo_puesto,
        must_have=rgs_norm.must_have,
        nice_to_have=rgs_norm.nice_to_have,
    )
    assert fit_res.score_porcentaje >= 80.0

    # =========================================================================
    # STAGE 3: Human-in-the-Loop Phone Screening (7 Dimensions) & One-Pager
    # =========================================================================
    # 3.1 Recruiter Cheat Sheet
    cheat_sheet = cheat_sheet_svc.generate_cheat_sheet(
        postulacion_id=postulacion.id,
        perfil_puesto=postulacion.perfil_tecnico,
    )
    assert len(cheat_sheet.preguntas) >= 3

    # 3.2 Commute Matrix Evaluation
    dictamen_commute, nota_commute = evaluate_commute(
        residence_district="Villa María del Triunfo",
        client_or_workplace="La Molina",
    )
    assert dictamen_commute == "Alerta_Distancia_Critica"

    # 3.3 Register 7-Dimension Screening
    screening = scr_svc.record_screening_call(
        evaluador_user_id=carmen_id,
        evaluador_email="carmen.rueda@tcs.com",
        evaluador_role="Senior_Technical_Recruiter",
        postulacion_id=postulacion.id,
        dim1_disponibilidad="2_semanas",
        dim2_resumen_tecnico="Experto en Java 17, Spring Boot y Kafka. Arquitectura limpia.",
        dim3_expectativa_declarada=8500.0,
        dim4_interes_vacante="Alto",
        dim5_modalidad_aceptada="Híbrido",
        dim7_impresion_general="Excelente solvencia técnica y disponibilidad para guardias.",
        dictamen_humano="Avanza_Entrevista_Tecnica",
    )
    assert screening.dictamen_humano == "Avanza_Entrevista_Tecnica"

    # Postulación funnel transitioned automatically to Pendiente_Entrevistas
    post_updated = post_repo.get_by_id(postulacion.id)
    assert post_updated.estado_embudo == "Pendiente_Entrevistas"

    # 3.4 Generate Executive One-Pager for BCP client
    one_pager_html = OnePagerBuilder.build_html(
        candidato_nombre=cand.nombres_completos,
        dni_masked="7612****",
        perfil_puesto=postulacion.perfil_tecnico,
        cliente=postulacion.cliente_cuenta,
        anios_experiencia=6.0,
        distrito=cand.distrito_residencia,
        modalidad="Híbrido",
        skills=["Java 17", "Spring Boot 3", "Kafka", "Docker"],
        resumen_tecnico=screening.dim2_resumen_tecnico,
        disponibilidad="2 semanas",
        expectativa_salarial=8500.0,
        bgc_status="Aprobado",
        evaluador_nombre="Carmen Rueda Vargas",
        dictamen_humano="Avanza a Entrevista Técnica Cliente",
        alumni_tcs=True,
        fit_score=fit_res.score_porcentaje,
    )
    assert "<!DOCTYPE html>" in one_pager_html
    assert "Carmen Rueda Vargas" in one_pager_html
    assert "BCP" in one_pager_html

    # =========================================================================
    # STAGE 4: CTC Financial Simulator (Factor 1.56) & Salary Radar
    # =========================================================================
    # 4.1 CTC calculation
    calc_res = ctc_calc.calculate(
        tipo_expectativa="Bruto",
        monto_declarado=8500.0,
        ctc_presupuestado=15000.0,  # Role CTC budget
        factor_ctc=1.56,
    )
    # CTC Solicitado: 8500 * 1.56 = 13260. Budget: 15000 -> Within budget (-11.6%)
    assert calc_res["ctc_solicitado"] == 13260.0
    assert calc_res["semaforo_presupuestal"] == "Dentro_Presupuesto"
    assert calc_res["requiere_aprobacion"] is False

    # Persist financial evaluation in database
    ctc_eval = ctc_svc.evaluate_and_persist_ctc(
        actor_user_id=carmen_id,
        actor_email="carmen.rueda@tcs.com",
        actor_role="Senior_Technical_Recruiter",
        postulacion_id=postulacion.id,
        tipo_expectativa="Bruto",
        monto_declarado=8500.0,
        ctc_presupuestado=15000.0,
    )
    assert ctc_eval.ctc_solicitado == 13260.0
    assert ctc_eval.semaforo_presupuestal == "Dentro_Presupuesto"

    # 4.2 Salary Radar Benchmarking
    radar = salary_radar_svc.evaluate_salary(
        perfil_puesto="Desarrollador Java",
        salario_pretendido=8500.0,
        seniority="Senior",
    )
    assert radar.p25 == 7500.0
    assert radar.p50 == 9500.0

    # =========================================================================
    # STAGE 5: Mass Adecco Spreadsheet Intake & Traffic Light Semaphores
    # =========================================================================
    # Process existing calibrated sample: data/Adecco_Semana_37.xlsx
    excel_path = Path("data/Adecco_Semana_37.xlsx")
    assert excel_path.exists()
    excel_bytes = excel_path.read_bytes()

    eval_result = adecco_svc.evaluate_spreadsheet(
        file_bytes=excel_bytes,
        filename="Adecco_Semana_37.xlsx",
        actor_user_id=carmen_id,
        actor_email="carmen.rueda@tcs.com",
        actor_role="Senior_Technical_Recruiter",
    )
    assert eval_result["total_filas"] == 20
    assert eval_result["total_rojos"] >= 1
    assert eval_result["total_verdes"] >= 1
    assert eval_result["total_alumni"] >= 1

    # Atomic import of clean candidates
    verdes_items = [it for it in eval_result["items"] if it["color_semaforo"] == "Verde"]
    imported_count = adecco_svc.import_clean_candidates(
        lote_id=eval_result["lote_id"],
        items_to_import=verdes_items,
        actor_user_id=carmen_id,
        actor_email="carmen.rueda@tcs.com",
        actor_role="Senior_Technical_Recruiter",
        cliente_cuenta="BCP",
        rgs_vacante_id=rgs_norm.rgs_id,
        perfil_tecnico=rgs_norm.titulo_puesto,
    )
    assert imported_count == eval_result["total_verdes"]

    # =========================================================================
    # STAGE 6: On-Demand Adecco Exclusion Report under Ley N° 29733
    # =========================================================================
    report_gen = exclusion_svc.generate_exclusion_report(
        actor_user_id=carmen_id,
        actor_email="carmen.rueda@tcs.com",
        actor_role="Senior_Technical_Recruiter",
        cliente_cuenta="BCP",
        periodo_vigencia_dias=180,
    )
    assert report_gen["total_registros"] >= 1
    assert len(report_gen["excel_bytes"]) > 0

    # Verify strict 5 columns and 0.00% privacy leakage
    wb = openpyxl.load_workbook(io.BytesIO(report_gen["excel_bytes"]))
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    assert headers == [
        "DNI",
        "Nombres y Apellidos",
        "Perfil",
        "Vigencia de Exclusión",
        "Estado",
    ]
    # Check that forbidden keywords are 0.00% present in headers
    headers_str = " ".join(headers).lower()
    for forbidden in ["teléfono", "telefono", "movil", "correo", "email", "salario", "tarifa"]:
        assert forbidden not in headers_str

    # =========================================================================
    # STAGE 7: Boomerang Alumni Protection against Agency Double-Billing
    # =========================================================================
    alumni_check = alumni_svc.detect_alumni(
        dni="76128709",
        email="diego.ramos@tcs.com",
    )
    assert alumni_check["is_alumni"] is True
    assert alumni_check["estatus_recontratacion"] == "Rehire_Eligible"
    assert alumni_check["ultima_cuenta_proyecto"] == "Cuenta Entel"

    # =========================================================================
    # STAGE 8: Immutable Audit Verification across Entire Journey
    # =========================================================================
    # Verify audit logs in database
    audit_logs = db_session.query(BitacoraAuditoriaModel).all()
    assert len(audit_logs) >= 5

    # Check key audit actions occurred
    acciones = [log.tipo_accion for log in audit_logs]
    assert "Autenticacion" in acciones
    assert "Modificacion_Rol" in acciones
    assert "Creacion" in acciones
    assert "Exportacion" in acciones
    assert "Carga_Archivo" in acciones

    # Verify all audit rows have immutable timestamps and actor tracking
    for log in audit_logs:
        assert log.usuario_email is not None
        assert log.rol_en_momento is not None
        assert log.timestamp is not None
