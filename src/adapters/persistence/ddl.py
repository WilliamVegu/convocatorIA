"""DDL and trigger management for ATS Core MVP."""
from __future__ import annotations

from pathlib import Path
import re
from sqlalchemy import text
from sqlalchemy.engine import Engine, Connection

IMMUTABILITY_TRIGGERS_SQLITE = """
CREATE TRIGGER IF NOT EXISTS trg_prevent_update_bitacora
BEFORE UPDATE ON bitacora_auditoria
BEGIN
    SELECT RAISE(ABORT, 'Violacion de Integridad: La bitacora de auditoria es estrictamente inmutable y de solo adicion (append-only).');
END;

CREATE TRIGGER IF NOT EXISTS trg_prevent_delete_bitacora
BEFORE DELETE ON bitacora_auditoria
BEGIN
    SELECT RAISE(ABORT, 'Violacion de Integridad: Prohibida la eliminacion de registros historicos en la bitacora de auditoria.');
END;
"""


def get_full_ddl_sql() -> str:
    """Read DDL SQL from specs/001-ats-core-mvp/data-model.md if available, or return canonical DDL."""
    data_model_path = Path(__file__).resolve().parent.parent.parent.parent / "specs" / "001-ats-core-mvp" / "data-model.md"
    if data_model_path.exists():
        content = data_model_path.read_text(encoding="utf-8")
        match = re.search(r"```sql\n(.*?)\n```", content, re.DOTALL)
        if match:
            return match.group(1)
    raise FileNotFoundError(f"data-model.md not found at {data_model_path}")


def install_immutability_triggers(target: Engine | Connection) -> None:
    """Install physical triggers preventing UPDATE and DELETE on bitacora_auditoria."""
    statements = [
        """
        CREATE TRIGGER IF NOT EXISTS trg_prevent_update_bitacora
        BEFORE UPDATE ON bitacora_auditoria
        BEGIN
            SELECT RAISE(ABORT, 'Violacion de Integridad: La bitacora de auditoria es estrictamente inmutable y de solo adicion (append-only).');
        END;
        """,
        """
        CREATE TRIGGER IF NOT EXISTS trg_prevent_delete_bitacora
        BEFORE DELETE ON bitacora_auditoria
        BEGIN
            SELECT RAISE(ABORT, 'Violacion de Integridad: Prohibida la eliminacion de registros historicos en la bitacora de auditoria.');
        END;
        """
    ]

    if isinstance(target, Engine):
        with target.connect() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
            conn.commit()
    else:
        for stmt in statements:
            target.execute(text(stmt))
