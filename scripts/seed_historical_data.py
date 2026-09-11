"""Historical data seeder script representing 'BD GENERAL FY27' (>100 candidates)."""
from __future__ import annotations

import json
import os
import random
import uuid
import sys
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.adapters.persistence.database import init_db, SessionLocal
from src.adapters.persistence.seed import seed_database, BOOTSTRAP_ADMIN_ID
from src.adapters.persistence.models import (
    UsuarioModel,
    CandidatoModel,
    PostulacionModel,
    ScreeningModel,
    EvaluacionCTCModel,
    HistorialAlumniModel,
    CacheDNIReniecModel,
    BitacoraAuditoriaModel,
)
from src.services.candidate_service import normalize_full_name

# Specific DNIs for Adecco Semana 37 calibration
RED_ACTIVE_DNIS = [
    ("76128709", "DIEGO ALONSO", "RAMOS", "QUISPE", "989322088", "diego.ramos@gmail.com", "BCP", "Desarrollador Java Senior", "Screening_Telefonico"),
    ("45892134", "JORGE LUIS", "CHAVEZ", "PINTO", "987654321", "jorge.chavez@gmail.com", "BBVA", "Cloud Architect", "Pendiente_Entrevistas"),
    ("71984512", "VALERIA BEATRIZ", "FLORES", "RODRIGUEZ", "976543210", "valeria.flores@gmail.com", "Interbank", "Full Stack Developer", "Entrevista_Cliente"),
    ("70812390", "MIGUEL ANGEL", "TORRES", "HUAMAN", "965432109", "miguel.torres@gmail.com", "Entel", "QA Automation", "Oferta_Economica"),
    ("47589623", "PATRICIA ELENA", "VARGAS", "DELGADO", "954321098", "patricia.vargas@gmail.com", "Falabella", "Scrum Master", "Contratado"),
    ("73412589", "RENZO PAOLO", "CASTILLO", "MORALES", "943210987", "renzo.castillo@gmail.com", "Rimac", "Backend Python Developer", "Descartado_Tecnico"),
    ("48912345", "MONICA BEATRIZ", "ROJAS", "SOTO", "932109876", "monica.rojas@gmail.com", "BCP", "Frontend Angular Specialist", "Descartado_Tecnico"),
]

YELLOW_REACTIVABLE_DNIS = [
    ("74890123", "SEBASTIAN ANDRES", "LOPEZ", "HERRERA", "921098765", "sebastian.lopez@gmail.com", "Interbank", "Mobile Developer Flutter", 210),
    ("43981276", "LUCIA ESPERANZA", "BENITEZ", "NAVARRO", "910987654", "lucia.benitez@gmail.com", "BBVA", "Security Engineer", 240),
    ("75619283", "GONZALO MARTIN", "PALACIOS", "VEGA", "909876543", "gonzalo.palacios@gmail.com", "Falabella", "Data Analyst", 280),
]

ALUMNI_SPECIFIC = [
    ("46753314", "CARLOS EDUARDO GARCIA SANCHEZ", "carlos.garcia1@tcs.com", "BCP Home Banking", date(2021, 3, 1), date(2024, 5, 30), "Rehire_Eligible", "Renuncia Voluntaria - Mejor Oferta"),
    ("41239876", "RAUL FERNANDO MUNOZ ARIAS", "raul.munoz@tcs.com", "Interbank Plin", date(2019, 8, 1), date(2023, 11, 15), "Rehire_Eligible", "Fin de Proyecto"),
    ("42345678", "MANUEL ALBERTO PAREDES MEZA", "manuel.paredes@tcs.com", "Banco Falabella Core", date(2020, 1, 15), date(2023, 8, 15), "Do_Not_Rehire", "Despido con Causa - Falta Grave de Seguridad"),
]

