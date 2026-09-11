"""Database seeding and bootstrap initialization for ATS Core MVP."""
from __future__ import annotations

import json
from datetime import datetime, date, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.adapters.persistence.models import (
    UsuarioModel,
    BitacoraAuditoriaModel,
    HistorialAlumniModel,
    CandidatoModel,
    PostulacionModel,
    CacheDNIReniecModel,
)
from src.adapters.security.password_hasher import hash_password

BOOTSTRAP_ADMIN_ID = "usr-admin-bootstrap-001"
BOOTSTRAP_ADMIN_EMAIL = "admin.ta@tcs.com"
BOOTSTRAP_PASSWORD_HASH = "$2b$10$tWCu/Q2bgbrav6OqZKxHEOcsOR269cc0Qh2axuaUlEp45DB7rq20y"  # Password123!


def seed_database(session: Session) -> None:
    """Idempotently seed bootstrap administrator and essential baseline data."""
    # 1. Bootstrap Admin
    admin = session.execute(
        select(UsuarioModel).where(UsuarioModel.email == BOOTSTRAP_ADMIN_EMAIL)
    ).scalar_one_or_none()

    if not admin:
        admin = UsuarioModel(
            id=BOOTSTRAP_ADMIN_ID,
            nombres_completos="Administrador Central Talent Acquisition",
            email=BOOTSTRAP_ADMIN_EMAIL,
            hashed_password=BOOTSTRAP_PASSWORD_HASH,
            rol="Head_of_Talent_Acquisition",
            estado_cuenta="Activa",
            intentos_fallidos=0,
            record_version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(admin)
        session.flush()

        # Audit initial seat
        audit_entry = BitacoraAuditoriaModel(
            id="aud-boot-001",
            usuario_id=BOOTSTRAP_ADMIN_ID,
            usuario_email=BOOTSTRAP_ADMIN_EMAIL,
            rol_en_momento="Head_of_Talent_Acquisition",
            tipo_accion="Creacion",
            entidad_objeto="Usuario",
            registro_id=BOOTSTRAP_ADMIN_ID,
            version_registro=1,
            valores_nuevos_json=json.dumps(
                {"email": BOOTSTRAP_ADMIN_EMAIL, "rol": "Head_of_Talent_Acquisition", "estado": "Activa"}
            ),
            justificacion_operativa="Inicializacion de cuenta fundacional Head of Talent Acquisition",
            ip_address="127.0.0.1",
            timestamp=datetime.now(timezone.utc),
        )
        session.add(audit_entry)

    # 2. Add Standard Demo Users if not present
    demo_users = [
        (
            "usr-recruiter-001",
            "Senior Technical Recruiter Demo",
            "recruiter.lead@tcs.com",
            "Senior_Technical_Recruiter",
        ),
        (
            "usr-coordinator-001",
            "Account Recruitment Coordinator Demo",
            "coordinator.tcs@tcs.com",
            "Account_Recruitment_Coordinator",
        ),
        (
            "usr-compliance-001",
            "Compliance Officer Demo",
            "compliance.officer@tcs.com",
            "Compliance_Officer",
        ),
    ]

    for uid, name, email, rol in demo_users:
        existing = session.execute(
            select(UsuarioModel).where(UsuarioModel.email == email)
        ).scalar_one_or_none()
        if not existing:
            u = UsuarioModel(
                id=uid,
                nombres_completos=name,
                email=email,
                hashed_password=BOOTSTRAP_PASSWORD_HASH,
                rol=rol,
                estado_cuenta="Activa",
                intentos_fallidos=0,
                autorizado_por_id=BOOTSTRAP_ADMIN_ID,
                record_version=1,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(u)

    # 3. Add Sample Alumni TCS
    sample_alumni = [
        HistorialAlumniModel(
            id="alm-001",
            tipo_documento="DNI",
            numero_documento="46753314",
            nombres_completos="CARLOS EDUARDO GARCIA SANCHEZ",
            nombres_normalizado="CARLOS EDUARDO GARCIA SANCHEZ",
            email_corporativo_historico="carlos.garcia1@tcs.com",
            fecha_ingreso=date(2021, 3, 1),
            fecha_cese=date(2024, 5, 30),
            ultima_cuenta_proyecto="BCP Home Banking",
            motivo_desvinculacion="Renuncia Voluntaria - Mejor Oferta",
            estatus_recontratacion="Rehire_Eligible",
        ),
        HistorialAlumniModel(
            id="alm-002",
            tipo_documento="DNI",
            numero_documento="10293847",
            nombres_completos="ROBERTO CARLOS DIAZ MENDOZA",
            nombres_normalizado="ROBERTO CARLOS DIAZ MENDOZA",
            email_corporativo_historico="roberto.diaz@tcs.com",
            fecha_ingreso=date(2020, 1, 15),
            fecha_cese=date(2023, 8, 15),
            ultima_cuenta_proyecto="Banco Falabella Core",
            motivo_desvinculacion="Despido con Causa - Falta Grave de Seguridad",
            estatus_recontratacion="Do_Not_Rehire",
        ),
    ]

    for alm in sample_alumni:
        exists_alm = session.execute(
            select(HistorialAlumniModel).where(
                HistorialAlumniModel.numero_documento == alm.numero_documento
            )
        ).scalar_one_or_none()
        if not exists_alm:
            session.add(alm)

    # 4. Add Baseline RENIEC cache records for offline testing
    cached_dnis = [
        CacheDNIReniecModel(
            dni="76128709",
            nombres="DIEGO ALONSO",
            apellido_paterno="RAMOS",
            apellido_materno="QUISPE",
            fecha_nacimiento=date(1995, 4, 12),
            ubigeo="150140",
            distrito="Santiago de Surco",
            direccion="Av. Caminos del Inca 1234",
        ),
        CacheDNIReniecModel(
            dni="46753314",
            nombres="CARLOS EDUARDO",
            apellido_paterno="GARCIA",
            apellido_materno="SANCHEZ",
            fecha_nacimiento=date(1991, 7, 24),
            ubigeo="150130",
            distrito="San Borja",
            direccion="Calle Las Artes 567",
        ),
        CacheDNIReniecModel(
            dni="72345678",
            nombres="ANA LUCIA",
            apellido_paterno="QUISPE",
            apellido_materno="MENDOZA",
            fecha_nacimiento=date(1998, 11, 3),
            ubigeo="150119",
            distrito="Los Olivos",
            direccion="Av. Antúnez de Mayolo 890",
        ),
    ]

    for c in cached_dnis:
        exists_c = session.execute(
            select(CacheDNIReniecModel).where(CacheDNIReniecModel.dni == c.dni)
        ).scalar_one_or_none()
        if not exists_c:
            session.add(c)

    session.commit()
