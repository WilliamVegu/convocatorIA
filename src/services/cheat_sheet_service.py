"""Technical Cheat Sheet generator service for non-technical recruiters conducting phone screening."""
from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
from src.domain.entities import CheatSheet, CheatSheetPregunta
from src.config import config
from src.logger import logger


# Curated question bank with expected concepts for non-technical recruiters
ROLE_QUESTION_BANK: Dict[str, List[Dict[str, str]]] = {
    "Desarrollador Java Senior": [
        {
            "pregunta": "¿Cómo manejas la tolerancia a fallos y Circuit Breaker en microservicios Spring Boot?",
            "concepto_clave": "Resilience4j / Hystrix / Fallback",
            "respuesta_esperada": "Debe mencionar Resilience4j o Hystrix, explicar que aísla servicios caídos y define un método fallback de respaldo para evitar caídas en cascada.",
            "criterio_evaluacion": "Aprobado si menciona Resilience4j o el concepto de circuito abierto/cerrado.",
        },
        {
            "pregunta": "¿Cuál es la diferencia entre `@Transactional` por defecto y con aislamiento `SERIALIZABLE`?",
            "concepto_clave": "Propagación, Aislamiento ACID, Dirty Reads",
            "respuesta_esperada": "Debe explicar que el aislamiento previene lecturas sucias (dirty reads) o no repetibles a costa de mayor bloqueo en base de datos.",
            "criterio_evaluacion": "Aprobado si demuestra entendimiento de concurrencia y bloqueos en base de datos.",
        },
        {
            "pregunta": "¿Cómo garantizas la idempotencia al procesar eventos asíncronos con Apache Kafka?",
            "concepto_clave": "Idempotent Producer, Offset commit, Deduplicación por Clave/ID",
            "respuesta_esperada": "Debe mencionar claves de mensaje únicas, configuración enable.idempotence=true, o almacenamiento de ID procesados para evitar duplicados.",
            "criterio_evaluacion": "Aprobado si sabe que un evento puede recibirse más de una vez (at-least-once).",
        },
    ],
    "Data Engineer": [
        {
            "pregunta": "¿En Apache Spark, qué diferencia hay entre una transformación 'narrow' y una 'wide'?",
            "concepto_clave": "Shuffle de datos, particiones de red",
            "respuesta_esperada": "En transformaciones narrow (como map o filter) los datos no cruzan particiones; en wide (como groupByKey o join) se requiere 'shuffle' de red.",
            "criterio_evaluacion": "Aprobado si menciona 'shuffle' o movimiento de datos entre nodos.",
        },
        {
            "pregunta": "¿Cómo gestionas la carga incremental (CDC) en un Data Lake o Data Warehouse?",
            "concepto_clave": "Change Data Capture (Debezium/Kafka), Watermark, Upsert / Merge",
            "respuesta_esperada": "Debe explicar que se identifican deltas mediante timestamps o logs de base de datos y se ejecuta un MERGE en tablas Delta/Iceberg.",
            "criterio_evaluacion": "Aprobado si distingue carga completa (full load) de carga incremental.",
        },
        {
            "pregunta": "¿Qué estrategias utilizas para optimizar queries lentas en Snowflake o Redshift?",
            "concepto_clave": "Clustering keys, Distribution / Sort keys, Evitar escaneo completo",
            "respuesta_esperada": "Debe mencionar clustering de particiones, ordenamiento de llaves y compresión columnar.",
            "criterio_evaluacion": "Aprobado si menciona reducción del volumen de particiones escaneadas.",
        },
    ],
    "DevOps Specialist": [
        {
            "pregunta": "¿Qué diferencia existe entre un Deployment y un StatefulSet en Kubernetes?",
            "concepto_clave": "Persistencia de volumen, nombres de pod predecibles",
            "respuesta_esperada": "Deployments son para aplicaciones stateless (sin estado); StatefulSets mantienen identidad única de pod y volúmenes persistentes ordenados (ej. bases de datos).",
            "criterio_evaluacion": "Aprobado si menciona que StatefulSet es para persistencia y nombres ordenados.",
        },
        {
            "pregunta": "¿Cómo gestionas el estado (`tfstate`) en Terraform cuando trabajas en equipo?",
            "concepto_clave": "Remote State Backend (S3 + DynamoDB Lock / Azure Blob)",
            "respuesta_esperada": "Debe guardarse en un backend remoto seguro con state locking (bloqueo) para evitar que dos personas modifiquen la infraestructura a la vez.",
            "criterio_evaluacion": "Aprobado si menciona backend remoto y bloqueo (locking).",
        },
        {
            "pregunta": "¿Qué estrategia de despliegue utilizas para evitar downtime (Canary vs Blue/Green)?",
            "concepto_clave": "Blue/Green (dos ambientes idénticos), Canary (tráfico gradual 5%-10%)",
            "respuesta_esperada": "Blue/Green conmuta el tráfico 100% de golpe tras pruebas; Canary envía un porcentaje pequeño (5-10%) para detectar anomalías antes de migrar todo.",
            "criterio_evaluacion": "Aprobado si explica claramente la diferencia de enrutamiento.",
        },
    ],
    "Full Stack Developer": [
        {
            "pregunta": "¿En React, en qué caso utilizarías `useMemo` o `useCallback`?",
            "concepto_clave": "Memoización de cálculos costosos, estabilidad de referencias en props",
            "respuesta_esperada": "Para evitar recálculos computacionalmente pesados o evitar re-renderizados innecesarios de componentes hijos memoizados (`React.memo`).",
            "criterio_evaluacion": "Aprobado si aclara que no debe usarse para todo, sino cuando hay costo medible.",
        },
        {
            "pregunta": "¿Cómo aseguras una API REST contra ataques CSRF y qué ventaja tiene usar JWT?",
            "concepto_clave": "SameSite Cookies, Bearer Tokens en headers, Sin estado (stateless)",
            "respuesta_esperada": "JWT en Authorization header (Bearer) no sufre CSRF nativo de cookies; es stateless y contiene claims firmados criptográficamente.",
            "criterio_evaluacion": "Aprobado si comprende que el token viaja en header y valida la firma.",
        },
    ],
}