PERUVIAN_FIRST_NAMES = [
    "Alonso", "Andrea", "Arturo", "Bruno", "Cesar", "Claudia", "Daniel", "Diana", "Eduardo", "Enrique",
    "Esteban", "Fabiana", "Fernando", "Fiorella", "Gabriel", "Gisella", "Gustavo", "Helena", "Ignacio", "Isabel",
    "Javier", "Jessica", "Jose", "Juan", "Julio", "Karina", "Leonardo", "Lorena", "Luis", "Manuel",
    "Maria", "Mario", "Martin", "Milagros", "Natalia", "Omar", "Oscar", "Paola", "Rafael", "Rodrigo",
    "Rosa", "Sandra", "Santiago", "Silvia", "Tatiana", "Victor", "Walter", "Ximena", "Yolanda", "Zarela"
]

PERUVIAN_LAST_NAMES = [
    "Alvarado", "Barrientos", "Cabrera", "Duran", "Espinoza", "Figueroa", "Gutierrez", "Hidalgo", "Ibanez", "Juarez",
    "Lozano", "Mamani", "Navarrete", "Ortega", "Peralta", "Quintana", "Ramirez", "Salazar", "Tapia", "Ugarte",
    "Valdivia", "Yanez", "Zambrano", "Acosta", "Becerra", "Carrasco", "Delgado", "Escalante", "Farfan", "Guevara",
    "Herrera", "Jauregui", "Lara", "Medina", "Noriega", "Ochoa", "Paredes", "Quispe", "Rivas", "Silva",
    "Toledo", "Urbina", "Villanueva", "Zapata", "Aliaga", "Bustamante", "Cornejo", "Diaz", "Enciso", "Fuentes"
]

CLIENTES = ["BCP", "BBVA", "Interbank", "Entel", "Falabella", "Rimac", "TCS Internal"]
PERFILES = [
    "Desarrollador Java Senior", "Data Engineer", "DevOps Specialist", "Full Stack Developer",
    "Cloud Architect", "QA Automation", "Scrum Master", "Frontend Angular Specialist",
    "Mobile Flutter Developer", "Backend Python Developer"
]
DISTRITOS = [
    "Santiago de Surco", "San Borja", "Miraflores", "San Isidro", "La Molina", "Magdalena del Mar",
    "Pueblo Libre", "Jesús María", "Lince", "San Miguel", "Los Olivos", "San Martín de Porres"
]


