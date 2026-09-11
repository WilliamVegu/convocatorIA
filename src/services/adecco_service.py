"""Adecco payroll validation and batch import application service."""
from __future__ import annotations

import hashlib
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.adapters.adecco.excel_validator import ExcelAdeccoValidator
from src.services.deduplication_service import DeduplicationService
from src.services.alumni_service import AlumniService
from src.adapters.persistence.repositories.candidato_repository import CandidatoRepository
from src.adapters.persistence.repositories.postulacion_repository import PostulacionRepository
from src.adapters.persistence.repositories.adecco_repository import AdeccoRepository
from src.services.audit_service import AuditService
from src.domain.value_objects import TelefonoE164, DocumentoIdentidad
from src.services.candidate_service import normalize_full_name


class AdeccoService:
    """Service governing algorithmic payroll validation, traffic lights, and atomic batch intake."""

    def __init__(
        self,
        candidato_repo: CandidatoRepository,
        postulacion_repo: PostulacionRepository,
        adecco_repo: AdeccoRepository,
        dedup_service: DeduplicationService,
        alumni_service: AlumniService,
        audit_service: AuditService,
        excel_validator: Optional[ExcelAdeccoValidator] = None,
    ):
        self.candidato_repo = candidato_repo
        self.postulacion_repo = postulacion_repo
        self.adecco_repo = adecco_repo
        self.dedup_service = dedup_service
        self.alumni_service = alumni_service
        self.audit_service = audit_service
        self.excel_validator = excel_validator or ExcelAdeccoValidator()

    def evaluate_spreadsheet(
        self,
        file_bytes: bytes,
        filename: str,
        actor_user_id: str,
        actor_email: str,
        actor_role: str,
    ) -> Dict[str, Any]:
        """Evaluate payroll file and categorize each row into semaphore categories."""
        start_time = time.perf_counter()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        parsed = self.excel_validator.parse_spreadsheet(file_bytes, filename)
        rows = parsed["rows"]

        total_rojos = 0
        total_amarillos = 0
        total_verdes = 0
        total_alumni = 0

        evaluated_items: List[Dict[str, Any]] = []

        for row in rows:
            doc_raw = row.get("documento_raw")
            phone_raw = row.get("telefono_raw")
            email_raw = row.get("email_raw")
            name_raw = row.get("nombres_raw") or "Candidato Desconocido"
            perfil_raw = row.get("perfil_raw") or "Perfil General"

            # 1. Check Boomerang (Alumni TCS)
            alumni_res = self.alumni_service.detect_alumni(
                dni=doc_raw,
                email=email_raw,
                nombre_completo=name_raw,
            )
            is_alumni = alumni_res["is_alumni"]
            if is_alumni:
                total_alumni += 1

            # 2. Check Deduplication against ATS database
            dedup_res = self.dedup_service.check_duplicate(
                dni=doc_raw,
                telefono=phone_raw,
                email=email_raw,
                nombre_completo=name_raw,
            )

            color = "Verde"
            categoria = "Verde_Limpio"
            detalle = "Perfil limpio sin antecedentes; listo para importación."

            if dedup_res["is_duplicate"]:
                existing_cand = dedup_res.get("existing_candidate")
                # Look up recent application
                postulaciones = self.postulacion_repo.get_by_candidato(existing_cand.id) if existing_cand else []
                latest_post = postulaciones[0] if postulaciones else None

                if latest_post:
                    # Check permanent exclusion
                    if latest_post.motivo_cierre_tipo == "Excluyente_Permanente":
                        color = "Rojo"
                        categoria = "Rojo_Exclusion_Permanente"
                        detalle = f"Exclusión permanente por antecedentes institucionales ({latest_post.motivo_cierre_detalle or 'Compliance/Ética'}). Prohibida importación."
                        total_rojos += 1
                    elif latest_post.estado_embudo in {"Contratado", "Pendiente_Entrevistas", "Screening_Telefonico", "Entrevista_Cliente", "Oferta_Economica", "Oferta_Aceptada", "Pendiente_Envio_Cliente"}:
                        color = "Rojo"
                        categoria = "Rojo_Duplicado_Activo"
                        detalle = f"Proceso activo en curso para cliente '{latest_post.cliente_cuenta}' (Estado: {latest_post.estado_embudo})."
                        total_rojos += 1
                    else:
                        # Check 180 days
                        dias_cierre = 999
                        if latest_post.fecha_cierre_descarte:
                            # ensure timezone
                            dt = latest_post.fecha_cierre_descarte
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            dias_cierre = (datetime.now(timezone.utc) - dt).days

                        if dias_cierre < 180:
                            color = "Rojo"
                            categoria = "Rojo_Duplicado_Activo"
                            detalle = f"Descarte reciente ({dias_cierre} días < 180 días de vigencia normativa) en cuenta '{latest_post.cliente_cuenta}'."
                            total_rojos += 1
                        else:
                            color = "Amarillo"
                            categoria = "Amarillo_Reactivable"
                            detalle = f"Reactivable: Descarte hace {dias_cierre} días (>180 días) con motivo no excluyente. Elegible para nueva vacante."
                            total_amarillos += 1
                else:
                    # Candidate exists in DB without applications
                    color = "Rojo"
                    categoria = "Rojo_Duplicado_Activo"
                    detalle = f"Candidato ya registrado en la base corporativa (Coincidencia por {dedup_res['matched_field']})."
                    total_rojos += 1
            else:
                total_verdes += 1

            evaluated_items.append({
                "fila_index": row["fila_original_index"],
                "documento": doc_raw,
                "nombres": name_raw,
                "telefono": phone_raw,
                "email": email_raw,
                "perfil": perfil_raw,
                "color_semaforo": color,
                "categoria": categoria,
                "detalle_clasificacion": detalle,
                "is_alumni": is_alumni,
                "alumni_estatus": alumni_res.get("estatus_recontratacion"),
                "bloquear_comision": is_alumni,
            })

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        lote_id = f"lot-{uuid.uuid4()}"

        # Persist audit record for the uploaded batch
        self.adecco_repo.create_lote(
            lote_id=lote_id,
            usuario_carga_id=actor_user_id,
            nombre_archivo_original=filename,
            hash_archivo_sha256=file_hash,
            total_filas=len(evaluated_items),
            cantidad_rojos_duplicados=total_rojos,
            cantidad_amarillos_reactivables=total_amarillos,
            cantidad_verdes_limpios=total_verdes,
            cantidad_alumni_detectados=total_alumni,
            estado_procesamiento="Completado",
        )

        self.audit_service.record_file_upload(
            usuario_id=actor_user_id,
            usuario_email=actor_email,
            rol_en_momento=actor_role,
            entidad_objeto="Planilla_Adecco",
            registro_id=lote_id,
            nombre_archivo=filename,
            hash_sha256=file_hash,
        )

        return {
            "lote_id": lote_id,
            "filename": filename,
            "file_hash_sha256": file_hash,
            "total_filas": len(evaluated_items),
            "total_rojos": total_rojos,
            "total_amarillos": total_amarillos,
            "total_verdes": total_verdes,
            "total_alumni": total_alumni,
            "tiempo_procesamiento_ms": duration_ms,
            "items": evaluated_items,
        }

    def import_clean_candidates(
        self,
        lote_id: str,
        items_to_import: List[Dict[str, Any]],
        actor_user_id: str,
        actor_email: str,
        actor_role: str,
        cliente_cuenta: str,
        rgs_vacante_id: str,
        perfil_tecnico: str,
    ) -> int:
        """Atomically import green clean candidates into candidates and applications tables."""
        session = self.candidato_repo.session
        imported_count = 0

        try:
            for item in items_to_import:
                doc_raw = item.get("documento")
                nombres_raw = item.get("nombres") or "Postulante Adecco"
                phone_raw = item.get("telefono") or "999999999"
                email_raw = item.get("email") or f"{doc_raw}@adecco-import.pe"

                # Parse names
                name_parts = nombres_raw.strip().split()
                if len(name_parts) >= 3:
                    nombres = " ".join(name_parts[:-2])
                    paterno = name_parts[-2]
                    materno = name_parts[-1]
                elif len(name_parts) == 2:
                    nombres = name_parts[0]
                    paterno = name_parts[1]
                    materno = ""
                else:
                    nombres = name_parts[0]
                    paterno = "NoEspecificado"
                    materno = ""

                try:
                    e164 = str(TelefonoE164(phone_raw))
                except Exception:
                    e164 = f"+51{phone_raw[:9].zfill(9)}"

                cand_id = f"cand-{uuid.uuid4()}"
                cand = self.candidato_repo.create(
                    candidato_id=cand_id,
                    tipo_documento="DNI" if len(doc_raw) == 8 and doc_raw.isdigit() else "CE",
                    numero_documento=doc_raw,
                    nombres=nombres,
                    apellido_paterno=paterno,
                    apellido_materno=materno,
                    nombres_completos_normalizado=normalize_full_name(nombres_raw),
                    telefono_e164=e164,
                    email=email_raw.lower(),
                    is_tcs_alumni=item.get("is_alumni", False),
                    created_by_user_id=actor_user_id,
                )

                post_id = f"post-{uuid.uuid4()}"
                self.postulacion_repo.create_postulacion(
                    postulacion_id=post_id,
                    candidato_id=cand.id,
                    cliente_cuenta=cliente_cuenta,
                    rgs_vacante_id=rgs_vacante_id,
                    perfil_tecnico=perfil_tecnico,
                    reclutador_asignado_id=actor_user_id,
                    fuente_origen="Adecco",
                    trimestre_fiscal="FY27-Q1",
                    created_by_user_id=actor_user_id,
                    estado_embudo="Nuevo",
                )
                imported_count += 1

            session.commit()
            return imported_count

        except Exception as e:
            session.rollback()
            # Update lote status to Fallido_Rollback
            lote = self.adecco_repo.get_lote_by_id(lote_id)
            if lote:
                lote.estado_procesamiento = "Fallido_Rollback"
                session.commit()
            raise RuntimeError(f"Fallo en importación atómica del lote Adecco; rollback ejecutado: {e}")
