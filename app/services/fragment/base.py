from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class FragmentDeliveryStatus(StrEnum):
    PENDING = "delivery_pending"
    COMPLETED = "completed"
    FAILED = "delivery_failed"


class FragmentError(Exception):
    pass


@dataclass(frozen=True)
class FragmentDeliveryResult:
    status: str
    transaction_id: str | None = None
    is_success: bool = False
    is_retryable: bool = False
    raw: dict[str, Any] = field(default_factory=dict)
