"""Shared Pytest fixtures for ATS Core MVP."""
import pytest
from datetime import datetime, date, timezone
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session

from src.adapters.persistence.models import (
    Base,
    UsuarioModel,
    CandidatoModel,
    PostulacionModel,
    HistorialAlumniModel,
    CacheDNIReniecModel,
)
from src.adapters.persistence.ddl import install_immutability_triggers
from src.adapters.persistence.seed import seed_database


@pytest.fixture(scope="session")
def engine():
    """Create in-memory SQLite engine with PRAGMA foreign_keys = ON."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        cursor.close()

    Base.metadata.create_all(bind=eng)
    install_immutability_triggers(eng)
    return eng


@pytest.fixture
def db_session(engine):
    """Provide an isolated database session with rollback after test execution."""
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    # Seed baseline admin and test data for tests
    try:
        seed_database(session)
    except Exception:
        session.rollback()
        # If already seeded in this connection, proceed
        pass

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def admin_user(db_session: Session) -> UsuarioModel:
    """Fixture providing the Head of Talent Acquisition admin user."""
    user = db_session.query(UsuarioModel).filter_by(email="admin.ta@tcs.com").first()
    assert user is not None
    return user


@pytest.fixture
def recruiter_user(db_session: Session) -> UsuarioModel:
    """Fixture providing a Senior Technical Recruiter user."""
    user = db_session.query(UsuarioModel).filter_by(email="recruiter.lead@tcs.com").first()
    assert user is not None
    return user


@pytest.fixture
def compliance_user(db_session: Session) -> UsuarioModel:
    """Fixture providing a read-only Compliance Officer user."""
    user = db_session.query(UsuarioModel).filter_by(email="compliance.officer@tcs.com").first()
    assert user is not None
    return user


@pytest.fixture
def sample_candidate(db_session: Session, recruiter_user: UsuarioModel) -> CandidatoModel:
    """Fixture providing a persisted candidate profile."""
    cand = CandidatoModel(
        id="cand-fixture-001",
        tipo_documento="DNI",
        numero_documento="76128709",
        nombres="DIEGO ALONSO",
        apellido_paterno="RAMOS",
        apellido_materno="QUISPE",
        nombres_completos_normalizado="DIEGO ALONSO RAMOS QUISPE",
        telefono_e164="+51989322088",
        email="diego.ramos@test.com",
        fecha_nacimiento=date(1995, 4, 12),
        ubigeo="150140",
        departamento="Lima",
        provincia="Lima",
        distrito_residencia="Santiago de Surco",
        created_by_user_id=recruiter_user.id,
    )
    db_session.add(cand)
    db_session.flush()
    return cand
