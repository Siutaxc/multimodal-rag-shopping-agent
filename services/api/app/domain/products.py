"""Product-domain enums shared by ingestion, persistence, and HTTP schemas."""

from enum import StrEnum


class ProductCategory(StrEnum):
    """Supported deterministic headphone form factors."""

    IN_EAR = "in_ear"
    SEMI_IN_EAR = "semi_in_ear"
    OVER_EAR = "over_ear"
    ON_EAR = "on_ear"
    BONE_CONDUCTION = "bone_conduction"
    OPEN_EAR = "open_ear"


class IngestionStatus(StrEnum):
    """Terminal and non-terminal states of an ingestion run."""

    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class DocumentType(StrEnum):
    """Document classes created before retrieval indexes exist."""

    MAIN = "main"


class ReviewTopic(StrEnum):
    """Evidence topics available to later evidence-constrained retrieval."""

    ANC = "anc"
    COMFORT = "comfort"
    SOUND = "sound"
    MICROPHONE = "microphone"
    BATTERY = "battery"
    OTHER = "other"