class CheatSheetService:
    """Generates 3-4 targeted questions with expected concepts and scoring criteria."""

    def generate_cheat_sheet(
        self,
        postulacion_id: str,
        perfil_puesto: str,
        cv_text: str = "",
        skills: Optional[List[str]] = None,
    ) -> CheatSheet:
        """Generate tailored questions crossing vacancy profile with candidate background."""
        # 1. Check if LLM is available for bespoke tailored generation
        if config.GEMINI_API_KEY and cv_text:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model="gemini-3.8-flash",
                    google_api_key=config.GEMINI_API_KEY,
                )
                return self._generate_with_llm(llm, postulacion_id, perfil_puesto, cv_text)
            except Exception as e:
                logger.warning(f"Error generando CheatSheet con LLM: {e}. Usando banco calibrado.")

        # 2. Fallback to calibrated technical bank
        preguntas_raw = ROLE_QUESTION_BANK.get(
            perfil_puesto,
            [
                {
                    "pregunta": f"¿Cómo ha sido tu experiencia técnica implementando soluciones en {perfil_puesto}?",
                    "concepto_clave": "Arquitectura, Buenas prácticas, Pruebas unitarias",
                    "respuesta_esperada": "Debe explicar proyectos reales de producción, decisiones de diseño y metodologías de trabajo.",
                    "criterio_evaluacion": "Aprobado si demuestra experiencia práctica y no solo teórica.",
                },
                {
                    "pregunta": "¿Cómo manejas el versionamiento, ramas y CI/CD en tu equipo actual?",
                    "concepto_clave": "Gitflow, Trunk-based, Pipelines automatizados",
                    "respuesta_esperada": "Debe describir su flujo de Pull Requests, code review y despliegue continuo.",
                    "criterio_evaluacion": "Aprobado si está habituado a trabajar con integración continua.",
                },
                {
                    "pregunta": "¿Cuál ha sido el reto de rendimiento o bug más complejo que resolviste y cómo lo diagnosticaste?",
                    "concepto_clave": "Profiling, Logs estructurados, Monitoreo (APM)",
                    "respuesta_esperada": "Debe explicar el problema técnico con causa raíz y herramientas de diagnóstico.",
                    "criterio_evaluacion": "Aprobado si tiene capacidad de resolución estructurada de incidentes.",
                },
            ],
        )

        items = [
            CheatSheetPregunta(
                pregunta=p["pregunta"],
                concepto_clave=p["concepto_clave"],
                respuesta_esperada=p["respuesta_esperada"],
                criterio_evaluacion=p["criterio_evaluacion"],
            )
            for p in preguntas_raw
        ]

        return CheatSheet(
            postulacion_id=postulacion_id,
            perfil=perfil_puesto,
            preguntas=items,
        )

    def _generate_with_llm(
        self,
        llm: Any,
        postulacion_id: str,
        perfil_puesto: str,
        cv_text: str,
    ) -> CheatSheet:
        """Query LLM for dynamic tailored screening questions."""
        prompt = (
            f"Eres el Líder Técnico de TCS para la cuenta. La vacante es '{perfil_puesto}'.\n"
            "Diseña 3 preguntas técnicas directas para la reclutadora de RRHH (quien no es ingeniera).\n"
            "Para cada pregunta, proporciona el concepto clave y qué respuesta exacta debe dar el candidato para aprobar.\n"
            "Devuelve ÚNICAMENTE un JSON con formato:\n"
            "{\n"
            '  "preguntas": [\n'
            "    {\n"
            '      "pregunta": "¿Cómo manejas ...?",\n'
            '      "concepto_clave": "Resilience4j / Circuit Breaker",\n'
            '      "respuesta_esperada": "Debe mencionar...",\n'
            '      "criterio_evaluacion": "Aprobado si..."\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"Resumen CV candidato:\n{cv_text[:2500]}"
        )
        try:
            resp = llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            if isinstance(content, list):
                content = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content])
            import json
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", str(content), re.DOTALL)
            raw = match.group(1) if match else str(content)
            data = json.loads(raw)
            items = [
                CheatSheetPregunta(
                    pregunta=p["pregunta"],
                    concepto_clave=p["concepto_clave"],
                    respuesta_esperada=p["respuesta_esperada"],
                    criterio_evaluacion=p.get("criterio_evaluacion", "Aprobado si menciona conceptos"),
                )
                for p in data.get("preguntas", [])
            ]
            if items:
                return CheatSheet(postulacion_id=postulacion_id, perfil=perfil_puesto, preguntas=items)
        except Exception as e:
            logger.warning(f"Error parseando preguntas LLM: {e}")

        return self.generate_cheat_sheet(postulacion_id, perfil_puesto)
