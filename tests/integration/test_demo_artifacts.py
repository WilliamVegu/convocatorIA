"""Integration tests for Phase 5 demo seed data and artifacts."""
import json
from pathlib import Path
import pandas as pd
import pytest

from src.adapters.persistence.database import SessionLocal, init_db
from src.adapters.persistence.models import CandidatoModel, CacheDNIReniecModel, HistorialAlumniModel
from scripts.seed_historical_data import seed_historical_pool


def test_demo_personas_json_integrity():
    personas_path = Path("data/demo_personas.json")
    assert personas_path.exists(), "data/demo_personas.json must exist"

    with open(personas_path, "r", encoding="utf-8") as f:
        personas = json.load(f)

    assert len(personas) >= 15
    for p in personas:
        assert "dni" in p
        assert len(p["dni"]) == 8
        assert p["dni"].isdigit()
        assert "nombres" in p
        assert "apellido_paterno" in p
        assert "fecha_nacimiento" in p
        assert "distrito" in p


def test_adecco_excel_sample_structure():
    excel_path = Path("data/Adecco_Semana_37.xlsx")
    assert excel_path.exists(), "data/Adecco_Semana_37.xlsx must exist"

    df = pd.read_excel(excel_path)
    assert len(df) == 20, f"Expected exactly 20 rows, got {len(df)}"

    # Check alias headers presence
    cols = list(df.columns)
    assert any("dni" in c.lower() or "documento" in c.lower() for c in cols)
    assert any("nombre" in c.lower() for c in cols)
    assert any("móvil" in c.lower() or "movil" in c.lower() or "celular" in c.lower() or "telefono" in c.lower() for c in cols)
    assert any("puesto" in c.lower() or "perfil" in c.lower() for c in cols)


def test_run_demo_bat_exists():
    bat_path = Path("run_demo.bat")
    assert bat_path.exists(), "run_demo.bat launcher must exist"
    content = bat_path.read_text(encoding="utf-8")
    assert "streamlit run" in content
    assert "seed_historical_data.py" in content


def test_historical_seeder_execution():
    # Verify historical seeder runs and populates >= 100 candidates
    seed_historical_pool(total_target=105)
    with SessionLocal() as db:
        count_cands = db.query(CandidatoModel).count()
        assert count_cands >= 100, f"Expected >= 100 candidates, found {count_cands}"

        count_cache = db.query(CacheDNIReniecModel).count()
        assert count_cache >= 3

        count_alumni = db.query(HistorialAlumniModel).count()
        assert count_alumni >= 2
