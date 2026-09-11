import re
import sqlite3
import pytest


@pytest.fixture
def db_conn():
    with open("specs/001-ats-core-mvp/data-model.md", "r", encoding="utf-8") as f:
        content = f.read()

    sql_match = re.search(r"```sql\n(.*?)\n```", content, re.DOTALL)
    assert sql_match, "DDL SQL block not found in data-model.md"
    sql_ddl = sql_match.group(1)

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    cursor.executescript(sql_ddl)
    yield conn
    conn.close()


def test_ddl_creates_all_11_tables(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    expected_tables = {
        "usuarios_rbac",
        "historial_alumni_tcs",
        "candidatos",
        "postulaciones_procesos",
        "screening_tecnico",
        "evaluacion_financiera_ctc",
        "compliance_verificaciones",
        "lotes_planilla_adecco",
        "reportes_cartera_exclusiones",
        "bitacora_auditoria",
        "cache_dni_reniec",
    }
    assert expected_tables.issubset(set(tables))


def test_ddl_bootstrap_admin_seed_inserted(db_conn):
    cursor = db_conn.cursor()
    cursor.execute("SELECT email, rol, estado_cuenta FROM usuarios_rbac WHERE email = 'admin.ta@tcs.com'")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "admin.ta@tcs.com"
    assert row[1] == "Head_of_Talent_Acquisition"
    assert row[2] == "Activa"


def test_ddl_bitacora_immutability_triggers(db_conn):
    cursor = db_conn.cursor()

    # Attempting UPDATE on bitacora_auditoria must fail with IntegrityError
    with pytest.raises(sqlite3.IntegrityError, match="Violacion de Integridad.*inmutable"):
        cursor.execute("UPDATE bitacora_auditoria SET usuario_email = 'tampered@tcs.com'")

    # Attempting DELETE on bitacora_auditoria must fail with IntegrityError
    with pytest.raises(sqlite3.IntegrityError, match="Violacion de Integridad.*eliminacion"):
        cursor.execute("DELETE FROM bitacora_auditoria")


def test_ddl_foreign_key_enforcement(db_conn):
    cursor = db_conn.cursor()
    # Inserting candidate with non-existent created_by_user_id must fail
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
        INSERT INTO candidatos (
            id, tipo_documento, numero_documento, nombres, apellido_paterno,
            nombres_completos_normalizado, telefono_e164, email, created_by_user_id
        ) VALUES (
            'c-fk-test', 'DNI', '99887766', 'Pedro', 'Ruiz',
            'PEDRO RUIZ', '+51999111222', 'pedro.ruiz@gmail.com', 'non-existent-user-id'
        )
        """)


def test_ddl_estado_embudo_check_constraint(db_conn):
    cursor = db_conn.cursor()
    # Insert candidate first
    cursor.execute("""
    INSERT INTO candidatos (
        id, tipo_documento, numero_documento, nombres, apellido_paterno,
        nombres_completos_normalizado, telefono_e164, email, created_by_user_id
    ) VALUES (
        'c-valid', 'DNI', '55667788', 'Maria', 'Flores',
        'MARIA FLORES', '+51988776655', 'maria.flores@gmail.com', 'usr-admin-bootstrap-001'
    )
    """)

    # Invalid state must fail
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: chk_postulacion_estado"):
        cursor.execute("""
        INSERT INTO postulaciones_procesos (
            id, candidato_id, cliente_cuenta, rgs_vacante_id, perfil_tecnico,
            reclutador_asignado_id, fuente_origen, trimestre_fiscal, estado_embudo, created_by_user_id
        ) VALUES (
            'p-bad', 'c-valid', 'BCP', 'RGS-001', 'Developer',
            'usr-admin-bootstrap-001', 'Adecco', 'FY27-Q1', 'Estado_Invalido_Total', 'usr-admin-bootstrap-001'
        )
        """)
