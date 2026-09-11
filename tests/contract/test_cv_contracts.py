import importlib
import pytest
from datetime import date

contracts = importlib.import_module("specs.001-ats-core-mvp.contracts")


def test_cv_extraction_result_with_typed_idiomas():
    result = contracts.CVExtractionResult(
        resumen_profesional="Desarrollador Full Stack con 5 años de experiencia en Python y React",
        seniority_estimado=contracts.NivelSeniorityEnum.SENIOR,
        anios_experiencia_total=5.0,
        modalidad_preferida=contracts.ModalidadLaboralEnum.HIBRIDO,
        habilidades_tecnicas=[
            contracts.HabilidadTecnica(nombre="Python", categoria="Backend", anios_experiencia=5.0),
            contracts.HabilidadTecnica(nombre="FastAPI", categoria="Backend", anios_experiencia=3.0),
        ],
        experiencias_laborales=[
            contracts.ExperienciaLaboral(
                puesto="Senior Backend Engineer",
                empresa="Tech Solutions S.A.C.",
                fecha_inicio="01/2021",
                fecha_fin="Actualidad",
                tecnologias_utilizadas=["Python", "PostgreSQL", "Docker"],
            )
        ],
        certificaciones_educacion=[
            contracts.EducacionCertificacion(
                titulo="Ingeniería de Sistemas",
                institucion="Universidad Nacional de Ingeniería",
                anio_obtencion=2020,
            )
        ],
        idiomas=[
            contracts.IdiomaCompetencia(idioma="Inglés", nivel=contracts.IdiomaNivelEnum.AVANZADO),
            contracts.IdiomaCompetencia(idioma="Portugués", nivel=contracts.IdiomaNivelEnum.INTERMEDIO),
        ],
        motor_extraccion_usado="GEMINI_LANGCHAIN",
    )
    assert result.seniority_estimado == contracts.NivelSeniorityEnum.SENIOR
    assert len(result.idiomas) == 2
    assert result.idiomas[0].nivel == contracts.IdiomaNivelEnum.AVANZADO
    assert result.modalidad_preferida == contracts.ModalidadLaboralEnum.HIBRIDO


def test_cul_data_extracted():
    cul = contracts.CULDataExtracted(
        tiene_antecedentes_penales_policiales=False,
        trayectoria_formal_registros=["Empresa A (2020-2022)", "Empresa B (2022-2024)"],
        fecha_emision_cul=date(2026, 8, 15),
    )
    assert cul.tiene_antecedentes_penales_policiales is False
    assert len(cul.trayectoria_formal_registros) == 2


def test_cv_upload_metadata():
    meta = contracts.CVUploadMetadata(
        nombre_archivo_original="cv_diego_ramos.pdf",
        tamanio_bytes=245800,
        hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        mime_type="application/pdf",
        subido_por_user_id="usr-123",
    )
    assert meta.fecha_subida is not None
    assert meta.fecha_subida.tzinfo is not None
