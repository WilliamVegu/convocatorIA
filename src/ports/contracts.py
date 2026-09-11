"""Proxy module to import schemas and constants from specs/001-ats-core-mvp/contracts."""
import importlib

_contracts = importlib.import_module("specs.001-ats-core-mvp.contracts")

ADECCO_COLUMN_ALIASES = _contracts.ADECCO_COLUMN_ALIASES
CarteraExclusionRow5Col = _contracts.CarteraExclusionRow5Col
AdeccoBatchSummary = _contracts.AdeccoBatchSummary
SemaforoClasificacionEnum = _contracts.SemaforoClasificacionEnum
MotivoExclusionEnum = _contracts.MotivoExclusionEnum

CTCCalculationInput = _contracts.CTCCalculationInput
CTCCalculationResult = _contracts.CTCCalculationResult
calculate_ctc = _contracts.calculate_ctc

DNIRequest = _contracts.DNIRequest
DNIResponseData = _contracts.DNIResponseData
DNIValidationResult = _contracts.DNIValidationResult

CVExtractionResult = _contracts.CVExtractionResult
CVUploadMetadata = _contracts.CVUploadMetadata

UserRegistrationRequest = _contracts.UserRegistrationRequest
SessionPayload = _contracts.SessionPayload
AuditSearchFilter = _contracts.AuditSearchFilter