def seed_historical_pool(total_target: int = 120) -> None:
    """Populate database with >100 historical candidate profiles and applications."""
    init_db()
    with SessionLocal() as db:
        seed_database(db)

        # 1. Load demo_personas.json into cache_dni_reniec
        personas_file = Path(__file__).parent.parent / "data" / "demo_personas.json"
        if personas_file.exists():
            with open(personas_file, "r", encoding="utf-8") as f:
                personas = json.load(f)
                for p in personas:
                    exists_cache = db.query(CacheDNIReniecModel).filter_by(dni=p["dni"]).first()
                    if not exists_cache:
                        c_entry = CacheDNIReniecModel(
                            dni=p["dni"],
                            nombres=p["nombres"],
                            apellido_paterno=p["apellido_paterno"],
                            apellido_materno=p["apellido_materno"],
                            fecha_nacimiento=date.fromisoformat(p["fecha_nacimiento"]),
                            ubigeo=p["ubigeo"],
                            distrito=p["distrito"],
                            direccion=p.get("direccion", ""),
                        )
                        db.add(c_entry)
            db.commit()

        # 2. Add specific Alumni
        for dni, names, email, proj, f_ing, f_ces, estatus, motivo in ALUMNI_SPECIFIC:
            exists_alm = db.query(HistorialAlumniModel).filter_by(numero_documento=dni).first()
            if not exists_alm:
                alm = HistorialAlumniModel(
                    id=f"alm-{uuid.uuid4()}",
                    tipo_documento="DNI",
                    numero_documento=dni,
                    nombres_completos=names,
                    nombres_normalizado=normalize_full_name(names),
                    email_corporativo_historico=email,
                    fecha_ingreso=f_ing,
                    fecha_cese=f_ces,
                    ultima_cuenta_proyecto=proj,
                    motivo_desvinculacion=motivo,
                    estatus_recontratacion=estatus,
                )
                db.add(alm)
        db.commit()

        # 3. Add Red Active Candidates
        for dni, nom, pat, mat, tel, email, cli, perf, estado in RED_ACTIVE_DNIS:
            if not db.query(CandidatoModel).filter_by(numero_documento=dni).first():
                c_id = f"cand-{uuid.uuid4()}"
                cand = CandidatoModel(
                    id=c_id,
                    tipo_documento="DNI",
                    numero_documento=dni,
                    nombres=nom,
                    apellido_paterno=pat,
                    apellido_materno=mat,
                    nombres_completos_normalizado=normalize_full_name(f"{nom} {pat} {mat}"),
                    telefono_e164=f"+51{tel}",
                    email=email,
                    fecha_nacimiento=date(1993, 5, 12),
                    distrito_residencia="Santiago de Surco",
                    created_by_user_id=BOOTSTRAP_ADMIN_ID,
                )
                db.add(cand)
                db.flush()

                p_id = f"post-{uuid.uuid4()}"
                descarte_dt = datetime.now(timezone.utc) - timedelta(days=45) if "Descartado" in estado else None
                post = PostulacionModel(
                    id=p_id,
                    candidato_id=c_id,
                    cliente_cuenta=cli,
                    rgs_vacante_id=f"RGS-{cli[:3].upper()}-01",
                    perfil_tecnico=perf,
                    reclutador_asignado_id=BOOTSTRAP_ADMIN_ID,
                    fuente_origen="LinkedIn_Oficial",
                    trimestre_fiscal="FY27-Q1",
                    estado_embudo=estado,
                    fecha_cierre_descarte=descarte_dt,
                    motivo_cierre_tipo="Temporal_No_Excluyente" if "Descartado" in estado else None,
                    created_by_user_id=BOOTSTRAP_ADMIN_ID,
                )
                db.add(post)
        db.commit()

        # 4. Add Yellow Reactivable Candidates (>180 days descarte)
        for dni, nom, pat, mat, tel, email, cli, perf, days_ago in YELLOW_REACTIVABLE_DNIS:
            if not db.query(CandidatoModel).filter_by(numero_documento=dni).first():
                c_id = f"cand-{uuid.uuid4()}"
                cand = CandidatoModel(
                    id=c_id,
                    tipo_documento="DNI",
                    numero_documento=dni,
                    nombres=nom,
                    apellido_paterno=pat,
                    apellido_materno=mat,
                    nombres_completos_normalizado=normalize_full_name(f"{nom} {pat} {mat}"),
                    telefono_e164=f"+51{tel}",
                    email=email,
                    fecha_nacimiento=date(1994, 8, 20),
                    distrito_residencia="San Borja",
                    created_by_user_id=BOOTSTRAP_ADMIN_ID,
                )
                db.add(cand)
                db.flush()

                p_id = f"post-{uuid.uuid4()}"
                descarte_dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
                post = PostulacionModel(
                    id=p_id,
                    candidato_id=c_id,
                    cliente_cuenta=cli,
                    rgs_vacante_id=f"RGS-{cli[:3].upper()}-HIST",
                    perfil_tecnico=perf,
                    reclutador_asignado_id=BOOTSTRAP_ADMIN_ID,
                    fuente_origen="Bolsa_Web",
                    trimestre_fiscal="FY26-Q3",
                    estado_embudo="Descartado_Economico",
                    fecha_cierre_descarte=descarte_dt,
                    motivo_cierre_tipo="Temporal_No_Excluyente",
                    created_by_user_id=BOOTSTRAP_ADMIN_ID,
                )
                db.add(post)
        db.commit()

        # 5. Populate remaining candidates up to total_target (e.g. 120)
        current_count = db.query(CandidatoModel).count()
        needed = total_target - current_count

        random.seed(42)
        estados_pool = [
            "Nuevo", "Screening_Telefonico", "Pendiente_Entrevistas", "Entrevista_Cliente",
            "Oferta_Economica", "Oferta_Aceptada", "Contratado", "Descartado_Tecnico"
        ]

        for i in range(needed):
            dni_num = f"{random.randint(40000000, 79999999)}"
            while db.query(CandidatoModel).filter_by(numero_documento=dni_num).first():
                dni_num = f"{random.randint(40000000, 79999999)}"

            fname = random.choice(PERUVIAN_FIRST_NAMES)
            paterno = random.choice(PERUVIAN_LAST_NAMES)
            materno = random.choice(PERUVIAN_LAST_NAMES)
            phone = f"+519{random.randint(10000000, 99999999)}"
            email_c = f"{fname.lower()}.{paterno.lower()}{i}@mailtest.pe"
            cli = random.choice(CLIENTES)
            perf = random.choice(PERFILES)
            dist = random.choice(DISTRITOS)
            est = random.choice(estados_pool)

            c_id = f"cand-{uuid.uuid4()}"
            cand = CandidatoModel(
                id=c_id,
                tipo_documento="DNI",
                numero_documento=dni_num,
                nombres=fname,
                apellido_paterno=paterno,
                apellido_materno=materno,
                nombres_completos_normalizado=normalize_full_name(f"{fname} {paterno} {materno}"),
                telefono_e164=phone,
                email=email_c,
                fecha_nacimiento=date(random.randint(1985, 2002), random.randint(1, 12), random.randint(1, 28)),
                distrito_residencia=dist,
                created_by_user_id=BOOTSTRAP_ADMIN_ID,
            )
            db.add(cand)
            db.flush()

            p_id = f"post-{uuid.uuid4()}"
            descarte_dt = datetime.now(timezone.utc) - timedelta(days=random.randint(10, 360)) if "Descartado" in est else None
            post = PostulacionModel(
                id=p_id,
                candidato_id=c_id,
                cliente_cuenta=cli,
                rgs_vacante_id=f"RGS-{cli[:3].upper()}-{random.randint(10, 99)}",
                perfil_tecnico=perf,
                reclutador_asignado_id=BOOTSTRAP_ADMIN_ID,
                fuente_origen=random.choice(["LinkedIn_Oficial", "BYB_Referido", "Bolsa_Web", "Adecco"]),
                trimestre_fiscal=random.choice(["FY26-Q4", "FY27-Q1"]),
                estado_embudo=est,
                fecha_cierre_descarte=descarte_dt,
                motivo_cierre_tipo="Temporal_No_Excluyente" if "Descartado" in est else None,
                created_by_user_id=BOOTSTRAP_ADMIN_ID,
            )
            db.add(post)
            db.flush()

            # For candidates in screening or later, add screening and ctc records
            if est in ["Pendiente_Entrevistas", "Entrevista_Cliente", "Oferta_Economica", "Contratado"]:
                scr_id = f"scr-{uuid.uuid4()}"
                scr = ScreeningModel(
                    id=scr_id,
                    postulacion_id=p_id,
                    evaluador_user_id=BOOTSTRAP_ADMIN_ID,
                    dim1_disponibilidad="2 semanas",
                    dim2_resumen_tecnico=f"Perfil calificado en {perf} con sólidos fundamentos.",
                    dim3_expectativa_declarada=float(random.randint(5000, 9000)),
                    dim4_interes_vacante="Alto",
                    dim5_modalidad_aceptada="Híbrido",
                    dim6_viabilidad_traslado="Viable",
                    dim7_impresion_general="Excelente desenvolvimiento verbal.",
                    dictamen_humano="Avanza_Entrevista_Tecnica",
                )
                db.add(scr)

                ctc_id = f"ctc-{uuid.uuid4()}"
                bruto = float(random.randint(5000, 8500))
                ctc_eval = EvaluacionCTCModel(
                    id=ctc_id,
                    postulacion_id=p_id,
                    tipo_expectativa="Bruto",
                    monto_declarado=bruto,
                    salario_bruto_mensual=bruto,
                    factor_ctc=1.56,
                    ctc_solicitado=round(bruto * 1.56, 2),
                    ctc_presupuestado=12000.0,
                    variacion_porcentual=round(((bruto * 1.56 - 12000.0) / 12000.0) * 100, 2),
                    semaforo_presupuestal="Dentro_Presupuesto",
                    evaluado_por_user_id=BOOTSTRAP_ADMIN_ID,
                )
                db.add(ctc_eval)

        db.commit()
        total_final = db.query(CandidatoModel).count()
        print(f"[OK] Seeding historico completado exitosamente: {total_final} candidatos registrados en la BD corporativa.")


if __name__ == "__main__":
    seed_historical_pool()
